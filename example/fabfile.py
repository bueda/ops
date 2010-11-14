#!/usr/bin/env python
import os
from fabric.api import *

from buedafab.test import test, django_test_runner as _django_test_runner, lint
from buedafab.deploy.types import django_deploy as deploy
from buedafab.environments import (django_development as development,
        django_production as production, django_localhost as localhost,
        django_staging as staging)
from buedafab.tasks import (setup, restart_webserver, rollback, enable,
        disable, maintenancemode, rechef)

# A short name for the app, used in folder names
env.unit = "five"

# Deploy target on remote server
env.path = "/var/webapps/%(unit)s" % env

# git-compatible path to remote repository
env.scm = "git@github.com:bueda/%(unit)s.git" % env

# HTTP-compatible path to the remote repository
# This is optional, and is used only to link Hoptoad deploys to source code
env.scm_http_url = "http://github.com/bueda/%(unit)s" % env

# The root directory of the project (where this fabfile.py resides)
env.root_dir = os.path.abspath(os.path.dirname(__file__))

# Paths to Python package requirements files for pip
# pip_requirements are installed in all environments
env.pip_requirements = ["requirements/common.txt",]
# pip_requirements_dev are installed only in the development environment
env.pip_requirements_dev = ["requirements/dev.txt",]
# pip_requirements_production are installed only in the production environment
env.pip_requirements_production = ["requirements/production.txt",]

# A Django-specific for projects using the South database migration app
env.migrate = True

# For projects using celery, the path to the system service script for celeryd
env.celeryd = 'scripts/init.d/celeryd'

# Name of the Amazon Elastic Load Balancer instance that sits in front of the
# app servers for this project - this is used to find all of the production
# servers for the app when re-deploying.
env.load_balancer = 'web'

# The test runner to use before deploying, and also when running 'fab test'
# Test runners are defined for Django, Tornado, web.py and general nosetests
# test suites. To define a custome test runner, just write a method and assign
# it to env.test_runner.
env.test_runner = _django_test_runner

# URL that returns the current git commit SHA this app is running
# This current must have a single string format parameter that is replaced by
# "dev." or "staging." or "www." depending on the environment - kind of a weird,
# strict requirement that should be re-worked.
env.sha_url_template = 'http://%sfivebybueda.com/version/'

# API key for the Hoptoad account associated with this project. Will report a
# deployment to Hoptoad to help keep track of resolved errors.
env.hoptoad_api_key = 'your-hoptoad-api-key'

# Campfire chat room information - will notify whenever someone deploys the app
env.campfire_subdomain = 'bueda'
env.campfire_room = 'YourRoom'
env.campfire_token = 'your-api-key'
