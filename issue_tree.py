"""
A class to represent a tree of issues.
"""

# Built in imports
import operator

# Our imports
from variable_loader import VariableLoader

# 3rd party imports
from rich.tree import Tree
from rich import print


# Custom exception hierarchy
class IssueTreeException(Exception): pass
class TooManyTopsException(IssueTreeException): pass
class DuplicateNameExecption(IssueTreeException): pass
class ArgumentException(IssueTreeException, ValueError): pass


class IssueTree(object):

    def __init__(self, jira=None, issues=None):
        self.issues = dict()
        self.uplinks = dict()
        self.downlinks = dict()
        self.missing = set()  # Issues referenced by name, but not in the tree yet
        self.top = None

        self.var_file = None
        self.var_schema = None

    def add_issue(self, issue):
        """
        Add an issue to the tree.
        """

        self.issues[issue.name] = issue
        self.refresh_links()

    def add_issues(self, issues):
        """
        Add multiple issues to the tree.
        """

        for issue in issues:
            self.issues[issue.name] = issue

        self.refresh_links()

    def remove_issue(self, name):
        # If the issue doesn't already exist in the tree, there's no work to do
        if name not in self.issues:
            return True

        if self.top == name:
            self.top = None

        del(self.issues[name])
        self.refresh_links()

    def refresh_links(self, validate=False):
        self.uplinks = dict()
        self.downlinks = dict()
        self.missing = set()
        self.top = None

        for issue in self.issues.values():
            if not issue.parent:
                if self.top and validate is True:
                    err_msg = "Multiple parentless issues found"
                    raise TooManyTopsException(err_msg)
                else:
                    self.top = issue.name

            else:
                self.uplinks[issue.name] = issue.parent
                self.downlinks.setdefault(issue.parent, set())
                self.downlinks[issue.parent].add(issue.name)

        # Find missing issues
        for uplink in self.uplinks.values():
            if uplink not in self.issues:
                self.missing.add(uplink)

    def print_tree(self, label_field="name"):
        self.refresh_links(validate=True)

        colors = {
            'epic': 'red',
            'story': 'green',
            'subtask': 'magenta',
        }

        issue = self.issues[self.top]
        label = getattr(issue, label_field, issue.name)
        color = colors[issue.issuetype.lower()]
        tree = Tree(f"[{color}]{label}")

        if self.top in self.downlinks: 
            for name in sorted(self.downlinks[self.top]):
                issue = self.issues[name]
                label = getattr(issue, label_field, issue.name)
                color = colors[issue.issuetype.lower()]
                sub_tree = tree.add(f"[{color}]{label}")

                if name in self.downlinks:
                    for st_name in sorted(self.downlinks[name]):
                        issue = self.issues[st_name]
                        label = getattr(issue, label_field, issue.name)
                        color = colors[issue.issuetype.lower()]
                        sub_tree.add(f"[{color}]{label}")

        print(tree)

    def debug(self):
        print("--")
        print(f"Issues: {self.issues}")
        print(f"Top: {self.top}")
        print(f"Uplinks: {self.uplinks}")
        print(f"Downlinks: {self.downlinks}")
        print(f"Missing: {self.missing}")

    def render(self):
        if not self.var_file:
            return True

        loader = VariableLoader(
            var_file=self.var_file,
            schema=self.var_schema,
        )

        if loader.state == "valid":
            variables = loader.get_data()

        for issue in self.issues.values():
            issue.render(variables)

    def as_list(self):
        """
        Takes the tree and returns it as an ordered list
        """

        ret_val = [self.issues[self.top]]

        if self.top in self.downlinks:
            # Get the list of stories and iterate
            stories = [
                self.issues[_]
                for _ in self.downlinks[self.top]
                if _ in self.issues
            ]
            stories = sorted(stories, key=operator.attrgetter('order'))

            for story in stories:
                # Add the story first, and then iterate through its children
                ret_val.append(story)

                if story.name in self.downlinks:
                    subtasks = [
                        self.issues[_]
                        for _ in self.downlinks[story.name]
                        if _ in self.issues
                    ]

                    subtasks = sorted(subtasks, key=operator.attrgetter('order'))
                    ret_val += subtasks

        return ret_val

