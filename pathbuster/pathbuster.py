#!/usr/bin/env python3

import requests
import argparse
import threading
from requests.packages import urllib3
from io import BytesIO
import os
import urllib.parse
import sys
import time
import re
from classes.config import Config
from classes.response import Response
from utils.common import random_str


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

get_work_locker = threading.Lock()
print_locker = threading.Lock()
preflight_iter = None
task_iter = None
preflight_samples = {} # for preflight results
results = [] # for workers results
err_table = dict()
uniq_locs = set()


#global settings
conf = Config()


def work_prod(urls, paths, extensions = [''], update_stats=False):
    for path in paths:
        for ext in extensions:
            p = path.lstrip('/')
            if ext:
                p += f".{ext.lstrip('.')}"
            if update_stats:
                stats['path'] = p
            for url in urls:
                if update_stats:
                    stats['reqs_done'] += 1
                if url in err_table and err_table[url] >= conf.max_errors:
                    continue
                yield (url.rstrip('/') , p)
            

def truncated_stream_res(s: requests.Response, max_size:int):
    readed = 0
    with BytesIO() as buf:
        for chunk in s.iter_content(None, False):
            readed += buf.write(chunk)
            if readed > max_size:
                break
        r = buf.getvalue()
    return r


def process_url(url, parent = None):
    with requests.request(conf.http_method, url, headers=conf.headers, timeout=conf.timeout, verify=False, stream=True, allow_redirects=False, proxies=conf.proxies) as s:
        body = truncated_stream_res(s, conf.max_response_size)
        return Response(url, s.status_code, s.reason, body, s.headers, parent_url=parent)


def lprint(s, **kwargs):
    with print_locker:
        print(s, **kwargs)


def save_res(s:Response):
    fn = f'{conf.res_dir}/{s.scheme}_{s.host}.txt'
    with print_locker:
        with open(fn, "a") as f:
            f.write(str(s) + "\n")
        with open(f'{conf.res_dir}/_{s.status}.txt', 'a') as f:
            f.write(str(s) + '\n')
    if conf.store_response and s.bodylen:
        site_dir = f'{conf.res_dir}/responses/{s.scheme}_{s.host}'
        res_fn = f'{site_dir}/{s.path_hash}.txt'
        if not os.path.exists(site_dir):
            os.mkdir(site_dir)
        with print_locker:
            with open(f'{conf.res_dir}/_index.txt', 'a') as f:
                f.write(f'{res_fn}\t{s.url}\n')
        with open(res_fn, 'wb') as f:
            f.write(f'HTTP/2 {s.status} {s.reason}\n'.encode())
            for k,v in s.headers.items():
                # remove because of nuclei parse error with passive mode
                if k.title() == 'Transfer-Encoding':
                    continue
                f.write(f'{k.title()}: {v}\n'.encode())
            f.write('\n'.encode())
            f.write(s.body)


def preflight_worker():
    while True:
        with get_work_locker:
            try:
                url, path = next(preflight_iter)
            except StopIteration:
                return

        try:
            res = process_url(f'{url}/{path}', url)
        except Exception as e:
            err_table[url] = err_table.get(url, 0) + 1
            # lprint(str(e), file=sys.stderr)
            continue

        # collect samples (status code, body length) for future comparison if response status of random url not excluded by settings
        if res.status not in conf.exclude_codes:
            if url not in preflight_samples:
                preflight_samples[url] = []

            if len(preflight_samples[url]) == 0 or samples_diff(res, url):
                lprint(f"{res} status code not excluded, add to preflight samples", file=sys.stderr)
                preflight_samples[url].append(res)


def samples_diff(res: Response, url: str):
    """is differ from ALL url samples?"""
    for sample in preflight_samples.get(url, []):
        if res.is_similar(sample):
            return False
    return True


def result_valid(res:Response):
    if res.status in conf.exclude_codes:
        return False

    if conf.filter_regex:
        if re.search(conf.filter_regex, res.body.decode('utf-8', 'ignore')):
            res.add_meta(f"{conf.filter_regex} match")
        else:
            return False

    # if ac
    if len(preflight_samples) > 0:
        if samples_diff(res, res.parent_url):
            res.add_meta('(preflight differ)')
        else:
            return False
                
    #pass all filters
    return True


def worker_process(url, parent, redirect_count = 0):
    try:
        res = process_url(url, parent)
    except requests.exceptions.RequestException as e:
        err_table[url] = err_table.get(url, 0) + 1
        #lprint(str(e))
        return

    if result_valid(res):
        results.append(res)
        if conf.json_print:
            lprint(res.to_json(conf.store_response))
        else:
            lprint(f"{res}")
        if conf.res_dir:
            save_res(res)
        # follow host redirects on valid results
        if res.location and conf.follow_redirects and redirect_count < conf.max_redirects:
            if res.location.startswith('http://') or res.location.startswith('https://'):
                location = res.location
            else:
                location = urllib.parse.urljoin(res.url, res.location)

            loc_p = urllib.parse.urlparse(location)
            loc_wo_query = f'{loc_p.scheme}://{loc_p.netloc}{loc_p.path}' 
            if loc_p.netloc == res.host and loc_wo_query not in uniq_locs:
                redirect_count += 1
                uniq_locs.add(loc_wo_query)
                worker_process(location, parent, redirect_count)


def worker():
    while True:
        with get_work_locker:
            try:
                url, path = next(task_iter)
            except StopIteration:
                return
        urlpath = f"{url}/{path}"
        worker_process(urlpath, url)


