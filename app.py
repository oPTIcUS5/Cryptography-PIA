"""
Web Flask
"""

import os
import re
import secrets
from datetime import timedelta
from functools import wraps
from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for

from votoSeguro.config import CANDIDATES, DATA, ELECTION_ID, ELECTION_NAME
from votoSeguro.crypto import public_encryption_spki_base64, validate_ballot_envelope
from votoSeguro.storage import get_voter, get_status, record_vote, get_ballot, count_ballots
from votoSeguro.services import authenticate, public_audit


def create_app(test_config=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.update(
        SECRET_KEY=os.environ.get("VOTOSEGURO_SECRET_KEY") or secrets.token_hex(32),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("VOTOSEGURO_HTTPS") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=25),
        MAX_CONTENT_LENGTH=16000,
    )
    if test_config:
        app.config.update(test_config)

    @app.after_request
    def security_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; img-src 'self'; frame-ancestors 'none'; form-action 'self'"
        )
        return response

    def csrf():
        if "csrf" not in session:
            session["csrf"] = secrets.token_urlsafe(32)
        return session["csrf"]

    def valid_csrf():
        supplied = request.headers.get("X-CSRF-Token") or request.form.get("csrf", "")
        return (bool(session.get("csrf")) and isinstance(supplied, str)
                and secrets.compare_digest(supplied, session["csrf"]))

    def login_required(handler):
        @wraps(handler)
        def wrapper(*args, **kwargs):
            if not session.get("voter"):
                return redirect(url_for("login"))
            return handler(*args, **kwargs)
        return wrapper

    @app.route("/")
    def index():
        return redirect(url_for("vote") if session.get("voter") else url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            if not valid_csrf():
                abort(400, "CSRF inválido")
            failures = int(session.get("failures", 0))
            if failures >= 5:
                return render_template("login.html", token=csrf(), error="Demasiados intentos en esta sesión"), 429
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if authenticate(username, password):
                session.clear()
                session["voter"] = username
                session.permanent = True
                csrf()
                return redirect(url_for("vote"))
            session["failures"] = failures + 1
            return render_template("login.html", token=csrf(), error="Credenciales incorrectas"), 401
        return render_template("login.html", token=csrf(), error=None)

    @app.route("/logout", methods=["POST"])
    def logout():
        if not valid_csrf():
            abort(400)
        session.clear()
        return redirect(url_for("login"))

    @app.route("/votar")
    @login_required
    def vote():
        voter = get_voter(session["voter"])
        if voter is None:
            session.clear()
            return redirect(url_for("login"))
        return render_template("vote.html", token=csrf(), election=ELECTION_NAME,
                               candidates=CANDIDATES, has_voted=voter["has_voted"],
                               status=get_status())

    @app.route("/api/config")
    def config():
        return jsonify({"election_id": ELECTION_ID, "name": ELECTION_NAME,
                        "candidates": CANDIDATES, "public_key_spki_base64": public_encryption_spki_base64(),
                        "status": get_status()})

    @app.route("/api/vote", methods=["POST"])
    @login_required
    def api_vote():
        if not valid_csrf():
            return jsonify({"error": "CSRF inválido"}), 403
        try:
            envelope = validate_ballot_envelope(request.get_json(silent=True))
            receipt = record_vote(session["voter"], envelope)
        except (ValueError, TypeError) as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"receipt": receipt, "verification_url": url_for("receipt", receipt=receipt)}), 201

    @app.route("/comprobante/<receipt>")
    def receipt(receipt):
        if not re.fullmatch(r"[0-9a-f]{64}", receipt):
            abort(404)
        ballot = get_ballot(receipt)
        if not ballot:
            abort(404)
        return render_template("receipt.html", ballot=ballot)

    @app.route("/auditoria")
    def audit():
        return render_template("audit.html", records=public_audit(), status=get_status(),
                               total=count_ballots())

    @app.route("/resultados")
    def results():
        filename = DATA / "results.json"
        record = __import__("json").loads(filename.read_text(encoding="utf-8")) if filename.exists() else None
        return render_template("results.html", record=record, candidates=CANDIDATES,
                               status=get_status())

    return app


if __name__ == "__main__":
    # HTTPS real y servidor WSGI dedicado serían obligatorios para despliegue.
    create_app().run(host="127.0.0.1", port=5000, debug=False)

