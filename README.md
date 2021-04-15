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

Before starting scanning, the program checks the server's responses on random string and, if the response code is not excluded by the program settings, writes a sample (code and size) of the response for subsequent comparison.
This allows us to exclude a large number of false positives (for example, if the server responds to us 200 OK for all requests)
And it allows you to find answers that differ from the recorded samples, even if the code was the same.

## usage: 
```
python3 pathbuster.py -u URLS_FILE -p PATHS_FILE 
```

## optional arguments:
```
  -u URLS_FILE, --urls_file URLS_FILE 
                        urls file

  -p PATHS_FILE, --paths_file PATHS_FILE 
                        file with paths to check

  -e EXCLUDE_CODES, --exclude_codes EXCLUDE_CODES
                        Exclude codes (404,403 etc) (default: 404)

  -x EXTENSIONS, --extensions EXTENSIONS
                        File extensions (try with each string)

  --proxy PROXY         proxy ip:port (default: None)

  --max_response_size MAX_RESPONSE_SIZE
                        Maximum response size (default: 250000)

  --max_errors MAX_ERRORS
                        Maximum errors before url exclude (default: 5)

  --threads THREADS     Number of threads (default: 10)

  --random_samples RANDOM_SAMPLES
                        how many responses to random urls we collect for
                        comparison (set 0 to disable preflight checks)
                        (default: 3)

  -H HEADER, --header HEADER
                        Add custom header (Header: content) you can set it
                        multiple times

  --user_agent USER_AGENT
                        User agent 
                        default: Mozilla/5.0 (compatible; pathbuster/0.1;https://github.com/rivalsec/pathbuster)
```
