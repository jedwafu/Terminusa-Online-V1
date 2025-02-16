import os
import threading
import time
import socket
import signal
import sys
from dotenv import load_dotenv
import logging
from flask import Flask
from werkzeug.serving import make_server

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

# Global variables for cleanup
server_instance = None
game_state_updater = None

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
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
    except Exception as e:
        logger.error(f"Error cleaning up port: {e}")
    return False

def start_game_state_updater(game_manager):
    """Start background thread to update game state"""
    def update_loop():
        while getattr(threading.current_thread(), "do_run", True):
            try:
                game_manager.update_game_state()
                time.sleep(60)  # Update every minute
            except Exception as e:
                logger.error(f"Error in game state update: {str(e)}", exc_info=True)
    
    thread = threading.Thread(target=update_loop, daemon=True)
    thread.do_run = True
    thread.start()
    return thread

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Shutdown signal received, cleaning up...")
    
    # Stop the game state updater
    global game_state_updater
    if game_state_updater:
        game_state_updater.do_run = False
        game_state_updater.join(timeout=5)
        logger.info("Game state updater stopped")

    # Import socketio here to avoid circular imports
    try:
        from app import socketio
        logger.info("Stopping SocketIO...")
        socketio.stop()
    except Exception as e:
        logger.error(f"Error stopping SocketIO: {e}")

    logger.info("Shutdown complete")
    sys.exit(0)

def main():
    try:
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')

        # Load environment variables
        load_dotenv(override=True)
        logger.info("Environment variables loaded")

        # Import app and game manager after environment is loaded
        from app import app, socketio
        from game_systems import GameManager

        # Initialize game manager
        game_manager = GameManager()
        logger.info("Game manager initialized")

        # Start game state updater
        global game_state_updater
        game_state_updater = start_game_state_updater(game_manager)
        logger.info("Game state updater started")

        # Configure server
        port = int(os.getenv('SERVER_PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

        # Check if port is in use
        if is_port_in_use(port):
            logger.warning(f"Port {port} is already in use")
            if cleanup_port(port):
                logger.info(f"Successfully cleaned up port {port}")
                time.sleep(1)  # Additional delay after cleanup
            else:
                alternative_port = port + 1
                while is_port_in_use(alternative_port) and alternative_port < port + 10:
                    alternative_port += 1
                if alternative_port < port + 10:
                    logger.info(f"Using alternative port {alternative_port}")
                    port = alternative_port
                else:
                    raise RuntimeError(f"Could not find available port in range {port}-{port+9}")

        logger.info(f"Starting server on port {port}")
        socketio.run(
            app,
            host='0.0.0.0',
            port=port,
            debug=debug,
            use_reloader=False,
            allow_unsafe_werkzeug=True,
            log_output=True
        )

    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        # Ensure cleanup on error
        signal_handler(signal.SIGTERM, None)
        raise
