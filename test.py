
import sys

from template_loader import TemplateLoader
from issue_tree import IssueTree

tloader = TemplateLoader()
issues = tloader.load(path=sys.argv[1])

tree = IssueTree()
tree.add_issues(issues.values())
tree.print_tree(label_field="summary")

tree.var_file = sys.argv[2]
tree.render()
print("")
for issue in tree.as_list():
    print("\n--")
    print(f"Name: {issue.name} ({issue.order or ''})")
    print(f"Type: {issue.issuetype}")
    print(f"Summary: {issue.summary}")
    print(f"Description: {issue.description}")


tree.debug()