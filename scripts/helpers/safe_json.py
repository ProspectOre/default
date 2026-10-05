import json
import os
import stat


MAX_MANIFEST_SIZE = 1024 * 1024


def read_json_regular_file(path, max_bytes=MAX_MANIFEST_SIZE):
    """Read bounded JSON without following a symlink or blocking on a FIFO."""
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC

    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise ValueError(f"Cannot safely open manifest {path}: {error}") from error

    try:
        file_info = os.fstat(descriptor)
        if not stat.S_ISREG(file_info.st_mode):
            raise ValueError(f"Manifest {path} must be a regular file")
        if file_info.st_size > max_bytes:
            raise ValueError(f"Manifest {path} exceeds the {max_bytes}-byte limit")

        content = bytearray()
        while len(content) <= max_bytes:
            remaining = max_bytes + 1 - len(content)
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            content.extend(chunk)
        if len(content) > max_bytes:
            raise ValueError(f"Manifest {path} exceeds the {max_bytes}-byte limit")

        try:
            return json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"Manifest {path} is not valid UTF-8 JSON") from error
    finally:
        os.close(descriptor)
