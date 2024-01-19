from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
import mysql.connector
import connect

app = Flask(__name__)

dbconn = None
connection = None


def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(user=connect.dbuser,
                                         port=connect.dbport,
                                         password=connect.dbpass, host=connect.dbhost,
                                         database=connect.dbname, autocommit=True)
    dbconn = connection.cursor()
    return dbconn


@app.route("/")
def home():
    return redirect("/currentjobs")


@app.route("/currentjobs")
def currentjobs():
    # assert request.json, '参数不为空'
    connection = getCursor()
    connection.execute("SELECT job_id,customer,job_date FROM job where completed=0;")
    jobList = connection.fetchall()
    return render_template("currentjoblist.html", job_list=jobList)


if __name__ == '__main__':
    app.run(port=8111, host="127.0.0.1", debug=True)
