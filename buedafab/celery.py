"""Utilities for configuring and managing celeryd processes on a remote
server.
"""
from fabric.api import require, env
from fabric.contrib.files import upload_template
import os

from buedafab.operations import chmod, sudo

def update_and_restart_celery():
    """Render a celeryd init.d script template and upload it to the remote
    server, then restart the celeryd process to reload the configuration.

    In addition to any env keys required by the celeryd template, requires:

        celeryd -- relateive path to the celeryd init.d script template from the
                    project root
        unit -- project's brief name, used to give each celeryd script and
                process a unique name, if more than one are running on the same
                host
        deployment_type -- app environment, to differentiate between celeryd
                processes for the same app in different environments on the
                same host (e.g. if staging and development run on the same
                physical server)

    The template is uploaded to: 

        /etc/init.d/celeryd-%(unit)s_%(deployment_type)s

    which in final form might look like:

        /etc/init.d/celeryd-five_DEV
    """

    require('path')
    require('celeryd')
    require('unit')
    require('deployment_type')
    if env.celeryd:
        celeryd_path = os.path.join(env.root_dir, env.celeryd)
        celeryd_remote_path = (
                '/etc/init.d/celeryd-%(unit)s_%(deployment_type)s' % env)
        upload_template(celeryd_path, celeryd_remote_path, env, use_sudo=True)

        # Wipe the -B option so it only happens once
        env.celeryd_beat_option = ""

        chmod(celeryd_remote_path, 'u+x')
        sudo(celeryd_remote_path + ' restart')
