import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


REPOSITORY_PATTERN = re.compile(r"^[\w.-]+/[\w.-]+$")
REPOSITORY_FILES = (
    "appdaemon",
    "blacklist",
    "integration",
    "netdaemon",
    "plugin",
    "python_script",
    "template",
    "theme",
)


def _load(path):
    try:
        with path.open(encoding="utf-8") as content:
            return json.load(content)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{path.name} is not readable valid JSON: {error}") from error


def _repository(value, source):
    if not isinstance(value, str) or not REPOSITORY_PATTERN.fullmatch(value):
        raise ValueError(f"{source} contains an invalid repository name: {value!r}")


def validate(directory):
    directory = Path(directory)
    for filename in REPOSITORY_FILES:
        items = _load(directory / filename)
        if not isinstance(items, list):
            raise ValueError(f"{filename} must be an array")
        for item in items:
            _repository(item, filename)

    critical = _load(directory / "critical")
    if not isinstance(critical, list):
        raise ValueError("critical must be an array")
    for index, item in enumerate(critical):
        source = f"critical[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{source} must be an object")
        for key in ("repository", "reason", "link"):
            if key not in item:
                raise ValueError(f"{source} is missing required property {key!r}")
        _repository(item["repository"], source)
        if not isinstance(item["reason"], str) or not isinstance(item["link"], str):
            raise ValueError(f"{source} reason and link must be strings")
        parsed_link = urlparse(item["link"])
        if not parsed_link.scheme or not parsed_link.netloc:
            raise ValueError(f"{source} link must be a URI")

    removed = _load(directory / "removed")
    if not isinstance(removed, list):
        raise ValueError("removed must be an array")
    for index, item in enumerate(removed):
        source = f"removed[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{source} must be an object")
        for key in ("removal_type", "repository"):
            if key not in item:
                raise ValueError(f"{source} is missing required property {key!r}")
        _repository(item["repository"], source)
        for key in ("link", "reason", "removal_type"):
            if key in item and not isinstance(item[key], str):
                raise ValueError(f"{source}.{key} must be a string")


if __name__ == "__main__":
    try:
        validate(sys.argv[1])
    except (IndexError, ValueError) as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)
