from metrico import MetricoCore

metrico = MetricoCore()
metrico.config.db.url = f"sqlite://"
metrico.db.reload_config()
metrico.db.setup()
