from metrico import schemas
from metrico.database.query import AccountQuery, MediaCommentQuery, MediaQuery

from . import metrico


def test_default_query():
    for query in [AccountQuery(), MediaQuery(), MediaCommentQuery()]:
        assert len(list(metrico.db.iter_query(query))) == 0

    account = metrico.db.create_account("test", schemas.Account(identifier="foo"))
    media = metrico.db.create_media("test", schemas.Media(identifier="foo", media_type=schemas.MediaType.TEXT, account=schemas.Account(identifier="foo")))
