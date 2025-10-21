from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import secrets
from datetime import datetime
import pytz
from functools import wraps
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
# CSRF を有効化
csrf = CSRFProtect()
csrf.init_app(app)
# 開発用警告
if os.environ.get("SECRET_KEY") is None:
    print("⚠ WARNING: 必ず本番環境では  setx SECRET_KEY\"本番用の安全なランダム文字列\"  をパワーシェルで行ってください。")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

TRUST_X_FORWARDED_FOR = os.environ.get("TRUST_X_FORWARDED_FOR", "false").lower() in {"1", "true", "yes"}


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if not current_user.is_admin:
            abort(403)
        return view_func(*args, **kwargs)

    return login_required(wrapper)


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": lambda: generate_csrf()}


def get_request_ip() -> str:
    ip = request.remote_addr or ""
    if TRUST_X_FORWARDED_FOR:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
    return ip

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(10), unique=True, nullable=False)
    password = db.Column(db.String(2000), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post = db.Column(db.String(200), nullable=False)
    ip = db.Column(db.String(45))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", backref="notes")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reply_to = db.Column(db.Integer, db.ForeignKey("note.id"))
    renote_from_id = db.Column(db.Integer, db.ForeignKey("note.id"))

class BlockedIP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(45))

class Reaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("note.id"), nullable=False)
    emoji_id = db.Column(db.Integer, db.ForeignKey("emoji.id"), nullable=False)
    emoji = db.relationship("Emoji", foreign_keys=[emoji_id])
    count = db.Column(db.Integer, default=1)
    note = db.relationship("Note", backref="reactions", lazy=True)

class Emoji(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)


with app.app_context():
    db.create_all()

    admin_username = os.environ.get("ADMIN_USERNAME")
    admin_password = os.environ.get("ADMIN_PASSWORD")

    if admin_username and admin_password:
        if len(admin_username) > User.username.type.length:
            print("⚠ WARNING: ADMIN_USERNAME は最大10文字までです。環境変数を更新してください。")
        else:
            existing_admin = User.query.filter_by(username=admin_username).first()
            if not existing_admin:
                hashed_password = generate_password_hash(admin_password)
                admin = User(
                    username=admin_username,
                    password=hashed_password,
                    is_admin=True,
                )
                db.session.add(admin)
                db.session.commit()
                print("環境変数から管理者アカウントを作成しました。")
            else:
                print("環境変数で指定された管理者アカウントは既に存在します。")
    elif not User.query.filter_by(is_admin=True).first():
        print("⚠ WARNING: ADMIN_USERNAME と ADMIN_PASSWORD を環境変数に設定して管理者アカウントを作成してください。")
    else:
        print("管理者アカウントは既に存在します。")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.template_filter("to_jst")
def to_jst(value):
    if value is None:
        return ""
    jst = pytz.timezone("Asia/Tokyo")
    if value.tzinfo is None:  # naive datetimeならUTC扱い
        value = value.replace(tzinfo=pytz.utc)
    return value.astimezone(jst).strftime("%Y-%m-%d %H:%M:%S")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        note_text = request.form.get("note", "").strip()
        if not note_text:
            abort(400)

        reply_to = None
        reply_to_raw = request.form.get("reply_to")
        if reply_to_raw:
            try:
                reply_to_candidate = int(reply_to_raw)
            except ValueError:
                abort(400)
            else:
                if Note.query.get(reply_to_candidate):
                    reply_to = reply_to_candidate

        ip = get_request_ip()

        if BlockedIP.query.filter_by(ip=ip).first():
            return "ipblock"

        new_note = Note(post=note_text, ip=ip, user=current_user if current_user.is_authenticated else None, reply_to=reply_to)
        db.session.add(new_note)
        db.session.commit()
        return redirect(url_for("index"))

    # 1000件を超えたら古い投稿のみ削除
    max_notes = 1000
    count = Note.query.count()
    if count > max_notes:
        overflow = count - max_notes
        old_notes = Note.query.order_by(Note.id).limit(overflow).all()
        for old_note in old_notes:
            db.session.delete(old_note)
        db.session.commit()
    
    # index.htmlに表示
    notes = Note.query.order_by(Note.id.desc()).all()
    emojis = Emoji.query.all()

    parent_map = {n.id: n for n in notes}

    reactions = {}
    for note in notes:
        reactions[note.id] = Reaction.query.filter_by(post_id=note.id).all()
    return render_template("index.html",notes=notes, parent_map=parent_map, reactions=reactions ,emojis=emojis)

