import pathbuster
import pytest


required_args = [
    '-u', './test/testurls',
    '-p', './test/testwordlist',
]


def test_filter_regex():
    args = required_args.copy()
    args.extend([
        '-e', '301',
        '-fe', '<title>Admin'
        ])
    pathbuster.parse_args(args)

    res1 = pathbuster.RequestResult(url='http://example.com/test', status=200, reason='OK', body=b'<title>Member</title> etc', headers=[], parent_url=None)
    assert(pathbuster.result_valid(res1) == False)

    res2 = pathbuster.RequestResult(url='http://example.com/test', status=404, reason='OK', body=b'bla \n <title>Admin Panel</title> ', headers=[], parent_url=None)
    assert(pathbuster.result_valid(res2) == True)

    #code is filtered
    res2 = pathbuster.RequestResult(url='http://example.com/test', status=301, reason='OK', body=b'bla \n <title>Admin Panel</title> ', headers=[], parent_url=None)
    assert(pathbuster.result_valid(res2) == False)


def test_not_ac():
    # only status code filter
    args = required_args.copy()
    args.extend(['-e', '401,404,400'])
    pathbuster.parse_args(args)

    res1 = pathbuster.RequestResult(url='http://example.com/test', status=200, reason='OK', body=b'', headers=[], parent_url=None)
    assert(pathbuster.result_valid(res1) == True)

    res2 = pathbuster.RequestResult(url='http://example.com/test', status=400, reason='NOT OK', body=b'', headers=[], parent_url=None)
    assert(pathbuster.result_valid(res2) == False)

    res3 = pathbuster.RequestResult(url='http://example.com/test', status=401, reason='NOT OK', body=b'', headers=[], parent_url=None)
    assert(pathbuster.result_valid(res3) == False)


def test_empty_e():
    args = required_args.copy()
    args.extend(['-e', ''])
    pathbuster.parse_args(args)
    
    res1 = pathbuster.RequestResult(url='http://example.com/test', status=200, reason='OK', body=b'', headers=[], parent_url=None)
    assert(pathbuster.result_valid(res1) == True)

    res2 = pathbuster.RequestResult(url='http://example.com/test', status=400, reason='NOT OK', body=b'', headers=[], parent_url=None)
    assert(pathbuster.result_valid(res2) == True)


def test_ac():
    args = required_args.copy()
    args.extend(['-ac'])
    pathbuster.parse_args(args)
    pf_res1 = pathbuster.RequestResult(url='http://example.com/test', status=200, reason='OK', body=b'1 2 3\n4 5', headers=[], parent_url='http://example.com')
    pathbuster.preflight_samples = {
        'http://example.com': [pf_res1,],
    }
    assert(pathbuster.result_valid(pf_res1) == False)
    res2 = pathbuster.RequestResult(url='http://example.com/test2', status=200, reason='OK', body=b'1 2 3\n4 5 6', headers=[], parent_url='http://example.com')
    assert(pathbuster.result_valid(res2) == True)
    

if __name__=="__main__":
    print(pytest.main())