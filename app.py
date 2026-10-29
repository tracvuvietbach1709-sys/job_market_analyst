import os
from flask import Flask
from controllers.job_controller import jobs
from models.job_model import init_db


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'local-development-only-change-this')
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
    init_db()
    app.register_blueprint(jobs)
    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=os.environ.get('FLASK_DEBUG') == '1')
