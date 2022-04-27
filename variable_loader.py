"""
This class is used to load a set of variables to apply to a template
"""

# Built in imports
from copy import deepcopy

# 3rd party imports
import yaml
import yamale

from rich.traceback import install
install(show_locals=False)


class VariableLoader(object):

    def __init__(self, var_file, schema=None):
        self._data = {}
        self.state = "invalid"

        self.var_file = var_file
        self.schema = schema

    def load(self):
        data = self.load_from_file(self.var_file)
        self._data = yaml.safe_load(data)
        self.updated = True

        self.validate()

    def load_from_file(self, var_file):
        return open(var_file, "r").read()

    def validate(self):
        if not hasattr(self, "schema") or self.schema is None:
            self.state = "valid"
            return True

        compiled_schema = yamale.make_schema(self.schema)
        compiled_data = yamale.make_data(content=yaml.dump(self._data))

        # TODO: Figure out how we want to handle a failure.  Likely a custom
        # exception of some sort?
        try:
            yamale.validate(compiled_schema, compiled_data)
        except ValueError:
            self.state = "invalid"
            return False
        else:
            self.state = "valid"
            return True

    def get_data(self):
        self.updated = False

        # Return a deepcopy of the data so that we keep it clean for other requestors
        return deepcopy(dict(self._data))

    def __setattr__(self, name, value):
        # state, updated, and _ vars get set normally
        if name in ('state', 'updated') or name.startswith('_'):
            return super(VariableLoader, self).__setattr__(name, value)

        # If defining the schema, we'll set the var and run the validation
        elif name == 'schema':
            ret = super(VariableLoader, self).__setattr__(name, value)

            if not hasattr(self, 'var_file') or self.var_file is None:
                return ret

            return self.validate() and ret

        # When setting the var file, we'll automatically load
        elif name == 'var_file':
            super(VariableLoader, self).__setattr__("var_file", value)
            self.load()
