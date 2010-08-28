from fabric.api import cd, require, local, env

from buedafab import deploy

def make_archive():
    require('release')
    require('scratch_path')
    deploy.release.make_pretty_release()
    with cd(env.scratch_path):
        if env.release != env.head_commit:
            local('git checkout %(release)s' % env)
            local('git submodule init')
            local('git submodule update')
        local('%(git_archive_all)s --prefix %(unit)s/ --format tar '
                '%(scratch_path)s/%(archive)s' % env)
