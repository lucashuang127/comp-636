# comp-636

# Report

## Web Application Structure:

The web application follows a typical MVC (Model-View-Controller) structure, with routes handling requests, functions processing data, and templates rendering the views.

    
### Routes & Functions:

- **Routes**:
  - `/currentjobs`: Obtain the uncompleted job, including the name of the service and part
    - `params`
    - `method`:get
    - `response`: currentjoblist.html
  - `/services`:Get all the services
    - `params`:
    - `method`:get
    - `response`: service.html
  - `/addJobServicePart`:Add parts and services to the job, along with the corresponding quantities
    - `params`: service_id、service_quantity、part_id、part_quantity、job_id
    - `method`:post
    - `response`: redirect /currentjobs
  - `/parts`:Get all the parts
    - `params`:
    - `method`:get
    - `response`: part.html
  - `/addCustomer`:Add a customer and include all the information
    - `params`:email、firstName、familyName、phone
    - `method`:post
    - `response`: redirect /customers
  - `/addPart`:  Add a part
    - `params`:partName、cost
    - `method`:post
    - `response`: redirect /parts
  - `/addService`: Add a service
    - `params`:serviceName、cost
    - `method`:post
    - `response`: redirect /services
  - `/customers`: Get all customers
    - `params`:name
    - `method`:get
    - `response`: customers.html
  - `/addScheduleJob`: add a job
    - `params`:customerId、date
    - `method`:post
    - `response`: redirect /unpaid_jobs
  - `/unpaid_jobs`: get all unpaid jobs 
    - `params`:page、customer_name
    - `method`:get
    - `response`: unpaidBills.html
  - `/pay_job`: paid the job
    - `params`:job_id
    - `method`:POST
    - `response`: redirect /unpaid_jobs
  - `/billing_history`: Billing History & Overdue Bills
    - `params`:job_id
    - `method`:get
    - `response`: billsHistory.html
  - `/complete_job`: complete the job and calculate total cost
    - `params`:job_id
    - `method`:get
    - `response`: redirect /currentjobs
- **Functions**:
  - Functions defined in `app.py` handle the logic associated with each route.
  - These functions interact with the database, process data, and pass it to the templates for rendering.

### Templates:

- HTML templates are stored in the `templates` directory.
- Each template corresponds to a specific route or functionality.
- Templates are rendered with dynamic data passed from the route functions.
- Templates utilize Jinja templating for dynamic content rendering.
- `unpaidBills.html`:There is a button to add a job, and all unpaid job information is displayed. Each column has a payment button.
- `base2.html` : Technician base page
- `base.html` : admin base page
- `billsHistory.html`:Billing History & Overdue Bills
- `currentjoblist.html` : Display all job information, including service name and part name
- `customers.html` : Display all customer information , including add customer button
- `part.html` : Display all part information, including add part button
- `service.html`: Display all service information, including add service button

## Design Decisions:

- **Template Structure**:
  - Each page has its own template for clarity and separation of concerns.
  - Shared components like navigation bars and footers are included using template inheritance.

- **Route Design**:
  - Routes are designed to follow RESTful principles for clear and predictable behavior.
  - GET requests are used for retrieving data or rendering views, while POST requests are used for submitting form data.

- **Data Passing**:
  - Data is passed between routes and templates using context variables.
  - Forms are used to collect user input and send it to the server for processing.

## Database Questions:

1. **Creating the Job Table**:
   - SQL Statement:
     ```sql
     CREATE TABLE IF NOT EXISTS job
      (
       job_id INT auto_increment PRIMARY KEY NOT NULL,
       job_date date NOT NULL,
       customer int NOT NULL,
       total_cost decimal(6,2) default null,
       completed tinyint default 0,
       paid tinyint default 0,
         
       FOREIGN KEY (customer) REFERENCES customer(customer_id)
       ON UPDATE CASCADE
     );   
     ```

2. **Relationship between Customer and Job Tables**:
   - SQL Code:
     ```sql
     FOREIGN KEY (customer) REFERENCES customer(customer_id)
     ```

3. **Which lines of SQL code insert details into the parts table?**
   - SQL Code:
     ```sql
     INSERT INTO part (`part_name`, `cost`) VALUES ('Windscreen', '560.65');
     INSERT INTO part (`part_name`, `cost`) VALUES ('Headlight', '35.65');
     INSERT INTO part (`part_name`, `cost`) VALUES ('Wiper blade', '12.43');
     INSERT INTO part (`part_name`, `cost`) VALUES ('Left fender', '260.76');
     INSERT INTO part (`part_name`, `cost`) VALUES ('Right fender', '260.76');
     INSERT INTO part (`part_name`, `cost`) VALUES ('Tail light', '120.54');
     INSERT INTO part (`part_name`, `cost`) VALUES ('Hub Cap', '22.89');
     ```

4. **Suppose that as part of an audit trail, the time and date a service or part was added to a job needed to be recorded, what fields/columns would you need to add to which tables? Provide the table name, new column name and the data type.**
   - Table: `job_service` and `job_part`
   - New Columns:
     - `added_date_time TIMESTAMP`

5. **Suppose logins were implemented. Why is it important for technicians and the office
administrator to access different routes?**
   - Technicians and administrators have different roles and responsibilities.
   - Separate routes ensure that technicians can only access functionalities relevant to their tasks, such as viewing job details(total_cost) or updating job paid statuses.
   - Allowing everyone access to all facilities could lead to unauthorized actions, such as modifying customer data or service information.

