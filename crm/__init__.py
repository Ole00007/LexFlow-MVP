from flask import Flask, jsonify
from .config import Config
from .extensions import db, migrate, jwt

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from .routes.health import health_bp
    from .routes.contacts import contacts_bp
    from .routes.cases import cases_bp
    from .routes.auth import auth_bp
    from .routes.tasks import tasks_bp
    from .routes.kanban import kanban_bp
    from .routes.notifications import notifications_bp
    from .routes.intake import intake_bp
    from .routes.appointments import appointments_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(contacts_bp, url_prefix="/api")
    app.register_blueprint(cases_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(tasks_bp, url_prefix="/api")
    app.register_blueprint(kanban_bp, url_prefix="/api")
    app.register_blueprint(notifications_bp, url_prefix="/api")
    app.register_blueprint(intake_bp, url_prefix="/api/intake")
    app.register_blueprint(appointments_bp, url_prefix="/api")

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(409)
    def conflict(error):
        return jsonify({"error": "Conflict"}), 409

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({"error": "Internal server error"}), 500

    return app

