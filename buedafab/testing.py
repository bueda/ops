"""Code style and unit testing utilities."""
from fabric.api import env, require, cd, runs_once, local, settings
import os

@runs_once
def lint():
    """Run pylint on the project, including the packages in `apps/`, `lib/` and
    `vendor/`, and using the `.pylintrc` file in the project's root.

    Requires the env keys:
        root_dir - root of the project, where the fabfile resides
    """
    require('root_dir')
    env.python_path_extensions = '%(root_dir)s/lib:%(root_dir)s/apps' % env
    for directory in os.listdir(os.path.join(env.root_dir, 'vendor')):
        full_path = os.path.join(env.root_dir, 'vendor', directory)
        if os.path.isdir(full_path):
            env.python_path_extensions += ':' + full_path
    with cd(env.root_dir):
        local('PYTHONPATH=$PYTHONPATH:%(python_path_extensions)s '
            'pylint %(root_dir)s --rcfile=.pylintrc 2>/dev/null' % env)

@runs_once
def test(dir=None, deployment_type=None):
    """Run the test suite for this project. There are current test runners defined for
    Django, Tornado, and general nosetests suites. Just set `env.test_runner` to the
    appropriate method (or write your own).

    Requires the env keys:
        root_dir - root of the project, where the fabfile resides
        test_runner - a function expecting the deployment_type as a parameter
                    that runs the test suite for this project
    """
    require('root_dir')
    require('test_runner')
    with settings(root_dir=(dir or env.root_dir), warn_only=True):
        return env.test_runner(deployment_type)

@runs_once
def nose_test_runner(deployment_type=None):
    """Basic nosetests suite runner."""
    return local('nosetests').return_code

@runs_once
def webpy_test_runner(deployment_type=None):
    # TODO
    #import manage
    #import nose
    #return nose.run()
    pass

@runs_once
def tornado_test_runner(deployment_type=None):
    """Tornado test suite runner - depends on using Bueda's tornado-boilerplate
    app layout."""
    return local('tests/run_tests.py').return_code

@runs_once
def django_test_runner(deployment_type=None):
    """Django test suite runer."""
    command = './manage.py test'
    if deployment_type:
        command = 'DEPLOYMENT_TYPE=%s ' % deployment_type + command
    return local(command).return_code
