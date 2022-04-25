
import sys

from template_loader import TemplateLoader
from issue_tree import IssueTree

tloader = TemplateLoader()
issues = tloader.load(sys.argv[1])

tree = IssueTree()
tree.add_issues(issues.values())
tree.print_tree()
