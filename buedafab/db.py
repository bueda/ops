"""Utilities for updating schema and loading data into a database (all Django
specific at the moment.
"""
from fabric.api import require, env
from fabric.contrib.console import confirm
from fabric.decorators import runs_once
from fabric.colors import yellow

from buedafab.django.management import django_manage_run

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
        for fixture in env.extra_fixtures:
            django_manage_run("loaddata %(fixture)s" % fixture)

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
    if (env.migrate and
            (deployed or confirm(yellow("Migrate database?"), default=True))):
        django_manage_run("migrate")
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
    if deployed or confirm(yellow("Update database?"), default=True):
        django_manage_run("syncdb --noinput")
        env.updated_db = True
