import hmac
import os
import re
import secrets
from datetime import datetime
from urllib.parse import urlparse

from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)
from flask_sqlalchemy import SQLAlchemy

from seed_data import SEED_LINKS, SEED_VIDEOS

MAX_VIDEOS = int(os.getenv("MAX_VIDEOS", "30"))
CATEGORIES = {
    "programacion": "Programación",
    "ciberseguridad": "Ciberseguridad",
    "ia-agentes": "IA y agentes",
}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "cambia-esto-en-produccion")

db_url = os.getenv("DATABASE_URL", "sqlite:///devhub.db")
if db_url.startswith("postgres://"):  # Render/Heroku usan este prefijo antiguo
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
db = SQLAlchemy(app)


class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(10), nullable=False, index=True)  # 'video' | 'enlace'
    title = db.Column(db.String(200), nullable=False)
    channel = db.Column(db.String(120), default="")
    category = db.Column(db.String(30), nullable=False, index=True)
    url = db.Column(db.String(500), nullable=False)
    youtube_id = db.Column(db.String(11))
    description = db.Column(db.String(400), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def yt_id(value):
    """Extrae el ID de 11 caracteres de una URL de YouTube (o de un ID suelto)."""
    value = value.strip()
    if re.fullmatch(r"[\w-]{11}", value):
        return value
    m = re.search(r"(?:v=|youtu\.be/|embed/|shorts/)([\w-]{11})", value)
    return m.group(1) if m else None


def add_video(vid, title, channel, category, description):
    db.session.add(Resource(
        kind="video", title=title, channel=channel, category=category,
        youtube_id=vid, url=f"https://www.youtube.com/watch?v={vid}",
        description=description))


def init_db():
    db.create_all()
    if Resource.query.count() == 0:
        for v in SEED_VIDEOS:
            add_video(*v)
        for title, category, url, desc in SEED_LINKS:
            db.session.add(Resource(kind="enlace", title=title, category=category,
                                    url=url, description=desc))
        db.session.commit()


with app.app_context():
    init_db()


# ---------- seguridad básica ----------
@app.context_processor
def inject_globals():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return {"csrf_token": session["csrf"], "CATEGORIES": CATEGORIES,
            "is_admin": session.get("admin", False)}


@app.before_request
def check_csrf():
    if request.method == "POST":
        if not hmac.compare_digest(request.form.get("csrf", ""), session.get("csrf", "x")):
            abort(400)


def admin_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*a, **kw):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return fn(*a, **kw)
    return wrapper


# ---------- rutas públicas ----------
@app.get("/")
def index():
    videos = Resource.query.filter_by(kind="video").order_by(Resource.id).all()
    links = Resource.query.filter_by(kind="enlace").order_by(Resource.id).all()
    return render_template("index.html", videos=videos, links=links)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- administración ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        expected = os.getenv("ADMIN_PASSWORD", "")
        given = request.form.get("password", "")
        if expected and hmac.compare_digest(given, expected):
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Contraseña incorrecta o ADMIN_PASSWORD no configurada.", "error")
    return render_template("login.html")


@app.post("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("index"))


@app.get("/admin")
@admin_required
def admin():
    items = Resource.query.order_by(Resource.kind, Resource.id.desc()).all()
    n_videos = Resource.query.filter_by(kind="video").count()
    return render_template("admin.html", items=items, n_videos=n_videos,
                           max_videos=MAX_VIDEOS)


@app.post("/admin/add")
@admin_required
def admin_add():
    kind = request.form.get("kind")
    title = request.form.get("title", "").strip()[:200]
    category = request.form.get("category")
    desc = request.form.get("description", "").strip()[:400]
    url = request.form.get("url", "").strip()[:500]

    if not title or category not in CATEGORIES or kind not in ("video", "enlace"):
        flash("Completa título, categoría y tipo.", "error")
        return redirect(url_for("admin"))

    if kind == "video":
        if Resource.query.filter_by(kind="video").count() >= MAX_VIDEOS:
            flash(f"Límite de {MAX_VIDEOS} videos alcanzado. Elimina uno o agrega un enlace.", "error")
            return redirect(url_for("admin"))
        vid = yt_id(url)
        if not vid:
            flash("URL de YouTube no válida.", "error")
            return redirect(url_for("admin"))
        add_video(vid, title, request.form.get("channel", "").strip()[:120], category, desc)
    else:
        if urlparse(url).scheme not in ("http", "https") or not urlparse(url).netloc:
            flash("El enlace debe empezar con http:// o https://", "error")
            return redirect(url_for("admin"))
        db.session.add(Resource(kind="enlace", title=title, category=category,
                                url=url, description=desc))
    db.session.commit()
    flash("Recurso agregado.", "ok")
    return redirect(url_for("admin"))


@app.post("/admin/delete/<int:rid>")
@admin_required
def admin_delete(rid):
    db.session.delete(db.get_or_404(Resource, rid))
    db.session.commit()
    flash("Recurso eliminado.", "ok")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True)
