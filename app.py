from flask import Flask, render_template, request
import pandas as pd

import sqlite3 as SQL

# from werkzeug import secure_filename
from werkzeug.utils import secure_filename, send_file


app = Flask(__name__)

ALLOWED_EXTENSIONS = set(["csv"])


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def upload_file():
    return render_template("index.html")


@app.route("/uploader", methods=["GET", "POST"])
def upload_file1():
    if request.method == "POST":
        files = request.files.getlist("file")

        if len(files) > 1:
            error = 'You are only allowed to upload one file.'
            return render_template("index.html", error = error)
        
        else:
            for file in files:
                if file and allowed_file(file.filename):
                    file_name = secure_filename(file.filename)                

                    # Initialise the connection to the db and make a cursor to execute queries
                    db = SQL.connect('Use_Case.db')
                    
                    # Initialise cursor
                    cursor = db.cursor()
                    
                    # Run pragma files for efficient access to dB
                    with open('SQL QUERIES/pragma runs test.sql', 'r') as sql_file:
                        sql_script = sql_file.read()

                    cursor.executescript(sql_script)
                    db.commit()

                    #Read csv
                    Use_Case = pd.read_csv(file)

                    #Load file in sql dB
                    Use_Case.to_sql("Use_Case",db,if_exists="replace",index=False)

                    # Run the procedures to get the related company structure data
                    with open('SQL QUERIES/Use_Case_Procedure_1.sql', 'r') as sql_file:
                        sql_script = sql_file.read()

                    cursor.executescript(sql_script)
                    db.commit()

                    with open('SQL QUERIES/Use_Case_Procedure_2.sql', 'r') as sql_file:
                        sql_script = sql_file.read()

                    output = pd.read_sql(sql_script,db)
                    db.commit()

                    #Drop temporary tables from dB
                    sql_script = '''
                    drop table if exists Use_Case;
                    drop table if exists Use_Case_Merge;'''

                    cursor.executescript(sql_script)
                    db.commit()

                    #Close connection to db
                    db.close()

                    # Initiate a writer for excel file
                    writer = pd.ExcelWriter("output.xlsx", engine = 'xlsxwriter')


                    # Saving dataframe to excel file
                    output.to_excel(writer,sheet_name="Sheet1",index=False)
                    
                    # Steps to apply filter on excel file
                    wb = writer.book
                    ws = writer.sheets['Sheet1']
                    
                    (max_row, max_col) = output.shape

                    ws.autofilter(0, 0, max_row, max_col - 1)

                    ws.filter_column(max_col - 1, "Exclude_Or_Not == 0")

                    # Steps to hide not relevant rows
                    for row_num in output.index[(output["Exclude_Or_Not"] != 0)].tolist():
                        ws.set_row(row_num + 1, options={"hidden": True})

                    # close the excel write

                    writer.close()                 

                    

        response = send_file("output.xlsx",environ=request.environ)
        

        return response




if __name__ == "__main__":
    app.run(host="0.0.0.0")
