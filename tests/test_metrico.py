from metrico import Hunter, __version__


def test_version():
    assert __version__ == "0.0.1"


def test_full():
    platform = "test"

    metrico = Hunter()
    metrico.config.db.url = f"sqlite://"
    metrico.db.reload_config()
    metrico.db.setup()

    metrico.hunters[platform].config["max_medias"] = 5
    metrico.hunters[platform].config["max_comments"] = 10

    account_ids = []
    for data in metrico.hunters[platform].analyze("foo", amount=1):
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
