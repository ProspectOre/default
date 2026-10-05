import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate_catalog import validate


ROOT = Path(__file__).resolve().parents[1]


class ValidateCatalogTest(unittest.TestCase):
    def _validate_critical_link(self, link):
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
            (candidate / "critical").write_text(
                json.dumps([{"repository": "owner/repo", "reason": "test", "link": link}]),
                encoding="utf-8",
            )
            validate(candidate)

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
            with self.assertRaisesRegex(ValueError, "is a required property"):
                validate(candidate)

    def test_critical_schema_accepts_absolute_uri_schemes_and_ipv6(self):
        for link in (
            "mailto:person@example.com",
            "urn:isbn:0451450523",
            "https://example.com/path?q=one%20two",
            "https://[2001:db8::1]/",
        ):
            with self.subTest(link=link):
                self._validate_critical_link(link)

    def test_critical_schema_rejects_malformed_absolute_uris(self):
        for link in (
            "https://exa mple.com",
            "https://example.com/bad\npath",
            "https://example.com/%GG",
            "https://[2001:db8::zzz]/",
        ):
            with self.subTest(link=link), self.assertRaisesRegex(ValueError, "uri"):
                self._validate_critical_link(link)


if __name__ == "__main__":
    unittest.main()
