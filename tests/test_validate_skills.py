"""Tests for the dependency-free skill validator."""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import validate_skills as validator  # noqa: E402


class FrontmatterParserTests(unittest.TestCase):
    def test_plain_and_quoted_scalars(self) -> None:
        fields = validator.parse_frontmatter(
            'name: test-skill\ndescription: "A skill"\ncompatibility: \'works\''
        )
        self.assertEqual(
            fields,
            {
                "name": "test-skill",
                "description": "A skill",
                "compatibility": "works",
            },
        )

    def test_comments_and_empty_values(self) -> None:
        fields = validator.parse_frontmatter(
            "# leading comment\nname: test # trailing comment\nlicense: # comment\n"
        )
        self.assertEqual(fields, {"name": "test", "license": None})

    def test_literal_block_scalar(self) -> None:
        fields = validator.parse_frontmatter(
            "description: |\n  line one\n  line two\n"
        )
        self.assertEqual(fields["description"], "line one\nline two\n")

    def test_folded_block_scalar(self) -> None:
        fields = validator.parse_frontmatter(
            "description: >-\n  line one\n  line two\n"
        )
        self.assertEqual(fields["description"], "line one line two")

    def test_block_chomping(self) -> None:
        strip = validator.parse_frontmatter("description: |-\n  value\n\n")
        keep = validator.parse_frontmatter("description: |+\n  value\n\n")
        self.assertEqual(strip["description"], "value")
        self.assertEqual(keep["description"], "value\n")

    def test_nested_block_is_skipped(self) -> None:
        fields = validator.parse_frontmatter(
            "metadata:\n  owner: team\nname: test-skill\n"
        )
        self.assertEqual(fields, {"metadata": None, "name": "test-skill"})

    def test_duplicate_key_is_rejected(self) -> None:
        with self.assertRaisesRegex(validator.FrontmatterError, "duplicate key"):
            validator.parse_frontmatter("name: one\nname: two\n")

    def test_multiline_plain_scalar_is_rejected(self) -> None:
        with self.assertRaisesRegex(validator.FrontmatterError, "indentation"):
            validator.parse_frontmatter("description: first\n  second\n")

    def test_unterminated_quote_is_rejected(self) -> None:
        with self.assertRaisesRegex(validator.FrontmatterError, "unterminated"):
            validator.parse_frontmatter('description: "unterminated\n')

    def test_tab_indentation_is_rejected(self) -> None:
        with self.assertRaisesRegex(validator.FrontmatterError, "indentation"):
            validator.parse_frontmatter("description:\n\tvalue\n")

    def test_double_quoted_escapes(self) -> None:
        fields = validator.parse_frontmatter(
            'description: "quote: \\"x\\", unicode: \\u0041, tab: \\t"\n'
        )
        self.assertEqual(fields["description"], 'quote: "x", unicode: A, tab: \t')


class SkillCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        validator.errors.clear()
        validator.warnings.clear()

    def tearDown(self) -> None:
        validator.errors.clear()
        validator.warnings.clear()

    def _write_skill(self, directory: str, body: str = "Body", **fields: str) -> Path:
        skill_dir = self.root / "skills" / directory
        skill_dir.mkdir(parents=True)
        lines = ["---"]
        lines.extend(f"{key}: {value}" for key, value in fields.items())
        lines.extend(["---", body])
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return skill_md

    def test_name_must_match_directory(self) -> None:
        skill_md = self._write_skill(
            "actual-name", name="different-name", description="A skill"
        )
        with mock.patch.object(validator, "ROOT", self.root):
            validator.check_skill(skill_md)
        self.assertTrue(
            any("does not match directory" in error for error in validator.errors)
        )

    def test_description_length_is_enforced(self) -> None:
        skill_md = self._write_skill(
            "long-description",
            name="long-description",
            description="x" * (validator.MAX_DESCRIPTION + 1),
        )
        with mock.patch.object(validator, "ROOT", self.root):
            validator.check_skill(skill_md)
        self.assertTrue(
            any("description" in error and "max" in error for error in validator.errors)
        )

    def test_long_body_warns_without_failing(self) -> None:
        skill_md = self._write_skill(
            "long-body",
            body="\n".join(["line"] * (validator.MAX_BODY_LINES + 1)),
            name="long-body",
            description="A skill",
        )
        with mock.patch.object(validator, "ROOT", self.root):
            validator.check_skill(skill_md)
        self.assertEqual(validator.errors, [])
        self.assertTrue(any("body is" in warning for warning in validator.warnings))

    def test_invalid_name_is_rejected(self) -> None:
        skill_md = self._write_skill(
            "Bad_Name", name="Bad_Name", description="A skill"
        )
        with mock.patch.object(validator, "ROOT", self.root):
            validator.check_skill(skill_md)
        self.assertTrue(
            any("invalid skill name" in error for error in validator.errors)
        )

    def test_compatibility_length_is_enforced(self) -> None:
        skill_md = self._write_skill(
            "long-compatibility",
            name="long-compatibility",
            description="A skill",
            compatibility="x" * (validator.MAX_COMPATIBILITY + 1),
        )
        with mock.patch.object(validator, "ROOT", self.root):
            validator.check_skill(skill_md)
        self.assertTrue(
            any("compatibility" in error and "max" in error for error in validator.errors)
        )

    def test_empty_compatibility_is_rejected(self) -> None:
        skill_md = self._write_skill(
            "empty-compatibility",
            name="empty-compatibility",
            description="A skill",
            compatibility="",
        )
        with mock.patch.object(validator, "ROOT", self.root):
            validator.check_skill(skill_md)
        self.assertTrue(
            any(
                "compatibility" in error and "non-empty" in error
                for error in validator.errors
            )
        )

    def test_empty_quoted_compatibility_is_rejected(self) -> None:
        skill_md = self._write_skill(
            "empty-quoted-compatibility",
            name="empty-quoted-compatibility",
            description="A skill",
            compatibility='""',
        )
        with mock.patch.object(validator, "ROOT", self.root):
            validator.check_skill(skill_md)
        self.assertTrue(
            any(
                "compatibility" in error and "non-empty" in error
                for error in validator.errors
            )
        )

    def test_whitespace_compatibility_is_rejected(self) -> None:
        skill_md = self._write_skill(
            "whitespace-compatibility",
            name="whitespace-compatibility",
            description="A skill",
            compatibility='"   "',
        )
        with mock.patch.object(validator, "ROOT", self.root):
            validator.check_skill(skill_md)
        self.assertTrue(
            any(
                "compatibility" in error and "non-empty" in error
                for error in validator.errors
            )
        )


