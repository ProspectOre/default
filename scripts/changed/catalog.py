import json
import re
import subprocess


CATEGORIES = (
    "appdaemon",
    "integration",
    "netdaemon",
    "plugin",
    "python_script",
    "template",
    "theme",
)
REPOSITORY_PATTERN = re.compile(r"^[\w.-]+/[\w.-]+$")


class AdmissionError(ValueError):
    pass


def _git(repo_path, *args):
    return subprocess.check_output(
        ["git", "-C", str(repo_path), *args], text=True
    ).strip()


def _json_at(repo_path, revision, path):
    content = _git(repo_path, "show", f"{revision}:{path}")
    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        raise AdmissionError(f"{path} at {revision} is not valid JSON") from error


def get_admission(repo_path, base_sha, head_sha):
    """Return the one permitted new repository from an exact base/head diff.

    The caller must run this code from a trusted base checkout and supply
    immutable commit IDs obtained from the pull_request event.
    """
    if not base_sha or not head_sha or base_sha == head_sha:
        raise AdmissionError("A distinct immutable base and head are required")

    changed = _git(repo_path, "diff", "--name-only", "--no-renames", base_sha, head_sha)
    paths = changed.splitlines() if changed else []
    if len(paths) != 1 or paths[0] not in CATEGORIES:
        raise AdmissionError(
            "New-repository admission permits changes to exactly one category file"
        )

    category = paths[0]
    current = _json_at(repo_path, base_sha, category)
    proposed = _json_at(repo_path, head_sha, category)
    if not isinstance(current, list) or not isinstance(proposed, list):
        raise AdmissionError(f"{category} must contain a JSON array")
    if any(not isinstance(item, str) or not REPOSITORY_PATTERN.fullmatch(item) for item in proposed):
        raise AdmissionError(f"{category} contains a malformed repository name")
    if len(set(current)) != len(current) or len(set(proposed)) != len(proposed):
        raise AdmissionError(f"{category} must not contain duplicate repositories")
    if proposed != sorted(proposed, key=str.casefold):
        raise AdmissionError(f"{category} must remain sorted")

    additions = set(proposed) - set(current)
    deletions = set(current) - set(proposed)
    if deletions or len(additions) != 1 or not set(current).issubset(proposed):
        raise AdmissionError(
            "The category change must preserve every existing repository and add exactly one"
        )

    return category, additions.pop()


def require_maintenance_scope(repo_path, base_sha, head_sha):
    changed = _git(repo_path, "diff", "--name-only", "--no-renames", base_sha, head_sha)
    paths = changed.splitlines() if changed else []
    protected_data = {*CATEGORIES, "blacklist", "critical", "removed"}
    touched_data = protected_data.intersection(paths)
    if touched_data:
        raise AdmissionError(
            "Registry data changes require their dedicated admission label: "
            + ", ".join(sorted(touched_data))
        )
