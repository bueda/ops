from fabric.api import cd, require, local, env

from buedafab import deploy

def make_archive():
    require('release')
    require('scratch_path')
    with cd(env.scratch_path):
        deploy.release.make_pretty_release()
        local('git checkout %(release)s' % env)
        local('git submodule init')
        local('git submodule update')
        local('git archive --prefix=%(unit)s/ --format tar '
                '%(release)s | gzip > %(scratch_path)s/%(archive)s' % env)
