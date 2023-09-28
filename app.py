from flask import Flask, render_template, request, send_file
import pandas as pd
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)

ALLOWED_EXTENSIONS = {"xlsx"}
DB_NAME = 'sqlite/Use_Case.db'
UPLOAD_FOLDER = 'uploads'


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
    wb = writer.book
    ws = writer.sheets['Sheet1']

    (max_row, max_col) = output.shape
    ws.autofilter(0, 0, max_row, max_col - 1)
    ws.filter_column(max_col - 1, "Exclude_Or_Not == 0")

    for row_num in output.index[(output["Exclude_Or_Not"] != 0)].tolist():
        ws.set_row(row_num + 1, options={"hidden": True})

    ws.set_column(first_col=0, last_col=50, width=20)
    ws.set_column(2, 3, options={"hidden": True})
    ws.set_column(6, 9, options={"hidden": True})
    ws.set_column(11, 40, options={"hidden": True})

    writer.close()


@app.route("/uploader", methods=["POST"])
def upload():
    files = request.files.getlist("file")
    if len(files) != 1:
        return render_template("index.html", error='You are only allowed to upload one file.')

    file = files[0]
    if file and allowed_file(file.filename):
        file_name = secure_filename(file.filename)

        use_case = pd.read_excel(
            file,
            sheet_name="Companies as columns (basic)",
            engine="openpyxl",
            dtype={"Companynumber": str, "SICs": str},
        )

        with sqlite3.connect(DB_NAME) as conn:
            execute_sql_file('SQL QUERIES/pragma runs test.sql', conn)
            use_case.to_sql("Use_Case", conn, if_exists="replace", index=False)
            execute_sql_file('SQL QUERIES/Use_Case_Procedure_1.sql', conn)

            output_query = open('SQL QUERIES/Use_Case_Procedure_2.sql', 'r').read()
            output = pd.read_sql(output_query, conn)

            drop_query = '''
            drop table if exists Use_Case;
            drop table if exists Use_Case_Merge;'''
            conn.executescript(drop_query)
            conn.commit()

        writer = pd.ExcelWriter("output/output.xlsx", engine='xlsxwriter')
        save_output_to_excel(output, writer)

    return send_file("output.xlsx", as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
