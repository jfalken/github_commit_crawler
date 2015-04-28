import supervisor.xmlrpc
import xmlrpclib


class SuperXMLRPC(object):
    ''' class to interface w/ xml-rpc interface of supervisord
        documentation: http://supervisord.org/api.html
    '''

    def __init__(self):
        self.p = self._connect()  # server object
        self.procs = self._get_proc_names()  # list of proc names

    def _connect(self):
        sock = 'unix://var/run/supervisor.sock'
        p = xmlrpclib.ServerProxy('http://127.0.0.1',
                                  transport=supervisor.xmlrpc.SupervisorTransport(None, None, sock))
        return p

    def _get_proc_names(self):
        info = self.get_procs_info()
        return [i['name'] for i in info]

    def get_state(self):
        return self.p.supervisor.getState()

    def get_procs_info(self):
        info = self.p.supervisor.getAllProcessInfo()
        return info

    def restart_proc(self, name):
        info = self.get_procs_info()
        try:
            assert name in [i['name'] for i in info]
        except:
            return
        try:
            self.p.supervisor.stopProcess(name)
        except:
            pass
        try:
            self.p.supervisor.startProcess(name)
        except:
            pass
        return

    def get_proc_log(self, name):
        ''' returns latest 1000 lines of log file, chronologically '''
        info = self.get_procs_info()
        try:
            assert name in [i['name'] for i in info]
        except:
            return
        log = self.p.supervisor.readProcessStdoutLog(name, 0, 0)
        return log.split('\n')[::-1][:1000]

