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
    sheet_id = db.Column(db.ForeignKey(Sheet.id), primary_key=True)


with app.app_context():
    db.create_all()

    # sheets = [
    #     {
    #         "id": 1,
    #         "name": "Planejamento Letivo 2023",
    #         "description": "Organização para o planejamento letivo de 2023",
    #         "url_sheet": "https://google.sheets/1/",
    #     },
    #     {
    #         "id": 2,
    #         "name": "Planejamento Letivo 2022",
    #         "description": "Já terminado!",
    #         "url_sheet": "https://google.sheets/2/",
    #     },
    # ]

    # tables = [
    #     {
    #         "id": 1,
    #         "name": "Matemática",
    #         "range": "A1:M",
    #         "sheet_id": 1,
    #     },
    #     {
    #         "id": 2,
    #         "name": "Artes",
    #         "range": "A1:M",
    #         "sheet_id": 1,
    #     },
    # ]

    # for sheet in sheets:
    #     db.session.add(
    #         Sheet(
    #             id=sheet["id"],
    #             name=sheet["name"],
    #             description=sheet["description"],
    #             url_sheet=sheet["url_sheet"],
    #         )
    #     )

    # db.session.commit()

    # for table in tables:
    #     db.session.add(
    #         Table(
    #             id=table["id"],
    #             name=table["name"],
    #             range=table["range"],
    #             sheet_id=table["sheet_id"],
    #         )
    #     )

    # db.session.commit()


@app.route("/")
def home():
    sheets = db.session.execute(db.select(Sheet).order_by(Sheet.created)).scalars()

    return render_template(
        "pages/dashboard_page.html",
        dash_infos=sheets,
        dash_name="Planilhas",
        dash_type="sheets",
    )


@app.route("/tables/")
def tables():
    sheet_id = request.args.get("sheet_id", "")
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
    )


@app.route("/sheet/create/", methods=["GET", "POST"])
def create_sheet():
    if request.method == "POST":
        name = request.form["nameInput"]
        description = request.form["descriptionInput"]
        url_sheet = request.form["urlSheetInput"]

        sheet = db.session.add(
            Sheet(name=name, description=description, url_sheet=url_sheet)
        )

        db.session.commit()

        return redirect("/")

    return render_template("pages/form.html")


if __name__ == "__main__":
    app.run(debug=True)
