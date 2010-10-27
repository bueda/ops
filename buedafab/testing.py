from fabric.api import env, require, cd, runs_once, local, settings
import os

@runs_once
def lint():
    require('root_dir')
    env.python_path_extensions = '%(root_dir)s/lib:%(root_dir)s/apps' % env
    for directory in os.listdir(os.path.join(env.root_dir, 'vendor')):
        full_path = os.path.join(env.root_dir, 'vendor', directory)
        if os.path.isdir(full_path):
            env.python_path_extensions += ':' + full_path
    with cd(env.root_dir):
        local('PYTHONPATH=$PYTHONPATH:%(python_path_extensions)s '
            'pylint %(root_dir)s --rcfile=.pylintrc 2>/dev/null' % env,
                capture=False)

@runs_once
def test(dir=None, deployment_type=None):
    require('root_dir')
    require('test_runner')
    with settings(root_dir=(dir or env.root_dir), warn_only=True):
        return env.test_runner(deployment_type)

@runs_once
def nose_test_runner(deployment_type=None):
    return local('nosetests', capture=False).return_code

@runs_once
def webpy_test_runner(deployment_type=None):
    # TODO
    #import manage
    #import nose
    #return nose.run()
    pass

@runs_once
def tornado_test_runner(deployment_type=None):
    return local('test/run_tests.py', capture=False).return_code

@runs_once
def django_test_runner(deployment_type=None):
    command = './manage.py test'
    if deployment_type:
        command = 'DEPLOYMENT_TYPE=%s ' % deployment_type + command
    return local(command, capture=False).return_code
