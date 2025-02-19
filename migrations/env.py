from __future__ import with_statement

import logging
from flask import current_app
from alembic import context
from sqlalchemy import engine_from_config, pool

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
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    # Get the database engine
    engine = current_app.extensions['migrate'].db.get_engine()

    # Configure the migration context with retry logic
    def run_migrations(connection):
        migration_config = {
            'connection': connection,
            'target_metadata': target_metadata,
            'process_revision_directives': process_revision_directives,
            'transaction_per_migration': True,
            'compare_type': True,
            **current_app.extensions['migrate'].configure_args
        }

        try:
            context.configure(**migration_config)
            with context.begin_transaction():
                context.run_migrations()
        except Exception as e:
            logger.error(f"Error during migration: {str(e)}")
            try:
                # Try to rollback using the raw connection
                connection.connection.rollback()
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {str(rollback_error)}")
            raise

    # Run migrations with connection handling
    with engine.connect() as connection:
        run_migrations(connection)

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
