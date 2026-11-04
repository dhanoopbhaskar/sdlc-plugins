#!/usr/bin/env python3
"""Validate Agent Skill packaging and repository metadata.

Dependency-free checks:

* Every ``skills/<name>/SKILL.md`` has parseable frontmatter with the required
  ``name`` and ``description`` fields, follows the Agent Skills naming rules,
  and warns when the body exceeds the recommended length. Frontmatter is
  parsed as a simple YAML mapping without external dependencies; unsupported
  constructs fail loudly instead of being silently truncated.
* Relative Markdown links and images in skills and the README resolve, including
  angle-bracket destinations, reference definitions, and heading anchors. Bundle-absolute OKF
  links (``/path``) resolve when a bundle root (an ``index.md`` with ``okf_version``)
  is found, and are ignored otherwise. Links inside fenced and indented code
  blocks, HTML comments, URLs, template placeholders, and footnote definitions
  are ignored.
* ``plugin.json``, ``.github/plugin/marketplace.json``, and ``CHANGELOG.md``
  agree on the current version; required manifest fields are present; and
  concrete ``generated``/``author`` actor versions in skills match that version.

Run from the repository root:

    python3 scripts/validate_skills.py

Exits non-zero on error. Warnings do not fail the build.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"

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
HEADING_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
HTML_TAG_RE = re.compile(r"<[^>]*>")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
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

    A block only starts after a blank line and outside a list item, so nested
    list content that happens to be indented is still scanned for links.
    """
    output: list[str] = []
    in_code = False
    list_indent: int | None = None
    previous_blank = True
    for line in text.splitlines(keepends=True):
        if not line.strip():
            if not in_code:
                output.append(line)
            previous_blank = True
            continue

        indent = len(line) - len(line.lstrip(" "))
        if (
            (indent >= 4 or line.startswith("\t"))
            and previous_blank
            and list_indent is None
        ):
            in_code = True
            previous_blank = True
            continue

        marker = LIST_ITEM_RE.match(line)
        if marker is not None:
            list_indent = (
                len(marker.group(1).replace("\t", "    "))
                + len(marker.group(2))
                + 1
            )
            in_code = False
            previous_blank = False
            output.append(line)
            continue

        if list_indent is not None and indent >= list_indent:
            in_code = False
            previous_blank = False
            output.append(line)
            continue

        if indent == 0:
            list_indent = None
        in_code = False
        previous_blank = False
        output.append(line)

    return "".join(output)


def strip_code(text: str) -> str:
    text = strip_fences(text)
    text = HTML_COMMENT_RE.sub("", text)
    text = strip_indented_code(text)
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
    for match in HEADING_RE.finditer(strip_fences(text)):
        heading = HEADING_LINK_RE.sub(r"\1", match.group(2))
        heading = HTML_TAG_RE.sub("", heading).replace("`", "").lower()
        heading = re.sub(r"[^\w\s-]", "", heading, flags=re.UNICODE)
        slug = re.sub(r"\s+", "-", heading.strip())
        if not slug:
            continue
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        slugs.add(slug if count == 0 else f"{slug}-{count}")
    return slugs


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


