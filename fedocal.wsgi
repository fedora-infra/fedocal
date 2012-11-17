#-*- coding: UTF-8 -*-

import os
## Set the environment variable pointing to the configuration file
os.environ['FEDOCAL_CONFIG'] = '/path/to/your/own/fedocal.cfg'

## The following is only needed if you did not install fedocal
## as a python module (for example if you run it from a git clone).
#import sys
#sys.path.insert(0, '/path/to/fedocal/')

from fedocal import APP as application
