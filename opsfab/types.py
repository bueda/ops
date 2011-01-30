"""
Definitions of available EC2 server types.
"""
#!/usr/bin/env python
from fabric.api import env

def _32bit():
    """ Ubuntu Maverick 10.10 32-bit """
    env.ami = "ami-a6f504cf"

def _32bit_ebs():
    """ Ubuntu Maverick 10.10 32-bit """
    env.ami = "ami-ccf405a5"

def _64bit_ebs():
    """ Ubuntu Maverick 10.10 64-bit """
    env.ami = "ami-cef405a7"

def _64bit():
    """ Ubuntu Maverick 10.10 64-bit """
    env.ami = "ami-08f40561"

def micro():
    """ Micro instance, 613MB, up to 2 CPU (64-bit) """
    _64bit_ebs()
    env.instance_type = 't1.micro'

def small():
    """ Small Instance, 1.7GB, 1 CPU (32-bit) """
    _32bit()
    env.instance_type = 'm1.small'

def large():
    """ Large Instance, 7.5GB, 4 CPU (64-bit) """
    _64bit()
    env.instance_type = 'm1.large'

def extra_large():
    """ Extra Large Instance, 16GB, 8 CPU (64-bit) """
    _64bit()
    env.instance_type = 'm1.xlarge'

def extra_large_mem():
    """ High-Memory Extra Large Instance, 17.1GB, 6.5 CPU (64-bit) """
    _64bit()
    env.instance_type = 'm2.xlarge'

def double_extra_large_mem():
    """ High-Memory Double Extra Large Instance, 34.2GB, 13 CPU (64-bit) """
    _64bit()
    env.instance_type = 'm2.2xlarge'

def quadruple_extra_large_mem():
    """ High-Memory Quadruple Extra Large Instance, 68.4GB, 26 CPU (64-bit) """
    _64bit()
    env.instance_type = 'm2.4xlarge'

def medium_cpu():
    """ High-CPU Medium Instance, 1.7GB, 5 CPU (32-bit) """
    _32bit()
    env.instance_type = 'c1.medium'

def extra_large_cpu():
    """ High-CPU Extra Large Instance, 7GB, 20 CPU (64-bit) """
    _64bit()
    env.instance_type = 'c1.xlarge'

