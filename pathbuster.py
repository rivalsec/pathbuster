import requests
import argparse
import threading
from requests.packages import urllib3
from io import BytesIO
import string
import random
import os
import urllib.parse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = None
get_work_locker = threading.Lock()
print_locker = threading.Lock()
timeout = 30
headers = dict()


class RequestResult:
    def __init__(self, url, status, bodylen, headers, meta = ''):
        self.base_url = None
        self.url = url
        self.status = status
        self.bodylen = bodylen
        self.meta = meta
        if 'location' in headers:
            self.location = headers['location']
        else:
            self.location = None


    def add_meta(self, s):
        self.meta += s


    def __str__(self):
        s = f"{self.status}\t{self.bodylen}\t{self.url}"
        if self.location:
            s += f"\t-> {self.location}"
        if self.meta:
            s += f"\t{self.meta}"
        return s


    def is_similar(self, other:'RequestResult'):
        if self.status == other.status:
            if other.location:
                return True #do not compare bodys on redirects
                #TODO: headers compare
            diff_threshold = 5
            diff_pc = abs(self.bodylen - other.bodylen) / self.bodylen * 100 if self.bodylen != 0 else other.bodylen
            if  diff_pc < diff_threshold:
                return True
        return False


def random_str(length=30):
    """Generate a random string of fixed length """
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))


def work_prod(urls, paths):
    for path in paths:
        path = path.strip().lstrip('/')
        if not path:
            continue
        for ext in extensions:
            p = path
            if ext:
                p += f".{ext}"
            for url in urls:
                if url in err_table and err_table[url] >= args.max_errors:
                    continue
                yield (url , p)
            

def truncated_stream_res(s: requests.Response, max_size:int):
    readed = 0
    with BytesIO() as buf:
        # for chunk in s.iter_content(1024):
        while True:
            chunk = s.raw.read(1024)
            readed += buf.write(chunk)
            if not chunk or readed > max_size:
                break
        r = buf.getvalue()
    return r


def process_url(url):
    with requests.get(url, headers=headers, timeout=timeout, verify=False, stream=True, allow_redirects=False, proxies=proxies) as s:
        body = truncated_stream_res(s, args.max_response_size)
        return RequestResult(url, s.status_code, len(body), s.headers)


def lprint(s):
    with print_locker:
        print(s)


def save_res(s:RequestResult, url = None):
    if url:
        sheme = urllib.parse.urlparse(url)[0]
        h = urllib.parse.urlparse(url)[1]
        fn = f"{res_dir}/{sheme}_{h}.txt"
        with print_locker:
            with open(f"{res_dir}/_{s.status}.txt", "a") as f:
                f.write(str(s) + "\n")
    else:
        fn = f"{res_dir}/_main.txt"
    with print_locker:
        with open(fn, "a") as f:
            f.write(str(s) + "\n")


def preflight_worker():
    while True:
        with get_work_locker:
            try:
                url = next(precheck_iter)
            except StopIteration:
                return
    
        for i in range(args.random_samples):
            rstr = random_str()
            urlpath = f"{url}/{rstr}"

            try:
                res = process_url(urlpath)
            except Exception as e:
                lprint(str(e))
                err_table[url] = args.max_errors
                break

            save_res(res)
            # collect samples (status code, body length) for future comparison if response status of random url not excluded by settings
            # TODO: headers compare
            if not status_excluded(res.status):
                if url not in preflight_samples:
                    preflight_samples[url] = []

                if len(preflight_samples[url]) == 0 or samples_diff(res, url):
                    lprint(f"{res} status code not excluded, add to preflight samples")
                    preflight_samples[url].append(res)


def status_excluded(status_code: int):
    return status_code in exclude_codes


def samples_diff(res: RequestResult, url: str):
    """is differ from ALL url samples?"""
    for sample in preflight_samples[url]:
        if res.is_similar(sample):
            return False
    return True


def result_valid(res:RequestResult, url):
    if not status_excluded(res.status):
        # if status code not excluded compare res with preflight samples
        if url in preflight_samples and any((True for x in preflight_samples[url] if x.status == res.status)): #end code to
            if samples_diff(res, url):
                #meta
                res.add_meta(' (preflight differ)')
                return True
        else:
            return True
    return False


def worker():
    while True:
        with get_work_locker:
            try:
                url, path = next(task_iter)
            except StopIteration:
                return

        urlpath = f"{url}/{path}"
        try:
            res = process_url(urlpath)
        except Exception as e:
            err_table[url] = err_table.get(url, 0) + 1
            lprint(str(e))
            continue

        if result_valid(res, url):
            lprint(f"{res}")
            save_res(res, url)


def start_thread_pool(threads, worker):
    workers = []
    for i in range(threads):
        t = threading.Thread(target=worker, name='worker {}'.format(i),args=())
        t.start()
        workers.append(t)

    for w in workers:
        w.join()


if __name__ == "__main__":
    err_table = dict()
    res_dir = "pathbuster-res"
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='multiple hosts web path scanner')
    parser.add_argument('-u', '--urls_file', type=argparse.FileType(mode='r', encoding='UTF-8'), help='urls file (base url)', required=True)
    parser.add_argument('-p', '--paths_file', type=argparse.FileType(mode='r', encoding='UTF-8'), help='paths wordlist', required=True)
    parser.add_argument('-e', '--exclude_codes', type=str, help="Exclude status codes, separated by commas (Example: 404,403)", default="404")
    parser.add_argument('-x', '--extensions', type=str, help="Extension list separated by commas (Example: php,asp)", default="")
    parser.add_argument('--proxy', type=str, help='proxy ip:port', default=None)
    parser.add_argument('--max_response_size', help='Maximum response size in bytes', default=250000)
    parser.add_argument('--max_errors', help='Maximum errors before url exclude', default=5)
    parser.add_argument('--threads', type=int, help='Number of threads (keep number of threads less than the number of hosts)', default=10)
    parser.add_argument('--random_samples', type=int, help='how many responses to random urls we collect for comparison (set 0 to disable preflight checks)', default=3)
    parser.add_argument('-H','--header', action='append', help="Add custom HTTP request header, support multiple flags (Example: -H \"Referer: example.com\" -H \"Accept: */*\")")
    parser.add_argument('--user_agent', type=str, help="User agent", default="Mozilla/5.0 (compatible; pathbuster/0.1; +https://github.com/rivalsec/pathbuster)")

    args = parser.parse_args()
    if args.proxy:
        proxies = {
            'http': args.proxy,
            'https': args.proxy
        }

    headers["User-Agent"] = args.user_agent

    if args.header:
        for h in args.header:
            k, v = [x.strip() for x in h.split(':', maxsplit=1)]
            headers[k] = v

    exclude_codes = [int(x.strip()) for x in args.exclude_codes.strip(',').split(',')]
    extensions = ['']
    if args.extensions:
        extensions.extend([x.strip() for x in args.extensions.strip().strip(',').split(',')])
    urls = []
    for url in args.urls_file:
        urls.append(url.strip().rstrip('/'))
    args.urls_file.close()

    if not os.path.exists(res_dir):
        os.mkdir(res_dir)

    print("Pre-Flight check on random urls")
    preflight_samples = {} # for preflight results
    precheck_iter = (x for x in urls)
    start_thread_pool(args.threads, preflight_worker)

    print("Pre-Flight ended, start main task")
    task_iter = work_prod(urls, args.paths_file)
    start_thread_pool(args.threads, worker)

    args.paths_file.close()
    print('THE END')
