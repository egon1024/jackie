"""
This class is intended to take an issue tree and reflect it into jira
"""

# Built in imports
import sys

# 3rd party imports
from jira import JIRA


class JiraReflectorException(Exception): pass
class TreeValidationException(JiraReflectorException): 
    def __init__(self, issues, *args, **kwargs):
        Super(TreeValidationException, self).__init__(*args, **kwargs)
        self.issues = issues

class JiraReflector(object):
    def __init__(self, config):
        # Dev notes:
        # We need a config field that defines what the "epic link" field is named.  Stories will use this, but subtasks won't.  
        # Stories will also need to have the subtask list defined

        self.jira = None
        self._project_cache = None

        self.config = config
        self.jira = None

    def get_jira(self, force=False):
        if self.jira is None or force is True:
            self.jira = JIRA(
                server=f'https://{self.config.jira_server}',
                options=getattr(self.config, 'jira_options', {}),
                # For a first pass, we'll just use simple user/pass auth
                # This should probably be matured soon
                basic_auth=(self.config.user, self.config.password)
            )

        return self.jira

    def get_projects(self):
        if not self._project_cache:
            jira = self.get_jira()
            self._project_cache = {
                _.key: _
                for _ in jira.projects()
            }

        return self._project_cache

    def validate(self, tree):
        """
        Perform validation on the tree, with respect to the connected JIRA
        """

        # Do all of the projects referenced actually exist?
        jira = self.get_jira()
        projects = jira.projects()
        project_keys = set(_.key for _ in projects)

        issues = tree.as_list()
        failed = [
            _ for _ in issues
            if _.jira_project not in project_keys
        ]

        if failed:
            raise TreeValidationException(issues=failed)

    def create(self, tree):
        """
        Uses the tree to constitute a new hierarchy of tickets.

        NB:
          - It will not attempt to render tickets.  That needs to be done in advance
          - It will not make any attempt to see if the tickets already exist.  New tickets WILL be created.
        """

        self.validate(tree)
        jira = self.get_jira()

        # Create the Epic itself
        epic = tree.issues[tree.top]
        epic_project_id = self.get_projects()[epic.jira_project].id
        jira_epic_data = {
            'project': {'id': epic_project_id},
            'summary': epic.summary,
            'description': epic.description,
            'issuetype': {'name': 'Epic'},

            # Required by our specific jira instance ... 
            # Really need to genericize this sort of thing somehow
            'customfield_10002': epic.summary,
        }

        jira_epic = jira.create_issue(notify=False, fields=jira_epic_data)
        print(f"Epic created: {jira_epic.key}")

        for story in tree.as_list():
            if story.parent == epic.name:
                story_project_id = self.get_projects()[story.jira_project].id
                jira_story_data = {
                    'project': {'id': story_project_id},
                    'summary': story.summary,
                    'description': story.description,
                    'issuetype': {'name': 'Story'},

                    # This ties it to the epic.  Again, this needs to be genericized
                    'customfield_10000': jira_epic.key
                }
                jira_story = jira.create_issue(notify=False, fields=jira_story_data)
                print(f"- Story created: {jira_story.key}")

                for subtask in tree.as_list():
                    if subtask.parent == story.name:
                        subtask_project_id = self.get_projects()[subtask.jira_project].id
                        jira_subtask_data = {
                            'project': {'id': subtask_project_id},
                            'summary': subtask.summary,
                            'description': subtask.description,
                            # TODO this needs to be parameterized
                            'issuetype': {'name': 'Operational Sub-Task'},
                            'parent': {'key': jira_story.key},
                        }
                        jira_subtask = jira.create_issue(notify=False, fields=jira_subtask_data)
                        print(f"-- Subtask created: {jira_subtask.key}")