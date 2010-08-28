from fabric.api import require, env
from fabric.decorators import runs_once
from fabric.contrib.files import upload_template
import os

from buedafab.operations import chmod, sudo

# TODO once we have more than one app server using celery, need to control who
# starts the beat scheduler (ie. -B flag)
@runs_once
def update_and_restart_celery():
    require('path')
    require('celeryd')
    require('unit')
    require('deployment_type')
    if env.celeryd:
        celeryd_path = os.path.join(env.root_dir, env.celeryd)
        celeryd_remote_path = (
                '/etc/init.d/celeryd-%(unit)s_%(deployment_type)s' % env)
        upload_template(celeryd_path, celeryd_remote_path, env, use_sudo=True)
        chmod(celeryd_remote_path, 'u+x')
        sudo(celeryd_remote_path + ' restart')

