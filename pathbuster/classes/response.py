import json
from utils.common import count_lines, count_words, md5str
import urllib.parse


class Response:
    def __init__(self, url, status, reason, body, headers, parent_url, meta = None):
        self.base_url = None
        self.url = url
        self.status = status
        self.reason = reason
        self.headers = headers
        self.parent_url = parent_url
        if "Content-Length" in headers:
            self.bodylen = int(headers["Content-Length"])
        else:
            self.bodylen = len(body)
        self.strbody = body.decode('utf-8', errors='ignore')
        self.bodywords = count_words(self.strbody)
        self.bodylines = count_lines(self.strbody)
        self.meta = []
        if meta:
            self.meta.append(meta)
        if 'location' in headers:
            self.location = headers['location']
        else:
            self.location = None
        up = urllib.parse.urlparse(url)
        self.scheme = up[0]
        self.host = up[1]
        self.path_hash = md5str(up[2])
        self.body = body


    def add_meta(self, s):
        self.meta.append(s)


    def __str__(self):
        s = f"{self.url}\t{self.status}\tBytes:{self.bodylen}/Lines:{self.bodylines}/Words:{self.bodywords}"
        if self.location:
            s += f"\t-> {self.location}"
        if self.meta:
            meta = ', '.join(self.meta)
            s += f"\t{meta}"
        return s


    def is_similar(self, other:'Response'):
        if  self.status == other.status and self.bodywords == other.bodywords and self.bodylines == other.bodylines:
            return True


    def to_json(self, store_response=False):
        jkeys = ['url', 'status', 'reason', 'parent_url', 'meta', 'scheme', 'host']
        if store_response:
            jkeys.append('strbody')
        jres = { k:getattr(self,k) for k in jkeys}
        return json.dumps(jres)