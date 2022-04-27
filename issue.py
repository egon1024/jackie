"""
A class (and related exceptions) for representing an issue
"""

# Built in imports
import sys

# 3rd party imports
import jinja2


class IssueException(Exception): pass
class InvalidStateException(IssueException): pass
class FieldTypeException(IssueException, TypeError): pass


class Issue(object):
    """
    Represents an issue to be reflected into Jira
    """

    ATTRS = {
        'name', 'parent', 'jira_project', 'issuetype',
        'summary', 'epic_name', 'description', 'order'
    }
    REQUIRED = {'name', 'jira_project', 'issuetype', 'summary'}

    META_ATTRS = {'vars', 'jira_id'}

    def __init__(self, **kwargs):
        self._vars = {}
        self._jira_id = None

        self._rendered = False
        self._jinja_env = None

        for attr in self.ATTRS:
            setattr(self, attr, None)

        bad_keys = []

        for key, val in kwargs.items():

            if key in self.META_ATTRS:
                attr_name = f"_{key}"
                setattr(self, attr_name, val)

            elif key not in self.ATTRS:
                bad_keys.append(key)
                continue

            else:
                setattr(self, key, val)

        if bad_keys:
            err_str = "The following keys are invalid: {}".format(', '.join(bad_keys))
            raise RuntimeError(err_str)

    def is_rendered(self):
        return self._rendered

    def create(self):
        if not self.is_rendered():
            self.render()

    def validate(self):
        print(f"Validating '{self.name}'")
        # Any missing attributes
        missing_attrs = [
            _ for _ in self.REQUIRED
            if not hasattr(self, _) or getattr(self, _) is None
        ]
        if missing_attrs:
            err_str = "Missing required attributes: {}".format(', '.join(missing_attrs))
            raise InvalidStateException(err_str)

        # Issue must either be an epic/story, or specify a parent
        if self.issuetype.lower() not in ('epic', 'story') and self.parent is None:
            err_str = "Issue must either be an Epic/Story or specify a parent"
            raise InvalidStateException(err_str)

        # Make sure everything is jinja renderable
        jinja_env = self.get_jinja_env()
        for field in self.ATTRS:
            val = getattr(self, field)
            if val is not None:
                # Try to load it
                try:
                    jinja_env.from_string(str(val))
                except jinja2.exceptions.TemplateSyntaxError:
                    # TODO: Find a better approach to this.  This will output
                    # to stderr even if the exception gets caught at a higher
                    # level.  Might have to get more familiar with jinja
                    # formatting
                    sys.stderr.write(f"Error in template for field: {field}")
                    raise

    def __setattr__(self, name, value):
        if name in self.ATTRS:
            self._rendered = False
            return super(Issue, self).__setattr__(name, value)

        elif name == 'vars':
            if not isinstance(value, dict):
                raise FieldTypeException("vars must be a dictionary")

            self._vars = vars

        elif name in self.META_ATTRS:
            attr_name = f"_{name}"
            super(Issue, self).__setattr_(attr_name, value)

        else:
            return super(Issue, self).__setattr__(name, value)

    def render(self, vars=None):
        self.validate()

        if vars is None:
            vars = self._vars

        jinja_env = self.get_jinja_env()

        self._rendered = True

        for field in self.ATTRS:
            val = getattr(self, field)
            if val is not None:
                template = jinja_env.from_string(str(val))
                setattr(self, field, template.render(vars))

    def get_jinja_env(self):
        if self._jinja_env is None:
            self._jinja_env = jinja2.Environment()

        return self._jinja_env
