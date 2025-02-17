from gevent import monkey
monkey.patch_all()

import os
import time
import socket
import signal
import sys
from dotenv import load_dotenv
import logging
from flask import Flask
import gevent
from gevent.event import Event

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/terminusa.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
should_exit = Event()

# Import app after monkey patching
from app import app, socketio

def update_game_state(game_manager):
    """Update game state periodically"""
    while not should_exit.is_set():
        try:
            game_manager.update_game_state()
            gevent.sleep(60)  # Update every minute
        except Exception as e:
            logger.error(f"Error in game state update: {str(e)}", exc_info=True)
            gevent.sleep(5)  # Wait a bit before retrying

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    should_exit.set()

def main():
    try:
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')

        # Load environment variables
        load_dotenv(override=True)
        logger.info("Environment variables loaded")

        # Import game manager after environment is loaded
        from game_systems import GameManager

        # Initialize game manager
        game_manager = GameManager()
        logger.info("Game manager initialized")

        # Configure server
        port = int(os.getenv('SERVER_PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        host = '0.0.0.0'  # Bind to all interfaces

        # Start game state updater in a greenlet
        updater = gevent.spawn(update_game_state, game_manager)
        logger.info("Game state updater started")

        # Start server
        logger.info(f"Starting server on {host}:{port}")
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=False,
            allow_unsafe_werkzeug=True,
            log_output=True
        )

    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        raise
    finally:
        # Ensure everything is cleaned up
        should_exit.set()
        logger.info("Shutdown complete")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
