from datetime import datetime

import osmapi
import pytest
from responses import GET, POST

from .conftest import API_BASE


def test_notes_get(api, add_response):
    resp = add_response(GET, "/notes")

    result = api.notes_get(-1.4998534, 45.9667901, -1.4831815, 52.4710193)

    assert resp.calls[0].request.method == "GET"
    assert resp.calls[0].request.params == {
        "bbox": "-1.499853,45.966790,-1.483181,52.471019",
        "limit": "100",
        "closed": "7",
    }
    assert len(result) == 14
    assert result[2] == {
        "id": "231775",
        "lon": -1.4929605,
        "lat": 52.4107312,
        "date_created": datetime(2014, 8, 28, 19, 25, 37),
        "date_closed": datetime(2014, 9, 27, 9, 21, 41),
        "status": "closed",
        "comments": [
            {
                "date": datetime(2014, 8, 28, 19, 25, 37),
                "action": "opened",
                "text": "Is it Paynes or Payne's",
                "html": "<p>Is it Paynes or Payne's</p>",
                "uid": "1486336",
                "user": "Wyken Seagrave",
            },
            {
                "date": datetime(2014, 9, 26, 13, 5, 33),
                "action": "commented",
                "text": "Royal Mail's postcode finder has PAYNES LANE",
                "html": "<p>Royal Mail's postcode finder has PAYNES LANE</p>",
                "uid": None,
                "user": None,
            },
        ],
    }


def test_notes_get_empty(api, add_response):
    resp = add_response(GET, "/notes")

    result = api.notes_get(
        -93.8472901, 35.9763601, -80, 36.176360100000004, limit=1, closed=0
    )

    assert resp.calls[0].request.params == {
        "bbox": "-93.847290,35.976360,-80.000000,36.176360",
        "limit": "1",
        "closed": "0",
    }
    assert result == []


def test_note_get(api, add_response):
    resp = add_response(GET, "/notes/1111")

    result = api.note_get(1111)

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/notes/1111"
    assert result == {
        "id": "1111",
        "lon": 12.3133135,
        "lat": 37.9305489,
        "date_created": datetime(2013, 5, 1, 20, 58, 21),
        "date_closed": datetime(2013, 8, 21, 16, 43, 26),
        "status": "closed",
        "comments": [
            {
                "date": datetime(2013, 5, 1, 20, 58, 21),
                "action": "opened",
                "text": "It does not exist this path",
                "html": "<p>It does not exist this path</p>",
                "uid": "1363438",
                "user": "giuseppemari",
            },
            {
                "date": datetime(2013, 8, 21, 16, 43, 26),
                "action": "closed",
                "text": "there is no path signed",
                "html": "<p>there is no path signed</p>",
                "uid": "1714220",
                "user": "luschi",
            },
        ],
    }


def test_note_get_invalid_xml(api, add_response):
    add_response(GET, "/notes/1111")

    with pytest.raises(osmapi.XmlResponseInvalidError):
        api.note_get(1111)


def test_note_create(auth_api, add_response):
    resp = add_response(POST, "/notes")
    note = {"lat": 47.123, "lon": 8.432, "text": "This is a test"}

    result = auth_api.note_create(note)

    assert resp.calls[0].request.method == "POST"
    assert resp.calls[0].request.params == {
        "lat": "47.123",
        "lon": "8.432",
        "text": "This is a test",
    }
    assert result == {
        "id": "816",
        "lat": 47.123,
        "lon": 8.432,
        "date_created": datetime(2014, 10, 3, 15, 21, 21),
        "date_closed": None,
        "status": "open",
        "comments": [
            {
                "date": datetime(2014, 10, 3, 15, 21, 22),
                "action": "opened",
                "text": "This is a test",
                "html": "<p>This is a test</p>",
                "uid": "1841",
                "user": "metaodi",
            }
        ],
    }


def test_note_create_anonymous(api, add_response):
    resp = add_response(POST, "/notes")
    note = {"lat": 47.123, "lon": 8.432, "text": "test 123"}

    result = api.note_create(note)

    assert resp.calls[0].request.params == {
        "lat": "47.123",
        "lon": "8.432",
        "text": "test 123",
    }
    assert result == {
        "id": "842",
        "lat": 58.3368222,
        "lon": 25.8826183,
        "date_created": datetime(2015, 1, 3, 10, 49, 39),
        "date_closed": None,
        "status": "open",
        "comments": [
            {
                "date": datetime(2015, 1, 3, 10, 49, 39),
                "action": "opened",
                "text": "test 123",
                "html": "<p>test 123</p>",
                "uid": None,
                "user": None,
            }
        ],
    }


