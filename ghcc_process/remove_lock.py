#!/usr/bin/env python

''' manually removes a ghcc process lock incase something screws up '''

import sys
import pymongo
from libs.mongo_utils import disable_lock

try:
    disable_lock()
except pymongo.errors.ConnectionFailure:
    print 'Error removing lock: {}'.format(sys.exc_info()[0])
    print 'Is mongod running?'
except:
    print 'Error removing lock: {}'.format(sys.exc_info()[0])
