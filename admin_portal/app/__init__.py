import logging
import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.extensions import csrf, db, login_manager, migrate


def create_app(config_object: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(
        config_object or os.environ.get("FLASK_CONFIG", "app.config.DevConfig")
    )

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    _configure_logging(app)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "error"
    migrate.init_app(app, db)
    csrf.init_app(app)

    from app.models.admin_user import AdminUser

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(AdminUser, int(user_id))

    _register_blueprints(app)
    _register_cli(app)
    _register_template_helpers(app)
    _register_health_check(app)

    if app.config.get("ENABLE_STATUS_SWEEP"):
        _start_status_sweep(app)

    return app


def _register_blueprints(app: Flask) -> None:
    from app.blueprints.api import api_bp
    from app.blueprints.api.v1 import v1_bp
    from app.blueprints.audit import audit_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.devices import devices_bp
    from app.blueprints.messages import messages_bp
    from app.blueprints.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(api_bp)

    # All /api/v1/* routes are either device-Bearer-token-authed (POST
    # endpoints) or GET-only (dashboard, which CSRF never applies to
    # anyway), so exempting the whole nested blueprint is safe. Flask-WTF's
    # exemption check matches on the *specific* Blueprint object bound to
    # request.blueprint, which for a nested blueprint is v1_bp itself, not
    # the parent api_bp it's registered under — exempting only api_bp here
    # would silently fail to exempt anything nested inside it.
    csrf.exempt(api_bp)
    csrf.exempt(v1_bp)


def _register_cli(app: Flask) -> None:
    from app import cli

    app.cli.add_command(cli.create_admin)
    app.cli.add_command(cli.set_admin_password)
    app.cli.add_command(cli.backfill_reference_ids)
    app.cli.add_command(cli.backfill_amounts)
    app.cli.add_command(cli.cleanup_test_records)


def _register_template_helpers(app: Flask) -> None:
    @app.context_processor
    def inject_nav_flags():
        return {}


def _register_health_check(app: Flask) -> None:
    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}, 200


def _configure_logging(app: Flask) -> None:
    level = getattr(logging, app.config.get("LOG_LEVEL", "INFO"), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _start_status_sweep(app: Flask) -> None:
    # Guard against the reloader starting this twice in debug mode.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        from apscheduler.schedulers.background import BackgroundScheduler

        from app.services.device_status import sweep_offline_devices

        scheduler = BackgroundScheduler(daemon=True)

        def _job():
            with app.app_context():
                sweep_offline_devices(app)

        scheduler.add_job(_job, "interval", seconds=60, id="device_status_sweep")
        scheduler.start()
        app.extensions["status_scheduler"] = scheduler