def test_note_comment(auth_api, add_response):
    resp = add_response(POST, "/notes/812/comment")

    result = auth_api.note_comment(812, "This is a comment")

    assert resp.calls[0].request.method == "POST"
    assert resp.calls[0].request.params == {"text": "This is a comment"}
    assert result == {
        "id": "812",
        "lat": 47.123,
        "lon": 8.432,
        "date_created": datetime(2014, 10, 3, 15, 11, 5),
        "date_closed": None,
        "status": "open",
        "comments": [
            {
                "date": datetime(2014, 10, 3, 15, 11, 5),
                "action": "opened",
                "text": "This is a test",
                "html": "<p>This is a test</p>",
                "uid": "1841",
                "user": "metaodi",
            },
            {
                "date": datetime(2014, 10, 4, 22, 36, 35),
                "action": "commented",
                "text": "This is a comment",
                "html": "<p>This is a comment</p>",
                "uid": "1841",
                "user": "metaodi",
            },
        ],
    }


def test_note_comment_anonymous(api, add_response):
    resp = add_response(POST, "/notes/842/comment")

    result = api.note_comment(842, "blubb")

    assert resp.calls[0].request.params == {"text": "blubb"}
    assert result["id"] == "842"
    assert result["comments"][1] == {
        "date": datetime(2015, 1, 3, 11, 6, 0),
        "action": "commented",
        "text": "blubb",
        "html": "<p>blubb</p>",
        "uid": None,
        "user": None,
    }


def test_note_comment_on_closed_note(api, add_response):
    add_response(POST, "/notes/817/comment", status=409)

    with pytest.raises(osmapi.NoteAlreadyClosedApiError) as execinfo:
        api.note_comment(817, "Comment on closed note")

    assert execinfo.value.status == 409
    assert (
        execinfo.value.payload_str
        == "The note 817 was closed at 2022-04-29 20:57:20 UTC"
    )


def test_note_comment_non_existing_note(api, add_response):
    add_response(POST, "/notes/817/comment", body="", status=404)

    with pytest.raises(osmapi.ElementNotFoundApiError) as execinfo:
        api.note_comment(817, "Comment on closed note")

    assert execinfo.value.status == 404


def test_note_close(auth_api, add_response):
    resp = add_response(POST, "/notes/819/close")

    result = auth_api.note_close(819, "Close this note!")

    assert resp.calls[0].request.method == "POST"
    assert resp.calls[0].request.params == {"text": "Close this note!"}
    assert result == {
        "id": "815",
        "lat": 47.123,
        "lon": 8.432,
        "date_created": datetime(2014, 10, 3, 15, 20, 57),
        "date_closed": datetime(2014, 10, 5, 16, 35, 13),
        "status": "closed",
        "comments": [
            {
                "date": datetime(2014, 10, 3, 15, 20, 57),
                "action": "opened",
                "text": "This is a test",
                "html": "<p>This is a test</p>",
                "uid": "1841",
                "user": "metaodi",
            },
            {
                "date": datetime(2014, 10, 5, 16, 35, 13),
                "action": "closed",
                "text": "Close this note!",
                "html": "<p>Close this note!</p>",
                "uid": "1841",
                "user": "metaodi",
            },
        ],
    }


def test_note_already_closed(auth_api, add_response):
    add_response(POST, "/notes/819/close", status=409)

    with pytest.raises(osmapi.NoteAlreadyClosedApiError) as execinfo:
        auth_api.note_close(819, "Close this note!")

    assert execinfo.value.status == 409
    assert (
        execinfo.value.payload_str
        == "The note 819 was closed at 2022-04-29 20:57:20 UTC"
    )


def test_note_reopen(auth_api, add_response):
    resp = add_response(POST, "/notes/815/reopen")

    result = auth_api.note_reopen(815, "Reopen this note!")

    assert resp.calls[0].request.method == "POST"
    assert resp.calls[0].request.params == {"text": "Reopen this note!"}
    assert result["id"] == "815"
    assert result["status"] == "open"
    assert result["date_closed"] is None
    assert result["comments"][2] == {
        "date": datetime(2014, 10, 5, 16, 44, 56),
        "action": "reopened",
        "text": "Reopen this note!",
        "html": "<p>Reopen this note!</p>",
        "uid": "1841",
        "user": "metaodi",
    }


def test_notes_search(api, add_response):
    resp = add_response(GET, "/notes/search")

    result = api.notes_search("street")

    assert resp.calls[0].request.params == {
        "q": "street",
        "limit": "100",
        "closed": "7",
    }
    assert len(result) == 3
    assert result[1] == {
        "id": "788",
        "lon": 11.96395,
        "lat": 57.70301,
        "date_created": datetime(2014, 7, 16, 16, 12, 41),
        "date_closed": None,
        "status": "open",
        "comments": [
            {
                "date": datetime(2014, 7, 16, 16, 12, 41),
                "action": "opened",
                "text": "One way street:\ncomment",
                "html": "<p>One way street:\n<br />comment</p>",
                "uid": None,
                "user": None,
            }
        ],
    }


def test_notes_search_with_limit_and_closed(api, add_response):
    resp = add_response(GET, "/notes/search", filename="test_notes_search.xml")

    api.notes_search("street", limit=10, closed=-1)

    assert resp.calls[0].request.params == {
        "q": "street",
        "limit": "10",
        "closed": "-1",
    }
