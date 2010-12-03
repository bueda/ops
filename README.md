buedafab -- a collection of Fabric utilities used at Bueda
===============================================================================

## Description

buedafab is a collection of methods for deploying Python apps using Fabric. 

At Bueda, we need to deploy Django, web.py and Tornado applications to our
servers in the Amazon EC2 cloud. A frequent topic of conversation in the Python
web application community seems to be a lack of a "default" pattern for
deploying applications to production servers. Our approach may not work for you,
but we would love to compare methods and see if both can't be improved.

Read the "Contributing" section of this README if you've got something to add.

### Related Projects

[django-boilerplate](https://github.com/bueda/django-boilerplate)
[tornado-boilerplate](https://github.com/bueda/tornado-boilerplate)
[python-webapp-etc](https://github.com/bueda/python-webapp-etc)
[comrade](https://github.com/bueda/django-comrade)

## Installation

buedafab only need be in your PYTHONPATH - a typical installation method is to
clone a copy of the repository somewhere:

    $ git clone git@github.com:bueda/ops ~/projects

Then edit your .bashrc or .zshrc file so your shell adds this directory to your
PYTHONPATH every time you open a new terminal:

    $ echo "export PYTHONPATH=$PYTHONPATH:$HOME/projects/ops" >> ~/.bashrc

In the future, it could be packaged up and installed with pip.

If you will be using the AWS features of buedafab, add your AWS access key ID
and secret access key to your shell environment:

    $ echo "export AWS_ACCESS_KEY_ID=<your access key id>" >> ~/.bashrc
    $ echo "export AWS_SECRET_ACCESS_KEY=<your secret key>" >> ~/.bashrc

### Python Package Dependencies

* fabric
* prettyprint
* boto (only if you are using the Amazon Web Services commands)
* pinder (only if you are using Campfire notification)
* hoppy (only if you are using Hoptoad notification)

You can install all of these with pip using the `pip-requirements.txt` file:

    $ pip install -r pip-requirements.txt

If you already have Fabric, the same can be accomplished with:

    $ fab setup

The recommended method is to install buedafab's dependencies in each of your
project's [virtualenv](http://pypi.python.org/pypi/virtualenv)s.

In any project that you will be using buedafab, activate that project's
virtualenv (using
[virtualenvwrapper](http://www.doughellmann.com/projects/virtualenvwrapper/)
here) and install the ops repo's pip requirements:

    web/$ workon web
    (web)web/$ pip install -r ~/projects/ops/pip-requirements.txt

An alternative is to install them system-wide, but depending the way Fabric is
installed you may encounter problems with Python imports.

## Usage

To use any of the utilities, your project must have a `fabfile.py` and
`buedafab` must be in your `PYTHONPATH`. Some of the utilities are ready-to-go
Fabric commands - the only requirement is that you import them at the top of
your `fabfile.py`.

For example, the `rollback` method in `buedafab/tasks.py` is s a complete Fabric
command. The method will roll back an app deployment to the previous version.
To use it in your project, import it at the top of the `fabfile.py`:

    from buedafab.tasks import rollback

and on the command line, run it like any other Fabric task:

    $ fab rollback

Most of the utilities (`rollback` included) depend on certain keys being set in
the Fabric `env`. Check the documentation of the method you'd like to use to
see what keys it will be expecting and set them to the correct value at the top
of your project's `fabfile.py`. For example, the `rollback` method expects the
`path` key to point to the deploy target on the server:

    env.path = "/var/webapps/myapp"

The default values for many keys are defined in `beudafab/defaults.py` and can
be overridden as needed by re-defining them at the top of your `fabfile.py`. The
defaults should be sufficient if you're using our deploy directory layout &
methodology as defined in the next section.

Here are the commands we use most often:

### fab test

Run the test suite for this project. There are currently test runners defined
for Django, Tornado, and general
[nose](http://somethingaboutorange.com/mrl/projects/nose/0.11.2/) test suites.
Just set `env.test_runner` to the appropriate method (or write your own).

### fab lint

Run pylint on the project, including the packages in `apps/`, `lib/` and
`vendor/`, and using the `.pylintrc` file in the project's root.

### fab <development/staging/production> ... 

Some of the commands require an app environment - `buedafab` defines four
different environments: localhost, development, staging and production. These
are defined in `buedafab/environments.py` and can be overridden or extended.

These commands don't do anything on their own, but are meant to prefix other
commands, such as...

### fab <environment> deploy

Deploy this app to the environment <environment> using the git-backed deploy
strategy defined at the end of this README. Some example use cases:

Deploy a new tagged release from HEAD to all production machines (will prompt
for the tag to use):

    ~/web$ fab production deploy

Tag a specific commit as a new release, then deploy to all production machines:

    ~/web$ fab production deploy:commit=6b4943c

Deploy HEAD to the development machine without making a tagged release:

    ~/web$ fab development deploy

Deploy a specific commit to the development machine without making a tagged
release:

    ~/web$ fab development deploy:commit=6b4943c

Deploy a tag that already exists to all production machines:

    ~/web$ fab production deploy:release=v0.1.1

### fab setup

A shortcut to bootstrap or update a virtualenv with the dependencies for this
project. Installs the pip requirements files listed in `env.pip_requirements`
and `env.pip_requirements_dev` and initializes/updates any git submodules.

It also supports the concept of "private packages" - i.e. Python packages that
are not available on PyPi but require some local compilation and thus don't work
well as git submodules. It can either download a tar file of the package from
S3 or clone a git repository, build and install the package. The private package
methods could use a little work - it's probably a better idea to clone a git
submodule and just run `python setup.py build`.

### fab restart_webserver

Assuming your remote server has an init script for this application's process at
`/etc/init.d/%(unit)s`, this command simple bounces the web server.

### fab rollback

Roll back the deployed version to the previously deployed version - i.e. swap
the `current` symlink from the `a` to the `b` directory (see below for the
methodology this uses).

### fab <enable/disable> maintenancemode

If your Django project uses the
[maintenancemode app](https://github.com/jezdez/django-maintenancemode), 
this command will toggle that on and off. It finds the `MAINTENANCE_MODE`
variable in your `settings.py` on the remote server, toggles its value and
restarts the web server.

## Deploy Directories & Methodology

After a few iterations, Bueda settled on a certain method for organizing
deployed code. Here's what we've come up with.

### Version Control

All projects are versioned with `git` in a remote repository accessible to all
developers. It need not be GitHub, and you need not have a special deploy key on
the remote server. You will need `ssh-agent` installed and running if you are
using git submodules in your app.

#### Motive

Developers should only be able to deploy from a remote repository to make sure
that deployed code (no matter if it's to a development, staging or production
environment) is always available to other developers. If a developer deploys
from a local repository and forgets to push their commits, it can wreak havoc if
that developer becomes unavailable. 

Additionally, deployment should always be a manually initiated push operation,
not an automated pull one. A developer or operations person should always be at
the helm of a deployment, no matter how automated the actual process is. This
person should ideally be able to triage and resolve a bad deploy manually if the
need arises.

Finally, servers shouldn't require any special authentication to deploy. Since
we've always got a live person leading the deploy, they can use their own
personal SSH authentication keys to clone or update a remote repository.

### Application Environments

We maintain four application environments across at least two servers at Bueda -
solo, development, staging and production. We use GitHub, and our commit and
deploy workflow goes something like this:

#### As a developer...

1. Create your own fork of the master repo on GitHub
1. Clone your fork and make changes locally, test at localhost:8000 with
    built-in Django server
1. Commit changes into a feature branch and push to your fork
1. Send a pull request on GitHub to the repo's owner

#### As the repository's integration master:

1. When someone sends a pull request, evaluate the difference and if it's good,
    merge it into the development branch of the main repo
1. Deploy to development server: `~/web$ fab development deploy`
1. Test again on live development server, make sure everything works (including
    database access, since that is the primary difference)
1. If all is good, merge the development branch into the master branch:
    `~/web$ git checkout master && git merge development master`
1. Deploy to to staging with Fabric to test the live production environment
    minus the public URL: `~/web$ fab staging deploy` 
1. Again, if everyone looks good, tag and push to production with Fabric:
    `~/web$ fab production deploy` 
1. If somehow after all of your diligent testing the update broke production,
    rollback to the last version: `~/web$ fab production rollback`

#### Motive

Beyond developing and testing locally, developers should have an easy way to get
their code onto a remote server somewhat similar to the production environment.
This is our `development` environment - it is backed by a completely isolated
database with no live user data, on a separate physical server (well, as
separate as a virtual machine can get). Any developer can deploy here anytime to
make collaborating with a distributed team as easy as possible. The
`development` environment is usually running the HEAD of the `development`
branch from git.

The `staging` environment is one big step closer to production. This environment
is usually running the HEAD of the `master` branch. This environment is on a
separate physical server from production, but uses the production database.

Finally, the `production` environment exists on its own server (or cluster of
load-balanced servers) and only ever runs a tagged commit from the `master`
branch in git. This way anyone can tell which version is in production by
looking in their git repository for the latest tag.

### Directories

All apps are deployed to `/var/webapps/appname` - the actual path is arbitrary,
this is just our convention. We bind this path to the EC2 instances ephemeral
storage on /mnt, to avoid filling up the root drive.  The path to an application
named `five` would be `/var/webapps/five`.

Within the deploy directory (continuing with our example of `/var/webapps/five`)
there is a `releases` subdirectory. This in turn contains two more
subdirectories, `a` and `b`. Each of these contains a clone of the project's git
repository. Why not put `a` and `b` at right at `/var/webapps/five`? There are
some cases where you need to store logs or data files along side an app, and
it's good not to mix those with `releases`.

There is also a `current` symlink that points to either `a` or `b`.  Wherever
`current` points, that's what's running in production.

The final directory structure looks like:

    /var/
       webapps/
            app/
                releases/
                    a/
                    b/
                    current -> a

#### Motive

Our Internet spelunking found four prevailing ways to organize deploy
directories:

##### Separate deploy directories by timestamp

Every time you deploy, a new directory is created on the remote server with the
current timestamp. The repository is either re-cloned from the remote, pushed
from the local repo, or archived and uploaded from the deploying
machine. A `current` symlink points to the deployed release. To rollback, find
the timestamp before `current`.

##### Separate deploy directories by commit SHA or tag

Each commit SHA or tag (or output from `git describe`) gets a separate folder.
The repository is either re-cloned from the remote, pushed from the local repo,
or archived and uploaded from the deploying machine. A `current` symlink points
to the deployed release, and `previous` to the last (for rollback purposes).

In both this scenario and the timestamp strategy, if the deploys are archived
and uploaded, it is a good idea to keep the original `app-VERSION.tar.gz` in a
`packages/` directory alongside `releases`.

##### Single deploy directory, version selected with git

Use one deploy target folder per application, and rely on git to update and
checkout the version you wish to deploy. No need for symlinks - the one folder
is always the deployed version. There is no specific way to 'rollback' since
there is no record of the 'previous' version except the git log.

GitHub [uses this approach](https://github.com/blog/470-deployment-script-spring-cleaning).

##### Two deploy directories, version selected with git

This method is similar to the single deploy directory approach in that it uses
git to update to the latest version, but it keeps two directories - an `a` and a
`b` (the names are arbitrary) and uses symlinks to bounce back and forth between
them on alternate deploys.

This method doesn't require a `git reset --hard` and gives you a bit of a buffer
between the currently deployed version and the one that's about to go live.
Especially considering that this gets you separate virtualenvs (and a thus a
buffer against funky egg installs or PyPi outages) it is the method we have
settled on and what buedafab uses.

### Virtualenv

Both the `a` and `b` directories have separate virtualenvs as a subdirectory
named `env`. The web server must be careful to either add this directory to the
`PYTHONPATH` or use the Python executable at `env/bin/python`. 

buedafab relies on pip's requirements file support to define package
dependencies in a project - see `buedafab/deploy/packages.py` for more details.

#### Motive

At one point in time, we wiped and rebuilt a virtualenv for the application from
scratch each deploy. This is clearly the safest solution, as it will always get
the correct versions of each package. The time spent, however, was not worth the
added safety to us. Our applications have dependencies that typically take 5-10
minutes to install from scratch - by sharing the virtualenv from the previous
deploy and using the `--update` flag to bump package versions as necessary, we
save a lot of time.

The only tricky point at the moment is if your pip requirements files have paths
to SCM repositories. Perhaps due to operator error, but we have found pip to be
unreliable when it comes to checking out specific tags or commit IDs from SCM.
It can often get in a bad state (e.g. a detached HEAD in a git repository that
pip can't seem to handle) that requires the `src/` directory inside the
virtualenv to be wiped.

## Example

The `fabfile-example.py` file in this repository has an example `fabfile.py` for
a project that uses a wide range of the methods from buedfab, and sets a few
extra `env` keys.

## TODO

* Document crontab support, and add the scripts directory to the boilerplate
    repository. We stopped using this in favor of celery scheduled tasks, but
    someone else may still want it (and the code works fine).

## Contributing

If you have improvements or bug fixes:

* Fork the repository on GitHub
* File an issue for the bug fix/feature request in GitHub
* Create a topic branch
* Push your modifications to that branch
* Send a pull request

## Authors

* [Bueda Inc.](http://www.bueda.com)
* Christopher Peplin, peplin@bueda.com, @[peplin](http://twitter.com/peplin)
