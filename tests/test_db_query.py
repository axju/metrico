from metrico import models
from metrico.database.query import AccountQuery, MediaCommentQuery, MediaQuery

from . import metrico


def test_default_query():
    for query in [AccountQuery(), MediaQuery(), MediaCommentQuery()]:
        assert len(list(metrico.db.iter_query(query))) == 0

    account = metrico.db.create_account("test", models.Account(identifier="foo"))
    media = metrico.db.create_media("test", models.Media(identifier="foo", media_type=models.MediaType.TEXT, account=models.Account(identifier="foo")))