def check_versions() -> None:
    plugin = _read_json_object(ROOT / "plugin.json", "plugin.json")
    if plugin is None:
        return
    market = _read_json_object(
        ROOT / ".github" / "plugin" / "marketplace.json",
        ".github/plugin/marketplace.json",
    )
    if market is None:
        return

    version = plugin.get("version")
    if not isinstance(version, str) or not version.strip():
        fail("plugin.json: missing or invalid 'version'")
        return
    if SEMVER_RE.fullmatch(version) is None:
        fail(f"plugin.json: 'version' must be semantic versioning, got {version!r}")
        return

    metadata = market.get("metadata")
    if not isinstance(metadata, dict):
        fail(".github/plugin/marketplace.json: 'metadata' must be an object")
    else:
        market_version = metadata.get("version")
        if market_version != version:
            fail(
                "version mismatch: plugin.json "
                f"{version!r} vs marketplace metadata {market_version!r}"
            )

    plugins = market.get("plugins")
    if not isinstance(plugins, list):
        fail(".github/plugin/marketplace.json: 'plugins' must be an array")
        return
    for index, entry in enumerate(plugins):
        if not isinstance(entry, dict):
            fail(
                f".github/plugin/marketplace.json: plugins[{index}] must be an object"
            )
            continue
        if entry.get("version") != version:
            fail(
                "version mismatch: plugin.json "
                f"{version!r} vs marketplace plugin {entry.get('name')!r} "
                f"{entry.get('version')!r}"
            )

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
    plugin = _read_json_object(ROOT / "plugin.json", "plugin.json")
    if plugin is not None:
        if plugin.get("$schema") != PLUGIN_SCHEMA:
            fail(f"plugin.json: '$schema' must be {PLUGIN_SCHEMA}")
        name = plugin.get("name")
        if not isinstance(name, str) or not name.strip():
            fail("plugin.json: 'name' must be a non-empty string")

    mcp_path = ROOT / "mcp.json"
    if mcp_path.exists():
        mcp = _read_json_object(mcp_path, "mcp.json")
        if mcp is not None:
            if mcp.get("$schema") != MCP_SCHEMA:
                fail(f"mcp.json: '$schema' must be {MCP_SCHEMA}")
            if not isinstance(mcp.get("mcpServers"), dict):
                fail("mcp.json: 'mcpServers' must be an object")

    market = _read_json_object(
        ROOT / ".github" / "plugin" / "marketplace.json",
        ".github/plugin/marketplace.json",
    )
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
    for index, entry in enumerate(plugins):
        label = f".github/plugin/marketplace.json: plugins[{index}]"
        if not isinstance(entry, dict):
            fail(f"{label} must be an object")
            continue
        if not isinstance(entry.get("name"), str) or not entry["name"].strip():
            fail(f"{label}: 'name' must be a non-empty string")
        source = entry.get("source")
        if isinstance(source, str):
            if not source.strip():
                fail(f"{label}: 'source' must not be empty")
            elif "://" not in source:
                resolved = (ROOT / source).resolve()
                if not resolved.is_dir():
                    fail(f"{label}: source directory {source!r} does not exist")
        elif not isinstance(source, dict):
            fail(f"{label}: 'source' must be a string or object")


def check_actor_versions(version: str | None = None) -> None:
    """Check that concrete skill actor versions match the plugin version.

    Templates use ``<writer>/<version>`` and are ignored; concrete examples such
    as ``generated: { by: repo-reconnaissance/0.2.0 }`` must be updated with the
    plugin release.
    """
    if version is None:
        plugin = _read_json_object(ROOT / "plugin.json", "plugin.json")
        if plugin is None:
            return
        version = plugin.get("version")
    if not isinstance(version, str) or not version.strip() or not SKILLS_DIR.is_dir():
        return

    skill_names = {path.name for path in SKILLS_DIR.iterdir() if path.is_dir()}
    for path in sorted(SKILLS_DIR.rglob("*.md")):
        body = path.read_text(encoding="utf-8-sig")
        for match in ACTOR_VERSION_RE.finditer(body):
            actor, actor_version = match.group(1), match.group(2)
            if actor in skill_names and actor_version != version:
                fail(
                    f"{display_path(path)}: actor {actor}/{actor_version} "
                    f"does not match plugin version {version}"
                )


def main() -> int:
    if not SKILLS_DIR.is_dir():
        fail("skills/ directory is missing")
        return report()

    skill_dirs = sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())
    if not skill_dirs:
        fail("skills/ contains no skill directories")

    names: dict[str, Path] = {}
    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            fail(f"{skill_dir.relative_to(ROOT)}: missing SKILL.md")
            continue
        name = check_skill(skill_md)
        if name:
            if name in names:
                fail(f"duplicate skill name {name!r} in {names[name]} and {skill_md}")
            names[name] = skill_md

    checked_docs = 0
    for path in sorted(SKILLS_DIR.rglob("*.md")):
        check_links(path)
        checked_docs += 1
    check_links(ROOT / "README.md")
    checked_docs += 1

    check_versions()
    check_manifest_shapes()
    check_actor_versions()

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
