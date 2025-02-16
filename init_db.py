#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import subprocess
from rich.console import Console
from rich.panel import Panel
from urllib.parse import urlparse

console = Console()

def init_database():
    """Initialize the database"""
    load_dotenv()

    # Parse DATABASE_URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        console.print("[red]DATABASE_URL not found in environment variables[/red]")
        return False

    try:
        # Parse the DATABASE_URL using urlparse
        parsed = urlparse(db_url)
        
        # Extract components
        user = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port or 5432
        db_name = parsed.path[1:] if parsed.path else 'terminusa'

        # Connect to PostgreSQL server
        console.print("[yellow]Connecting to PostgreSQL server...[/yellow]")
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cur.fetchone()

        if not exists:
            console.print(f"[yellow]Creating database {db_name}...[/yellow]")
            cur.execute(f'CREATE DATABASE {db_name}')
            console.print(f"[green]Database {db_name} created successfully[/green]")
        else:
            console.print(f"[yellow]Database {db_name} already exists[/yellow]")

        cur.close()
        conn.close()

        # Connect to the new database
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=db_name
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Create extensions if they don't exist
        cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        cur.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

        cur.close()
        conn.close()

        # Run database migrations
        console.print("[yellow]Running database migrations...[/yellow]")
        subprocess.run(['flask', 'db', 'upgrade'], check=True)
        console.print("[green]Database migrations completed successfully[/green]")

        return True

    except Exception as e:
        console.print(f"[red]Error initializing database: {str(e)}[/red]")
        return False

def main():
    console.print(Panel.fit("Terminusa Online Database Initialization"))
    
    if init_database():
        console.print(Panel.fit("[green]Database initialization completed successfully![/green]"))
    else:
        console.print(Panel.fit("[red]Database initialization failed![/red]"))

if __name__ == "__main__":
    main()
