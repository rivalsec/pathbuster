from pathbuster.pathbuster import RequestResult


def test_init():
    bodyb = b'one two\nthree four'
    headers = {'Cookie': 'test=1234;'}
    parent_url = 'http://example.com'
    req = RequestResult('http://example.com/admin', 200, 'OK', bodyb, headers, parent_url, 'meta1')
    assert(len(req.headers) == 1)
    assert(req.headers['Cookie'] == 'test=1234;')
    assert(req.strbody == 'one two\nthree four')
    assert(req.bodylen == len(bodyb))
    assert(req.scheme == 'http')
    assert(req.parent_url == parent_url)
    assert(req.bodylines == 2)
    assert(req.bodywords == 3)
