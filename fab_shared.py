"""
Included for legacy support of fabfiles depending on a one-file fab_shared.
"""
import buedafab
from buedafab.aws import *
from buedafab.celery import *
from buedafab.commands import *
from buedafab.db import *
from buedafab.environments import *
from buedafab.notify import *
from buedafab.operations import *
from buedafab.testing import *
from buedafab.utils import *

import buedafab.deploy
from buedafab.deploy.cron import *
from buedafab.deploy.packages import *
from buedafab.deploy.release import *
from buedafab.deploy.types import *
from buedafab.deploy.utils import *