def statworker(looptime = 5):
    while True:
        time.sleep(looptime)
        time_passed = time.time() - stats['starttime']
        req_left = stats['allreqs'] - stats['reqs_done']
        vel = int(stats["reqs_done"] / time_passed * 60)  
        try:
            timeleft = req_left // vel
        except ZeroDivisionError:
            timeleft = 0
        lprint(f'[Statistics] path: {stats["path"]}, {stats["reqs_done"]}/{stats["allreqs"]} requests, speed {vel} req/min (about {timeleft} min left)', file=sys.stderr)            


def start_thread_pool(threads, worker):
    workers = []
    for i in range(threads):
        t = threading.Thread(target=worker, name='worker {}'.format(i),args=())
        t.start()
        workers.append(t)

    for w in workers:
        w.join()


def parse_args(sys_args):
    global conf

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='multiple hosts web path scanner')
    parser.add_argument('-m', '--http_method', type=str, help='HTTP method to use', default='GET')
    parser.add_argument('-u', '--urls_file', type=argparse.FileType(mode='r', encoding='UTF-8'), help='urls file (base url)', required=True)
    parser.add_argument('-p', '--paths_file', type=argparse.FileType(mode='r', encoding='UTF-8'), help='paths wordlist', required=True)
    parser.add_argument('-e', '--exclude_codes', type=str, help="Exclude status codes, separated by commas (Example: 404,403)", default="404")
    parser.add_argument('-x', '--extensions', type=str, help="Extension list separated by commas (Example: php,asp)", default="")
    parser.add_argument('-ac', action='store_true', help='Automatically calibrate filtering options')
    parser.add_argument('-sr', '--store_response', action='store_true', help='Store finded HTTP responses')
    parser.add_argument('-srd', '--store_response_dir', type=str, help='Output directory')
    parser.add_argument('-fe', '--filter-regex', type=str, help='filter response with specified regex (-fe admin)', default=None)
    parser.add_argument('-json', action='store_true', help='store output in JSONL(ines) format')
    parser.add_argument('-f', '--follow_redirects', action='store_true', help='Follow HTTP redirects (same host only)')
    parser.add_argument('-H','--header', action='append', help="Add custom HTTP request header, support multiple flags (Example: -H \"Referer: example.com\" -H \"Accept: */*\")")
    parser.add_argument('--proxy', type=str, help='proxy ip:port', default=None)
    parser.add_argument('--max_response_size', help='Maximum response size in bytes', default=250000)
    parser.add_argument('--max_errors', type=int, help='Maximum errors before url exclude', default=5)
    parser.add_argument('-t', '--threads', type=int, help='Number of threads (keep number of threads less than the number of hosts)', default=10)
    parser.add_argument('-ua', '--user_agent', type=str, help="User agent", default="Mozilla/5.0 (compatible; pathbuster/0.1; +https://github.com/rivalsec/pathbuster)")
    parser.add_argument('--stats_interval', type=int, help="number of seconds to wait between showing a statistics update", default = 60)
    parser.add_argument('-maxr', '--max_redirects', type=int, help='Max number of redirects to follow', default=5)

    args = parser.parse_args(sys_args)

    if args.proxy:
        conf.proxies = {
            'http': 'http://' + args.proxy,
            'https': 'https://' + args.proxy
        }

    conf.headers["User-Agent"] = args.user_agent
    if args.header:
        for h in args.header:
            k, v = [x.strip() for x in h.split(':', maxsplit=1)]
            conf.headers[k] = v

    if args.exclude_codes:
        conf.exclude_codes = [int(x.strip()) for x in args.exclude_codes.strip(',').split(',')]

    if args.extensions:
        conf.extensions.extend([x.strip() for x in args.extensions.strip().strip(',').split(',')])

    conf.max_errors = args.max_errors
    conf.http_method = args.http_method
    conf.max_response_size = args.max_response_size
    conf.store_response = args.store_response
    conf.filter_regex = args.filter_regex
    conf.json_print = args.json
    conf.follow_redirects = args.follow_redirects
    conf.max_redirects = args.max_redirects
    conf.res_dir = args.store_response_dir
    conf.stats_interval = args.stats_interval
    return args


def auto_calibration(urls, threads):
    global preflight_iter
    print("Collecting auto-calibration samples...", file=sys.stderr)
    # auto calibration like in ffuf
    acStrings = [
        random_str(16),
        random_str(16) + '/',
        '.' + random_str(16) + '/',
        '.htaccess' + random_str(16),
        'admin' + random_str(16) + '/'
    ]
    acStrings.extend( [ random_str(16) + '.' + ext for ext in conf.extensions if ext] )
    preflight_iter = work_prod(urls, acStrings)
    start_thread_pool(threads, preflight_worker)


def fuzz(urls, paths, extensions, threads, ac=False ):
    global task_iter, stats

    if conf.res_dir:
        if not os.path.exists(conf.res_dir):
            os.mkdir(conf.res_dir)
        if conf.store_response and not os.path.exists(conf.res_dir + "/responses"):
            os.mkdir(conf.res_dir + "/responses")

    if ac:
        auto_calibration(urls, threads)

    #stats
    stats = {
        "allreqs": len(urls) * len(paths) * len(conf.extensions),
        "reqs_done": 0,
        "path": "",
        "starttime": time.time(),
    }
    st = threading.Thread(target=statworker, daemon=True, name='StatThread', args=(conf.stats_interval,))
    st.start()

    task_iter = work_prod(urls, paths, extensions, True)
    start_thread_pool(threads, worker)
    #return all found results
    return results


def main():
    global stats, task_iter
    args = parse_args(sys.argv[1:])

    urls = [l.strip() for l in args.urls_file]
    args.urls_file.close()

    paths = [l.strip() for l in args.paths_file]
    args.paths_file.close()

    fuzz(urls, paths, conf.extensions, args.threads, args.ac)

    print('THE END', file=sys.stderr)


if __name__ == "__main__":
    main()