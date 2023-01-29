from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import datetime as dt


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
db = SQLAlchemy(app)


class Sheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    url_sheet = db.Column(db.String, unique=True, nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    updated = db.Column(db.DateTime, onupdate=dt.datetime.utcnow)


class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    range = db.Column(db.String, nullable=False)
    sheet_id = db.Column(db.ForeignKey(Sheet.id), primary_key=True)


with app.app_context():
    db.create_all()

    # db.session.add(Sheet(name="test_name", url_sheet="test_url"))
    # db.session.commit()


@app.route("/")
def home():
    sheets = db.session.execute(db.select(Sheet).order_by(Sheet.created)).scalars()
    return render_template("home.html", sheets=sheets)


if __name__ == "__main__":
    app.run(debug=True)
