from flask import make_response, jsonify


class Errors:

    def __init__(self, app):
        self.app = app
        self.register_errors()

    def register_errors(self):
        @self.app.errorhandler(404)
        def not_found_error(error):
            return make_response(jsonify({'error': 'Not found'}), 404)

        @self.app.errorhandler(500)
        def internal_server_error(error):
            return make_response(jsonify({'error': 'Internal Server Error'}), 500)

        @self.app.errorhandler(400)
        def bad_request(error):
            return make_response(jsonify({'error': 'Bad Request'}), 400)

        @self.app.errorhandler(405)
        def method_not_allowed(error):
            return make_response(jsonify({'error': 'Method Not Allowed'}), 405)
