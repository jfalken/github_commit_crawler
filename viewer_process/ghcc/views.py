''' flask app for viewing ghcc results. run runserver.py to run this '''

import sys
from flask import Flask
from flask import request
from flask import render_template
from flask import redirect
from libs.utils import slice_fn
from libs.utils import get_gh_audit_results
from libs.utils import get_gh_audit_result
from libs.utils import get_gh_count
from libs.utils import get_log
from libs.utils import disable_lock
from libs.superxmlrpc import SuperXMLRPC
from libs.config import ConfigChanger
import pymongo


app = Flask(__name__)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', message='Not Found')


@app.route('/')
def index():
    # set the config upon first load
    c = ConfigChanger('/ghcc_process/config/config.yaml')
    if not c.config_file_ok():
        return redirect('/config')

    return redirect('/ghaudit?s=0&l=100')


@app.route('/info')
def info_page():
    return render_template('info.html')


@app.route('/ghaudit', methods=['GET'])
def gh_audit():

    try:
        limit = int(request.args.get('l'))
        skip = int(request.args.get('s'))
        assert int(limit)
        assert int(skip)
    except:
        skip = 0
        limit = 100

    try:
        results = get_gh_audit_results(limit=limit, skip=skip)
    except pymongo.errors.ConnectionFailure:
        return render_template('error.html',
                               message='Can\'t connect to MongoDB. Is it running?')
    except:
        return render_template('error.html',
                               message='Unknown Err: {}'.format(
                                       sys.exc_info()))

    if len(results) == 0:
        return render_template('no_more.html',
                               skip=skip,
                               limit=limit)

    return render_template('gh_audit.html',
                           results=results,
                           slice_fn=slice_fn,
                           limit=limit,
                           skip=skip,
                           total_count=get_gh_count())


@app.route('/ghrecord', methods=['GET'])
def gh_audit_record():

    try:
        if request.args.get('oid'):
            oid = request.args.get('oid')
            assert oid
    except:
        return render_template('error.html',
                               message='Invalid Parameters')

    try:
        result = get_gh_audit_result(oid)
    except:
        return render_template('error.html',
                               message=str(sys.exc_info()))

    return render_template('ghrecord.html',
                           result=result)


@app.route('/logs', methods=['GET'])
def read_log_file():

    log = get_log()
    no_log = False
    if len(log) == 0:
        no_log = True

    return render_template('log.html',
                           log=log,
                           no_log=no_log)


@app.route('/supervisor', methods=['GET'])
def supervisor():

    sxr = SuperXMLRPC()
    return render_template('supervisor.html',
                           SXR=sxr)


@app.route('/supervisor/getlogs', methods=['GET'])
def supervisor_get_logs():

    sxr = SuperXMLRPC()
    try:
        proc = request.args.get('proc').lower()
        assert proc in sxr.procs
    except:
        return redirect('/')

    log = sxr.get_proc_log(proc)
    if len(log) == 0:
        no_log = True
    else:
        no_log = False
    return render_template('log.html',
                           log=log,
                           no_log=no_log)


@app.route('/supervisor/restart', methods=['GET'])
def supervisor_restart():

    sxr = SuperXMLRPC()
    try:
        proc = request.args.get('proc').lower()
        assert proc in sxr.procs
    except:
        return redirect('/')

    disable_lock()
    sxr.restart_proc(proc)
    return redirect('/supervisor')


@app.route('/config', methods=['GET'])
def edit_config():

    c = ConfigChanger('/ghcc_process/config/config.yaml')
    if not c.config_file_ok():
        config = c.get_empty_config()
        default_config = True
    else:
        config = c.load_config()
        default_config = False

    return render_template('config.html',
                           config=config,
                           default_config=default_config)


@app.route('/config/update', methods=['POST'])
def update_config():

    c = ConfigChanger('/ghcc_process/config/config.yaml')
    config = c.get_empty_config()
    config['github']['accesstoken'] = request.form['token']
    config['github']['org_name'] = request.form['orgname']
    config['github']['username'] = request.form['username']
    c.write_config(config)

    # restart ghcc process
    return redirect('/supervisor/restart?proc=ghcc')


