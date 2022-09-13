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


# TO-DO:
# def test_ac():
#     pass


if __name__=="__main__":
    print(pytest.main())