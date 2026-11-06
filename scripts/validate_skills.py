#!/usr/bin/env python3
"""Validate Agent Skill packaging and repository metadata.

Dependency-free checks:

* Every plugin root under ``plugins/<plugin>`` has a ``plugin.json`` and a
  ``skills/`` directory. Every ``skills/<name>/SKILL.md`` has parseable
  frontmatter with the required ``name`` and ``description`` fields, follows
  the Agent Skills naming rules, and warns when the body exceeds the
  recommended length. Frontmatter is parsed as a simple YAML mapping without
  external dependencies; unsupported constructs fail loudly instead of being
  silently truncated.
* Relative Markdown links and images in plugin skills and the README resolve,
  including angle-bracket destinations, reference definitions, and heading
  anchors. Bundle-absolute OKF links (``/path``) resolve when a bundle root (an
  ``index.md`` with ``okf_version``) is found, and are ignored otherwise. Links
  inside fenced and indented code blocks, HTML comments, URLs, template
  placeholders, and footnote definitions are ignored.
* Plugin manifests and ``.github/plugin/marketplace.json`` agree: every plugin
  is listed once, the marketplace source resolves to its plugin root, and the
  versions are lockstep. ``CHANGELOG.md`` has a section for that version, and
  concrete ``generated``/``author`` actor versions in skills match it.
* ``.sdlc/profile.json`` samples satisfy the profile contract, and
  ``evals/fixtures/**/verdict.md`` samples parse and recompute through
  ``evals/verdict.py``.

Run from the repository root:

    python3 scripts/validate_skills.py

Exits non-zero on error. Warnings do not fail the build.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from html import unescape
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(
    r"(?<!!)\[(?:[^\[\]]|\[[^\[\]]*\])*\]\(\s*"
    r"(<[^>\n]+>|[^)\s]+)(?:\s+\"[^\"]*\")?\s*\)"
)
IMAGE_RE = re.compile(
    r"!\[(?:[^\[\]]|\[[^\[\]]*\])*\]\(\s*"
    r"(<[^>\n]+>|[^)\s]+)(?:\s+\"[^\"]*\")?\s*\)"
)
REF_USE_RE = re.compile(r"(?<!!)\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\[([^\]]*)\]")
REF_DEF_RE = re.compile(
    r"^[ \t]*(?:>[ \t]*)*(?:(?:[-*+]|\d+\.)[ \t]+)?"
    r"\[(?!\^)([^\]]+)\]:[ \t]*(.*)$"
)
FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.S)
FENCE_OPEN_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
FENCE_CLOSE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})[ \t]*$")
PLACEHOLDER_RE = re.compile(r"^[A-Za-z0-9_-]+$")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
LIST_ITEM_RE = re.compile(r"^([ \t]*)((?:[-*+]|\d+[.)]))[ \t]+")
HEADING_RE = re.compile(r"(?m)^[ \t]{0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
SETEXT_HEADING_RE = re.compile(r"^[ \t]{0,3}(?:=+|-+)[ \t]*$")
HEADING_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
HTML_TAG_RE = re.compile(r"<[^>]*>")
SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
KEY_RE = re.compile(r"^([A-Za-z0-9_.-]+):(?:[ \t]*(.*))?$")
BLOCK_RE = re.compile(r"^[|>]([+-]?)[ \t]*(?:#.*)?$")
ACTOR_VERSION_RE = re.compile(
    r"(?:generated:\s*\{\s*by:|author:|\bby:)\s*([a-z0-9-]+)/(\d+\.\d+\.\d+)\b"
)
PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"

MAX_NAME = 64
MAX_DESCRIPTION = 1024
MAX_COMPATIBILITY = 500
MAX_BODY_LINES = 500

errors: list[str] = []
warnings: list[str] = []


class FrontmatterError(ValueError):
    """Raised when frontmatter is not a simple YAML mapping we can validate."""


def fail(message: str) -> None:
    errors.append(message)


def warn(message: str) -> None:
    warnings.append(message)


def read_frontmatter(path: Path) -> str | None:
    match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8-sig"))
    return match.group(1) if match else None


def _decode_escape(text: str, index: int, key: str) -> tuple[str, int]:
    escapes = {
        '"': '"',
        "\\": "\\",
        "/": "/",
        "n": "\n",
        "t": "\t",
        "r": "\r",
        "0": "\0",
        " ": " ",
    }
    if index + 1 >= len(text):
        raise FrontmatterError(f"trailing backslash in {key!r}")
    esc = text[index + 1]
    if esc in escapes:
        return escapes[esc], index + 2
    if esc in ("x", "u", "U"):
        width = {"x": 2, "u": 4, "U": 8}[esc]
        digits = text[index + 2 : index + 2 + width]
        if len(digits) != width or re.fullmatch(r"[0-9A-Fa-f]+", digits) is None:
            raise FrontmatterError(f"invalid \\{esc} escape in {key!r}")
        return chr(int(digits, 16)), index + 2 + width
    raise FrontmatterError(f"unsupported escape \\{esc} in {key!r}")


def _parse_quoted(lines: list[str], index: int, raw: str, key: str) -> tuple[str, int]:
    quote = raw[0]
    body = raw[1:]
    out: list[str] = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == quote:
            if quote == "'" and i + 1 < len(body) and body[i + 1] == "'":
                out.append("'")
                i += 2
                continue
            trailing = body[i + 1 :].strip()
            if trailing and not trailing.startswith("#"):
                raise FrontmatterError(f"unexpected text after quoted value for {key!r}")
            return "".join(out), index + 1
        if ch == "\\" and quote == '"':
            decoded, i = _decode_escape(body, i, key)
            out.append(decoded)
            continue
        out.append(ch)
        i += 1
    raise FrontmatterError(
        f"unterminated quoted value for {key!r}; use a block scalar (| or >) "
        "for multi-line values"
    )


def _fold(lines: list[str]) -> str:
    parts: list[str] = []
    paragraph: list[str] = []
    blanks = 0
    for line in lines:
        if line == "":
            if paragraph:
                parts.append(" ".join(paragraph))
                paragraph = []
            blanks += 1
            continue
        if not paragraph and parts and blanks:
            parts.append("\n" * blanks)
        blanks = 0
        paragraph.append(line)
    if paragraph:
        parts.append(" ".join(paragraph))
    return "".join(parts)


def _parse_block(lines: list[str], index: int, indicator: str, key: str) -> tuple[str, int]:
    match = BLOCK_RE.match(indicator)
    if match is None:
        raise FrontmatterError(f"unsupported block scalar header for {key!r}")
    style = indicator[0]
    chomp = match.group(1)

    content: list[str] = []
    block_indent: int | None = None
    i = index + 1
    while i < len(lines):
        line = lines[i]
        if line.strip():
            indent = len(line) - len(line.lstrip(" "))
            if block_indent is None:
                if indent == 0:
                    break
                block_indent = indent
            if indent < block_indent:
                break
            content.append(line[block_indent:])
        else:
            content.append("")
        i += 1

    if chomp in ("", "-"):
        while content and content[-1] == "":
            content.pop()

    value = "\n".join(content) if style == "|" else _fold(content)
    if chomp == "" and value:
        value += "\n"
    return value, i


def _parse_plain(raw: str) -> str:
    return re.split(r"[ \t]+#", raw, maxsplit=1)[0].rstrip()


def _reject_tab_indent(line: str) -> None:
    prefix = line[: len(line) - len(line.lstrip(" \t"))]
    if "\t" in prefix:
        raise FrontmatterError("tab characters are not allowed for indentation")


def parse_frontmatter(frontmatter: str) -> dict[str, str | None]:
    """Parse the top-level fields of a simple YAML frontmatter block.

    Supports plain, single-line quoted, and block (``|`` / ``>``) scalars.
    Nested mappings and lists are skipped. Multi-line plain or quoted scalars
    are rejected with a clear error instead of being silently truncated.
    """

    lines = frontmatter.splitlines()
    fields: dict[str, str | None] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if line[0] in " \t":
            raise FrontmatterError(
                f"unexpected indentation on line {i + 1}; multi-line plain or quoted "
                "scalars are not supported, use a block scalar (| or >)"
            )
        match = KEY_RE.match(line)
        if match is None:
            raise FrontmatterError(f"expected a 'key: value' entry on line {i + 1}")
        key, raw = match.group(1), (match.group(2) or "").strip()
        if key in fields:
            raise FrontmatterError(f"duplicate key {key!r} on line {i + 1}")

        if raw.startswith(("|", ">")):
            value, i = _parse_block(lines, i, raw, key)
        elif raw.startswith(("'", '"')):
            value, i = _parse_quoted(lines, i, raw, key)
        elif raw and not raw.startswith("#"):
            plain = _parse_plain(raw)
            fields[key] = (
                None
                if plain.startswith(("[", "{")) or plain in ("~", "null", "Null", "NULL")
                else plain
            )
            i += 1
            continue
        else:
            i += 1
            while i < len(lines) and (not lines[i].strip() or lines[i][0] in " \t"):
                if lines[i].strip():
                    _reject_tab_indent(lines[i])
                i += 1
            value = None
        fields[key] = value
    return fields


def strip_fences(text: str) -> str:
    """Remove fenced code blocks, including backtick and tilde fences."""
    output: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    for line in text.splitlines(keepends=True):
        if fence_char is None:
            opening = FENCE_OPEN_RE.match(line)
            if opening is not None:
                fence_char = opening.group(1)[0]
                fence_length = len(opening.group(1))
                continue
            output.append(line)
            continue
        closing = FENCE_CLOSE_RE.match(line)
        if (
            closing is not None
            and closing.group(1)[0] == fence_char
            and len(closing.group(1)) >= fence_length
        ):
            fence_char = None
            fence_length = 0
        # Skip the content and the closing fence.
    return "".join(output)


def strip_indented_code(text: str) -> str:
    """Remove CommonMark indented code blocks (four spaces or a tab).

    A block starts after a blank line and requires four spaces beyond the
    containing list item's content indentation when nested in a list.
    """
    output: list[str] = []
    in_code = False
    list_indents: list[tuple[int, int]] = []
    code_indent: int | None = None
    previous_blank = True
    for line in text.splitlines(keepends=True):
        if not line.strip():
            if not in_code:
                output.append(line)
            previous_blank = True
            continue

        leading = line[: len(line) - len(line.lstrip(" \t"))]
        indent = len(leading.expandtabs(4))
        if in_code:
            if indent >= (code_indent or 0):
                previous_blank = False
                continue
            in_code = False
            code_indent = None

        while list_indents and indent < list_indents[-1][1]:
            list_indents.pop()
        marker = LIST_ITEM_RE.match(line)
        if marker is not None and not (
            previous_blank
            and indent >= (list_indents[-1][1] + 4 if list_indents else 4)
        ):
            marker_indent = len(marker.group(1).replace("\t", "    "))
            while list_indents and marker_indent < list_indents[-1][1]:
                list_indents.pop()
            content_indent = marker_indent + len(marker.group(2)) + 1
            list_indents.append((marker_indent, content_indent))
            output.append(line)
            previous_blank = False
            continue

        while list_indents and indent < list_indents[-1][1]:
            list_indents.pop()
        list_indent = list_indents[-1][1] if list_indents else None
        if (
            previous_blank
            and (
                (list_indent is None and (indent >= 4 or line.startswith("\t")))
                or (list_indent is not None and indent >= list_indent + 4)
            )
        ):
            in_code = True
            code_indent = 4 if list_indent is None else list_indent + 4
            previous_blank = True
            continue

        previous_blank = False
        output.append(line)

    return "".join(output)


def strip_html_comments(text: str) -> str:
    """Remove HTML comments without treating comment delimiters in code as markup."""
    code_spans: list[str] = []

    def protect_code_span(match: re.Match[str]) -> str:
        code_spans.append(match.group(0))
        return f"\0{len(code_spans) - 1}\0"

    text = INLINE_CODE_RE.sub(protect_code_span, text)
    text = HTML_COMMENT_RE.sub("", text)
    for index, code_span in enumerate(code_spans):
        text = text.replace(f"\0{index}\0", code_span)
    return text


def strip_code(text: str) -> str:
    text = strip_fences(text)
    text = strip_indented_code(text)
    text = strip_html_comments(text)
    return INLINE_CODE_RE.sub("", text)


def normalize_label(label: str) -> str:
    return " ".join(label.split()).casefold()


def reference_target(text: str) -> str | None:
    text = text.strip()
    if not text or text.startswith(("\"", "'", "-", "*", "+", ">", "|", "[")):
        return None
    if text.startswith("<"):
        end = text.find(">")
        return text[: end + 1] if end != -1 else None
    return text.split()[0]


def looks_like_target_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if line[:1].isspace():
        return True
    return stripped.startswith(
        ("<", "/", "./", "../", "#", "http://", "https://", "mailto:", "data:")
    )


def collect_reference_definitions(body: str) -> dict[str, str]:
    """Map normalized reference labels to their targets.

    Handles blockquotes, list items, and a target on the following line. The
    first definition for a label wins, matching CommonMark.
    """
    definitions: dict[str, str] = {}
    lines = body.splitlines()
    for index, line in enumerate(lines):
        match = REF_DEF_RE.match(line)
        if match is None:
            continue
        label = normalize_label(match.group(1))
        target = reference_target(match.group(2))
        if target is None:
            for next_line in lines[index + 1 : index + 4]:
                if not next_line.strip():
                    continue
                if not looks_like_target_line(next_line):
                    break
                target = reference_target(next_line)
                break
        definitions.setdefault(label, target or "")
    return definitions


def display_path(path: Path) -> Path:
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path


def find_bundle_root(start: Path) -> Path | None:
    """Return the nearest ancestor directory that looks like an OKF bundle root."""
    for directory in (start, *start.parents):
        index = directory / "index.md"
        if not index.is_file():
            continue
        try:
            frontmatter = read_frontmatter(index)
            if frontmatter is None:
                continue
            fields = parse_frontmatter(frontmatter)
        except (OSError, FrontmatterError):
            continue
        if fields.get("okf_version"):
            return directory
    return None


def heading_slugs(text: str) -> set[str]:
    """Return GitHub-style anchor slugs for the headings in a Markdown document."""
    slugs: set[str] = set()
    counts: dict[str, int] = {}
    lines = strip_html_comments(strip_fences(text)).splitlines()
    headings: list[str] = []
    index = 0
    while index < len(lines):
        match = HEADING_RE.match(lines[index])
        if match is not None:
            headings.append(match.group(2))
        elif (
            index + 1 < len(lines)
            and lines[index].strip()
            and len(lines[index]) - len(lines[index].lstrip(" ")) <= 3
            and SETEXT_HEADING_RE.match(lines[index + 1])
        ):
            headings.append(lines[index].strip())
            index += 1
        index += 1

    for heading in headings:
        heading = HEADING_LINK_RE.sub(r"\1", heading)
        heading = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", heading)
        heading = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", heading)
        heading = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"\1", heading)
        heading = HTML_TAG_RE.sub("", heading).replace("`", "")
        heading = unescape(heading).lower()
        heading = re.sub(r"[^\w\s-]", "", heading, flags=re.UNICODE)
        slug = re.sub(r"\s+", "-", heading.strip())
        if not slug:
            continue
        count = counts.get(slug, 0)
        candidate = slug if count == 0 else f"{slug}-{count}"
        while candidate in slugs:
            count += 1
            candidate = f"{slug}-{count}"
        counts[slug] = count + 1
        slugs.add(candidate)
    return slugs


def is_semver(version: str) -> bool:
    match = SEMVER_RE.fullmatch(version)
    if match is None:
        return False
    prerelease = match.group(4)
    return prerelease is None or all(
        not (
            identifier.isdigit()
            and len(identifier) > 1
            and identifier.startswith("0")
        )
        for identifier in prerelease.split(".")
    )


def check_links(path: Path) -> None:
    try:
        body = strip_code(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        fail(f"{display_path(path)}: cannot read: {exc}")
        return
    bundle_root: Path | None = None

    def check_fragment(target: Path, fragment: str) -> None:
        if not fragment:
            return
        try:
            text = target.read_text(encoding="utf-8-sig")
        except OSError:
            return
        if unquote(fragment) not in heading_slugs(text):
            fail(
                f"{display_path(path)}: unresolved anchor #{fragment} "
                f"in {display_path(target)}"
            )

    def check_target(target: str) -> None:
        nonlocal bundle_root
        target = target.strip()
        if target.startswith("<") and target.endswith(">"):
            inner = target[1:-1]
            if "<" in inner or ">" in inner:
                return
            if PLACEHOLDER_RE.fullmatch(inner):
                return
            target = inner
        if not target or target.startswith(
            ("http://", "https://", "mailto:", "data:")
        ):
            return
        if target.startswith("#"):
            check_fragment(path, target[1:])
            return
        target_path, _, fragment = target.partition("#")
        target_path = target_path.split("?", 1)[0]
        if not target_path:
            return
        if target_path.startswith("/"):
            if bundle_root is None:
                bundle_root = find_bundle_root(path.parent)
            if bundle_root is None:
                # Bundle-absolute links only resolve inside an OKF bundle.
                return
            resolved = (bundle_root / target_path.lstrip("/")).resolve()
        else:
            resolved = (path.parent / target_path).resolve()
        if not resolved.exists():
            fail(f"{display_path(path)}: unresolved link {target_path!r}")
        elif fragment and resolved.suffix.lower() == ".md":
            check_fragment(resolved, fragment)

    for match in LINK_RE.finditer(body):
        check_target(match.group(1))
    for match in IMAGE_RE.finditer(body):
        check_target(match.group(1))

    definitions = collect_reference_definitions(body)
    for target in definitions.values():
        if target:
            check_target(target)
    for match in REF_USE_RE.finditer(body):
        label = match.group(2) or match.group(1)
        if normalize_label(label) not in definitions:
            fail(f"{display_path(path)}: undefined reference link label {label!r}")


def check_skill(skill_md: Path) -> str:
    rel = skill_md.relative_to(ROOT)
    frontmatter = read_frontmatter(skill_md)
    if frontmatter is None:
        fail(f"{rel}: missing YAML frontmatter")
        return ""

    try:
        fields = parse_frontmatter(frontmatter)
    except FrontmatterError as exc:
        fail(f"{rel}: invalid frontmatter: {exc}")
        return ""

    def scalar(key: str, required: bool) -> str | None:
        if key not in fields:
            if required:
                fail(f"{rel}: missing required '{key}' field")
            return None
        value = fields[key]
        if value is None:
            fail(f"{rel}: '{key}' must be a scalar, not a nested block")
            return None
        return value

    name = scalar("name", required=True)
    description = scalar("description", required=True)
    compatibility = scalar("compatibility", required=False)

    if name is not None:
        if name != skill_md.parent.name:
            fail(f"{rel}: name {name!r} does not match directory {skill_md.parent.name!r}")
        if len(name) > MAX_NAME or not NAME_RE.fullmatch(name):
            fail(f"{rel}: invalid skill name {name!r}")

    if description is not None:
        if not description.strip():
            fail(f"{rel}: 'description' must not be empty")
        elif len(description) > MAX_DESCRIPTION:
            fail(
                f"{rel}: description is {len(description)} characters "
                f"(max {MAX_DESCRIPTION})"
            )

    if "compatibility" in fields:
        if compatibility is None or not compatibility.strip():
            fail(f"{rel}: 'compatibility' must be a non-empty string")
        elif len(compatibility) > MAX_COMPATIBILITY:
            fail(
                f"{rel}: compatibility is {len(compatibility)} characters "
                f"(max {MAX_COMPATIBILITY})"
            )

    text = skill_md.read_text(encoding="utf-8-sig")
    match = FRONTMATTER_RE.match(text)
    assert match is not None
    body_lines = len(text.splitlines()) - len(match.group(0).splitlines())
    if body_lines > MAX_BODY_LINES:
        warn(f"{rel}: body is {body_lines} lines (guidance: under {MAX_BODY_LINES})")

    return name or ""


def plugins_root() -> Path:
    return ROOT / "plugins"


def marketplace_path() -> Path:
    return ROOT / ".github" / "plugin" / "marketplace.json"


def plugin_dirs() -> list[Path]:
    """Return the plugin roots under ``plugins/``."""
    root = plugins_root()
    if not root.is_dir():
        return []
    return sorted(
        path for path in root.iterdir() if path.is_dir() and not path.name.startswith(".")
    )


def plugin_manifests() -> list[tuple[Path, dict]]:
    manifests: list[tuple[Path, dict]] = []
    for plugin_dir in plugin_dirs():
        label = f"{display_path(plugin_dir)}/plugin.json"
        manifest = _read_json_object(plugin_dir / "plugin.json", label)
        if manifest is not None:
            manifests.append((plugin_dir, manifest))
    return manifests


def lockstep_version() -> str | None:
    """Return the shared plugin version, or None when it is missing or split."""
    version: str | None = None
    for _, manifest in plugin_manifests():
        candidate = manifest.get("version")
        if not isinstance(candidate, str) or not is_semver(candidate):
            continue
        if version is None:
            version = candidate
        elif candidate != version:
            return None
    return version


def check_versions() -> None:
    manifests = plugin_manifests()
    if not manifests:
        fail("plugins/: no plugin manifests found")
        return

    versions: dict[str, str] = {}
    for plugin_dir, manifest in manifests:
        label = f"{display_path(plugin_dir)}/plugin.json"
        name = manifest.get("name")
        if not isinstance(name, str) or not name.strip():
            fail(f"{label}: 'name' must be a non-empty string")
        elif name != plugin_dir.name:
            fail(f"{label}: name {name!r} does not match directory {plugin_dir.name!r}")
        version = manifest.get("version")
        if not isinstance(version, str) or not version.strip():
            fail(f"{label}: missing or invalid 'version'")
        elif not is_semver(version):
            fail(f"{label}: 'version' must be semantic versioning, got {version!r}")
        else:
            versions[plugin_dir.name] = version

    if not versions:
        return

    version = next(iter(versions.values()))
    for name, candidate in versions.items():
        if candidate != version:
            fail(f"version lockstep: {name} is {candidate!r}, expected {version!r}")

    market = _read_json_object(marketplace_path(), ".github/plugin/marketplace.json")
    if market is None:
        return

    metadata = market.get("metadata")
    if not isinstance(metadata, dict):
        fail(".github/plugin/marketplace.json: 'metadata' must be an object")
    else:
        market_version = metadata.get("version")
        if market_version != version:
            fail(
                "version mismatch: plugins "
                f"{version!r} vs marketplace metadata {market_version!r}"
            )

    plugins = market.get("plugins")
    if not isinstance(plugins, list):
        fail(".github/plugin/marketplace.json: 'plugins' must be an array")
        return

    listed: dict[str, dict] = {}
    for index, entry in enumerate(plugins):
        label = f".github/plugin/marketplace.json: plugins[{index}]"
        if not isinstance(entry, dict):
            fail(f"{label} must be an object")
            continue
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            fail(f"{label}: 'name' must be a non-empty string")
            continue
        if name in listed:
            fail(f"{label}: duplicate marketplace entry {name!r}")
            continue
        listed[name] = entry
        if entry.get("version") != version:
            fail(
                "version mismatch: plugins "
                f"{version!r} vs marketplace plugin {name!r} "
                f"{entry.get('version')!r}"
            )
        if name not in versions:
            fail(f"{label}: no plugin manifest named {name!r}")
            continue
        source = entry.get("source")
        if isinstance(source, str) and "://" not in source:
            resolved = (ROOT / source).resolve()
            expected = (plugins_root() / name).resolve()
            if resolved != expected:
                fail(
                    f"{label}: source {source!r} does not resolve to "
                    f"{display_path(expected)}"
                )

    for name in versions:
        if name not in listed:
            fail(f".github/plugin/marketplace.json: plugin {name!r} is not listed")

    try:
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"CHANGELOG.md: cannot read: {exc}")
        return
    if f"## [{version}]" not in changelog:
        fail(f"CHANGELOG.md: no section for version {version}")


def _read_json_object(path: Path, label: str) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{label}: cannot parse: {exc}")
        return None
    if not isinstance(data, dict):
        fail(f"{label}: expected a JSON object")
        return None
    return data


def check_manifest_shapes() -> None:
    """Check the fields the Agent Plugins manifests require."""
    manifests = plugin_manifests()
    if not manifests:
        fail("plugins/: no plugin manifests found")

    for plugin_dir, plugin in manifests:
        label = f"{display_path(plugin_dir)}/plugin.json"
        if plugin.get("$schema") != PLUGIN_SCHEMA:
            fail(f"{label}: '$schema' must be {PLUGIN_SCHEMA}")
        name = plugin.get("name")
        if not isinstance(name, str) or not name.strip():
            fail(f"{label}: 'name' must be a non-empty string")

        mcp_path = plugin_dir / "mcp.json"
        if mcp_path.exists():
            mcp = _read_json_object(
                mcp_path, f"{display_path(plugin_dir)}/mcp.json"
            )
            if mcp is not None:
                if mcp.get("$schema") != MCP_SCHEMA:
                    fail(
                        f"{display_path(plugin_dir)}/mcp.json: "
                        f"'$schema' must be {MCP_SCHEMA}"
                    )
                if not isinstance(mcp.get("mcpServers"), dict):
                    fail(
                        f"{display_path(plugin_dir)}/mcp.json: "
                        "'mcpServers' must be an object"
                    )

    market = _read_json_object(marketplace_path(), ".github/plugin/marketplace.json")
    if market is None:
        return
    if not isinstance(market.get("name"), str) or not market["name"].strip():
        fail(".github/plugin/marketplace.json: 'name' must be a non-empty string")
    owner = market.get("owner")
    if (
        not isinstance(owner, dict)
        or not isinstance(owner.get("name"), str)
        or not owner["name"].strip()
    ):
        fail(".github/plugin/marketplace.json: 'owner.name' must be a non-empty string")
    plugins = market.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        fail(".github/plugin/marketplace.json: 'plugins' must be a non-empty array")
        return

    seen: set[str] = set()
    for index, entry in enumerate(plugins):
        label = f".github/plugin/marketplace.json: plugins[{index}]"
        if not isinstance(entry, dict):
            fail(f"{label} must be an object")
            continue
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            fail(f"{label}: 'name' must be a non-empty string")
        elif name in seen:
            fail(f"{label}: duplicate plugin name {name!r}")
        else:
            seen.add(name)
        source = entry.get("source")
        if isinstance(source, str):
            if not source.strip():
                fail(f"{label}: 'source' must not be empty")
            elif "://" not in source:
                resolved = (ROOT / source).resolve()
                if not resolved.is_dir():
                    fail(f"{label}: source directory {source!r} does not exist")
                elif not (resolved / "plugin.json").is_file():
                    fail(
                        f"{label}: source directory {source!r} has no plugin.json"
                    )
        elif not isinstance(source, dict):
            fail(f"{label}: 'source' must be a string or object")


def check_actor_versions(version: str | None = None) -> None:
    """Check that concrete skill actor versions match the plugin version.

    Templates use ``<writer>/<version>`` and are ignored; concrete examples such
    as ``generated: { by: repo-reconnaissance/0.2.0 }`` must be updated with the
    plugin release.
    """
    if version is None:
        version = lockstep_version()
    if not isinstance(version, str) or not version.strip():
        return

    roots = plugin_dirs()
    skill_names: set[str] = set()
    for plugin_dir in roots:
        skills_dir = plugin_dir / "skills"
        if skills_dir.is_dir():
            skill_names.update(
                path.name for path in skills_dir.iterdir() if path.is_dir()
            )

    for plugin_dir in roots:
        for path in sorted(plugin_dir.rglob("*.md")):
            body = path.read_text(encoding="utf-8-sig")
            for match in ACTOR_VERSION_RE.finditer(body):
                actor, actor_version = match.group(1), match.group(2)
                if actor in skill_names and actor_version != version:
                    fail(
                        f"{display_path(path)}: actor {actor}/{actor_version} "
                        f"does not match plugin version {version}"
                    )


PROFILE_SCHEMA = "sdlc.profile/v1"
PROFILE_COMMAND_KEYS = ("install", "test", "lint", "typecheck", "build")


def _check_profile_command(value, label: str) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        fail(f"{label}: must be an object or null")
        return
    for key in ("cmd", "source"):
        item = value.get(key)
        if not isinstance(item, str) or not item.strip():
            fail(f"{label}: {key!r} must be a non-empty string")
    for key in value:
        if key not in ("cmd", "source"):
            warn(f"{label}: unknown command field {key!r}")


def _check_profile_commands(value, label: str) -> None:
    if not isinstance(value, dict):
        fail(f"{label}: must be an object")
        return
    for key in value:
        if key not in PROFILE_COMMAND_KEYS:
            fail(f"{label}: unknown command {key!r}")
    for key, command in value.items():
        if key in PROFILE_COMMAND_KEYS:
            _check_profile_command(command, f"{label}.{key}")


def check_profile_contract(data: dict, label: str) -> None:
    """Validate a ``.sdlc/profile.json`` document against the M1 contract."""
    if data.get("schema") != PROFILE_SCHEMA:
        fail(f"{label}: 'schema' must be {PROFILE_SCHEMA!r}")
    for key in ("generated_by", "base"):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            fail(f"{label}: {key!r} must be a non-empty string")

    stack = data.get("stack")
    if not isinstance(stack, list) or any(
        not isinstance(item, str) or not item.strip() for item in stack
    ):
        fail(f"{label}: 'stack' must be an array of non-empty strings")

    _check_profile_commands(data.get("commands"), f"{label}.commands")

    workspaces = data.get("workspaces", {})
    if not isinstance(workspaces, dict):
        fail(f"{label}: 'workspaces' must be an object")
    else:
        for name, workspace in workspaces.items():
            parts = name.split("/")
            if (
                not name
                or name.startswith("/")
                or "\\" in name
                or any(part in ("", ".", "..") for part in parts)
            ):
                fail(f"{label}: workspace {name!r} must be a relative POSIX path")
            if not isinstance(workspace, dict):
                fail(f"{label}.workspaces[{name!r}]: must be an object")
                continue
            if "commands" not in workspace:
                fail(f"{label}.workspaces[{name!r}]: missing 'commands'")
            else:
                _check_profile_commands(
                    workspace["commands"], f"{label}.workspaces[{name!r}].commands"
                )
            for key in workspace:
                if key != "commands":
                    warn(f"{label}.workspaces[{name!r}]: unknown field {key!r}")

    ci = data.get("ci")
    if ci is not None:
        if not isinstance(ci, dict):
            fail(f"{label}: 'ci' must be an object or null")
        else:
            if not isinstance(ci.get("file"), str) or not ci["file"].strip():
                fail(f"{label}.ci: 'file' must be a non-empty string")
            jobs = ci.get("jobs", [])
            if not isinstance(jobs, list) or any(
                not isinstance(job, str) or not job.strip() for job in jobs
            ):
                fail(f"{label}.ci: 'jobs' must be an array of non-empty strings")

    for key in ("risk_paths", "exclusions"):
        value = data.get(key, [])
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item.strip() for item in value
        ):
            fail(f"{label}: {key!r} must be an array of non-empty strings")

    if "notes" in data and not isinstance(data["notes"], str):
        fail(f"{label}: 'notes' must be a string")


def check_profile_samples() -> None:
    sample_dir = ROOT / "tests" / "fixtures" / "profile"
    if not sample_dir.is_dir():
        return
    for path in sorted(sample_dir.glob("*.json")):
        label = str(display_path(path))
        data = _read_json_object(path, label)
        if data is not None:
            check_profile_contract(data, label)


def _load_verdict_module():
    path = ROOT / "evals" / "verdict.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("sdlc_verdict", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_verdict_samples() -> None:
    """Recompute committed verdict fixtures so Gate A covers the artifact format."""
    fixtures = ROOT / "evals" / "fixtures"
    if not fixtures.is_dir():
        return
    module = _load_verdict_module()
    if module is None:
        return
    for path in sorted(fixtures.rglob("verdict.md")):
        label = str(display_path(path))
        try:
            text = path.read_text(encoding="utf-8")
            module.check(module.extract_json(text))
        except (OSError, module.VerdictError) as exc:
            fail(f"{label}: {exc}")


def main() -> int:
    roots = plugin_dirs()
    if not roots:
        fail("plugins/ directory is missing or empty")
        return report()

    names: dict[str, Path] = {}
    checked_docs = 0
    for plugin_dir in roots:
        plugin_label = display_path(plugin_dir)
        if not (plugin_dir / "plugin.json").is_file():
            fail(f"{plugin_label}: missing plugin.json")
        skills_dir = plugin_dir / "skills"
        if not skills_dir.is_dir():
            fail(f"{plugin_label}: missing skills/ directory")
            continue
        skill_dirs = sorted(path for path in skills_dir.iterdir() if path.is_dir())
        if not skill_dirs:
            fail(f"{plugin_label}/skills: contains no skill directories")
        for skill_dir in skill_dirs:
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                fail(f"{display_path(skill_dir)}: missing SKILL.md")
                continue
            name = check_skill(skill_md)
            if name:
                if name in names:
                    fail(
                        f"duplicate skill name {name!r} in "
                        f"{display_path(names[name])} and {display_path(skill_md)}"
                    )
                names[name] = skill_md
        for path in sorted(skills_dir.rglob("*.md")):
            check_links(path)
            checked_docs += 1

    check_links(ROOT / "README.md")
    checked_docs += 1

    check_versions()
    check_manifest_shapes()
    check_actor_versions()
    check_profile_samples()
    check_verdict_samples()

    print(f"Checked {len(names)} skills and {checked_docs} Markdown files.")
    return report()


def report() -> int:
    for message in warnings:
        print(f"warning: {message}")
    for message in errors:
        print(f"error: {message}")
    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s).")
        return 1
    print(f"OK: {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
