# PathBuster - multiple hosts Web path scanner

This scanner is designed to check paths on multiple hosts at the same time.
One path is taken and checked multithreaded across all hosts, then the next path is taken, etc.

This gives us the following benefits:
- there is no heavy load on one host (if we checked many paths in several threads on one host).
- prevents a possible ban on the scanner by the WAF.
- saving time, there is no need to run the scanner for each host separately.
- a large number of results at once.

For convenience, the results are written to two files at once in the pathbuster-res folder:
- file with hostname (all paths found for this host)
- file with response code (file with all responses 200, 301, etc.)

![image](https://user-images.githubusercontent.com/50343281/114876542-de8ab200-9e17-11eb-9c1c-78702fd2d4f1.png)


Before starting scanning, the program checks the server's responses on random string and, if the response code is not excluded by the program settings, writes a sample (code and size) of the response for subsequent comparison.
This allows us to exclude a large number of false positives (for example, if the server responds to us 200 OK for all requests)
And it allows you to find answers that differ from the recorded samples, even if the code was the same.

## Installation: 
```
git clone https://github.com/rivalsec/pathbuster.git
cd pathbuster
pip3 install -r requirements.txt
```

## Basic usage:
```
python3 pathbuster.py -u /path/to/URLS_FILE -p /path/to/wordlist 
```

## options:
```
usage: pathbuster.py [-h] [-m HTTP_METHOD] -u URLS_FILE -p PATHS_FILE [-e EXCLUDE_CODES] [-x EXTENSIONS] [--proxy PROXY]
                     [--max_response_size MAX_RESPONSE_SIZE] [--max_errors MAX_ERRORS] [--threads THREADS] [-ac] [-H HEADER]
                     [--user_agent USER_AGENT] [--stats_interval STATS_INTERVAL] [-sr]

multiple hosts web path scanner

optional arguments:
  -h, --help            show this help message and exit
  -m HTTP_METHOD, --http_method HTTP_METHOD
                        HTTP method to use (default: GET)
  -u URLS_FILE, --urls_file URLS_FILE
                        urls file (base url) (default: None)
  -p PATHS_FILE, --paths_file PATHS_FILE
                        paths wordlist (default: None)
  -e EXCLUDE_CODES, --exclude_codes EXCLUDE_CODES
                        Exclude status codes, separated by commas (Example: 404,403) (default: 404)
  -x EXTENSIONS, --extensions EXTENSIONS
                        Extension list separated by commas (Example: php,asp) (default: )
  --proxy PROXY         proxy ip:port (default: None)
  --max_response_size MAX_RESPONSE_SIZE
                        Maximum response size in bytes (default: 250000)
  --max_errors MAX_ERRORS
                        Maximum errors before url exclude (default: 5)
  --threads THREADS     Number of threads (keep number of threads less than the number of hosts) (default: 10)
  -ac                   Automatically calibrate filtering options (default: False)
  -H HEADER, --header HEADER
                        Add custom HTTP request header, support multiple flags (Example: -H "Referer: example.com" -H "Accept: */*")
                        (default: None)
  --user_agent USER_AGENT
                        User agent (default: Mozilla/5.0 (compatible; pathbuster/0.1; +https://github.com/rivalsec/pathbuster))
  --stats_interval STATS_INTERVAL
                        number of seconds to wait between showing a statistics update (default: 60)
  -sr, --store_response
                        Store finded HTTP responses (default: False)
```
