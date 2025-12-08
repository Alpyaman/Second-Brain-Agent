"""
create_blog_tables

Revision ID: 20251208140103
Created: 2025-12-08 14:01:03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251208140103'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Apply migration."""
    # Create User table
    op.create_table(
        'user',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('username', sa.String(50), nullable=False, unique=True),
        sa.Column('email', sa.String(100), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100)),
        sa.Column('last_name', sa.String(100)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_admin', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, default='now'),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_index(
        'ix_user_email',
        'user',
        ['email']
    )

    # Create Post table
    op.create_table(
        'post',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False, unique=True),
        sa.Column('content', sa.Text),
        sa.Column('excerpt', sa.String(500)),
        sa.Column('user_id', sa.Integer, nullable=False, sa.ForeignKey('user.id')),
        sa.Column('published', sa.Boolean, default=False),
        sa.Column('view_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, default='now'),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_index(
        'ix_post_title',
        'post',
        ['title']
    )

    # Create Comment table
    op.create_table(
        'comment',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('post_id', sa.Integer, nullable=False, sa.ForeignKey('post.id')),
        sa.Column('user_id', sa.Integer, nullable=False, sa.ForeignKey('user.id')),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('approved', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, default='now'),
    )

    # Create Tag table
    op.create_table(
        'tag',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('slug', sa.String(50), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime, default='now'),
    )



def downgrade():
    """Revert migration."""
    op.drop_table('tag')
    op.drop_table('comment')
    op.drop_index('ix_post_title')
    op.drop_table('post')
    op.drop_index('ix_user_email')
    op.drop_table('user')
