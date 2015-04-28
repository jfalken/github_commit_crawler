#!/usr/bin/env python

''' mongodb related methods for github audit
'''

from pymongo import MongoClient


def check_lock_status():
    ''' returns status of lock; creates lock record
        if it does not already exist
    '''
    db = _connect_mongo()
    col = db['lock']
    doc = col.find({'type': 'lock'})
    # If we dont have a lock document; create one
    if doc.count() == 0:
        col.update({'type'  : 'lock'},
                   {'type'  : 'lock',
                    'status': 'not_locked'},
                   upsert = True)
        return 'not_locked'
    else:
        return doc[0]['status']


def enable_lock():
    ''' enabled service lock '''
    db = _connect_mongo()
    col = db['lock']
    col.update({'type': 'lock'},
               {'type': 'lock',
                'status': 'locked'},
               upsert = True)
    return


def disable_lock():
    ''' disables service lock '''
    db = _connect_mongo()
    col = db['lock']
    col.update({'type': 'lock'},
               {'type': 'lock',
                'status': 'not_locked'},
               upsert=True)
    return


def _connect_mongo():
    ''' returns a mongodb collection to github database '''
    client = MongoClient()
    return client['github_audit']


def mdb_insert_results(results):
    ''' inserts result records into mongodb
        :param results: a list of result dicts, from `do_audit_events`

        returns object id of the insert
    '''
    db = _connect_mongo()
    col = db['results']
    col.ensure_index('uid')
    col.ensure_index('matched')
    oid = col.insert(results)
    return oid


def audit_event_update(audit_event):
    ''' updates the audit event tracking collection
        :param audit_event: an audit event object
    '''
    event_unique_id = '%s-%s' % (audit_event.actor.login, str(audit_event.id))
    db = _connect_mongo()
    col = db['history']
    col.ensure_index('uid')
    oid = col.insert({'uid': event_unique_id})
    return oid


def audit_event_already_done(audit_event):
    ''' checks to see if an audit event has already been processed
        :param audit_event: an audit_event object

        returns bool
    '''
    event_unique_id = '%s-%s' % (audit_event.actor.login, str(audit_event.id))

    db = _connect_mongo()
    col = db['history']
    c = col.find({'uid': event_unique_id})
    if c.count() > 0:
        return True
    else:
        return False
