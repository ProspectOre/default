import os

from scripts.helpers.integration_path import get_integration_path
from scripts.helpers.safe_json import read_json_regular_file


def get_manifest():
    manifest_path = os.path.join(get_integration_path(), "manifest.json")
    manifest = read_json_regular_file(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError(f"Manifest {manifest_path} must contain a JSON object")
    return manifest
