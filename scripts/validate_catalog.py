import json
import re
import sys
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker
from rfc3986_validator import validate_rfc3986


REPOSITORY_PATTERN = re.compile(r"^[\w.-]+/[\w.-]+$")
CRITICAL_SCHEMA = Path(__file__).resolve().parents[1] / "tools/jsonschema/critical.schema.json"
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
    schema = _load(CRITICAL_SCHEMA)
    if not validate_rfc3986("mailto:validator@example.com", rule="URI") or validate_rfc3986(
        "https://bad host/", rule="URI"
    ):
        raise RuntimeError("RFC 3986 URI format validation is unavailable")
    validator = Draft7Validator(schema, format_checker=FormatChecker(formats=("uri",)))
    error = next(validator.iter_errors(critical), None)
    if error is not None:
        location = ".".join(map(str, error.absolute_path)) or "critical"
        raise ValueError(f"{location}: {error.message}")
    for index, item in enumerate(critical):
        _repository(item["repository"], f"critical[{index}]")

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
