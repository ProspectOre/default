import asyncio

from scripts.helpers.event import get_event


def is_editable(pull_request):
    if pull_request["maintainer_can_modify"]:
        return True

    head_repository = pull_request["head"]["repo"]["full_name"]
    base_repository = pull_request["base"]["repo"]["full_name"]
    return head_repository in {"hacs/default", base_repository}


async def check():
    event = get_event()
    pull_request = event["pull_request"]
    if not is_editable(pull_request):
        exit("::error::The PR is not editable by HACS maintainers")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(check())
