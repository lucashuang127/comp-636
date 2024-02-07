from datetime import datetime

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect, jsonify, url_for
from decimal import Decimal
import mysql.connector
import connect
import sqlite3
import math

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
    connection = getCursor()
    connection.execute("SELECT job_id,customer,job_date FROM job where completed=0;")
    jobList = connection.fetchall()
    return render_template("currentjoblist.html", job_list=jobList)


@app.post("/addCustomer")
def add_customer():
    data = request.json
    email = data['email']
    first_name = data['first_name']
    family_name = data['family_name']
    phone = data['phone']

    if not email or not first_name or not family_name or not phone:
        return jsonify({'error': 'Missing required fields'}), 400

    # insert into db
    try:
        connection = getCursor()
        connection.execute('INSERT INTO customer (email, first_name, family_name, phone) VALUES (%s, %s, %s, %s)',
                           (email, first_name, family_name, phone))

    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 400

    return redirect(url_for('customer_list'))


@app.post("/addPart")
def add_part():
    data = request.json
    part_name = data['part_name']
    cost = data['cost']

    # validate params
    if not part_name or not cost:
        return jsonify({'error': 'Missing required fields'}), 400

    #
    try:
        cost = Decimal(cost)
    except ValueError:
        return jsonify({'error': 'Invalid cost format'}), 400

    try:
        connection = getCursor()
        connection.execute('INSERT INTO part (part_name, cost) VALUES (%s, %s)', (part_name, cost))
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Part already exists'}), 400

    return jsonify({'success': True}), 200


@app.post('/addService')
def add_service():
    data = request.json
    service_name = data['service_name']
    cost = data['cost']

    # validate params
    if not service_name or not cost:
        return jsonify({'error': 'Missing required fields'}), 400

    # change to decimal
    try:
        cost = Decimal(cost)
    except ValueError:
        return jsonify({'error': 'Invalid cost format'}), 400

    # insert into db
    try:
        connection = getCursor()
        connection.execute('INSERT INTO service (service_name, cost) VALUES (%s, %s)', (service_name, cost))
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Service already exists'}), 400

    return jsonify({'success': True}), 200


@app.get('/customers')
def get_customers():
    # get request param
    name = request.args.get('name')

    connect = getCursor()
    # build sql
    sql = "SELECT * FROM customer"
    orderBy = "order by family_name,first_name"
    if name:
        sql += " WHERE first_name LIKE %s OR family_name LIKE %s"
        query_str = f"%{name}%"
        sql += orderBy
        connect.execute(sql, (query_str, query_str))
    else:
        sql += orderBy
        connect.execute(sql)

    # get results
    customers = connect.fetchall()

    # format results
    result = [{'id': row[0], 'first_name': row[1], 'family_name': row[2]} for row in customers]
    return jsonify(result)


@app.post('/addScheduleJob')
def schedule_job():
    data = request.json
    #
    customer = data['customerId']
    date_str = data['date']

    # validate params
    if not customer or not date_str:
        return jsonify({'error': 'Missing required fields'}), 400

    # Conversion type
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format, please use YYYY-MM-DD'}), 400

    # validate date (The date must be today or in the future)
    if date < datetime.now():
        return jsonify({'error': 'Date must be today or in the future'}), 400

    connect = getCursor()
    # insert into db
    connect.execute('INSERT INTO job (customer, job_date) VALUES (%s, %s)', (customer, date_str))

    return jsonify({'success': True}), 200


@app.route('/unpaid_jobs', methods=['GET'])
def unpaid_jobs():
    # Get query parameters
    customer_name = request.args.get('customer_name')
    page = int(request.args.get('page', 1))  # Default to page 1
    page_size = int(request.args.get('page_size', 10))  # Default to 10 records per page

    connect = getCursor()
    # Calculate the offset
    offset = (page - 1) * page_size

    # Build the SQL query statement to get unpaid jobs
    unpaid_jobs_query = '''
        SELECT j.job_id, j.customer, j.job_date, j.total_cost, c.phone, c.first_name, c.family_name
        FROM job j
        JOIN customer c ON j.customer = c.customer_id
        WHERE j.paid = 0
    '''

    if customer_name:
        unpaid_jobs_query += " AND (c.first_name LIKE '%{}%' OR c.family_name LIKE '%{}%')".format(customer_name,
                                                                                                   customer_name)

    unpaid_jobs_query += " LIMIT {} OFFSET {}".format(page_size, offset)

    # Execute the unpaid jobs query
    connect.execute(unpaid_jobs_query)
    unpaid_jobs = connect.fetchall()

    # Construct the JSON response for unpaid jobs
    unpaid_jobs_list = [{'id': row[0], 'customer': row[1], 'job_date': row[2], 'total_cost': row[3], 'phone': row[4],
                         'first_name': row[5], 'family_name': row[6]} for row in unpaid_jobs]

    # Build the SQL query statement to get the total count of unpaid jobs
    total_count_query = "SELECT COUNT(*) FROM job j JOIN customer c ON j.customer = c.customer_id WHERE j.paid = 0"

    if customer_name:
        total_count_query += " AND (c.first_name LIKE '%{}%' OR c.family_name LIKE '%{}%')".format(customer_name,
                                                                                                   customer_name)

    # Execute the total count query
    connect.execute(total_count_query)
    total_count = connect.fetchall()[0][0]

    # Calculate the total number of pages
    total_pages = math.ceil(total_count / page_size)

    return jsonify({'unpaid_jobs': unpaid_jobs_list, 'total_count': total_count, 'total_pages': total_pages}), 200


@app.route('/pay_job', methods=['POST'])
def pay_job():
    # Get job_id from the request parameters
    job_id = request.json.get('job_id')

    connect = getCursor()
    # Validate job_id
    if not job_id:
        return jsonify({'error': 'job_id is required'}), 400

    # Check if the job exists and is unpaid
    check_query = "SELECT job_id FROM job WHERE job_id = {} AND paid = 0".format(job_id)
    connect.execute(check_query)
    job = connect.fetchone()
    if not job:
        return jsonify({'error': 'Invalid or already paid job_id'}), 400

    # Build the SQL query statement to update job status to paid
    update_query = "UPDATE job SET paid = 1 WHERE job_id = {}".format(job_id)

    # Execute the update query
    connect.execute(update_query)

    return jsonify({'message': 'Job payment successful'}), 200


if __name__ == '__main__':
    app.run(port=8111, host="127.0.0.1", debug=True)




