buedafab Usage Example
============================

The example `fabfile.py` in this directory assumes that you are using the deploy
directories & methodology laid out in buedafab's README. 

## Usage

    example/$ fab -l
    Available commands:

        deploy
        development
        disable
        enable
        lint
        localhost
        production
        reset
        restart_webserver   Restart the Gunicorn application webserver
        rollback            Swaps the current and previous release that was depl...
        setup
        staging
        test

    bc. $ fab <development/production/localhost> deploy[:release=<tag>]

A Fabric run must have one of `production`, `development` or `localhost` as the
first parameter to specify which environment you would like the following
commands to operate. For example, the `production` environment updates all
servers behind the load balancer, while the `development` environment only
updates dev.bueda.com. 

Tag a specific commit of djangoapp as a new release, then deploy to all
production machines:

    bc. ~/web$ fab production deploy:commit=6b4943c

Deploy HEAD to the development machine without making a tagged release:

    bc. ~/web$ fab development deploy

Deploy a specific commit to the development machine without making a tagged
release:

    bc. ~/web$ fab development deploy:commit=6b4943c

Deploy a tag that already exists to all production machines:

    bc. ~/web$ fab production deploy:release=v0.1.1

## Server Provisioning

The Fabfile in the [ops](http://github.com/bueda/ops) repository supports
provisioning new servers in EC2 using Chef. You can import the methods it uses
into your own `fabfile.py` as well. There are quite a few prerequisites not
mentioned here, namely a working Chef setup, but this should be a good start.

This requires gems, installed with rubygems.

    $ gem install chef fog net-ssh-multi

    ~/ops$ fab -l
    Available commands:
        deploy                     Deploy the shared fabfile.
        development                Sets roles for development server.
        double_extra_large_mem     High-Memory Double Extra Large Instance, 34.2...
        extra_large                Extra Large Instance, 16GB, 8 CPU (64-bit)
        extra_large_cpu            High-CPU Extra Large Instance, 7GB, 20 CPU (6...
        extra_large_mem            High-Memory Extra Large Instance, 17.1GB, 6.5...
        large                      Large Instance, 7.5GB, 4 CPU (64-bit)
        medium_cpu                 High-CPU Medium Instance, 1.7GB, 5 CPU (32-bi...
        production                 Sets roles for production servers behind load...
        put
        quadruple_extra_large_mem  High-Memory Quadruple Extra Large Instance, 6...
        rechef                     Run the latest Chef cookbooks on all servers.
        small                      Small Instance, 1.7GB, 1 CPU (32-bit)
        spawn                      Create a new server instance, which will boot...

To create a test machine with your base config (so you can SSH in with your
regular user credentials):

    $ fab <small/large/extra_large/etc> spawn

To create a production/development machine:

    $ fab <small/large/extra_large/etc> <development/production> spawn

To force a re-run of Chef *immediately*:

    $ fab production rechef