class RepositorySkillsTests(unittest.TestCase):
    def _skill_files(self) -> list[Path]:
        return sorted(
            path
            for plugin_dir in validator.plugin_dirs()
            for path in plugin_dir.glob("skills/*/SKILL.md")
        )

    def test_every_skill_parses(self) -> None:
        skill_files = self._skill_files()
        self.assertTrue(skill_files)

        for path in skill_files:
            with self.subTest(path=str(path.relative_to(validator.ROOT))):
                frontmatter = validator.read_frontmatter(path)
                self.assertIsNotNone(frontmatter)
                fields = validator.parse_frontmatter(frontmatter or "")
                self.assertEqual(fields.get("name"), path.parent.name)
                self.assertIsInstance(fields.get("description"), str)
                self.assertTrue((fields.get("description") or "").strip())

    def test_every_skill_passes_validation(self) -> None:
        validator.errors.clear()
        validator.warnings.clear()
        for path in self._skill_files():
            validator.check_skill(path)
        self.assertEqual(validator.errors, [])

    def test_plugin_roots_are_discovered(self) -> None:
        names = [path.name for path in validator.plugin_dirs()]
        self.assertIn("sdlc", names)
        self.assertIn("discovery", names)
        for plugin_dir in validator.plugin_dirs():
            self.assertTrue((plugin_dir / "plugin.json").is_file())
            self.assertTrue((plugin_dir / "skills").is_dir())


