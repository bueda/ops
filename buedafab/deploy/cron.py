from fabric.operations import sudo
import os

from buedafab.operations import exists

def conditional_install_crontab(base_path, crontab, user):
    if crontab:
        crontab_path = os.path.join(base_path, crontab)
        if crontab and exists(crontab_path):
            sudo('crontab -u %s %s' % (user, crontab_path))

