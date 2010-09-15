from fabric.api import env, warn
import datetime
import os

env.time_now = datetime.datetime.now().strftime("%H%M%S-%d%m%Y")
env.version_pattern = r'^v\d+(\.\d+)+?$'
env.pip_install_command = 'pip install -i http://d.pypi.python.org/simple'

env.releases_root = 'releases'
env.current_release_symlink = 'current'
env.current_release_path = os.path.join(env.releases_root, env.current_release_symlink)
env.release_paths = ('a', 'b',)
env.virtualenv = 'env'
env.ssh_port = 1222
env.default_revision = 'HEAD'
env.deploy_user = 'deploy'
env.deploy_group = 'bueda'
env.master_remote = 'origin'
env.settings = "settings.py"
env.scm_url_template = None

# Defaults to avoid using hasattr on env
env.private_requirements = []
env.extra_fixtures = ["permissions"]
env.crontab = None
env.updated_db = False
env.migrated = False
env.celeryd = None
env.hoptoad_api_key = None
env.campfire_token = None
env.sha_url_template = None
env.deployed_version = None

# TODO open source the now deleted upload_to_s3 utils
if 'AWS_ACCESS_KEY_ID' in os.environ and 'AWS_SECRET_ACCESS_KEY' in os.environ:
    import boto.ec2
    import boto.ec2.elb
    import boto.s3
    import boto.s3.connection
    import boto.s3.key
    env.aws_access_key = os.environ['AWS_ACCESS_KEY_ID']
    env.aws_secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
    env.elb_connection = boto.ec2.elb.ELBConnection(
            env.aws_access_key, env.aws_secret_key)
    env.ec2_connection = boto.ec2.EC2Connection(
                env.aws_access_key, env.aws_secret_key)
    _s3_connection = boto.s3.connection.S3Connection(env.aws_access_key,
            env.aws_secret_key)

    env.s3_bucket_name = 'bueda.deploy'
    _bucket = _s3_connection.get_bucket(env.s3_bucket_name)
    env.s3_key = boto.s3.connection.Key(_bucket)
else:
    warn('No S3 key set. To use S3 or EC2 for deployment, '
        'you will need to set one -- '
        'see https://github.com/bueda/buedaweb/wikis/deployment-with-fabric')
