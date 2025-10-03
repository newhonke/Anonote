from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import secrets
from datetime import datetime 
import pytz

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
# 開発用警告
if os.environ.get("SECRET_KEY") is None:
    print("⚠ WARNING: 必ず本番環境では  setx SECRET_KEY\"本番用の安全なランダム文字列\"  をパワーシェルで行ってください。")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)

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
    emoji = db.Column(db.String(50), nullable=False)
    count = db.Column(db.Integer, default=1)

with app.app_context():
    db.create_all()

    if not User.query.filter_by(username="admin").first():
        # 管理者を作成
        admin = User(
            username = "admin", #必ず変更
            password = generate_password_hash("password"), #必ず変更
            is_admin = True
        )
        db.session.add(admin)
        db.session.commit()
        print("管理者アカウントを作成しました")
    else:
        print("管理者アカウントは既に存在します")

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
        note_text = request.form["note"]
        reply_to = request.form.get("reply_to")
        if reply_to == "": reply_to = None

        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        if ip and "," in ip:
            ip = ip.split(",")[0].strip()

        if BlockedIP.query.filter_by(ip=ip).first():
            return "ipblock"

        new_note = Note(post=note_text, ip=ip, user=current_user if current_user.is_authenticated else None,reply_to=reply_to)
        db.session.add(new_note)
        db.session.commit()
        return redirect(url_for("index"))

    # 1000件超えたら全noteを自動削除
    count = Note.query.count()
    if count >= 1000:
        db.session.query(Note).delete()
        db.session.commit()
        return redirect(url_for("index"))
    
    # index.htmlに表示
    notes = Note.query.order_by(Note.id.desc()).all()

    parent_map = {n.id: n for n in notes}

    reactions = {}
    for note in notes:
        reactions[note.id] = Reaction.query.filter_by(post_id=note.id).all()
    return render_template("index.html",notes=notes, parent_map=parent_map, reactions=reactions)

@app.route("/renote/<int:id>", methods=["GET","POST"])
def renote(id):
    original_note = Note.query.get_or_404(id)

    if (not original_note.post) or original_note.renote_from_id:
        return "この投稿はリノートできません"

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()

    new_note = Note(post="",ip=ip,user=current_user if current_user.is_authenticated else None,renote_from_id=original_note.id)
    db.session.add(new_note)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(url_for("admin"))
        return "ログイン失敗"
    return render_template("login.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if current_user.is_authenticated:
        notes = Note.query.order_by(Note.id.desc()).all()
        ips = BlockedIP.query.all()
        return render_template("admin.html",notes=notes,ips=ips)
    else:
        return redirect(url_for("login"))
        
@app.route("/delete/<int:id>", methods=["GET", "POST"])
def delete(id):
    if current_user.is_authenticated:
        note = Note.query.get(id)
        db.session.delete(note)
        db.session.commit()
        return redirect(url_for("admin"))
    else:
        return redirect(url_for("login"))

@app.route("/block/<ip>")
def block(ip):
    if current_user.is_authenticated and current_user.is_admin:
        if not BlockedIP.query.filter_by(ip=ip).first():
            blocked = BlockedIP(ip=ip)
            db.session.add(blocked)
            db.session.commit()
        return redirect(url_for("admin"))
    else:
        return redirect(url_for("login"))

@app.route("/unblock/<ip>")
def unblock(ip):
    blocked = BlockedIP.query.filter_by(ip=ip).first()
    if blocked:
        db.session.delete(blocked)
        db.session.commit()
        return f"{ip}解除しました。"
    return f"{ip}はブロックされてません。"

@app.route("/react", methods=["GET", "POST"])
def react():
    post_id = request.form["post_id"]
    emoji = request.form["emoji"]

    cookie_key = f"reaction_{post_id}"
    prev_emoji = request.cookies.get(cookie_key)

    if prev_emoji == emoji:
        return jsonify({"success":False,"message":"Already reacted with this emoji."})
    
    if prev_emoji:
        prev_reaction = Reaction.query.filter_by(post_id=post_id, emoji=prev_emoji).first()
        if prev_reaction:
            prev_reaction.count -= 1
            if prev_reaction.count <= 0:
                db.session.delete(prev_reaction)

    reaction = Reaction.query.filter_by(post_id=post_id,emoji=emoji).first()
    if reaction:
        reaction.count += 1
    else:
        reaction = Reaction(post_id=post_id, emoji=emoji,count=1)
        db.session.add(reaction)
    db.session.commit()

    resp = make_response(jsonify({"success": True, "emoji":emoji, "count":reaction.count}))
    resp.set_cookie(cookie_key, emoji, max_age=60*60*24*365)
    return resp


@app.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        return redirect(url_for("index"))
    else:
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)