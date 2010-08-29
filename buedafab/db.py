from fabric.api import require, env, cd
from fabric.contrib.console import confirm
from fabric.decorators import runs_once
import os

from buedafab.operations import run

@runs_once
def load_data():
    require('path')
    require('release_path')
    require('deployment_type')
    require('virtualenv')
    if env.migrated or env.updated_db:
        with cd(env.release_path):
            for fixture in env.extra_fixtures:
                env.fixture = fixture
                run("""
                    export DEPLOYMENT_TYPE="%(deployment_type)s"
                    %(virtualenv)s/bin/python ./manage.py loaddata %(fixture)s
                    """ % env)

@runs_once
def migrate(deployed=False):
    require('path')
    require('release_path')
    require('deployment_type')
    require('virtualenv')
    if (env.migrate and deployed or confirm("Migrate database?", default=True)):
        with cd(env.release_path):
            run("""
                export DEPLOYMENT_TYPE="%(deployment_type)s"
                    %(virtualenv)s/bin/python ./manage.py migrate
                """ % env)
        env.migrated = True

@runs_once
def update_db(deployed=False):
    require('path')
    require('deployment_type')
    require('virtualenv')
    require('release_path')
    if deployed or confirm("Update database?", default=True):
        with cd(env.release_path):
            run("""
                export DEPLOYMENT_TYPE="%(deployment_type)s"
                %(virtualenv)s/bin/python ./manage.py syncdb --noinput
                """ % env)
        env.updated_db = True

