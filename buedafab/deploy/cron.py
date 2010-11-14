"""Utilities to manage crontabs on a remote server.

These aren't used at Bueda anymore, since migrating to celery's scheduled tasks.
"""
from fabric.operations import sudo
import os

from buedafab.operations import exists

def conditional_install_crontab(base_path, crontab, user):
    """If the project specifies a crontab, install it for the specified user on
    the remote server.
    """
    if crontab:
        crontab_path = os.path.join(base_path, crontab)
        if crontab and exists(crontab_path):
            sudo('crontab -u %s %s' % (user, crontab_path))

