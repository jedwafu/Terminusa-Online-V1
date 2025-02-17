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
from werkzeug.serving import make_server
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

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            # Try to bind to all interfaces
            s.bind(('', port))
            s.close()
            return False
        except socket.error:
            return True

def cleanup_port(port):
    """Attempt to cleanup a port that's in use"""
    logger.info(f"Attempting to cleanup port {port}")
    try:
        # On Linux, you can use fuser to find and kill processes
        if os.name != 'nt':  # Not Windows
            os.system(f'fuser -k {port}/tcp')
            time.sleep(2)  # Increased delay to ensure port is released
            return not is_port_in_use(port)
        else:  # On Windows
            os.system(f'netstat -ano | findstr :{port}')
            time.sleep(2)
            return not is_port_in_use(port)
    except Exception as e:
        logger.error(f"Error cleaning up port: {e}")
    return False

def update_game_state(game_manager, stop_event):
    """Update game state periodically"""
    while not stop_event.is_set():
        try:
            game_manager.update_game_state()
            gevent.sleep(60)  # Update every minute
        except Exception as e:
            logger.error(f"Error in game state update: {str(e)}", exc_info=True)
            gevent.sleep(5)  # Wait a bit before retrying

def run_server(app, host, port, debug):
    """Run the Flask-SocketIO server"""
    from app import socketio
    try:
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
        logger.error(f"Server error: {e}")
        should_exit.set()

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

        # Import app and game manager after environment is loaded
        from app import app
        from game_systems import GameManager

        # Initialize game manager
        game_manager = GameManager()
        logger.info("Game manager initialized")

        # Configure server
        port = int(os.getenv('SERVER_PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        host = '0.0.0.0'  # Bind to all interfaces

        # Check if port is in use
        if is_port_in_use(port):
            logger.warning(f"Port {port} is already in use")
            if cleanup_port(port):
                logger.info(f"Successfully cleaned up port {port}")
                gevent.sleep(1)  # Additional delay after cleanup
            else:
                alternative_port = port + 1
                while is_port_in_use(alternative_port) and alternative_port < port + 10:
                    alternative_port += 1
                if alternative_port < port + 10:
                    logger.info(f"Using alternative port {alternative_port}")
                    port = alternative_port
                else:
                    raise RuntimeError(f"Could not find available port in range {port}-{port+9}")

        # Start game state updater in a greenlet
        updater = gevent.spawn(update_game_state, game_manager, should_exit)
        logger.info("Game state updater started")

        # Start server in a greenlet
        server = gevent.spawn(run_server, app, host, port, debug)
        logger.info("Server started")

        # Wait for either the server to finish or a shutdown signal
        gevent.joinall([server, updater], timeout=None, count=1)

        # Cleanup
        logger.info("Initiating shutdown...")
        should_exit.set()
        gevent.joinall([server, updater], timeout=5)
        logger.info("Shutdown complete")

    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        raise
    finally:
        # Ensure everything is cleaned up
        should_exit.set()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
