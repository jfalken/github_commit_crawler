#!/usr/bin/python

import bson
from pymongo import MongoClient


def connect_mongo():
    ''' connects to mongodb and returns client object '''
    client = MongoClient()
    return client


def slice_fn(s):
    ''' hack to slice filename in 'blob' entries in github audit '''
    try:
        return s.split('/')[-1]
    except:
        return ''


def get_gh_count():
    ''' return count of all results '''
    client = connect_mongo()
    col = client['github_audit']['results']
    return col.count()


def get_gh_audit_results(limit, skip=0):
    ''' returns a result set of github audit results '''
    client = connect_mongo()
    col = client['github_audit']['results']
    c = col.find().sort('audit_date', -1).skip(skip).limit(limit)
    return [i for i in c]


def get_gh_audit_result(oid):
    ''' returns a result set of github audit results '''
    client = connect_mongo()
    col = client['github_audit']['results']
    try:
        c = col.find({'_id': bson.ObjectId(oid)})
        return c[0]
    except:
        return {'string': 'Not Found'}


def get_log(logfile_path='ghcc.log'):
    ''' returns a list of lines from the log file, chronologically sorted
        this was added to easily read logs when in docker; this may not work
        in other implementations depending on where your log file is
    '''
    try:
        logf = open(logfile_path, 'r').readlines()
        logf = logf[::-1]  # reverse for newest on top
        logf = logf[:1000]  # limit the output
        return [i.strip() for i in logf]
    except:
        return []


def disable_lock():
    ''' disables service lock; call before process restarts '''
    client = MongoClient()
    db = client['github_audit']
    col = db['lock']
    col.update({'type': 'lock'},
               {'type': 'lock',
                'status': 'not_locked'},
               upsert=True)
    return

