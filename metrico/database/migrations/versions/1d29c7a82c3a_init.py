"""init

Revision ID: 1d29c7a82c3a
Revises: 
Create Date: 2023-01-26 23:16:03.026506

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1d29c7a82c3a"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "account",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("status", sa.Enum("OKAY", "FAIL", name="modelstatus"), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("identifier", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("subscriptions_last_update", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("info_last_update", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("info_name", sa.String(), nullable=True),
        sa.Column("info_bio", sa.String(), nullable=True),
        sa.Column("stats_last_update", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("stats_medias", sa.Integer(), nullable=True),
        sa.Column("stats_views", sa.BigInteger(), nullable=True),
        sa.Column("stats_followers", sa.BigInteger(), nullable=True),
        sa.Column("stats_subscriptions", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "triggers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("status", sa.Enum("WAIT", "RUN", "ERROR", name="triggerstatus"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "account_info",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("bio", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "account_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("medias", sa.Integer(), nullable=True),
        sa.Column("views", sa.BigInteger(), nullable=True),
        sa.Column("followers", sa.BigInteger(), nullable=True),
        sa.Column("subscriptions", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "account_subscription",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("subscribed_account_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
        ),
        sa.ForeignKeyConstraint(
            ["subscribed_account_id"],
            ["account.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "media",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("status", sa.Enum("OKAY", "FAIL", name="modelstatus"), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("identifier", sa.String(), nullable=False),
        sa.Column("media_type", sa.Enum("IMAGE", "VIDEO", "TEXT", name="mediatype"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("comments_last_update", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("info_last_update", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("info_title", sa.String(), nullable=True),
        sa.Column("info_caption", sa.String(), nullable=True),
        sa.Column("info_disable_comments", sa.Boolean(), nullable=False),
        sa.Column("stats_last_update", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("stats_comments", sa.Integer(), nullable=True),
        sa.Column("stats_likes", sa.Integer(), nullable=True),
        sa.Column("stats_views", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "trigger_account",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("trigger_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
        ),
        sa.ForeignKeyConstraint(
            ["trigger_id"],
            ["triggers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "trigger_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("trigger_id", sa.Integer(), nullable=False),
        sa.Column("started", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("finished", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["trigger_id"],
            ["triggers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "media_comment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("status", sa.Enum("OKAY", "FAIL", name="modelstatus"), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=True),
        sa.Column("identifier", sa.String(), nullable=False),
        sa.Column("text", sa.String(), nullable=True),
        sa.Column("likes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
        ),
        sa.ForeignKeyConstraint(
            ["media_id"],
            ["media.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "media_info",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("caption", sa.String(), nullable=False),
        sa.Column("disable_comments", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["media_id"],
            ["media.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "media_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.Column("comments", sa.Integer(), nullable=True),
        sa.Column("likes", sa.Integer(), nullable=True),
        sa.Column("views", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["media_id"],
            ["media.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "trigger_media",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("trigger_id", sa.Integer(), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["media_id"],
            ["media.id"],
        ),
        sa.ForeignKeyConstraint(
            ["trigger_id"],
            ["triggers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("trigger_media")
    op.drop_table("media_stats")
    op.drop_table("media_info")
    op.drop_table("media_comment")
    op.drop_table("trigger_stats")
    op.drop_table("trigger_account")
    op.drop_table("media")
    op.drop_table("account_subscription")
    op.drop_table("account_stats")
    op.drop_table("account_info")
    op.drop_table("triggers")
    op.drop_table("account")
    # ### end Alembic commands ###
