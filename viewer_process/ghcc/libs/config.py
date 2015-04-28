import yaml


class ConfigChanger(object):
    ''' class to read/write the config file
    '''

    def __init__(self, location):
        self.loc = location  # path to yaml file

    def config_file_ok(self):
        ''' returns boolean if config file is OK and contains good values,
            or false if config needs to be edited
        '''
        # try to load the config
        try:
            f = open(self.loc, 'r')
        except:
            return False
        # check for default values
        try:
            config = yaml.load(f)
            if config['github']['accesstoken'] == 'secret_access_token':
                return False
            if config['github']['org_name'] == 'org_name':
                return False
            if config['github']['username'] == 'githubhandle':
                return False
        except:
            return False
        return True

    def write_config(self, config):
        ''' write the yaml file '''
        f = open(self.loc, 'w')
        return yaml.dump(config, f)

    def load_config(self):
        ''' load the yaml file; return it '''
        f = open(self.loc, 'r')
        return yaml.load(f)

    def get_empty_config(self):
        return {'github': {'accesstoken': 'secret_access_token',
                           'org_name': 'org_name',
                           'username': 'githubhandle'},
                'log': {'dateformat': '%Y-%m-%d %H:%M:%S',
                        'file': 'ghcc.log',
                        'format': '[%(asctime)s] [%(levelname)s] - %(message)s'}
                }


