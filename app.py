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
    page = request.args.get('page', 1, type=int)
    per_page = 10
    connection = getCursor()
    connection.execute('''SELECT job_id,first_name,family_name,customer,job_date,completed FROM job j join customer c on
                           j.customer = c.customer_id where completed=0;''')
    jobList = connection.fetchall()

    format_job_list = []

    for job_info in jobList:
        # add part names of the job
        connection.execute(
            f'''select part_name from job_part jp  left join part p on jp.part_id = p.part_id where jp.job_id = {job_info[0]}''')
        part_names = connection.fetchall()
        part_name = ''
        for part in part_names:
            part_name += str(part[0]) + ','
        # add service names of the job
        connection.execute(
            f'''select service_name from job_service js  left join service s on js.service_id = s.service_id where js.job_id = {job_info[0]}''')
        service_names = connection.fetchall()
        service_name = ''
        for service in service_names:
            service_name += str(service[0]) + ','
        # format job item
        job = {
            'job_id': job_info[0],
            'first_name': job_info[1],
            'family_name': job_info[2],
            'customer_id': job_info[3],
            'job_date': job_info[4],
            'completed': job_info[5],
            'part_name': part_name,
            'service_name': service_name
        }
        format_job_list.append(job)
    return render_template("currentjoblist.html", jobs=format_job_list, services=get_service_list(),
                           parts=get_part_list())


@app.get("/services")
def get_services():
    result = get_service_list()
    return render_template("service.html", services=result)


@app.post("/addJobServicePart")
def add_service_part():
    data = request.form
    service_id = data.get("service_id")
    service_quantity = data.get("service_quantity")
    part_id = data.get("part_id")
    part_quantity = data.get("part_quantity")
    job_id = data.get("job_id")
    part_insert_sql = '''INSERT INTO job_part (job_id, part_id,qty) VALUES (%s, %s,%s)'''
    service_insert_sql = '''INSERT INTO job_service (job_id, service_id,qty) VALUES (%s, %s,%s)'''
    connect = getCursor()

    connect.execute(part_insert_sql, (job_id, part_id, part_quantity))
    connect.execute(service_insert_sql, (job_id, service_id, service_quantity))
    return redirect(url_for('currentjobs'))


def get_service_list():
    connect = getCursor()
    # build sql
    sql = "SELECT service_id,service_name,cost FROM service"

    # get results
    connect.execute(sql)
    services = connect.fetchall()

    # format results
    result = [{'service_id': row[0], 'service_name': row[1], 'cost': row[2]} for row in services]
    return result


@app.get("/parts")
def get_parts():
    result = get_part_list()
    return render_template("part.html", parts=result)


def get_part_list():
    connect = getCursor()
    # build sql
    sql = "SELECT part_id,part_name,cost FROM part"

    # get results
    connect.execute(sql)
    services = connect.fetchall()

    # format results
    result = [{'part_id': row[0], 'part_name': row[1], 'cost': row[2]} for row in services]
    return result


@app.post("/addCustomer")
def add_customer():
    data = request.form
    email = data.get('email')
    first_name = data.get('firstName')
    family_name = data.get('familyName')
    phone = data.get('phone')

    if not email or not family_name or not phone:
        return jsonify({'error': 'Missing required fields'}), 400

    # insert into db
    try:
        connection = getCursor()
        connection.execute('INSERT INTO customer (email, first_name, family_name, phone) VALUES (%s, %s, %s, %s)',
                           (email, first_name, family_name, phone))

    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 400

    return redirect(url_for('get_customers'))


@app.post("/addPart")
def add_part():
    data = request.form
    part_name = data.get('partName')
    cost = data.get('cost')

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

    return redirect(url_for('get_parts'))


@app.post('/addService')
def add_service():
    data = request.form
    service_name = data.get('serviceName')
    cost = data.get('cost')

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

    return redirect(url_for('get_services'))


