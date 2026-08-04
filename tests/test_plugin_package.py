import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCANNER_PATH = ROOT / "skills" / "humanize" / "scripts" / "doc_humanizer.py"
EXPECTED_VERSION = "1.2.1"


def load_scanner_module():
    spec = importlib.util.spec_from_file_location("humanize_doc_humanizer", SCANNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load scanner from {SCANNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SCANNER = load_scanner_module()


class HumanizePluginPackageTests(unittest.TestCase):
    def test_codex_manifest_exposes_the_humanize_skill(self):
        manifest_path = ROOT / ".codex-plugin" / "plugin.json"

        self.assertTrue(manifest_path.is_file(), "Codex plugin manifest is missing")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["name"], "humanize")
        self.assertEqual(manifest["version"], EXPECTED_VERSION)
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(manifest["author"]["name"], "Luke Steuber")
        self.assertNotIn("Claude", manifest["description"])

        interface = manifest["interface"]
        self.assertEqual(interface["developerName"], "Luke Steuber")
        self.assertNotIn("Claude", interface["shortDescription"])
        self.assertNotIn("Claude", interface["longDescription"])
        prompts = interface["defaultPrompt"]
        self.assertIsInstance(prompts, list)
        self.assertGreaterEqual(len(prompts), 1)
        self.assertLessEqual(len(prompts), 3)
        self.assertTrue(all(isinstance(prompt, str) and prompt for prompt in prompts))
        self.assertTrue(all(len(prompt) <= 128 for prompt in prompts))

    def test_runtime_manifests_and_marketplace_share_package_identity(self):
        paths = {
            "Codex": ROOT / ".codex-plugin" / "plugin.json",
            "Cursor": ROOT / ".cursor-plugin" / "plugin.json",
            "Claude": ROOT / ".claude-plugin" / "plugin.json",
        }
        manifests = {
            runtime: json.loads(path.read_text(encoding="utf-8"))
            for runtime, path in paths.items()
        }
        marketplace = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        listing = marketplace["plugins"][0]

        for field in ("name", "version"):
            values = {manifest[field] for manifest in manifests.values()}
            values.add(listing[field])
            self.assertEqual(values, {listing[field]}, f"mismatched {field}")
        self.assertEqual(listing["version"], EXPECTED_VERSION)
        self.assertEqual(manifests["Codex"]["skills"], "./skills/")
        self.assertEqual(manifests["Cursor"]["skills"], "./skills/")
        self.assertEqual(manifests["Cursor"]["author"]["name"], "Luke Steuber")

    def test_readme_documents_current_codex_and_claude_install_paths(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("### Codex", readme)
        self.assertIn("Plugin Directory", readme)
        self.assertIn("Import local plugin", readme)
        self.assertIn('if [ -e "$target" ] || [ -L "$target" ]', readme)
        self.assertIn("### Claude Code", readme)
        self.assertIn("/plugin marketplace add actually-useful-ai/humanize", readme)
        self.assertIn(
            "/plugin install humanize@actually-useful-ai-humanize", readme
        )
        self.assertNotIn("/install actually-useful-ai/humanize", readme)

    def test_skill_resolves_the_scanner_from_its_own_directory(self):
        skill = (ROOT / "skills" / "humanize" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("HUMANIZE_SKILL_ROOT", skill)
        self.assertIn("loaded `SKILL.md`", skill)
        self.assertNotIn("python3 scripts/doc_humanizer.py", skill)

    def test_public_manifests_use_the_public_author_email(self):
        paths = (
            ROOT / ".codex-plugin" / "plugin.json",
            ROOT / ".cursor-plugin" / "plugin.json",
            ROOT / ".claude-plugin" / "plugin.json",
            ROOT / ".claude-plugin" / "marketplace.json",
        )
        for path in paths:
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("dr.eamer.dev", content)
            self.assertIn("luke@lukesteuber.com", content)

    def test_plural_first_person_requires_manual_context_review(self):
        humanizer = SCANNER.DocumentHumanizer()

        transformed = humanizer.apply_transforms("We are ready. Our work is done.")

        self.assertEqual(transformed, "We are ready. Our work is done.")
        self.assertNotIn("I are", transformed)

    def test_high_confidence_transforms_compose_on_the_same_line(self):
        humanizer = SCANNER.DocumentHumanizer()

        transformed = humanizer.apply_transforms(
            "Made with Claude ✅ fully implemented"
        )

        self.assertEqual(transformed.strip(), "")

    def test_eof_paragraph_em_dashes_are_detected_and_fixed_consistently(self):
        humanizer = SCANNER.DocumentHumanizer()
        content = "First — one\nsecond — two\nthird — three"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.md"
            path.write_text(content, encoding="utf-8")

            results = humanizer.scan_file(str(path))

        self.assertIn("em_dashes", results)
        self.assertEqual(len(results["em_dashes"]), 1)
        transformed = humanizer.apply_transforms(content)
        self.assertNotIn("—", transformed)


if __name__ == "__main__":
    unittest.main()
