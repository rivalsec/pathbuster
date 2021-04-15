# PathBuster - multiple hosts Web path scanner

## usage: 
python3 pathbuster.py -u URLS_FILE -p PATHS_FILE 

## optional arguments:
  -h, --help            show this help message and exit

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
