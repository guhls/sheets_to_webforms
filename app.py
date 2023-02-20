from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import datetime as dt
from auth.google.creds import get_creds
from googleapiclient.discovery import build
from unidecode import unidecode


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

        sheet = db.session.execute(db.select(Sheet).filter_by(id=sheet_id)).scalar()

        service_gsheets = build("sheets", "v4", credentials=get_creds())
        response = (
            service_gsheets.spreadsheets()
            .values()
            .get(spreadsheetId=sheet.url_sheet, range=range)
            .execute()
        )

        columns = response["values"][0]

        dynamic_table = type(
            name,
            (db.Model,),
            {"__tablename__": name, "id": db.Column(db.Integer, primary_key=True)},
        )
        for column in columns:
            setattr(dynamic_table, column, db.Column(db.String(50)))

        db.create_all()

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


@app.route("/table/<int:sheet_id>/add/gsheet/<table_name>", methods=["GET", "POST"])
def add_gsheet(sheet_id, table_name):
    table = db.session.execute(db.select(Table).filter_by(sheet_id=sheet_id)).scalar()

    range = table.range

    new_range = []
    for i, value in enumerate(range.split("!")[1].split(":")):
        if i == 0:
            range_int = int(value[1]) + 1
            new_range.append(f"{value[0]}{range_int}")
        else:
            new_range.append(value[0])

    updated_range = f"{table_name}!{':'.join(new_range)}"

    sheet = db.session.execute(db.select(Sheet).filter_by(id=sheet_id)).scalar()

    service = build("sheets", "v4", credentials=get_creds())
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet.url_sheet, range=updated_range)
    ).execute()["values"]

    if request.method == "POST":
        values_in_sheet = result
        values_to_append = [[request.form[column] for column in request.form]]

        values_in_sheet.extend(values_to_append)

        data_ascii = [[unidecode(cell) for cell in row] for row in values_in_sheet]

        service.spreadsheets().values().update(
            spreadsheetId=sheet.url_sheet,
            range=updated_range,
            valueInputOption="USER_ENTERED",
            body={"values": data_ascii},
        ).execute()

        return redirect(f"/table/{sheet_id}/add/gsheet/{table_name}")

    columns_tuple = db.session.execute(
        text(f"PRAGMA table_info('{table_name}')")
    ).fetchall()
    columns = [column[1].strip() for column in columns_tuple[1:]]

    return render_template(
        "pages/gsheet_form.html",
        columns=columns,
        table_name=table_name,
        sheet_id=sheet_id,
        last_result=result[-1],
        columns_type={
            "Data da Aula": "date",
            "Local da aula": "options",
            "Assunto apresentado na aula": "textarea",
            "Desenvolvimento - Metodologia / Estratégia": "textarea",
            "Avaliação de aula": "textarea",
        },
        option_data={
            "Local da aula": set(
                [row[2] for row in result if row]
                + ["Sala de aula", "Sala de leitura", "Sala digital"]
            )
        },
    )


if __name__ == "__main__":
    app.run(debug=True)
