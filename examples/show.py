from metrico import MetricoCore
from metrico.database.query import AccountOrder, AccountQuery

metrico = MetricoCore.default()


# to list all accounts
query = AccountQuery(limit=50, order_by=AccountOrder.VIEWS)
for account in metrico.db.iter_query(query):
    print(f"{account.id:>6} {account.created_at:%Y-%m-%d} {account.stats_medias:>6} {account.stats_followers:>9} {account.stats_views:>12} {account.info_name}")
