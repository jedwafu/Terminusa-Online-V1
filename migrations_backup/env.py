from __future__ import with_statement

import logging
from flask import current_app
from alembic import context
from sqlalchemy import engine_from_config, pool, text
import psycopg2

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set up logging
logging.basicConfig(
    format='%(levelname)-5.5s [%(name)s] %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('alembic.env')

# Configure Flask app
app = current_app

# add your model's MetaData object here
# for 'autogenerate' support
config.set_main_option(
    'sqlalchemy.url', current_app.config.get('SQLALCHEMY_DATABASE_URI')
)
target_metadata = current_app.extensions['migrate'].db.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = current_app.config.get('SQLALCHEMY_DATABASE_URI')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    # Get the database engine
    engine = current_app.extensions['migrate'].db.get_engine()

    def run_migration_with_retry(connection):
        migration_config = {
            'connection': connection,
            'target_metadata': target_metadata,
            'process_revision_directives': process_revision_directives,
            'transaction_per_migration': True,
            'compare_type': True,
            **current_app.extensions['migrate'].configure_args
        }

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Get raw psycopg2 connection
                raw_connection = connection.connection.connection
                # Ensure we're starting with a clean slate
                raw_connection.rollback()
                
                context.configure(**migration_config)
                with context.begin_transaction():
                    context.run_migrations()
                break
            except Exception as e:
                retry_count += 1
                logger.error(f"Error during migration (attempt {retry_count}): {str(e)}")
                
                try:
                    # Rollback using raw psycopg2 connection
                    raw_connection = connection.connection.connection
                    raw_connection.rollback()
                except Exception as rollback_error:
                    logger.error(f"Error during rollback: {str(rollback_error)}")
                
                if retry_count >= max_retries:
                    raise

    # Run migrations with connection handling
    with engine.connect() as connection:
        run_migration_with_retry(connection)

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
