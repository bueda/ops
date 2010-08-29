from fabric.api import cd, require, local, env, prompt
from fabric.contrib.console import confirm
from fabric.decorators import runs_once
import os
import re

from buedafab.operations import run, exists, conditional_mkdir, conditional_rm
from buedafab import utils

def bootstrap_release_folders():
    require('path')
    require('deploy_group')
    conditional_mkdir(env.path, env.deploy_group, 'g+w', use_sudo=True)
    with cd(env.path):
        first_exists = exists(env.release_paths[0])
        if not first_exists:
            run('git clone %s %s' % (env.scm, env.release_paths[0]),
                    forward_agent=True)
    with cd(env.path):
        if not exists(env.release_paths[1]):
            run('cp -R %s %s' % (env.release_paths[0], env.release_paths[1]))

def make_pretty_release():
    require('release')
    require('scratch_path')
    require('default_revision')
    with cd(env.scratch_path):
        revision = local('git rev-list %(default_revision)s '
                '-n 1 --abbrev-commit --abbrev=7' % env)
        env.head_commit = revision.rstrip('\n')
    with cd(env.scratch_path):
        env.pretty_release = local(
            'git describe %(release)s' % env).rstrip('\n')
    env.archive = '%(pretty_release)s-%(unit)s.tar' % env

@runs_once
def make_release(release=None):
    require('allow_no_tag')
    require('scratch_path')
    require('default_revision')

    env.release = release
    env.tagged = False
    if not env.release or env.release == 'latest_tag':
        with cd(env.scratch_path):
            if not env.allow_no_tag:
                local('git checkout master')
            description = local('git describe master' % env).rstrip('\n')
        if '-' in description:
            env.latest_tag = description[:description.find('-')]
        else:
            env.latest_tag = description
        if not re.match(env.version_pattern, env.latest_tag):
            env.latest_tag = None
        env.release = env.release or env.latest_tag
        env.commit = 'HEAD'
        if not env.allow_no_tag:
            if confirm("Tag this release?", default=False):
                require('master_remote')
                with cd(env.scratch_path):
                    from prettyprint import pp
                    print("The last 5 tags were: ")
                    tags = local('git tag | tail -n 20')
                    pp(sorted(tags.split('\n'), utils.compare_versions,
                            reverse=True))
                    prompt("New release tag in the format vX.Y[.Z]?",
                            'tag',
                            validate=env.version_pattern)
                    require('commit')
                    local('git tag -s %(tag)s %(commit)s' % env, capture=False)
                    local('git push --tags %(master_remote)s' % env)
                    env.tagged = True
                    env.release = env.tag
                local('git fetch --tags %(master_remote)s' % env)
            else:
                print("Using latest tag %(latest_tag)s" % env)
                env.release = env.latest_tag
        else:
            env.release = env.commit
    else:
        with cd(env.scratch_path):
            local('git checkout %s' % env.release)
        env.tagged = re.match(env.version_pattern, env.release)
    make_pretty_release()

def conditional_symlink_current_release(deployed=False):
    if exists(utils.absolute_release_path()):
        with cd(utils.absolute_release_path()):
            current_version = run('git describe')
    if (not exists(utils.absolute_release_path())
            or deployed or current_version != env.pretty_release):
        next_release_path = alternative_release_path()
        symlink_current_release(next_release_path)

def symlink_current_release(next_release_path):
    with cd(os.path.join(env.path, env.releases_root)):
        conditional_rm(env.current_release_symlink)
        run('ln -s %s %s' % (next_release_path, env.current_release_symlink))

def alternative_release_path():
    if exists(utils.absolute_release_path()):
        current_release_path = run('readlink %s' % utils.absolute_release_path())
        if current_release_path == env.release_paths[0]:
            alternative = env.release_paths[1]
        else:
            alternative = env.release_paths[0]
        return alternative
    else:
        return env.release_paths[0]