class RepositoryChecksTests(unittest.TestCase):
    def setUp(self) -> None:
        validator.errors.clear()
        validator.warnings.clear()

    def tearDown(self) -> None:
        validator.errors.clear()
        validator.warnings.clear()

    def test_check_links_accepts_existing_and_ignored_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "other.md").write_text("# Other\n", encoding="utf-8")
            (root / "image.png").write_bytes(b"")
            doc = root / "doc.md"
            doc.write_text(
                "# Section\n\n"
                "[ok](other.md)\n"
                "[anchor](#section)\n"
                "[web](https://example.com)\n"
                "[placeholder](<path>)\n"
                "[![image](image.png)](other.md)\n"
                "![inline](data:image/png;base64,AAAA)\n",
                encoding="utf-8",
            )
            validator.check_links(doc)
        self.assertEqual(validator.errors, [])

    def test_check_links_accepts_existing_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "other.md").write_text(
                "# Overview\n\n## Scoring anchors\n", encoding="utf-8"
            )
            doc = root / "doc.md"
            doc.write_text("[x](other.md#scoring-anchors)\n", encoding="utf-8")
            validator.check_links(doc)
        self.assertEqual(validator.errors, [])

    def test_check_links_reports_missing_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "other.md").write_text("# Overview\n", encoding="utf-8")
            doc = root / "doc.md"
            doc.write_text("[x](other.md#missing)\n", encoding="utf-8")
            validator.check_links(doc)
        self.assertEqual(len(validator.errors), 1)
        self.assertIn("unresolved anchor", validator.errors[0])

    def test_check_links_reports_missing_local_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text("# Overview\n\n[x](#missing)\n", encoding="utf-8")
            validator.check_links(doc)
        self.assertEqual(len(validator.errors), 1)
        self.assertIn("unresolved anchor", validator.errors[0])

    def test_check_links_reports_missing_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text("![missing](nope.png)\n", encoding="utf-8")
            validator.check_links(doc)
        self.assertEqual(len(validator.errors), 1)
        self.assertIn("unresolved link", validator.errors[0])

    def test_check_links_reports_missing_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text("[missing](nope.md)\n", encoding="utf-8")
            validator.check_links(doc)
        self.assertEqual(len(validator.errors), 1)
        self.assertIn("unresolved link", validator.errors[0])

    def test_check_links_ignores_fenced_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text("```\n[missing](nope.md)\n```\n", encoding="utf-8")
            validator.check_links(doc)
        self.assertEqual(validator.errors, [])

    def test_check_links_ignores_tilde_fenced_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text("~~~\n[missing](nope.md)\n~~~\n", encoding="utf-8")
            validator.check_links(doc)
        self.assertEqual(validator.errors, [])

    def test_check_links_ignores_longer_backtick_fences(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text(
                "````\n```\n[missing](nope.md)\n```\n````\n", encoding="utf-8"
            )
            validator.check_links(doc)
        self.assertEqual(validator.errors, [])

    def test_check_links_ignores_indented_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text(
                "Example:\n\n    [missing](nope.md)\n    - [also missing](nope.md)\n\nAfter.\n",
                encoding="utf-8",
            )
            validator.check_links(doc)
        self.assertEqual(validator.errors, [])

    def test_check_links_ignores_html_comments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text(
                "<!-- [missing](nope.md) -->\n[ok](https://example.com)\n",
                encoding="utf-8",
            )
            validator.check_links(doc)
        self.assertEqual(validator.errors, [])

    def test_check_links_preserves_comment_delimiters_inside_code_spans(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text(
                "`<!--` [missing](nope.md) `-->`\n", encoding="utf-8"
            )
            validator.check_links(doc)
        self.assertEqual(len(validator.errors), 1)
        self.assertIn("unresolved link", validator.errors[0])

    def test_check_links_scans_nested_list_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "guide.md").write_text("# Guide\n", encoding="utf-8")
            doc = root / "doc.md"
            doc.write_text("- item\n\n    [guide](guide.md)\n", encoding="utf-8")
            validator.check_links(doc)
        self.assertEqual(validator.errors, [])

    def test_check_links_ignores_indented_code_inside_list_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text(
                "- item\n\n      [missing](nope.md)\n", encoding="utf-8"
            )
            validator.check_links(doc)
        self.assertEqual(validator.errors, [])

    def test_check_links_scans_nested_list_paragraphs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text(
                "- item\n\n    [missing](nope.md)\n", encoding="utf-8"
            )
            validator.check_links(doc)
        self.assertEqual(len(validator.errors), 1)
        self.assertIn("unresolved link", validator.errors[0])

    def test_heading_slugs_handle_comments_setext_markup_and_collisions(self) -> None:
        text = (
            "<!--\n# Hidden\n-->\n"
            "Overview\n========\n"
            "# _Emphasized Overview_\n"
            "# A\n# A\n# A-1\n"
        )
        self.assertEqual(
            validator.heading_slugs(text),
            {"overview", "emphasized-overview", "a", "a-1", "a-1-1"},
        )

    def test_check_links_validates_angle_bracket_destinations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "guide.md").write_text("# Guide\n", encoding="utf-8")
            (root / "install guide.md").write_text("# Guide\n", encoding="utf-8")
            doc = root / "doc.md"
            doc.write_text(
                "[guide](<guide.md>) and [spaced](<install guide.md>)\n",
                encoding="utf-8",
            )
            validator.check_links(doc)
        self.assertEqual(validator.errors, [])

    def test_check_links_reports_missing_angle_bracket_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text("[guide](<missing guide.md>)\n", encoding="utf-8")
            validator.check_links(doc)
        self.assertEqual(len(validator.errors), 1)
        self.assertIn("unresolved link", validator.errors[0])

    def test_check_links_validates_reference_definitions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "guide.md").write_text("# Guide\n", encoding="utf-8")
            doc = root / "doc.md"
            doc.write_text(
                "See [the guide][g] and [the guide][].\n\n"
                "[G]: guide.md\n[the guide]: guide.md\n",
                encoding="utf-8",
            )
            validator.check_links(doc)
        self.assertEqual(validator.errors, [])

    def test_check_links_validates_multiline_reference_definitions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "guide.md").write_text("# Guide\n", encoding="utf-8")
            doc = root / "doc.md"
            doc.write_text(
                "See [the guide][g].\n\n[g]:\n  guide.md\n", encoding="utf-8"
            )
            validator.check_links(doc)
        self.assertEqual(validator.errors, [])

    def test_check_links_validates_blockquote_reference_definitions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "guide.md").write_text("# Guide\n", encoding="utf-8")
            doc = root / "doc.md"
            doc.write_text(
                "> [g]: guide.md\n\nSee [the guide][g].\n", encoding="utf-8"
            )
            validator.check_links(doc)
        self.assertEqual(validator.errors, [])

    def test_check_links_reports_missing_reference_definition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text("[g]: missing.md\n", encoding="utf-8")
            validator.check_links(doc)
        self.assertEqual(len(validator.errors), 1)
        self.assertIn("unresolved link", validator.errors[0])

    def test_check_links_reports_undefined_reference_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text("See [the guide][missing].\n", encoding="utf-8")
            validator.check_links(doc)
        self.assertEqual(len(validator.errors), 1)
        self.assertIn("undefined reference link label", validator.errors[0])

    def test_check_links_ignores_footnote_definitions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text(
                "Claim.[^note]\n\n[^note]: src/not-a-link.cs L1-L2\n",
                encoding="utf-8",
            )
            validator.check_links(doc)
        self.assertEqual(validator.errors, [])

    def test_check_links_reports_unreadable_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            validator.check_links(Path(tmp) / "missing.md")
        self.assertEqual(len(validator.errors), 1)
        self.assertIn("cannot read", validator.errors[0])

    def test_check_links_resolves_bundle_absolute_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.md").write_text(
                '---\nokf_version: "0.2"\n---\n', encoding="utf-8"
            )
            (root / "concept.md").write_text("# Concept\n", encoding="utf-8")
            doc = root / "inventory" / "doc.md"
            doc.parent.mkdir()
            doc.write_text("[x](/concept.md)\n", encoding="utf-8")
            validator.check_links(doc)
        self.assertEqual(validator.errors, [])

    def test_check_links_reports_missing_bundle_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.md").write_text(
                '---\nokf_version: "0.2"\n---\n', encoding="utf-8"
            )
            doc = root / "doc.md"
            doc.write_text("[x](/inventory/missing.md)\n", encoding="utf-8")
            validator.check_links(doc)
        self.assertEqual(len(validator.errors), 1)
        self.assertIn("unresolved link", validator.errors[0])

    def test_check_links_skips_bundle_links_without_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text("[x](/inventory/missing.md)\n", encoding="utf-8")
            validator.check_links(doc)
        self.assertEqual(validator.errors, [])

    def test_find_bundle_root_returns_nearest_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.md").write_text(
                '---\nokf_version: "0.2"\n---\n', encoding="utf-8"
            )
            nested = root / "inventory" / "nested"
            nested.mkdir(parents=True)
            self.assertEqual(validator.find_bundle_root(nested), root)

    def test_find_bundle_root_ignores_index_without_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.md").write_text("# Index\n", encoding="utf-8")
            nested = root / "inventory"
            nested.mkdir()
            self.assertIsNone(validator.find_bundle_root(nested))

    def _write_plugin(
        self, root: Path, name: str, version: str = "1.0.0"
    ) -> Path:
        plugin_dir = root / "plugins" / name
        plugin_dir.mkdir(parents=True, exist_ok=True)
        (plugin_dir / "plugin.json").write_text(
            json.dumps(
                {"$schema": validator.PLUGIN_SCHEMA, "name": name, "version": version}
            ),
            encoding="utf-8",
        )
        return plugin_dir

    def _write_market(
        self, root: Path, version: str, entries: list[dict] | None = None
    ) -> None:
        market = root / ".github" / "plugin"
        market.mkdir(parents=True, exist_ok=True)
        if entries is None:
            entries = [
                {
                    "name": "sdlc",
                    "version": version,
                    "source": "./plugins/sdlc",
                }
            ]
        (market / "marketplace.json").write_text(
            json.dumps({"metadata": {"version": version}, "plugins": entries}),
            encoding="utf-8",
        )

    def _write_versions(
        self,
        root: Path,
        plugin_version: str,
        metadata_version: str,
        entry_version: str,
        changelog: str,
        plugin_name: str = "sdlc",
    ) -> None:
        self._write_plugin(root, plugin_name, plugin_version)
        self._write_market(
            root,
            metadata_version,
            [
                {
                    "name": plugin_name,
                    "version": entry_version,
                    "source": f"./plugins/{plugin_name}",
                }
            ],
        )
        (root / "CHANGELOG.md").write_text(changelog, encoding="utf-8")

    def test_check_versions_accepts_matching_versions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_versions(root, "9.9.9", "9.9.9", "9.9.9", "## [9.9.9]\n")
            with mock.patch.object(validator, "ROOT", root):
                validator.check_versions()
        self.assertEqual(validator.errors, [])

    def test_check_versions_accepts_lockstep_plugins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_plugin(root, "sdlc", "9.9.9")
            self._write_plugin(root, "discovery", "9.9.9")
            self._write_market(
                root,
                "9.9.9",
                [
                    {
                        "name": "sdlc",
                        "version": "9.9.9",
                        "source": "./plugins/sdlc",
                    },
                    {
                        "name": "discovery",
                        "version": "9.9.9",
                        "source": "./plugins/discovery",
                    },
                ],
            )
            (root / "CHANGELOG.md").write_text("## [9.9.9]\n", encoding="utf-8")
            with mock.patch.object(validator, "ROOT", root):
                validator.check_versions()
        self.assertEqual(validator.errors, [])

    def test_check_versions_reports_lockstep_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_plugin(root, "sdlc", "1.0.0")
            self._write_plugin(root, "discovery", "1.1.0")
            self._write_market(
                root,
                "1.0.0",
                [
                    {
                        "name": "sdlc",
                        "version": "1.0.0",
                        "source": "./plugins/sdlc",
                    },
                    {
                        "name": "discovery",
                        "version": "1.0.0",
                        "source": "./plugins/discovery",
                    },
                ],
            )
            (root / "CHANGELOG.md").write_text("## [1.0.0]\n", encoding="utf-8")
            with mock.patch.object(validator, "ROOT", root):
                validator.check_versions()
        self.assertTrue(
            any("version lockstep" in error for error in validator.errors)
        )

    def test_check_versions_reports_unlisted_plugin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_plugin(root, "sdlc", "1.0.0")
            self._write_plugin(root, "discovery", "1.0.0")
            self._write_market(root, "1.0.0")
            (root / "CHANGELOG.md").write_text("## [1.0.0]\n", encoding="utf-8")
            with mock.patch.object(validator, "ROOT", root):
                validator.check_versions()
        self.assertTrue(
            any("is not listed" in error for error in validator.errors)
        )

    def test_check_versions_reports_source_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_plugin(root, "sdlc", "1.0.0")
            self._write_market(
                root,
                "1.0.0",
                [
                    {
                        "name": "sdlc",
                        "version": "1.0.0",
                        "source": "./plugins/elsewhere",
                    }
                ],
            )
            (root / "CHANGELOG.md").write_text("## [1.0.0]\n", encoding="utf-8")
            with mock.patch.object(validator, "ROOT", root):
                validator.check_versions()
        self.assertTrue(
            any("does not resolve to" in error for error in validator.errors)
        )

    def test_check_versions_reports_unknown_marketplace_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_plugin(root, "sdlc", "1.0.0")
            self._write_market(
                root,
                "1.0.0",
                [
                    {
                        "name": "ghost",
                        "version": "1.0.0",
                        "source": "./plugins/ghost",
                    }
                ],
            )
            (root / "CHANGELOG.md").write_text("## [1.0.0]\n", encoding="utf-8")
            with mock.patch.object(validator, "ROOT", root):
                validator.check_versions()
        self.assertTrue(
            any("no plugin manifest named" in error for error in validator.errors)
        )

    def test_check_versions_reports_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_versions(root, "1.0.0", "1.0.0", "2.0.0", "## [1.0.0]\n")
            with mock.patch.object(validator, "ROOT", root):
                validator.check_versions()
        self.assertTrue(any("version mismatch" in error for error in validator.errors))

    def test_check_versions_rejects_non_semver_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_versions(root, "1.0", "1.0", "1.0", "## [1.0]\n")
            with mock.patch.object(validator, "ROOT", root):
                validator.check_versions()
        self.assertTrue(
            any("semantic versioning" in error for error in validator.errors)
        )

    def test_is_semver_validates_prerelease_and_build_identifiers(self) -> None:
        self.assertTrue(validator.is_semver("1.2.3-rc.1+build.4"))
        self.assertTrue(validator.is_semver("1.2.3+build.01"))
        self.assertFalse(validator.is_semver("01.2.3"))
        self.assertFalse(validator.is_semver("1.2.3-01"))

    def test_check_versions_reports_missing_changelog_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_versions(root, "1.0.0", "1.0.0", "1.0.0", "# Changelog\n")
            with mock.patch.object(validator, "ROOT", root):
                validator.check_versions()
        self.assertTrue(any("CHANGELOG.md" in error for error in validator.errors))

    def test_check_versions_reports_unreadable_changelog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_versions(root, "1.0.0", "1.0.0", "1.0.0", "## [1.0.0]\n")
            (root / "CHANGELOG.md").unlink()
            with mock.patch.object(validator, "ROOT", root):
                validator.check_versions()
        self.assertTrue(any("cannot read" in error for error in validator.errors))

    def test_check_versions_reports_non_object_plugin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_versions(root, "1.0.0", "1.0.0", "1.0.0", "## [1.0.0]\n")
            (root / "plugins" / "sdlc" / "plugin.json").write_text(
                "[]", encoding="utf-8"
            )
            with mock.patch.object(validator, "ROOT", root):
                validator.check_versions()
        self.assertTrue(
            any("plugin.json" in error and "JSON object" in error for error in validator.errors)
        )

    def test_check_versions_reports_non_object_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_versions(root, "1.0.0", "1.0.0", "1.0.0", "## [1.0.0]\n")
            market = root / ".github" / "plugin" / "marketplace.json"
            market.write_text(
                json.dumps({"metadata": [], "plugins": []}), encoding="utf-8"
            )
            with mock.patch.object(validator, "ROOT", root):
                validator.check_versions()
        self.assertTrue(
            any("'metadata' must be an object" in error for error in validator.errors)
        )

    def test_check_versions_reports_non_array_plugins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_versions(root, "1.0.0", "1.0.0", "1.0.0", "## [1.0.0]\n")
            market = root / ".github" / "plugin" / "marketplace.json"
            market.write_text(
                json.dumps({"metadata": {"version": "1.0.0"}, "plugins": {}}),
                encoding="utf-8",
            )
            with mock.patch.object(validator, "ROOT", root):
                validator.check_versions()
        self.assertTrue(
            any("'plugins' must be an array" in error for error in validator.errors)
        )

    def test_check_versions_reports_non_object_plugin_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_versions(root, "1.0.0", "1.0.0", "1.0.0", "## [1.0.0]\n")
            market = root / ".github" / "plugin" / "marketplace.json"
            market.write_text(
                json.dumps({"metadata": {"version": "1.0.0"}, "plugins": ["bad"]}),
                encoding="utf-8",
            )
            with mock.patch.object(validator, "ROOT", root):
                validator.check_versions()
        self.assertTrue(
            any("plugins[0] must be an object" in error for error in validator.errors)
        )

    def test_check_actor_versions_reports_non_object_plugin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_plugin(root, "sdlc", "1.0.0")
            (root / "plugins" / "sdlc" / "plugin.json").write_text(
                "[]", encoding="utf-8"
            )
            with mock.patch.object(validator, "ROOT", root):
                validator.check_actor_versions()
        self.assertTrue(
            any("plugin.json" in error and "JSON object" in error for error in validator.errors)
        )

    def _write_actor(
        self,
        root: Path,
        skill: str,
        version: str,
        plugin_version: str,
        plugin: str = "sdlc",
    ) -> None:
        skill_dir = root / "plugins" / plugin / "skills" / skill
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            f"generated: {{ by: {skill}/{version}, at: 2026-01-01T00:00:00Z }}\n",
            encoding="utf-8",
        )
        self._write_plugin(root, plugin, plugin_version)

    def test_check_actor_versions_accepts_matching_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_actor(root, "demo-skill", "1.0.0", "1.0.0")
            with mock.patch.object(validator, "ROOT", root):
                validator.check_actor_versions()
        self.assertEqual(validator.errors, [])

    def test_check_actor_versions_reports_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_actor(root, "demo-skill", "9.9.9", "1.0.0")
            with mock.patch.object(validator, "ROOT", root):
                validator.check_actor_versions()
        self.assertTrue(
            any("does not match plugin version" in error for error in validator.errors)
        )

    def test_check_actor_versions_skips_non_skill_actors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_actor(root, "demo-skill", "1.0.0", "2.0.0")
            skill_md = (
                root / "plugins" / "sdlc" / "skills" / "demo-skill" / "SKILL.md"
            )
            skill_md.write_text(
                "generated: { by: external-tool/9.9.9, at: 2026-01-01T00:00:00Z }\n",
                encoding="utf-8",
            )
            with mock.patch.object(validator, "ROOT", root):
                validator.check_actor_versions("2.0.0")
        self.assertEqual(validator.errors, [])

    def test_check_actor_versions_reads_multiline_generated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_actor(root, "demo-skill", "1.0.0", "1.0.0")
            skill_md = (
                root / "plugins" / "sdlc" / "skills" / "demo-skill" / "SKILL.md"
            )
            skill_md.write_text(
                "generated:\n  by: demo-skill/9.9.9\n  at: 2026-01-01T00:00:00Z\n",
                encoding="utf-8",
            )
            with mock.patch.object(validator, "ROOT", root):
                validator.check_actor_versions()
        self.assertTrue(
            any("does not match plugin version" in error for error in validator.errors)
        )

    def _write_manifest_shapes(
        self,
        root: Path,
        plugin_name: str = "sdlc",
        manifest_name: str | None = None,
        source: str = "./plugins/sdlc",
        mcp_servers: object = None,
    ) -> None:
        dir_name = plugin_name or "demo"
        plugin_dir = root / "plugins" / dir_name
        plugin_dir.mkdir(parents=True, exist_ok=True)
        (plugin_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "$schema": validator.PLUGIN_SCHEMA,
                    "name": plugin_name if manifest_name is None else manifest_name,
                }
            ),
            encoding="utf-8",
        )
        if mcp_servers is not None:
            (plugin_dir / "mcp.json").write_text(
                json.dumps(
                    {
                        "$schema": validator.MCP_SCHEMA,
                        "mcpServers": mcp_servers,
                    }
                ),
                encoding="utf-8",
            )
        market = root / ".github" / "plugin"
        market.mkdir(parents=True, exist_ok=True)
        (market / "marketplace.json").write_text(
            json.dumps(
                {
                    "name": "sdlc-plugins",
                    "owner": {"name": "Owner"},
                    "plugins": [{"name": plugin_name, "source": source}],
                }
            ),
            encoding="utf-8",
        )

    def test_check_manifest_shapes_accepts_valid_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_manifest_shapes(root)
            with mock.patch.object(validator, "ROOT", root):
                validator.check_manifest_shapes()
        self.assertEqual(validator.errors, [])

    def test_check_manifest_shapes_reports_missing_source_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_manifest_shapes(root, source="./missing")
            with mock.patch.object(validator, "ROOT", root):
                validator.check_manifest_shapes()
        self.assertTrue(any("does not exist" in error for error in validator.errors))

    def test_check_manifest_shapes_reports_source_without_plugin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "plugins" / "empty").mkdir(parents=True)
            self._write_manifest_shapes(root, source="./plugins/empty")
            with mock.patch.object(validator, "ROOT", root):
                validator.check_manifest_shapes()
        self.assertTrue(any("has no plugin.json" in error for error in validator.errors))

    def test_check_manifest_shapes_reports_invalid_plugin_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_manifest_shapes(root, plugin_name="", manifest_name="")
            with mock.patch.object(validator, "ROOT", root):
                validator.check_manifest_shapes()
        self.assertTrue(
            any("plugin.json" in error and "name" in error for error in validator.errors)
        )

    def test_check_manifest_shapes_reports_invalid_mcp_servers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_manifest_shapes(root, mcp_servers=[])
            with mock.patch.object(validator, "ROOT", root):
                validator.check_manifest_shapes()
        self.assertTrue(any("mcpServers" in error for error in validator.errors))


class MultiRootRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        validator.errors.clear()
        validator.warnings.clear()

    def tearDown(self) -> None:
        validator.errors.clear()
        validator.warnings.clear()

    def _write_skill(self, root: Path, plugin: str, skill: str) -> None:
        skill_dir = root / "plugins" / plugin / "skills" / skill
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {skill}\ndescription: A skill.\n---\n\nBody.\n",
            encoding="utf-8",
        )

    def _write_plugin(self, root: Path, name: str) -> None:
        plugin_dir = root / "plugins" / name
        plugin_dir.mkdir(parents=True, exist_ok=True)
        (plugin_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "$schema": validator.PLUGIN_SCHEMA,
                    "name": name,
                    "version": "1.0.0",
                }
            ),
            encoding="utf-8",
        )

    def _write_market(self, root: Path, names: list[str]) -> None:
        market = root / ".github" / "plugin"
        market.mkdir(parents=True, exist_ok=True)
        (market / "marketplace.json").write_text(
            json.dumps(
                {
                    "name": "test-market",
                    "owner": {"name": "Owner"},
                    "metadata": {"version": "1.0.0"},
                    "plugins": [
                        {
                            "name": name,
                            "version": "1.0.0",
                            "source": f"./plugins/{name}",
                        }
                        for name in names
                    ],
                }
            ),
            encoding="utf-8",
        )

    def _write_support(self, root: Path) -> None:
        (root / "README.md").write_text("# Test\n", encoding="utf-8")
        (root / "CHANGELOG.md").write_text("## [1.0.0]\n", encoding="utf-8")

    def _run_main(self) -> int:
        with contextlib.redirect_stdout(io.StringIO()):
            return validator.main()

    def test_main_accepts_two_valid_plugins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for plugin in ("alpha", "beta"):
                self._write_plugin(root, plugin)
                self._write_skill(root, plugin, f"{plugin}-skill")
            self._write_market(root, ["alpha", "beta"])
            self._write_support(root)
            with mock.patch.object(validator, "ROOT", root):
                result = self._run_main()
        self.assertEqual(result, 0, validator.errors)

    def test_main_reports_duplicate_skill_across_plugins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for plugin in ("alpha", "beta"):
                self._write_plugin(root, plugin)
                self._write_skill(root, plugin, "shared-name")
            self._write_market(root, ["alpha", "beta"])
            self._write_support(root)
            with mock.patch.object(validator, "ROOT", root):
                result = self._run_main()
        self.assertEqual(result, 1)
        self.assertTrue(
            any("duplicate skill name" in error for error in validator.errors)
        )

    def test_main_reports_missing_plugin_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_skill(root, "ghost", "ghost-skill")
            self._write_market(root, ["ghost"])
            self._write_support(root)
            with mock.patch.object(validator, "ROOT", root):
                result = self._run_main()
        self.assertEqual(result, 1)
        self.assertTrue(any("missing plugin.json" in error for error in validator.errors))

    def test_main_reports_missing_skills_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_plugin(root, "alpha")
            self._write_market(root, ["alpha"])
            self._write_support(root)
            with mock.patch.object(validator, "ROOT", root):
                result = self._run_main()
        self.assertEqual(result, 1)
        self.assertTrue(any("missing skills/" in error for error in validator.errors))

    def test_repository_main_passes(self) -> None:
        self.assertEqual(self._run_main(), 0, validator.errors)


