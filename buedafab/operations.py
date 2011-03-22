"""Lower-level Fabric extensions for common tasks. None of these are ready-to-go
Fabric commands.
"""
from fabric.api import (run as fabric_run, local, sudo as fabric_sudo, hide,
        put as fabric_put, settings, env, require, abort, cd)
from fabric.contrib.files import (exists as fabric_exists, sed as fabric_sed)
import os

from buedafab.utils import absolute_release_path

def chmod(path, mode, recursive=True, use_sudo=False):
    cmd = 'chmod %(mode)s %(path)s' % locals()
    if recursive:
        cmd += ' -R'
    _conditional_sudo(cmd, use_sudo)

def chgrp(path, group, recursive=True, use_sudo=False):
    cmd = 'chgrp %(group)s %(path)s' % locals()
    if recursive:
        cmd += ' -R'
    _conditional_sudo(cmd, use_sudo)

def chown(path, user, recursive=True, use_sudo=False):
    cmd = 'chown %(user)s %(path)s' % locals()
    if recursive:
        cmd += ' -R'
    _conditional_sudo(cmd, use_sudo)

def _conditional_sudo(cmd, use_sudo):
    if use_sudo:
        sudo(cmd)
    else:
        run(cmd)

def put(local_path, remote_path, mode=None, **kwargs):
    """If the host is localhost, puts the file without requiring SSH."""
    require('hosts')
    if 'localhost' in env.hosts:
        if (os.path.isdir(remote_path) and
                (os.path.join(remote_path, os.path.basename(local_path)))
                == local_path):
            return 0
        result = local('cp -R %s %s' % (local_path, remote_path))
        if mode:
            local('chmod -R %o %s' % (mode, remote_path))
        return result
    else:
        return fabric_put(local_path, remote_path, mode, **kwargs)

def run(command, forward_agent=False, use_sudo=False, **kwargs):
    require('hosts')
    if 'localhost' in env.hosts:
        return local(command)
    elif forward_agent:
        if not env.host:
            abort("At least one host is required")
        return sshagent_run(command, use_sudo=use_sudo)
    else:
        return fabric_run(command, **kwargs)

def virtualenv_run(command, path=None):
    path = path or absolute_release_path()
    with cd(path):
        run("%s/bin/python %s" % (env.virtualenv, command))

def sshagent_run(command, use_sudo=False):
    """
    Helper function.
    Runs a command with SSH agent forwarding enabled.

    Note:: Fabric (and paramiko) can't forward your SSH agent.
    This helper uses your system's ssh to do so.
    """

    if use_sudo:
        command = 'sudo %s' % command

    cwd = env.get('cwd', '')
    if cwd:
        cwd = 'cd %s && ' % cwd
    real_command = cwd + command

    with settings(cwd=''):
        if env.port:
            port = env.port
            host = env.host
        else:
            try:
                # catch the port number to pass to ssh
                host, port = env.host.split(':')
            except ValueError:
                port = None
                host = env.host

        if port:
            local('ssh -p %s -A %s "%s"' % (port, host, real_command))
        else:
            local('ssh -A %s "%s"' % (env.host, real_command))

def sudo(command, shell=True, user=None, pty=False):
    """If the host is localhost, runs without requiring SSH."""
    require('hosts')
    if 'localhost' in env.hosts:
        command = 'sudo %s' % command
        return local(command, capture=False)
    else:
        return fabric_sudo(command, shell, user, pty)

def exists(path, use_sudo=False, verbose=False):
    require('hosts')
    if 'localhost' in env.hosts:
        capture = not verbose
        command = 'test -e "%s"' % path
        func = use_sudo and sudo or run
        with settings(hide('everything'), warn_only=True):
            return not func(command, capture=capture).failed
    else:
        return fabric_exists(path, use_sudo, verbose)

def sed(filename, before, after, limit='', use_sudo=False, backup='.bak'):
    require('hosts')
    if 'localhost' in env.hosts:
        # Code copied from Fabric - is there a better way to have Fabric's sed()
        # use our sudo and run functions?
        expr = r"sed -i%s -r -e '%ss/%s/%s/g' %s"
        # Characters to be escaped in both
        for char in "/'":
            before = before.replace(char, r'\%s' % char)
            after = after.replace(char, r'\%s' % char)
        # Characters to be escaped in replacement only (they're useful in
        # regexe in the 'before' part)
        for char in "()":
            after = after.replace(char, r'\%s' % char)
        if limit:
            limit = r'/%s/ ' % limit
        command = expr % (backup, limit, before, after, filename)
        func = use_sudo and sudo or run
        return func(command)
    else:
        return fabric_sed(filename, before, after, limit, use_sudo, backup)

def conditional_mv(source, destination):
    if exists(source):
        run('mv %s %s' % (source, destination))

def conditional_rm(path, recursive=False):
    if exists(path):
        cmd = 'rm'
        if recursive:
            cmd += ' -rf'
        run('%s %s' % (cmd, path))

def conditional_mkdir(path, group=None, mode=None, user=None, use_local=False,
        use_sudo=False):
    cmd = 'mkdir -p %s' % path
    if not exists(path):
        if use_local:
            local(cmd)
        else:
            _conditional_sudo(cmd, use_sudo)
    if group:
        chgrp(path, group, use_sudo=True)
    if user:
        chown(path, user, use_sudo=True)
    if mode:
        chmod(path, mode, use_sudo=True)
