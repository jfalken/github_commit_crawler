#!/usr/bin/env python

''' Find organizational github users, look at recent commits, audit
    for keywords, flag anything questionable and write the audit results
    into a mongodb collection for later viewing.
'''

import sys
import yaml
import argparse
from github import GithubException
from libs.github_audit_libs import setup_logging
from libs.github_audit_libs import get_github_org_users
from libs.github_audit_libs import github_authenticate
from libs.github_audit_libs import get_audit_events_for_user
from libs.github_audit_libs import do_audit_event
from libs.mongo_utils import mdb_insert_results
from libs.mongo_utils import audit_event_update
from libs.mongo_utils import audit_event_already_done
from libs.mongo_utils import check_lock_status
from libs.mongo_utils import enable_lock
from libs.mongo_utils import disable_lock


def main(config):
    ''' main '''

    try:
        logging = setup_logging(config=config)
        logging.info('[Github_Audit] - Starting')

        # Check for a lock (other service is running?)
        lock_status = check_lock_status()
        if lock_status == 'locked':
            logging.info('[Github_Audit] Lock in Place. Quitting')
            sys.exit(0)

        if lock_status != 'not_locked':
            logging.error('[Github_Audit] Invalid Lock Status, Quitting')
            sys.exit(0)

        # Enable the lock
        enable_lock()
        logging.info('[Github_Audit] Enabling lock')

        # github credentials and api object
        username = config['github']['username']
        password = config['github']['accesstoken']
        org_name = config['github']['org_name']
        ghapi = github_authenticate(username, password)

        # get all the org users and their public events
        logging.info('[Github_Audit] Getting users...')
        org_users = get_github_org_users(ghapi, org_name)
        for user in org_users:
            logging.info('[Github_Audit] Auditing user: "%s"' % user.login)
            logging.info('[Github_Audit] Current Rate Limit: %s remaining' %
                         str(ghapi.rate_limiting[0]))
            audit_events = get_audit_events_for_user(user)

            # if nothing, move on
            if len(audit_events) == 0:
                logging.info('[Github_Audit] No audit events for "%s"' % user.login)
                continue

            logging.info('[Github_Audit] Found %d audit events for "%s"'
                         % (len(user.login), user.login))

            for ae in audit_events:
                # check to see if we've done this already
                if audit_event_already_done(ae):
                    continue

                # audit the events, and mark them as done
                results = do_audit_event(ae, ghapi)
                if not results:
                    oid = audit_event_update(ae)
                    continue

                oid = mdb_insert_results(results)
                oid = audit_event_update(ae)

                logging.info('[Github_Audit] Inserted %s results into mdb. oid: %s'
                             % (len(results), str(oid)))

        logging.info('[Github_Audit] Process done')
        disable_lock()

    except SystemExit:
        # occurs if lock is in place
        sys.exit(0)
    except GithubException:
        print '[Github_Audit] Github Error: Rate limit: %s' % str(sys.exc_info())
        disable_lock()
    except:
        if 'API rate limit exceeded' in str(sys.exc_info()[1]):
            logging.info('[Github_Audit] Rate limit exceeded currently')
            logging.info('[Github_Audit] Run this again next hour.')
            disable_lock()
            sys.exit(0)
        else:
            print 'Error: %s' % str(sys.exc_info())
            try:
                disable_lock()
            except:
                pass
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''GitHub organizational
        auditor''')

    parser.add_argument('-c', '--config', dest='config', required=True,
                        help='(Required) YAML configuration file')

    args = parser.parse_args()

    try:
        config = yaml.load(open(args.config, 'r').read())
    except:
        print 'Could not load the config file: "%s"' % str(sys.exc_info()[1])
        sys.exit(1)

    main(config=config)