class ProfileContractTests(unittest.TestCase):
    def setUp(self) -> None:
        validator.errors.clear()
        validator.warnings.clear()

    def tearDown(self) -> None:
        validator.errors.clear()
        validator.warnings.clear()

    def _profile(self) -> dict:
        path = validator.ROOT / "tests" / "fixtures" / "profile" / "example.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_committed_sample_is_valid(self) -> None:
        validator.check_profile_contract(self._profile(), "profile")
        self.assertEqual(validator.errors, [])

    def test_missing_schema_is_rejected(self) -> None:
        profile = self._profile()
        del profile["schema"]
        validator.check_profile_contract(profile, "profile")
        self.assertTrue(any("'schema' must be" in error for error in validator.errors))

    def test_unknown_command_is_rejected(self) -> None:
        profile = self._profile()
        profile["commands"]["deploy"] = {"cmd": "make deploy", "source": "Makefile"}
        validator.check_profile_contract(profile, "profile")
        self.assertTrue(any("unknown command" in error for error in validator.errors))

    def test_command_without_source_is_rejected(self) -> None:
        profile = self._profile()
        profile["commands"]["test"] = {"cmd": "pytest"}
        validator.check_profile_contract(profile, "profile")
        self.assertTrue(
            any("'source' must be a non-empty string" in error for error in validator.errors)
        )

    def test_absolute_workspace_path_is_rejected(self) -> None:
        profile = self._profile()
        profile["workspaces"]["/etc/passwd"] = {"commands": {}}
        validator.check_profile_contract(profile, "profile")
        self.assertTrue(
            any("relative POSIX path" in error for error in validator.errors)
        )

    def test_workspace_must_override_commands(self) -> None:
        profile = self._profile()
        profile["workspaces"]["services/api"] = {}
        validator.check_profile_contract(profile, "profile")
        self.assertTrue(any("missing 'commands'" in error for error in validator.errors))

    def test_invalid_ci_is_rejected(self) -> None:
        profile = self._profile()
        profile["ci"] = {"file": "", "jobs": "test"}
        validator.check_profile_contract(profile, "profile")
        self.assertTrue(
            any("'file' must be a non-empty string" in error for error in validator.errors)
        )
        self.assertTrue(
            any("'jobs' must be an array" in error for error in validator.errors)
        )


class OkfBundleFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        validator.errors.clear()
        validator.warnings.clear()

    def tearDown(self) -> None:
        validator.errors.clear()
        validator.warnings.clear()

    def test_minimal_fixture_bundle_is_conformant(self) -> None:
        """The fixture is deliberately minimal: it exercises packaging, not every template section."""
        root = validator.ROOT / "tests" / "fixtures" / "okf-bundle"

        index_frontmatter = validator.read_frontmatter(root / "index.md")
        self.assertIsNotNone(index_frontmatter)
        index_fields = validator.parse_frontmatter(index_frontmatter or "")
        self.assertEqual(index_fields.get("okf_version"), "0.2")

        index_text = (root / "index.md").read_text(encoding="utf-8")
        for target in (
            "charter.md",
            "system.md",
            "ledger.md",
            "inventory/invoice-calculator.md",
            "flows/invoice-event.md",
        ):
            self.assertIn(target, index_text)

        log_text = (root / "log.md").read_text(encoding="utf-8")
        self.assertRegex(log_text, r"(?m)^## \d{4}-\d{2}-\d{2}$")

        charter_text = (root / "charter.md").read_text(encoding="utf-8")
        self.assertIn("# Questions asked", charter_text)

        ledger_text = (root / "ledger.md").read_text(encoding="utf-8")
        for heading in ("# Repositories", "# Shards", "# Coverage", "# Exclusions",
                        "# Budget", "# Inventory-only"):
            self.assertIn(heading, ledger_text)

        system_text = (root / "system.md").read_text(encoding="utf-8")
        self.assertIn("inventory/invoice-calculator.md", system_text)

        concept_paths: list[str] = []
        for path in sorted(root.rglob("*.md")):
            with self.subTest(path=str(path.relative_to(root))):
                validator.check_links(path)
                if path.name in ("index.md", "log.md"):
                    continue
                relative = path.relative_to(root).as_posix()
                concept_paths.append(relative)
                frontmatter = validator.read_frontmatter(path)
                self.assertIsNotNone(frontmatter)
                fields = validator.parse_frontmatter(frontmatter or "")
                self.assertTrue(fields.get("type"))
                self.assertTrue(fields.get("title"))
                self.assertTrue(fields.get("description"))
                self.assertIn(
                    fields.get("evidence"),
                    {"confirmed", "corroborated", "inferred", "unknown"},
                )
                self.assertIn(
                    fields.get("status"), {"draft", "stable", "deprecated"}
                )
                text = path.read_text(encoding="utf-8")
                self.assertRegex(
                    text,
                    r"(?m)^generated:\s*\{\s*by:\s*[a-z0-9-]+/\d+\.\d+\.\d+,\s*"
                    r"at:\s*[^}]+\}\s*$",
                )
                if "repo://" in text:
                    source_entries = re.findall(
                        r"(?ms)^  - id:\s*[^\n]+\n(.*?)(?=^  - id:|\Z)",
                        frontmatter or "",
                    )
                    repo_sources = 0
                    for entry in source_entries:
                        resource = re.search(
                            r"(?m)^\s+resource:\s*repo://([^/\s#]+)",
                            entry,
                        )
                        if resource is None:
                            continue
                        repo_sources += 1
                        repo = re.search(r"(?m)^\s+repo:\s*(\S+)", entry)
                        commit = re.search(r"(?m)^\s+commit:\s*(\S+)", entry)
                        self.assertIsNotNone(repo, "repo:// source needs its own repo field")
                        self.assertIsNotNone(
                            commit, "repo:// source needs its own commit field"
                        )
                        self.assertEqual(repo.group(1), resource.group(1))
                    self.assertGreater(
                        repo_sources, 0, "repo:// evidence needs source entries"
                    )
                    self.assertIn("sources:", text)
                if path.name in ("charter.md", "ledger.md", "system.md"):
                    # Process and aggregate documents link to sourced concepts instead.
                    self.assertNotRegex(validator.strip_code(text), r"(?m)^sources:")

        for relative in concept_paths:
            with self.subTest(reachable=relative):
                self.assertTrue(
                    self._is_reachable(relative, root, index_text, system_text)
                )

        self.assertEqual(validator.errors, [])

    def _is_reachable(
        self, relative: str, root: Path, index_text: str, system_text: str
    ) -> bool:
        """A concept is reachable from the root index, system map, or a parent index."""
        if relative in index_text or relative in system_text:
            return True
        concept = root / relative
        for parent in concept.parents:
            if parent == root:
                break
            parent_index = parent / "index.md"
            if not parent_index.is_file():
                continue
            parent_text = parent_index.read_text(encoding="utf-8")
            if relative in parent_text or concept.name in parent_text:
                return True
        return False


if __name__ == "__main__":
    unittest.main()
