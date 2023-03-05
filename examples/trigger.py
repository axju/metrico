from metrico import MetricoCore

metrico = MetricoCore.default()

print("Account:", metrico.db.stats("Account"))
print("Media:  ", metrico.db.stats("Media"))

metrico.run_trigger("init", limit=10)

print("Account:", metrico.db.stats("Account"))
print("Media:  ", metrico.db.stats("Media"))
