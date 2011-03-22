from fabric.api import require, prefix, env
from fabric.decorators import runs_once

from buedafab.operations import virtualenv_run

def django_manage_run(cmd):
    require('deployment_type')
    with prefix("export DEPLOYMENT_TYPE='%(deployment_type)s'" % env):
        virtualenv_run("./manage.py %s" % cmd)

@runs_once
def shell():
    virtualenv_run("./manage.py shell")
