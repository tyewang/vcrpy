# -*- coding: utf-8 -*-
'''Test requests' interaction with vcr'''

import pytest
import vcr
from assertions import assert_cassette_empty, assert_is_json


requests = pytest.importorskip("requests")


def test_status_code(httpbin_both, tmpdir):
    '''Ensure that we can read the status code'''
    url = httpbin_both.url + '/'
    with vcr.use_cassette(str(tmpdir.join('atts.yaml'))):
        status_code = requests.get(url).status_code

    with vcr.use_cassette(str(tmpdir.join('atts.yaml'))):
        assert status_code == requests.get(url).status_code


def test_headers(httpbin_both, tmpdir):
    '''Ensure that we can read the headers back'''
    url = httpbin_both + '/'
    with vcr.use_cassette(str(tmpdir.join('headers.yaml'))):
        headers = requests.get(url).headers

    with vcr.use_cassette(str(tmpdir.join('headers.yaml'))):
        assert headers == requests.get(url).headers


def test_body(tmpdir, httpbin_both):
    '''Ensure the responses are all identical enough'''
    url = httpbin_both + '/bytes/1024'
    with vcr.use_cassette(str(tmpdir.join('body.yaml'))):
        content = requests.get(url).content

    with vcr.use_cassette(str(tmpdir.join('body.yaml'))):
        assert content == requests.get(url).content


def test_auth(tmpdir, httpbin_both):
    '''Ensure that we can handle basic auth'''
    auth = ('user', 'passwd')
    url = httpbin_both + '/basic-auth/user/passwd'
    with vcr.use_cassette(str(tmpdir.join('auth.yaml'))):
        one = requests.get(url, auth=auth)

    with vcr.use_cassette(str(tmpdir.join('auth.yaml'))):
        two = requests.get(url, auth=auth)
        assert one.content == two.content
        assert one.status_code == two.status_code


def test_auth_failed(tmpdir, httpbin_both):
    '''Ensure that we can save failed auth statuses'''
    auth = ('user', 'wrongwrongwrong')
    url = httpbin_both + '/basic-auth/user/passwd'
    with vcr.use_cassette(str(tmpdir.join('auth-failed.yaml'))) as cass:
        # Ensure that this is empty to begin with
        assert_cassette_empty(cass)
        one = requests.get(url, auth=auth)
        two = requests.get(url, auth=auth)
        assert one.content == two.content
        assert one.status_code == two.status_code == 401


def test_post(tmpdir, httpbin_both):
    '''Ensure that we can post and cache the results'''
    data = {'key1': 'value1', 'key2': 'value2'}
    url = httpbin_both + '/post'
    with vcr.use_cassette(str(tmpdir.join('requests.yaml'))):
        req1 = requests.post(url, data).content

    with vcr.use_cassette(str(tmpdir.join('requests.yaml'))):
        req2 = requests.post(url, data).content

    assert req1 == req2


def test_redirects(tmpdir, httpbin_both):
    '''Ensure that we can handle redirects'''
    url = httpbin_both + '/redirect-to?url=bytes/1024'
    with vcr.use_cassette(str(tmpdir.join('requests.yaml'))):
        content = requests.get(url).content

    with vcr.use_cassette(str(tmpdir.join('requests.yaml'))) as cass:
        assert content == requests.get(url).content
        # Ensure that we've now cached *two* responses. One for the redirect
        # and one for the final fetch
        assert len(cass) == 2
        assert cass.play_count == 2


def test_cross_scheme(tmpdir, httpbin_secure, httpbin):
    '''Ensure that requests between schemes are treated separately'''
    # First fetch a url under http, and then again under https and then
    # ensure that we haven't served anything out of cache, and we have two
    # requests / response pairs in the cassette
    with vcr.use_cassette(str(tmpdir.join('cross_scheme.yaml'))) as cass:
        requests.get(httpbin_secure + '/')
        requests.get(httpbin + '/')
        assert cass.play_count == 0
        assert len(cass) == 2


