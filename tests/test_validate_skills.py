"""Tests for the dependency-free skill validator."""

from __future__ import annotations

import json
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
    def test_every_skill_parses(self) -> None:
        skill_files = sorted((validator.SKILLS_DIR).glob("*/SKILL.md"))
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
        for path in sorted(validator.SKILLS_DIR.glob("*/SKILL.md")):
            validator.check_skill(path)
        self.assertEqual(validator.errors, [])


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

    def _write_versions(
        self,
        root: Path,
        plugin_version: str,
        metadata_version: str,
        entry_version: str,
        changelog: str,
    ) -> None:
        (root / "plugin.json").write_text(
            json.dumps({"version": plugin_version}), encoding="utf-8"
        )
        market = root / ".github" / "plugin"
        market.mkdir(parents=True)
        (market / "marketplace.json").write_text(
            json.dumps(
                {
                    "metadata": {"version": metadata_version},
                    "plugins": [{"name": "sdlc-plugins", "version": entry_version}],
                }
            ),
            encoding="utf-8",
        )
        (root / "CHANGELOG.md").write_text(changelog, encoding="utf-8")

    def test_check_versions_accepts_matching_versions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_versions(root, "9.9.9", "9.9.9", "9.9.9", "## [9.9.9]\n")
            with mock.patch.object(validator, "ROOT", root):
                validator.check_versions()
        self.assertEqual(validator.errors, [])

    def test_check_versions_reports_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_versions(root, "1.0.0", "1.0.0", "2.0.0", "## [1.0.0]\n")
            with mock.patch.object(validator, "ROOT", root):
                validator.check_versions()
        self.assertTrue(any("version mismatch" in error for error in validator.errors))

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

    def _write_actor(
        self, root: Path, skill: str, version: str, plugin_version: str
    ) -> None:
        skill_dir = root / "skills" / skill
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"generated: {{ by: {skill}/{version}, at: 2026-01-01T00:00:00Z }}\n",
            encoding="utf-8",
        )
        (root / "plugin.json").write_text(
            json.dumps({"version": plugin_version}), encoding="utf-8"
        )

    def test_check_actor_versions_accepts_matching_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_actor(root, "demo-skill", "1.0.0", "1.0.0")
            with mock.patch.object(validator, "ROOT", root), mock.patch.object(
                validator, "SKILLS_DIR", root / "skills"
            ):
                validator.check_actor_versions()
        self.assertEqual(validator.errors, [])

    def test_check_actor_versions_reports_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_actor(root, "demo-skill", "9.9.9", "1.0.0")
            with mock.patch.object(validator, "ROOT", root), mock.patch.object(
                validator, "SKILLS_DIR", root / "skills"
            ):
                validator.check_actor_versions()
        self.assertTrue(
            any("does not match plugin version" in error for error in validator.errors)
        )

    def test_check_actor_versions_skips_non_skill_actors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_actor(root, "demo-skill", "1.0.0", "2.0.0")
            skill_md = root / "skills" / "demo-skill" / "SKILL.md"
            skill_md.write_text(
                "generated: { by: external-tool/9.9.9, at: 2026-01-01T00:00:00Z }\n",
                encoding="utf-8",
            )
            with mock.patch.object(validator, "ROOT", root), mock.patch.object(
                validator, "SKILLS_DIR", root / "skills"
            ):
                validator.check_actor_versions()
        self.assertEqual(validator.errors, [])

    def test_check_actor_versions_reads_multiline_generated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "demo-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "generated:\n  by: demo-skill/9.9.9\n  at: 2026-01-01T00:00:00Z\n",
                encoding="utf-8",
            )
            (root / "plugin.json").write_text(
                json.dumps({"version": "1.0.0"}), encoding="utf-8"
            )
            with mock.patch.object(validator, "ROOT", root), mock.patch.object(
                validator, "SKILLS_DIR", root / "skills"
            ):
                validator.check_actor_versions()
        self.assertTrue(
            any("does not match plugin version" in error for error in validator.errors)
        )

    def _write_manifest_shapes(
        self,
        root: Path,
        plugin_name: str = "sdlc-plugins",
        source: str = ".",
        mcp_servers: object = None,
    ) -> None:
        (root / "plugin.json").write_text(
            json.dumps({"$schema": validator.PLUGIN_SCHEMA, "name": plugin_name}),
            encoding="utf-8",
        )
        (root / "mcp.json").write_text(
            json.dumps(
                {
                    "$schema": validator.MCP_SCHEMA,
                    "mcpServers": {} if mcp_servers is None else mcp_servers,
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
                    "plugins": [{"name": "sdlc-plugins", "source": source}],
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

    def test_check_manifest_shapes_reports_invalid_plugin_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_manifest_shapes(root, plugin_name="")
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



if __name__ == "__main__":
    unittest.main()
