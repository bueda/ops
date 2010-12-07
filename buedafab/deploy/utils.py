"""General deployment utilities (not Fabric commands)."""
from fabric.api import cd, require, local, env

from buedafab import deploy

def make_archive():
    """Create a compressed archive of the project's repository, complete with
    submodules.

    TODO We used to used git-archive-all to archive the submodules as well,
    since 'git archive' doesn't touch them. We reverted back at some point and
    stopped using archives in our deployment strategy, so this may not work with
    submodules.
    """
    require('release')
    require('scratch_path')
    with cd(env.scratch_path):
        deploy.release.make_pretty_release()
        local('git checkout %(release)s' % env)
        local('git submodule update --init')
        local('git archive --prefix=%(unit)s/ --format tar '
                '%(release)s | gzip > %(scratch_path)s/%(archive)s' % env)

def run_extra_deploy_tasks(deployed=False):
    """Run arbitrary functions listed in env.package_installation_scripts.

    Each function must accept a single parameter (or just kwargs) that will
    indicates if the app was deployed or already existed.

    """
    require('release_path')
    if not env.extra_deploy_tasks:
        return

    with cd(env.release_path):
        for task in env.extra_deploy_tasks:
            task(deployed=deployed)
