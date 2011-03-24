from fabric.api import require, prefix, env
from fabric.decorators import runs_once

from buedafab.operations import virtualenv_run
from buedafab.utils import absolute_release_path

def django_manage_run(cmd):
    require('deployment_type')
    with prefix("export DEPLOYMENT_TYPE='%(deployment_type)s'" % env):
        virtualenv_run("./manage.py %s" % cmd, env.release_path)

@runs_once
def shell():
    env.release_path = absolute_release_path()
    django_manage_run('shell')
