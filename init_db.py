#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import subprocess
from rich.console import Console
from rich.panel import Panel
from app import app
from database import db, init_db

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
        if db_url.startswith('postgresql://'):
            db_url = db_url[len('postgresql://'):]

        user_pass, host_port_db = db_url.split('@')
        if ':' in user_pass:
            user, password = user_pass.split(':')
        else:
            user = user_pass
            password = ''

        if '/' in host_port_db:
            host_port, db_name = host_port_db.split('/')
        else:
            host_port = host_port_db
            db_name = 'terminusa'

        if ':' in host_port:
            host, port = host_port.split(':')
            port = int(port)
        else:
            host = host_port
            port = 5432

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

        # Initialize Flask app and database
        with app.app_context():
            # Initialize database
            init_db(app)
            
            # Create all tables
            db.create_all()
            
            console.print("[green]Database tables created successfully[/green]")

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
