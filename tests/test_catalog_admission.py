import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.changed.catalog import (
    AdmissionError,
    get_admission,
    require_maintenance_scope,
)


class CatalogAdmissionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        self.write_json("integration", ["owner/one", "owner/two"])
        self.write_json("blacklist", [])
        self.git("add", "integration", "blacklist")
        self.git("commit", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD")

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.check_output(
            ["git", "-C", str(self.repo), *args], text=True
        ).strip()

    def write_json(self, path, value):
        (self.repo / path).write_text(json.dumps(value), encoding="utf-8")

    def commit_head(self):
        self.git("add", "-A")
        self.git("commit", "-qm", "candidate")
        return self.git("rev-parse", "HEAD")

    def test_accepts_exactly_one_sorted_addition(self):
        self.write_json("integration", ["owner/one", "owner/three", "owner/two"])
        head = self.commit_head()
        self.assertEqual(
            get_admission(self.repo, self.base, head),
            ("integration", "owner/three"),
        )

    def test_rejects_bundled_deletion(self):
        self.write_json("integration", ["owner/three", "owner/two"])
        head = self.commit_head()
        with self.assertRaises(AdmissionError):
            get_admission(self.repo, self.base, head)

    def test_rejects_unrelated_registry_or_policy_edit(self):
        self.write_json("integration", ["owner/one", "owner/three", "owner/two"])
        self.write_json("blacklist", ["owner/blocked"])
        head = self.commit_head()
        with self.assertRaises(AdmissionError):
            get_admission(self.repo, self.base, head)

    def test_rejects_duplicate_or_malformed_repository_entries(self):
        for proposed in (
            ["owner/one", "owner/three", "owner/three", "owner/two"],
            ["owner/one", "bad name", "owner/two"],
        ):
            with self.subTest(proposed=proposed):
                self.write_json("integration", proposed)
                head = self.commit_head()
                with self.assertRaises(AdmissionError):
                    get_admission(self.repo, self.base, head)

    def test_rejects_category_symlink_blob(self):
        (self.repo / "integration").unlink()
        (self.repo / "integration").symlink_to("blacklist")
        head = self.commit_head()
        with self.assertRaisesRegex(AdmissionError, "regular non-executable file"):
            get_admission(self.repo, self.base, head)

    def test_maintenance_allows_docs_but_requires_label_for_registry_changes(self):
        (self.repo / "README.md").write_text("maintenance\n", encoding="utf-8")
        documentation_head = self.commit_head()
        require_maintenance_scope(self.repo, self.base, documentation_head)

        self.write_json("integration", ["owner/one", "owner/two", "owner/three"])
        registry_head = self.commit_head()
        with self.assertRaisesRegex(AdmissionError, "dedicated admission label"):
            require_maintenance_scope(self.repo, self.base, registry_head)


if __name__ == "__main__":
    unittest.main()