def test_gzip(tmpdir, httpbin_both):
    '''
    Ensure that requests (actually urllib3) is able to automatically decompress
    the response body
    '''
    url = httpbin_both + '/gzip'
    response = requests.get(url)

    with vcr.use_cassette(str(tmpdir.join('gzip.yaml'))):
        response = requests.get(url)
        assert_is_json(response.content)

    with vcr.use_cassette(str(tmpdir.join('gzip.yaml'))):
        assert_is_json(response.content)


def test_session_and_connection_close(tmpdir, httpbin):
    '''
    This tests the issue in https://github.com/kevin1024/vcrpy/issues/48

    If you use a requests.session and the connection is closed, then an
    exception is raised in the urllib3 module vendored into requests:
    `AttributeError: 'NoneType' object has no attribute 'settimeout'`
    '''
    with vcr.use_cassette(str(tmpdir.join('session_connection_closed.yaml'))):
        session = requests.session()

        session.get(httpbin + '/get', headers={'Connection': 'close'})
        session.get(httpbin + '/get', headers={'Connection': 'close'})


def test_https_with_cert_validation_disabled(tmpdir, httpbin_secure):
    with vcr.use_cassette(str(tmpdir.join('cert_validation_disabled.yaml'))):
        requests.get(httpbin_secure.url, verify=False)


def test_session_can_make_requests_after_requests_unpatched(tmpdir, httpbin):
    with vcr.use_cassette(str(tmpdir.join('test_session_after_unpatched.yaml'))):
        session = requests.session()
        session.get(httpbin + '/get')

    with vcr.use_cassette(str(tmpdir.join('test_session_after_unpatched.yaml'))):
        session = requests.session()
        session.get(httpbin + '/get')

    session.get(httpbin + '/status/200')


def test_session_created_before_use_cassette_is_patched(tmpdir, httpbin_both):
    url = httpbin_both + '/bytes/1024'
    # Record arbitrary, random data to the cassette
    with vcr.use_cassette(str(tmpdir.join('session_created_outside.yaml'))):
        session = requests.session()
        body = session.get(url).content

    # Create a session outside of any cassette context manager
    session = requests.session()
    # Make a request to make sure that a connectionpool is instantiated
    session.get(httpbin_both + '/get')

    with vcr.use_cassette(str(tmpdir.join('session_created_outside.yaml'))):
        # These should only be the same if the patching succeeded.
        assert session.get(url).content == body


def test_nested_cassettes_with_session_created_before_nesting(httpbin_both, tmpdir):
    '''
    This tests ensures that a session that was created while one cassette was
    active is patched to the use the responses of a second cassette when it
    is enabled.
    '''
    url = httpbin_both + '/bytes/1024'
    with vcr.use_cassette(str(tmpdir.join('first_nested.yaml'))):
        session = requests.session()
        first_body = session.get(url).content
        with vcr.use_cassette(str(tmpdir.join('second_nested.yaml'))):
            second_body = session.get(url).content
            third_body = requests.get(url).content

    with vcr.use_cassette(str(tmpdir.join('second_nested.yaml'))):
        session = requests.session()
        assert session.get(url).content == second_body
        with vcr.use_cassette(str(tmpdir.join('first_nested.yaml'))):
            assert session.get(url).content == first_body
        assert session.get(url).content == third_body

    # Make sure that the session can now get content normally.
    session.get(httpbin_both.url)


def test_post_file(tmpdir, httpbin_both):
    '''Ensure that we handle posting a file.'''
    url = httpbin_both + '/post'
    with vcr.use_cassette(str(tmpdir.join('post_file.yaml'))) as cass:
        # Don't use 2.7+ only style ',' separated with here because we support python 2.6
        with open('tox.ini') as f:
            original_response = requests.post(url, f).content

    # This also tests that we do the right thing with matching the body when they are files.
    with vcr.use_cassette(str(tmpdir.join('post_file.yaml')),
                          match_on=('method', 'scheme', 'host', 'port', 'path', 'query', 'body')) as cass:
        with open('tox.ini', 'rb') as f:
            tox_content = f.read()
        assert cass.requests[0].body.read() == tox_content
        with open('tox.ini', 'rb') as f:
            new_response = requests.post(url, f).content
        assert original_response == new_response
