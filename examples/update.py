from metrico import MetricoCore
from metrico.database.query import AccountOrder, AccountQuery, ModelStatus

metrico = MetricoCore.default()

print("Account:", metrico.db.stats("Account"))
print("Media:  ", metrico.db.stats("Media"))

# all new accounts will be added to trigger 'init'
metrico.run_trigger("init", limit=10)

# get some stats for all account with none views (stats_views_null=True)
query = AccountQuery(limit=2000, order_by=AccountOrder.MEDIAS, status=ModelStatus.OKAY, stats_views_null=True)
metrico.update_query(query)

# # update the top 2000 accounts order by views
# query = AccountQuery(limit=2000, order_by=AccountOrder.VIEWS, status=ModelStatus.OKAY)
# metrico.update_query(query)

# # update the top 2000 accounts order by followers
# query = AccountQuery(limit=20, order_by=AccountOrder.FOLLOWERS, status=ModelStatus.OKAY)
# metrico.update_query(query)

print("Account:", metrico.db.stats("Account"))
print("Media:  ", metrico.db.stats("Media"))
