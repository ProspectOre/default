import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate_catalog import validate


ROOT = Path(__file__).resolve().parents[1]


class ValidateCatalogTest(unittest.TestCase):
    def test_current_catalog_matches_the_trusted_schema_rules(self):
        validate(ROOT)

    def test_rejects_malformed_repository_and_required_properties(self):
        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp)
            for name in (
                "appdaemon",
                "blacklist",
                "critical",
                "integration",
                "netdaemon",
                "plugin",
                "python_script",
                "removed",
                "template",
                "theme",
            ):
                shutil.copy(ROOT / name, candidate / name)

            (candidate / "integration").write_text(
                json.dumps(["not a repository"]), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "invalid repository name"):
                validate(candidate)

            shutil.copy(ROOT / "integration", candidate / "integration")
            (candidate / "critical").write_text(
                json.dumps([{"repository": "owner/repo"}]), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "missing required property"):
                validate(candidate)


if __name__ == "__main__":
    unittest.main()
