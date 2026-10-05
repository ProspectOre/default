import os

from scripts.changed.catalog import get_admission


def get_category():
    category, _ = get_admission(
        os.environ.get("GITHUB_WORKSPACE", "."),
        os.environ.get("BASE_SHA"),
        os.environ.get("HEAD_SHA"),
    )
    return category


if __name__ == "__main__":
    print(get_category())
