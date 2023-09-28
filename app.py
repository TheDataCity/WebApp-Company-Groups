from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, send_file
from pathlib import Path
import os
import pandas as pd
import sentry_sdk
import sqlite3
from werkzeug.utils import secure_filename

load_dotenv(override=True)
if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        environment=os.getenv('APP_ENV'),
        traces_sample_rate=1.0
    )

ALLOWED_EXTENSIONS = {"xlsx"}
DB_NAME = 'sqlite/use_case.db'
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'

Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def execute_sql_file(file_path, conn):
    with open(file_path, 'r') as sql_file:
        sql_script = sql_file.read()
    conn.executescript(sql_script)
    conn.commit()


@app.route("/")
def index():
    return render_template("index.html")


def save_output_to_excel(output, writer):
    output.to_excel(writer, sheet_name="Sheet1", index=False)
    work_sheet = writer.sheets['Sheet1']

    (max_row, max_col) = output.shape
    work_sheet.autofilter(0, 0, max_row, max_col - 1)
    work_sheet.filter_column(max_col - 1, "Exclude_Or_Not == 0")

    for row_num in output.index[(output["Exclude_Or_Not"] != 0)].tolist():
        work_sheet.set_row(row_num + 1, options={"hidden": True})

    work_sheet.set_column(first_col=0, last_col=50, width=20)
    work_sheet.set_column(2, 3, options={"hidden": True})
    work_sheet.set_column(6, 9, options={"hidden": True})
    work_sheet.set_column(11, 40, options={"hidden": True})

    writer.close()


@app.route("/uploader", methods=["POST"])
def upload():
    files = request.files.getlist("file")
    if len(files) != 1:
        return render_template("index.html", error='You are only allowed to upload one file.')

    file = files[0]
    print(file)
    if file and allowed_file(file.filename):

        file.filename = secure_filename(file.filename)

        use_case = pd.read_excel(
            file,
            sheet_name="Companies as columns (basic)",
            engine="openpyxl",
            dtype={"Companynumber": str, "SICs": str},
        )

        with sqlite3.connect(DB_NAME) as conn:
            execute_sql_file('sql-queries/pragma-runs-test.sql', conn)
            use_case.to_sql("Use_Case", conn, if_exists="replace", index=False)
            execute_sql_file('sql-queries/use_case_procedure_1.sql', conn)

            output_query = open('sql-queries/use_case_procedure_2.sql', 'r', encoding='utf-8').read()
            output = pd.read_sql(output_query, conn)

            drop_query = '''
            drop table if exists Use_Case;
            drop table if exists Use_Case_Merge;'''
            conn.executescript(drop_query)
            conn.commit()

        output_filename = f"{OUTPUT_FOLDER}/output-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.xlsx"
        writer = pd.ExcelWriter(output_filename, engine='xlsxwriter')  #pylint: disable=abstract-class-instantiated
        save_output_to_excel(output, writer)

    return send_file(output_filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