@app.route("/renote/<int:id>", methods=["POST"])
def renote(id):
    original_note = Note.query.get_or_404(id)

    if (not original_note.post) or original_note.renote_from_id:
        return "この投稿はリノートできません"

    ip = get_request_ip()

    new_note = Note(post="",ip=ip,user=current_user if current_user.is_authenticated else None,renote_from_id=original_note.id)
    db.session.add(new_note)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("admin"))
        error = "ログインに失敗しました。"
    return render_template("login.html", error=error)

@app.route("/admin", methods=["GET"])
@admin_required
def admin():
    notes = Note.query.order_by(Note.id.desc()).limit(100).all()
    ips = BlockedIP.query.all()
    emojis = Emoji.query.all()
    return render_template("admin.html", notes=notes, ips=ips, emojis=emojis)
    
@app.route("/admin/emojis", methods=["POST"])
@admin_required
def add_emoji():
    name = request.form.get("name", "").strip()
    image = request.files.get("image")
    if not name or image is None or not image.filename:
        abort(400)

    filename = secure_filename(image.filename)
    if not filename:
        abort(400)

    os.makedirs("static/emojis", exist_ok=True)
    path = os.path.join("static/emojis", filename)
    image.save(path)
    db.session.add(Emoji(name=name, image_url=f"emojis/{filename}"))
    db.session.commit()
    return redirect("/admin")

@app.route("/admin/emojis/delete/<int:id>", methods=["POST"])
@admin_required
def delete_emoji(id):
    emoji = Emoji.query.get_or_404(id)
    db.session.delete(emoji)
    db.session.commit()
    return redirect("/admin")

        
@app.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete(id):
    note = Note.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for("admin"))

@app.route("/block", methods=["POST"])
@admin_required
def block():
    ip = request.form.get("ip", "").strip()
    if not ip:
        abort(400)
    if not BlockedIP.query.filter_by(ip=ip).first():
        blocked = BlockedIP(ip=ip)
        db.session.add(blocked)
        db.session.commit()
    return redirect(url_for("admin"))

@app.route("/unblock", methods=["POST"])
@admin_required
def unblock():
    ip = request.form.get("ip", "").strip()
    if not ip:
        abort(400)
    blocked = BlockedIP.query.filter_by(ip=ip).first()
    if blocked:
        db.session.delete(blocked)
        db.session.commit()
    return redirect(url_for("admin"))

@app.route("/react", methods=["POST"])
def react():
    try:
        post_id = int(request.form["post_id"])
        emoji_id = int(request.form["emoji_id"])
    except (KeyError, TypeError, ValueError):
        abort(400)
    cookie_key = f"reaction_{post_id}"

    Note.query.get_or_404(post_id)
    Emoji.query.get_or_404(emoji_id)

    # すでにリアクションしていた場合（絵文字が違っても）
    prev_emoji_id = request.cookies.get(cookie_key)
    if prev_emoji_id and prev_emoji_id.isdigit():
        prev_emoji_int = int(prev_emoji_id)
        # 前のリアクションを減らす
        prev_reaction = Reaction.query.filter_by(post_id=post_id, emoji_id=prev_emoji_int).first()
        if prev_reaction:
            prev_reaction.count -= 1
            if prev_reaction.count <= 0:
                db.session.delete(prev_reaction)

    if request.cookies.get(cookie_key) == str(emoji_id):
        return jsonify(success=False)
    
    reaction = Reaction.query.filter_by(post_id=post_id,emoji_id=emoji_id).first()
    if reaction:
        reaction.count += 1
    else:
        reaction = Reaction(post_id=post_id, emoji_id=emoji_id,count=1)
        db.session.add(reaction)
    db.session.commit()

    resp = jsonify(success=True)
    resp.set_cookie(
        cookie_key,
        str(emoji_id),
        httponly=True,
        samesite="Lax",
        secure=request.is_secure,
    )
    return resp


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG") == "1"
    app.run(debug=debug_mode)
