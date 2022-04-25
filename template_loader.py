"""
This class is used to load a set of templates
"""

# Built in imports
import os
import os.path

# Our imports
from issue import Issue

# 3rd party imports
import yaml

from rich.traceback import install
install(show_locals=False)


class TemplateLoader(object):
    def __init__(self):
        self._files = []

    def load(self, path):
        if not os.path.exists(path):
            raise RuntimeError(f"The provided path ({path}) does not exist")

        keepers = []

        for root, dirs, files in os.walk(path):
            for name in files:
                if name.startswith(".") or not (name.endswith(".yml") or name.endswith(".yaml")):
                    continue
                else:
                    keepers.append(os.path.join(root, name))

        issues = {}
        for keeper in keepers:
            data = open(keeper, "r").read()
            parsed = yaml.safe_load_all(data)

            for doc in parsed:
                i = Issue(**doc)

                if i.name in issues:
                    raise ValueError("Duplicate issue name '{}' found".format(i.name))

                issues[i.name] = i

        return issues
