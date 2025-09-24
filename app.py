from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
db = SQLAlchemy(app)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post = db.Column(db.String(200))

with app.app_context():
    db.create_all()

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



if __name__ == "__main__":
    app.run(debug=True)