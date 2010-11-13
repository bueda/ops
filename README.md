buedafab -- a collection of Fabric utilities used at Bueda
===============================================================================

## Description

buedafab is a collection of methods for deploying Python apps using Fabric. 

At Bueda, we need to deploy Django, web.py and Tornado applications to our
servers on the Amazon EC2 cloud servers. A frequent point of contention in the
Python web application community seems to be a lack of a "default" pattern for
dpeloying applications to production servers. Our approach may not work for you,
but we would love to compare methods and see if both can't be improved.

## Installation

### Python Package Dependencies

* fabric
* prettyprint
* boto (only if you are using the EC2 methods)
* pinder (only if you are using Campfire notification)
* hoppy (only if you are using Hoptoad notification)

You can install all of these with pip using the `pip-requirements.txt` file:

    $ pip install -r pip-requirements.txt

The recommended method is to install buedafab's dependencies in each of your
project's virtualenvs. An alternative is to install them system-wide, but
depending the way Fabric is installed you may encounter import problems.

buedafab must be in your PYTHONPATH to use its methods - a typical installation
method is to clone a copy of the repository somewhere:

    $ git clone git@github.com:bueda/ops ~

Then edit your .bashrc or .zshrc file so your shell adds this directory to your
PYTHONPATH every time you open a new terminal:

    $ echo "export PYTHONPATH=$PYTHONPATH:$HOME/ops" >> ~/.bashrc

If you will be using the EC2 features of buedafab, add your AWS S3 access key
and secret access key to your shell environment:

    $ echo "export AWS_ACCESS_KEY_ID=<your access key id>" >> ~/.bashrc
    $ echo "export AWS_SECRET_ACCESS_KEY=<your secret key>" >> ~/.bashrc

In any project that you will be using buedafab, activate that project's
virtualenv (using virtualenvwrapper here) and install the ops repo's pip
requirements:

    web/$ workon web
    (web)web/$ pip install -r ~/ops/pip-requirements.txt

## Usage

To use any of the utilies, your project must have a `fabfile.py` and `buedafab`
must be in your `PYTHONPATH`. Some of the utilities are ready-to-go Fabric
commands - the only requirement is that you import them at the top of your
`fabfile.py`.

The `rollback` method in `buedafab/tasks.py` is one of these complete tasks. The
method will roll back an app deployment to the previous version. To use it
in your project, import it at the top of the `fabfile.py`:

    from buedafab.tasks import rollback

and on the commandline, run it like any other Fabric task:

    $ fab rollback

Most of the utilities (`rollback` included) depend on certain keys being set in
the Fabric `env`. Check the documentation of the method you'd like to use to
see what keys it will be expecting and set them to the correct value at the top
of your project's `fabfile.py`. For example, the `rollback` method expects the
`path` key to point to the deploy target on the server. Define it like so:

    env.path = "/var/django/myapp"

The default values for many keys are defined in `beudafab/defaults.py` and can
optionally be overridden by re-defining them just like any other key at the top
of your `fabfile.py`. The defaults should be sufficient if you're following our
deploy directories & methodology as defined in the next section.

## Deploy Directories & Methodology

After a few iterations, Bueda settled on a certain method for organizing
deployed code. Here's what we've come up with.

### Version Control

All projects are maintained with `git` in a remote repository that you have
access to. It need not be GitHub, and you need not have a special deploy key on
the remote server. You will need ssh-agent installed and running if you are
using git submodules in your app.

#### Motive

TODO

### Servers

We maintain four application environments at Bueda - solo, development, staging
and production. We use GitHub, and our commit and deploy workflow goes something
like this:

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

TODO

### Directories

All apps are deployed to `/var` - the actual path is arbitrary, but we've
settled on using `/var/<framework>/appname` so in the case of a Django
application named `five` the path would be `/var/django/five`. The more apps we
deploy, the less I see the value in differentiating based on framework, so this
guideline is the mmostly likely to change.

Within the deploy directory - we will use `/var/django/five` for this example -
there are two subdirectories, `a` and `b`. Each of these contains a clone of the
project's git repository. 

There is additionally a `current` symlink that points to either `a` or `b`.
Whever `current` points, that's what's running in production.

#### Motive

TODO 

### Virtualenv

Both the `a` and `b` directories have separate virtualenvs as a subdirectory
named `env`. The web server must be careful to either add this directory to the
`PYTHONPATH` or use the Python executable at `env/bin/python`. 

buedafab relies on pip's requirements file support to define package depencies
in a project - see `buedafab/deploy/packages.py` for more details.

#### Motive

TODO 

## Example

The `fabfile-example.py` file in this repository has an example `fabfile.py` for
a project that uses a wide range of the methods from buedfab, and sets a few
extra `env` keys.
