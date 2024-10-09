from flask import Flask, flash, render_template, request, redirect, jsonify, url_for
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
import jwt
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'xyzabc'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Abhinaya@2004'
app.config['MYSQL_DB'] = 'student'

def get_db_connection():
    return mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )

def generate_token(username):
    payload = {
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def jwt_token_required(f):
    def decorator(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return redirect(url_for('index'))
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.username = data['username']
        except jwt.ExpiredSignatureError:
            return redirect(url_for('index'))
        except jwt.InvalidTokenError:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorator.__name__ = f.__name__
    return decorator

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/faculty')
def faculty():
    return render_template('login.html')

@app.route('/student')
def student():
    return render_template('login1.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        db_connection = get_db_connection()
        try:
            with db_connection.cursor(dictionary=True) as cursor:
                cursor.execute('SELECT * FROM user WHERE username = %s AND password = %s', (username, password))
                user = cursor.fetchone()
                if user:
                    token = generate_token(username)
                    response = redirect(url_for('dashboard'))
                    response.set_cookie('token', token)
                    return response
                else:
                    message = 'Please enter correct email / password!'
        except Error as e:
            print(f"Error: {e}")
        finally:
            db_connection.close()
    return render_template('login.html', message=message)


@app.route('/login1', methods=['GET', 'POST'])
def login1():
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        db_connection = get_db_connection()
        try:
            with db_connection.cursor(dictionary=True) as cursor:
                cursor.execute('SELECT * FROM user WHERE username = %s AND password = %s', (username, password))
                user = cursor.fetchone()
                if user:
                    token = generate_token(username)
                    response = redirect(url_for('Student_dashboard'))
                    response.set_cookie('token', token)
                    cursor.execute('SELECT * FROM student WHERE rollno = %s', (username,))
                    details = cursor.fetchall()
                    return render_template('student.html', details=details)
                else:
                    message = 'Please enter correct email / password!'
        except Error as e:
            print(f"Error: {e}")
        finally:
            db_connection.close()
    return render_template('login1.html', message=message)


@app.route('/dashboard')
@jwt_token_required
def dashboard():
    return render_template('home.html')

@app.route('/student_dashboard')
@jwt_token_required
def Student_dashboard():
    return render_template('student.html')


@app.route('/event', methods=['GET', 'POST'])
def event_form():
    if request.method == 'POST':
        event_name = request.form['event_name']
        event_date = request.form['event_date']
        location = request.form['location']
        description = request.form.get('description', '')  # Optional field

        # Validate the input data
        if not event_name or not event_date or not location:
            flash('Event name, date, and location are required!', 'error')
            return redirect(url_for('event_form'))

        # Store the event in the database
        try:
            db_connection = get_db_connection()
            with db_connection.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO events (event_name, event_date, location, description) VALUES (%s, %s, %s, %s)',
                    (event_name, event_date, location, description)
                )
                db_connection.commit()
            flash('Event created successfully!', 'success')
            return redirect(url_for('event_form'))  # Redirect to the form page after submission
        except Error as e:
            flash(f"Error: {e}", 'error')
        finally:
            db_connection.close()

    return render_template('event_form.html')


@app.route('/events')
@jwt_token_required
def events():
    db_connection = get_db_connection()
    events = []
    try:
        with db_connection.cursor(dictionary=True) as cursor:
            cursor.execute('SELECT * FROM events')  # Replace 'events' with your actual table name
            events = cursor.fetchall()
    except Error as e:
        print(f"Error: {e}")
    finally:
        db_connection.close()
    
    return render_template('events.html', events=events)



@app.route('/student_home', methods=['GET', 'POST'])
@jwt_token_required
def student_home():
    message = ''
    
    if request.method == 'POST':
        event_name = request.form['event_name']
        student_id = request.form['student_id']  # Assuming you have student ID in the form
        # Assuming you also have an 'event_id' to associate the registration
        event_id = request.form['event_id']  
        
        db_connection = get_db_connection()
        try:
            with db_connection.cursor() as cursor:
                # Insert registration into the database
                cursor.execute('INSERT INTO event_registrations (event_id, student_id) VALUES (%s, %s)', (event_id, student_id))
                db_connection.commit()
                message = 'Successfully registered for the event!'
        except Error as e:
            print(f"Error: {e}")
            message = 'Failed to register for the event.'
        finally:
            db_connection.close()

    return render_template('student_home.html', message=message)


@app.route('/register_event', methods=['GET', 'POST'])
@jwt_token_required
def register_event():
    db_connection = get_db_connection()
    events = []
    message = ''

    # Fetch events from the database
    try:
        with db_connection.cursor(dictionary=True) as cursor:
            cursor.execute('SELECT * FROM events')  # Fetch all events
            events = cursor.fetchall()
    except Error as e:
        print(f"Error: {e}")
    finally:
        db_connection.close()

    if request.method == 'POST':
        student_id = request.form['student_id']
        event_id = request.form['event_id']

        # Insert registration into the database
        try:
            db_connection = get_db_connection()
            with db_connection.cursor() as cursor:
                cursor.execute('INSERT INTO event_registrations (event_id, student_id) VALUES (%s, %s)', (event_id, student_id))
                db_connection.commit()
                message = 'Successfully registered for the event!'
        except Error as e:
            print(f"Error: {e}")
            message = 'Failed to register for the event.'
        finally:
            db_connection.close()

    return render_template('student_home.html', events=events, message=message)


if __name__ == '__main__':
    app.run(debug=True)
