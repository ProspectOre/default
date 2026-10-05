import json
import sys
from pathlib import Path

categories = [
    "blacklist",
    "appdaemon",
    "integration",
    "netdaemon",
    "plugin",
    "python_script",
    "template",
    "theme",
]
directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

for category in categories:
    with (directory / category).open("r", encoding="utf-8") as cat_file:
        content = json.loads(cat_file.read())
        if content != sorted(content, key=str.casefold):
            print(f"{category} is not sorted correctly")
            print("It should look like")
            print(sorted(content, key=str.casefold))
            print("But it is")
            print(content)
            exit(1)
