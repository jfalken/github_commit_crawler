#!/usr/bin/env python

''' library to be used with github organization audit script
'''

import re
import sys
import json
import github
import logging
import datetime
from keywords import KEYWORDS


def github_authenticate(username, password):
    ''' return authenticated github api object
        username and password should be personal access tokens '''
    try:
        return github.Github(username, password)
    except:
        raise Exception('Cannot authenticate: %s'
                        % str(sys.exc_info()[1]))


def _ghapi_get(ghapi, url, method='GET'):
    ''' wrapper for a generic authenticated GET request using github api '''
    try:
        resp = ghapi._Github__requester.requestJson('GET', url)
        return {'resp_code': resp[0],
                'headers': resp[1],
                'content': json.loads(resp[2])}
    except:
        raise Exception('Cannot get url "%s": %s'
                        % (url, str(sys.exc_info()[1])))


def get_github_org_users(ghapi, org_name):
    ''' return a list of github user objects in org_name '''
    try:
        org = ghapi.get_organization(org_name)
        return [i for i in org.get_members()]
    except:
        raise Exception('Error getting Github users: %s'
                        % str(sys.exc_info()[1]))
    pass


def get_audit_events_for_user(user_object):
    ''' returns a list of public events for github user_object '''
    etypes = ['PushEvent']
    return [i for i in user_object.get_public_events() if i.type in etypes]


def get_audit_events_for_org(org_users):
    ''' returns a list of audit events for all org_users '''
    return [user.get_audit_events_for_user(user) for user in org_users]


def _parse_for_aws_creds(input_string):
    ''' parses input_string to see if it contains AWS credentials
        returns boolean if set of matching regexes are found
    '''
    # regexes from http://blogs.aws.amazon.com/security/blog/tag/key+rotation
    ak_pat = '(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])'
    sk_pat = '(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])'
    if re.search(ak_pat, input_string):
        if re.search(sk_pat, input_string):
            return True
    return False


def _parse_keywords(input_string):
    ''' parses input_string for keywords and aws credentials '''
    keywords = KEYWORDS
    matches = []
    for kw in keywords:
        if kw.lower() in input_string.lower():
            match = {'string'      : input_string,
                     'matched_word': kw}
            matches.append(match)
    if _parse_for_aws_creds(input_string):
        matches.append({'string'      : input_string,
                        'matched_word': 'AWS Credential'})
    return matches


def _parse_push_event(event, ghapi):
    ''' parses a push event payload and returns a dict of (source, txt)
        of the files modified in that push event '''
    results = []
    audit_dt = datetime.datetime.utcnow()
    try:
        # get all the commit(s)
        event_unique_id = '%s-%s' % (event.actor.login, str(event.id))
        author = event.actor.login
        for commit in event.payload['commits']:
            # unique id for tracking
            # get the details
            resp = _ghapi_get(ghapi, commit['url'])
            content = resp['content']
            # review the patches
            for f in content['files']:
                if 'patch' in f:
                    patch = f['patch']
                    # look for keyword matches
                    matches = _parse_keywords(patch)
                    if len(matches) > 0:
                        for m in matches:
                            results.append({
                                           'audit_date': audit_dt,
                                           'blob'      : f['blob_url'],
                                           'string'    : m['string'],
                                           'matched'   : m['matched_word'],
                                           'commit_url': commit['url'],
                                           'author'    : author,
                                           'uid'       : event_unique_id,
                                           'html_url'  : content['html_url']})
    except:
        pass
        # print str(sys.exc_info())
    return results


def do_audit_event(audit_event, ghapi):
    ''' audits event(s). returns results object '''
    results = []
    if audit_event.type == 'PushEvent':
        results += _parse_push_event(audit_event, ghapi)
    if len(results) == 0:
        return None
    else:
        return results


def setup_logging(config):
    logging.basicConfig(filename=config['log']['file'],
                        format=config['log']['format'],
                        datefmt=config['log']['dateformat'],
                        level=logging.INFO)
    logging.getLogger('requests').propagate = False
    return logging
