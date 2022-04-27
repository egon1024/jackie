
import getpass
import sys

from template_loader import TemplateLoader
from issue_tree import IssueTree
from jira_reflector import JiraReflector

tloader = TemplateLoader()
issues = tloader.load(path=sys.argv[1])

tree = IssueTree()
tree.add_issues(issues.values())
tree.print_tree(label_field="summary")

tree.var_file = sys.argv[2]
tree.render()
print("")
#for issue in tree.as_list():
#    print("\n--")
#    print(f"Name: {issue.name} ({issue.order or ''})")
#    print(f"Type: {issue.issuetype}")
#    print(f"Summary: {issue.summary}")
#    print(f"Description: {issue.description}")
tree.print_tree(label_field="summary")
tree.debug()

class Config(object): pass
config = Config()

config.jira_server = sys.argv[3]
config.user = sys.argv[4]
config.password = getpass.getpass("Jira password: ")

reflector = JiraReflector(config=config)
reflector.create(tree)