@app.get('/customers')
def get_customers():
    # get request param
    name = request.args.get('name')

    connect = getCursor()
    # build sql
    sql = "SELECT customer_id,first_name,family_name,email,phone FROM customer"
    orderBy = " order by family_name,first_name"
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
    result = [{'customer_id': row[0], 'first_name': row[1], 'family_name': row[2], 'email': row[3], 'phone': row[4]} for
              row in customers]
    return render_template("customers.html", customers=result, services=get_service_list())


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
        SELECT j.job_id, j.customer, j.job_date, j.total_cost, c.phone, c.first_name, c.family_name ,c.email
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
    unpaid_jobs_list = [
        {'job_id': row[0], 'customer': row[1], 'job_date': row[2], 'total_cost': row[3], 'phone': row[4],
         'first_name': row[5], 'family_name': row[6], 'email': row[7]} for row in unpaid_jobs]

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
    return render_template("unpaidBills.html", unpaid_jobs=unpaid_jobs_list, total_count=total_count,
                           total_pages=total_pages, page=page)


@app.route('/pay_job', methods=['POST'])
def pay_job():
    # Get job_id from the request parameters
    job_id = request.form.get('job_id')

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

    return redirect(url_for('unpaid_jobs'))


@app.route('/billing_history', methods=['GET'])
def billing_history():
    # Build the SQL query to gwet billing history
    query = """
    SELECT 
        c.family_name,
        c.first_name,
        c.phone,
        c.email,
        j.job_date,
        j.total_cost
    FROM 
        job j
    JOIN 
        customer c ON j.customer = c.customer_id
    ORDER BY 
        c.family_name, c.first_name, j.job_date DESC
    """

    connect = getCursor()

    # Execute the query to get billing history
    connect.execute(query)
    billing_history = connect.fetchall()

    # Group billing history by customer
    grouped_billing_history = {}
    for row in billing_history:
        customer_key = (row[0], row[1], row[2], row[3])  # Using family_name, first_name, phone ,email as key
        if customer_key not in grouped_billing_history:
            grouped_billing_history[customer_key] = []
            # Calculate overdue status
        job_date = datetime.strptime(str(row[4]), '%Y-%m-%d')
        days_since_job = (datetime.now() - job_date).days
        overdue = days_since_job > 14
        grouped_billing_history[customer_key].append({'job_date': row[4], 'total_cost': row[5], 'overdue': overdue})

    # Prepare response
    response = []
    for customer_key, bills in grouped_billing_history.items():
        # sorted job_date
        sorted_bills = sorted(bills, key=lambda x: datetime.strptime(str(x['job_date']), '%Y-%m-%d'))
        customer_data = {
            'family_name': customer_key[0],
            'first_name': customer_key[1],
            'phone': customer_key[2],
            'email': customer_key[3],
            'bills': sorted_bills
        }
        response.append(customer_data)

    return render_template("billsHistory.html", history_data=response)


@app.post('/complete_job')
def complete_job():
    job_id = int(request.form.get('job_id'))
    # calculate total cost
    # get all parts and services
    service_query_sql = '''select s.service_id,cost,qty from job_service js  left join
                            job j on js.job_id = j.job_id left join service s on js.service_id = s.service_id
                            where j.job_id  = {}'''.format(job_id)
    part_query_sql = '''select p.part_id,cost,qty from job_part jp  left join
                            job j on jp.job_id = j.job_id left join part p on jp.part_id = p.part_id
                            where j.job_id = {}'''.format(job_id)
    connect = getCursor()
    connect.execute(service_query_sql)
    services = connect.fetchall()

    connect.execute(part_query_sql)
    parts = connect.fetchall()

    total_cost = Decimal(0)
    # through the parts list and calculate the total cost
    for service in services:
        service_cost = service[1] * Decimal(service[2])
        total_cost += service_cost

    # through the parts list and calculate the total cost
    for part in parts:
        part_cost = part[1] * Decimal(part[2])
        total_cost += part_cost

    updateSql = '''update job set completed = 1 ,total_cost = %s where job_id = %s'''
    connect.execute(updateSql, (total_cost, job_id))
    return redirect(url_for('currentjobs'))

@app.route('/admin_page')
def admin_page():
    return render_template('base.html')

if __name__ == '__main__':
    app.run(port=8111, host="127.0.0.1", debug=True)
