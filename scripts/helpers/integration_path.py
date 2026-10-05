import os
import stat

from scripts.helpers.safe_json import read_json_regular_file


ADDITION_ROOT = "/tmp/repositories/addition"


def _raise_walk_error(error):
    raise error


def get_integration_path(root=ADDITION_ROOT):
    try:
        root_info = os.lstat(root)
    except OSError as error:
        raise ValueError(f"Cannot inspect cloned repository at {root}: {error}") from error
    if not stat.S_ISDIR(root_info.st_mode):
        raise ValueError(f"Cloned repository root {root} must be a real directory")

    manifests = []
    for directory, child_directories, filenames in os.walk(
        root, topdown=True, followlinks=False, onerror=_raise_walk_error
    ):
        child_directories[:] = [
            name
            for name in child_directories
            if not os.path.islink(os.path.join(directory, name))
        ]
        if "manifest.json" not in filenames:
            continue

        manifest_path = os.path.join(directory, "manifest.json")
        manifest = read_json_regular_file(manifest_path)
        if not isinstance(manifest, dict):
            raise ValueError(f"Manifest {manifest_path} must contain a JSON object")
        manifests.append(manifest_path)

    if len(manifests) != 1:
        raise ValueError("Expected exactly one regular integration manifest")
    return os.path.dirname(manifests[0])


if __name__ == "__main__":
    print(get_integration_path())
