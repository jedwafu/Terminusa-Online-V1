import os
import threading
import time
from dotenv import load_dotenv
import logging
from flask import Flask
from werkzeug.serving import make_server

from server import app as server_app
from web_app import app as web_app
from game_systems import GameManager

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

class ServerThread(threading.Thread):
    def __init__(self, app, host, port):
        threading.Thread.__init__(self)
        self.srv = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        logger.info('Starting server')
        self.srv.serve_forever()

    def shutdown(self):
        logger.info('Stopping server')
        self.srv.shutdown()

def start_game_state_updater(game_manager):
    """Start background thread to update game state"""
    def update_loop():
        while True:
            try:
                game_manager.update_game_state()
                time.sleep(60)  # Update every minute
            except Exception as e:
                logger.error(f"Error in game state update: {str(e)}", exc_info=True)
    
    thread = threading.Thread(target=update_loop, daemon=True)
    thread.start()
    return thread

def main():
    try:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')

        # Load environment variables
        load_dotenv(override=True)
        logger.info("Environment variables loaded")

        # Initialize game manager
        game_manager = GameManager()
        logger.info("Game manager initialized")

        # Start game state updater
        state_updater = start_game_state_updater(game_manager)
        logger.info("Game state updater started")

        # Configure server app
        server_port = int(os.getenv('SERVER_PORT', 5000))
        server_thread = ServerThread(server_app, '0.0.0.0', server_port)
        server_thread.start()
        logger.info(f"Game server started on port {server_port}")

        # Configure web app
        web_port = int(os.getenv('WEBAPP_PORT', 5001))
        web_thread = ServerThread(web_app, '0.0.0.0', web_port)
        web_thread.start()
        logger.info(f"Web server started on port {web_port}")

        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down servers...")
            server_thread.shutdown()
            web_thread.shutdown()
            logger.info("Servers stopped")

    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        raise
