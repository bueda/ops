from fabric.api import env, require, cd
from fabric.decorators import runs_once

import os

from buedafab.utils import absolute_release_path
from buedafab.operations import run

def _run_interactive_virtualenv_python(command):
    require('deployment_type')
    env.command = command
    with cd(absolute_release_path()):
        run("""
            export DEPLOYMENT_TYPE='%(deployment_type)s'
            %(virtualenv)s/bin/python -i %(command)s
            """ % env, capture=False, forward_agent=True)

@runs_once
def shell():
    _run_interactive_virtualenv_python("./manage.py shell")
