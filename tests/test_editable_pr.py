import unittest

from scripts.check.edits import is_editable


class EditablePullRequestTest(unittest.TestCase):
    def pull_request(self, head, base="ProspectOre/default", maintainer_can_modify=False):
        return {
            "maintainer_can_modify": maintainer_can_modify,
            "head": {"repo": {"full_name": head}},
            "base": {"repo": {"full_name": base}},
        }

    def test_same_repository_branch_is_editable(self):
        self.assertTrue(is_editable(self.pull_request("ProspectOre/default")))

    def test_hacs_default_and_maintainer_editable_forks_remain_supported(self):
        self.assertTrue(is_editable(self.pull_request("hacs/default")))
        self.assertTrue(
            is_editable(
                self.pull_request("contributor/fork", maintainer_can_modify=True)
            )
        )

    def test_uneditable_external_fork_is_rejected(self):
        self.assertFalse(is_editable(self.pull_request("contributor/fork")))


if __name__ == "__main__":
    unittest.main()
