import os

from scripts.changed.catalog import require_maintenance_scope


if __name__ == "__main__":
    require_maintenance_scope(
        os.environ.get("GITHUB_WORKSPACE", "."),
        os.environ.get("BASE_SHA"),
        os.environ.get("HEAD_SHA"),
    )
