from metrico import Hunter

metrico = Hunter()
metrico.config.db.url = f"sqlite://"
metrico.db.reload_config()
metrico.db.setup()
