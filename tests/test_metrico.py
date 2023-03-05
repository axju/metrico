from metrico import MetricoCore, __version__


def test_version():
    assert __version__ == "0.0.1"


def test_full():
    platform = "test"

    metrico = MetricoCore()
    metrico.config.db.url = f"sqlite://"
    metrico.db.reload_config()
    metrico.db.setup()

    metrico.hunter[platform].config["max_medias"] = 5
    metrico.hunter[platform].config["max_comments"] = 10

    account_ids = []
    for data in metrico.hunter[platform].analyze("foo", amount=1):
        account = metrico.db.create_account(platform, data)
        account_ids.append(account.id)
    for account_id in account_ids:
        metrico.update_account(account_id, media_count=-2, comment_count=-2, subscription_count=-1)

    stats = metrico.db.stats()
    assert stats["Account"] == 51
    assert stats["Media"] == 5
    assert stats["Media-Info"] == 5
    assert stats["Media-Info"] == 5
    assert stats["Media-Comment"] == 50
