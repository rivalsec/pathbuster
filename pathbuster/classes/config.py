class Config:
    def __init__(self):
        #global settings
        self.proxies = None
        self.timeout = 30
        self.headers = dict()
        self.max_errors = 5
        self.http_method = 'GET'
        self.max_response_size = 250000
        self.store_response = False
        self.filter_regex = None
        self.json_print = False
        self.follow_redirects = False
        self.max_redirects = 3
        self.exclude_codes = [404,]
        self.extensions = ['']
        self.stats = None
        self.res_dir = None
        self.stats_interval = 60