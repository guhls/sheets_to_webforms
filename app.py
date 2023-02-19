from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import datetime as dt


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
db = SQLAlchemy(app)


class Sheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String)
    url_sheet = db.Column(db.String, unique=True, nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    updated = db.Column(db.DateTime, onupdate=dt.datetime.utcnow)


class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    range = db.Column(db.String, nullable=False)
    sheet_id = db.Column(db.ForeignKey(Sheet.id))


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    sheets = db.session.execute(db.select(Sheet).order_by(Sheet.created)).scalars()

    return render_template(
        "pages/dashboard_page.html",
        dash_infos=sheets,
        dash_name="Planilhas",
        dash_type="sheets",
    )


@app.route("/tables/<int:sheet_id>")
def tables(sheet_id):
    sheet_name = (
        db.session.execute(db.select(Sheet).filter_by(id=sheet_id)).scalar().name
    )

    tables = db.session.execute(db.select(Table).filter_by(sheet_id=sheet_id)).scalars()

    return render_template(
        "pages/dashboard_page.html",
        dash_infos=tables,
        dash_name="Tabelas",
        dash_type="tables",
        sheet_name=sheet_name,
        sheet_id=sheet_id,
    )


@app.route("/sheet/create/", methods=["GET", "POST"])
def create_sheet():
    if request.method == "POST":
        name = request.form["nameInput"]
        description = request.form["descriptionInput"]
        url_sheet = request.form["urlSheetInput"]

        sheet = Sheet(name=name, description=description, url_sheet=url_sheet)
        db.session.add(sheet)

        db.session.commit()

        return redirect("/")

    return render_template("pages/sheet_form.html")


@app.route("/sheet/delete/<int:sheet_id>", methods=["GET", "POST"])
def delete_sheet(sheet_id):
    if request.method == "POST":
        sheet = db.get_or_404(Sheet, sheet_id)
        tables = db.session.execute(
            db.select(Table).filter_by(sheet_id=sheet_id)
        ).scalars()
        for table in tables:
            db.session.delete(table)
        db.session.delete(sheet)
        db.session.commit()

    return redirect("/")


@app.route("/sheet/edit/<int:sheet_id>", methods=["GET", "POST"])
def edit_sheet(sheet_id):
    sheet = db.get_or_404(Sheet, sheet_id)
    if request.method == "POST":
        sheet.name = request.form["nameInput"]
        sheet.description = request.form["descriptionInput"]
        sheet.url_sheet = request.form["urlSheetInput"]

        db.session.commit()
        return redirect("/")
    return render_template("pages/sheet_edit.html", sheet=sheet)


@app.route("/table/create/<int:sheet_id>", methods=["GET", "POST"])
def create_table(sheet_id):
    if request.method == "POST":
        name = request.form["nameInput"]
        range = request.form["rangeInput"]

        table = Table(name=name, range=range, sheet_id=sheet_id)
        db.session.add(table)
        db.session.commit()

        return redirect(f"/tables/{sheet_id}")

    return render_template("pages/table_form.html", sheet_id=sheet_id)


@app.route("/table/delete/<int:table_id>", methods=["POST"])
def delete_table(table_id):
    if request.method == "POST":
        table = db.get_or_404(Table, table_id)
        sheet_id = table.sheet_id
        db.session.delete(table)
        db.session.commit()

    return redirect(f"/tables/{sheet_id}")


@app.route("/table/edit/<int:table_id>", methods=["GET", "POST"])
def edit_table(table_id):
    table = db.get_or_404(Table, table_id)
    if request.method == "POST":
        table.name = request.form["nameInput"]
        table.range = request.form["rangeInput"]

        db.session.commit()
        return redirect(f"/tables/{table.sheet_id}")
    return render_template("pages/table_edit.html", table=table)


if __name__ == "__main__":
    app.run(debug=True)
