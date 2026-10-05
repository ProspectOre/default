import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.helpers.integration_path import get_integration_path
from scripts.helpers.manifest import get_manifest
from scripts.helpers.safe_json import MAX_MANIFEST_SIZE, read_json_regular_file


class SafeManifestTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.integration = self.root / "custom_components" / "sample"
        self.integration.mkdir(parents=True)
        self.manifest = self.integration / "manifest.json"
        self.manifest.write_text(json.dumps({"domain": "sample"}), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_reads_one_regular_bounded_manifest(self):
        self.assertEqual(get_integration_path(str(self.root)), str(self.integration))
        self.assertEqual(read_json_regular_file(self.manifest), {"domain": "sample"})

    def test_rejects_symlink_manifest(self):
        self.manifest.unlink()
        self.manifest.symlink_to("/dev/zero")

        with self.assertRaises(ValueError):
            get_integration_path(str(self.root))
        with patch("scripts.helpers.manifest.get_integration_path", return_value=str(self.integration)):
            with self.assertRaises(ValueError):
                get_manifest()

    def test_rejects_fifo_manifest_without_blocking(self):
        self.manifest.unlink()
        os.mkfifo(self.manifest)

        with self.assertRaisesRegex(ValueError, "regular file"):
            get_integration_path(str(self.root))

    def test_rejects_manifest_over_size_limit(self):
        self.manifest.write_bytes(b" " * (MAX_MANIFEST_SIZE + 1))

        with self.assertRaisesRegex(ValueError, "byte limit"):
            get_integration_path(str(self.root))


if __name__ == "__main__":
    unittest.main()
