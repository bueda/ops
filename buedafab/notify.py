from fabric.api import env, require, cd, local
from fabric.decorators import runs_once
import os

@runs_once
def hoptoad_deploy(deployed=False):
    require('hoptoad_api_key')
    require('deployment_type')
    require('release')
    require('scm')
    if deployed and env.hoptoad_api_key:
        commit = local('git rev-parse --short %(release)s' % env)
        import hoppy.deploy
        hoppy.api_key = env.hoptoad_api_key
        hoppy.deploy.Deploy().deploy(
            env=env.deployment_type,
            scm_revision=commit,
            scm_repository=env.scm,
            local_username=os.getlogin())
        print ('Hoptoad notified of deploy of %s@%s to %s environment by %s'
                % (env.scm, commit, env.deployment_type, os.getlogin()))

@runs_once
def campfire_notify(deployed=False):
    require('deployment_type')
    require('release')

    if (deployed and env.hoptoad_api_key and env.campfire_token
            and env.campfire_room):
        from pinder import Campfire
        deploying = local('git rev-parse --short %(release)s' % env)
        branch = local("git symbolic-ref %(release)s 2>/dev/null "
                "| awk -F/ {'print $NF'}" % env)

        if env.tagged:
            require('release')
            branch = env.release

        deployer = os.getlogin()
        deployed = env.deployed_version
        target = env.deployment_type.lower()
        source_repo_url = env.scm_http_url
        compare_url = ('%(source_repo_url)s/compare/%(deployed)s'
                '...%(deploying)s' % locals())

        campfire = Campfire(env.campfire_subdomain, env.campfire_token)
        room = campfire.find_room_by_name(env.campfire_room)
        room.join()
        message = ('%(deployer)s is deploying %(branch)s '
            '(%(deployed)s..%(deploying)s) to %(target)s %(compare_url)s'
            % locals())
        room.speak(message)
        room.leave()
        print 'Campfire notified that %s' % message

