"""Utilities for updating schema and loading data into a database (all Django
specific at the moment.
"""
from fabric.api import require, env, cd
from fabric.contrib.console import confirm
from fabric.decorators import runs_once
import os

from buedafab.operations import run

@runs_once
def load_data():
    """Load extra fixtures into the database.

    Requires the env keys:
        
        release_path -- remote path of the deployed app
        deployment_type -- app environment to set before loading the data (i.e.
                            which database should it be loaded into)
        virtualenv -- path to this app's virtualenv (required to grab the
                        correct Python executable)
        extra_fixtures -- a list of names of fixtures to load (empty by default)
    """
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
    """Migrate the database to the currently deployed version using South. If
    the app wasn't deployed (e.g. we are redeploying the same version for some
    reason, this command will prompt the user to confirm that they want to
    migrate.

    Requires the env keys:
        
        release_path -- remote path of the deployed app
        deployment_type -- app environment to set before loading the data (i.e.
                            which database should it be loaded into)
        virtualenv -- path to this app's virtualenv (required to grab the
                        correct Python executable)
    """
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
    """Update the database to the currently deployed version using syncdb. If
    the app wasn't deployed (e.g. we are redeploying the same version for some
    reason, this command will prompt the user to confirm that they want to
    update.

    Requires the env keys:
        
        release_path -- remote path of the deployed app
        deployment_type -- app environment to set before loading the data (i.e.
                            which database should it be loaded into)
        virtualenv -- path to this app's virtualenv (required to grab the
                        correct Python executable)
    """
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
