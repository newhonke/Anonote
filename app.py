from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import secrets

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

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        note_text = request.form["note"]
        new_note = Note(post=note_text)
        db.session.add(new_note)
        db.session.commit()

    # 1000件超えたら全noteを自動削除
    count = Note.query.count()
    if count >= 1000:
        db.session.query(Note).delete()
        db.session.commit()
        return redirect(url_for("index"))
    
    # index.htmlに表示
    notes = Note.query.all()
    return render_template("index.html",notes=notes)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(url_for("index"))
        return "ログイン失敗"
    return render_template("login.html")
        


if __name__ == "__main__":
    app.run(debug=True)