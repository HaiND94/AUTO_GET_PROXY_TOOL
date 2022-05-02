from app import app
from flask import jsonify

from werkzeug.exceptions import HTTPException

import werkzeug
import json



@app.errorhandler(Exception)
def handle_unexpected_error(error):
    status_code = 500
    success = False
    response = {
        'is_success': success,
        'error': {
            'type': 'UnexpectedException',
            'message': 'An unexpected error has occurred.',
            'exception': error
        }
    }

    return jsonify(response), status_code


@app.errorhandler(404)
def invalid_route(e):
    return jsonify({'errorCode': 404, 'message': 'Route not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'errorCode': 500, 'message': 'Internal server error template'}), 500


@app.errorhandler(werkzeug.exceptions.BadRequest)
def handle_bad_request(e):
    return 'bad request!', 400


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9090, debug=True)
