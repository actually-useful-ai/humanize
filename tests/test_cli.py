"""End-to-end command, profile, catalog, and nonmutation contracts."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/humanize/scripts/doc_humanizer.py'
RULES = json.loads((SCRIPT.parent.parent / 'references/rules.json').read_text())['rules']
spec = importlib.util.spec_from_file_location('cli_scanner', SCRIPT)
M = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = M
spec.loader.exec_module(M)

class CatalogTests(unittest.TestCase):
    def test_each_rule_has_positive_and_negative_examples(self):
        self.assertEqual(len({r['id'] for r in RULES}), len(RULES))
        for rule in RULES:
            with self.subTest(rule=rule['id']):
                h = M.DocumentHumanizer(profile=rule['profiles'][0])
                self.assertIn(rule['id'], [d.rule_id for d in h.scan_text(rule['example'], strict=True)])
                self.assertNotIn(rule['id'], [d.rule_id for d in h.scan_text(rule['counterexample'], strict=True)])
                self.assertFalse(rule['autofix'])

    def test_strict_and_profile_scope(self):
        h = M.DocumentHumanizer()
        self.assertEqual(h.scan_text('Furthermore, we exported CSV.'), [])
        self.assertEqual([d.rule_id for d in h.scan_text('Furthermore, we exported CSV.', strict=True)], ['H010'])
        self.assertEqual([d.rule_id for d in M.DocumentHumanizer('luke').scan_text('We exported CSV.')], ['H012'])

    def test_allow_terms_and_disabled_rules(self):
        text = 'At its core, the result? A timer.'
        h = M.DocumentHumanizer(config={'allow_terms': ['At its core'], 'disabled_rules': ['H004']})
        self.assertEqual(h.scan_text(text), [])
        with self.assertRaises(ValueError):
            M.DocumentHumanizer(config={'disabled_rules': ['typo']})

class CLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.file = self.root / 'sample.md'
        self.file.write_bytes(b'\xef\xbb\xbfIt is important to note that this might fail.\r\n')
    def tearDown(self):
        self.temp.cleanup()
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], cwd=self.root,
                              text=True, capture_output=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'})
    def test_fix_diff_and_dry_run_preserve_bytes_and_metadata(self):
        before = (self.file.read_bytes(), self.file.stat())
        for args in [('fix', self.file), ('diff', self.file), ('fix', self.file, '--dry-run', '--strict')]:
            r = self.run_cli(*args)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('0 files changed', r.stdout)
            self.assertIn('no automatic text changes', r.stdout)
        after = (self.file.read_bytes(), self.file.stat())
        self.assertEqual(before[0], after[0])
        self.assertEqual((before[1].st_mtime_ns,before[1].st_mode,before[1].st_ino),
                         (after[1].st_mtime_ns,after[1].st_mode,after[1].st_ino))
    def test_json_determinism_and_check_exit(self):
        a = self.run_cli('scan', self.root, '--format', 'json', '--check')
        b = self.run_cli('batch', self.root, '--parallel', '--format', 'json', '--check')
        self.assertEqual(a.returncode, 1, a.stderr)
        self.assertEqual(b.returncode, 1, b.stderr)
        first, second = json.loads(a.stdout), json.loads(b.stdout)
        self.assertEqual(first['files'], second['files'])
        self.assertEqual(first['changed_files'], 0)
    def test_protected_and_unsupported_are_not_clean(self):
        for name in ['AGENTS.md','page.html','LICENSE','CHANGELOG.md','CHANGELOG.txt']:
            path = self.root / name
            path.write_text('It is important to note that this fails.')
            r = self.run_cli('scan', path, '--format', 'json')
            self.assertEqual(r.returncode, 2)
            self.assertEqual(json.loads(r.stdout)['files'][0]['status'], 'skipped')
    def test_generated_directory_is_protected(self):
        directory = self.root/'generated'
        directory.mkdir()
        (directory/'sample.md').write_text('It is important to note that this fails.')
        r = self.run_cli('scan', directory, '--format', 'json')
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout)['files'][0]['status'], 'skipped')
    def test_errors_override_findings_and_batch_cannot_hide_failure(self):
        r = self.run_cli('scan', self.file, self.root/'missing.md', '--check', '--format', 'json')
        self.assertEqual(r.returncode, 2)
        self.assertIn('error', [f['status'] for f in json.loads(r.stdout)['files']])
    def test_invalid_utf8_is_an_error(self):
        self.file.write_bytes(b'\xff')
        self.assertEqual(self.run_cli('scan', self.file).returncode, 2)
    def test_duplicate_inputs_are_scanned_once(self):
        r = self.run_cli('scan', self.file, self.file, '--format', 'json')
        self.assertEqual(len(json.loads(r.stdout)['files']), 1)
    def test_symlink_is_skipped(self):
        link = self.root/'linked.md'
        link.symlink_to(self.file)
        self.assertEqual(self.run_cli('scan', link).returncode, 2)
    def test_config_narrows_and_rejects_unknown_keys(self):
        config = self.root/'config.json'
        config.write_text(json.dumps({'disabled_rules':['H001'],'audience':'installers'}))
        r = self.run_cli('scan', self.file, '--config', config, '--check', '--format', 'json')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)['context']['audience'], 'installers')
        config.write_text('{"shell":"echo bad"}')
        self.assertEqual(self.run_cli('scan', self.file, '--config', config).returncode, 2)
    def test_removed_flags_fail_with_migration_message(self):
        r = self.run_cli('fix', self.file, '--confidence', '0.1')
        self.assertEqual(r.returncode, 2)
        self.assertIn('removed in 2.0', r.stderr)
    def test_zero_files_and_invalid_worker_count(self):
        self.assertEqual(self.run_cli('scan').returncode, 2)
        self.assertEqual(self.run_cli('scan', self.file, '--max-workers','0').returncode, 2)

if __name__ == '__main__':
    unittest.main()
