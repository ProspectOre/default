import os

from scripts.changed.catalog import get_admission


def get_repo():
    _, repository = get_admission(
        os.environ.get("GITHUB_WORKSPACE", "."),
        os.environ.get("BASE_SHA"),
        os.environ.get("HEAD_SHA"),
    )
    return repository


if __name__ == "__main__":
    print(get_repo())
