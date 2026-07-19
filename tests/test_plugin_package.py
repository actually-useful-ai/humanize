import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HumanizePluginPackageTests(unittest.TestCase):
    def test_codex_manifest_exposes_the_humanize_skill(self):
        manifest_path = ROOT / ".codex-plugin" / "plugin.json"

        self.assertTrue(manifest_path.is_file(), "Codex plugin manifest is missing")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["name"], "humanize")
        self.assertEqual(manifest["version"], "1.2.0")
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


if __name__ == "__main__":
    unittest.main()
