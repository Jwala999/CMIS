from flask import Flask, request, render_template, redirect, url_for, flash, session
import psycopg2
import bcrypt
import uuid
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'd7e6b1ed9ee6ba1fb1e89473509c2870')  # Use a secure key in production

# Database connection setup
def get_db_connection():
    conn = psycopg2.connect(
        database=os.getenv('DB_NAME', 'cmis_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', ''),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432')
    )
    return conn

# Initialize the database schema
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id SERIAL PRIMARY KEY, email TEXT UNIQUE, password_hash TEXT, role TEXT, 
                  reset_token TEXT, token_expiry TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (student_id SERIAL PRIMARY KEY, name TEXT, course_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS subject_marks 
                 (mark_id SERIAL PRIMARY KEY, student_id INTEGER, subject TEXT, mark INTEGER, 
                  FOREIGN KEY(student_id) REFERENCES students(student_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS courses 
                 (course_id SERIAL PRIMARY KEY, name TEXT, description TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fees 
                 (fee_id SERIAL PRIMARY KEY, student_id INTEGER, amount_paid REAL, balance_due REAL)''')
    # Insert sample data
    c.execute("INSERT INTO courses (course_id, name, description) VALUES (1, 'CS101', 'Intro to Computer Science') ON CONFLICT DO NOTHING")
    c.execute("INSERT INTO students (student_id, name, course_id) VALUES (1, 'John Doe', 1) ON CONFLICT DO NOTHING")
    c.execute("INSERT INTO subject_marks (student_id, subject, mark) VALUES (1, 'Math', 90), (1, 'Physics', 85), (1, 'Chemistry', 88) ON CONFLICT DO NOTHING")
    c.execute("INSERT INTO fees (fee_id, student_id, amount_paid, balance_due) VALUES (1, 1, 5000.0, 2000.0) ON CONFLICT DO NOTHING")
    conn.commit()
    conn.close()

# Middleware to check if user is logged in
def login_required(f):
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# Function to send email via Gmail SMTP
def send_reset_email(to_email, token):
    sender_email = "jwalakumar961645@gmail.com"
    app_password = os.getenv('GMAIL_APP_PASSWORD')  # Correctly load from environment variable

    # Create the email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = 'CMIS Password Reset Request'

    # Email body
    reset_url = f"https://{os.getenv('HEROKU_APP_NAME', 'localhost:5000')}/reset_password/{token}"
    body = f"""
    Hello,

    You have requested to reset your password for the College Management Information System (CMIS).

    Please click the following link to reset your password:
    {reset_url}

    This link will expire in 1 hour. If you did not request a password reset, please ignore this email.

    Best regards,
    CMIS Team
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to Gmail's SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Enable TLS
        server.login(sender_email, app_password)  # Login with App Password
        server.sendmail(sender_email, to_email, msg.as_string())  # Send email
        server.quit()
        print(f"Email sent to {to_email} with reset token: {token}")  # Debug
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")  # Debug
        return False

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM students')
    total_students = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM courses')
    total_courses = c.fetchone()[0]
    c.execute('SELECT SUM(balance_due) FROM fees')
    total_fees_due = c.fetchone()[0] or 0
    conn.close()
    return render_template('dashboard.html', students=total_students, courses=total_courses, fees_due=total_fees_due)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match!')
            return redirect(url_for('register'))
        
        try:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            print(f"Registering user {email} with hash: {password_hash}")  # Debug
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s)', 
                      (email, password_hash, 'User'))
            conn.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('home'))
        except psycopg2.IntegrityError:
            flash('User is already registered. Please login to the application.')
            return redirect(url_for('register'))
        except Exception as e:
            flash(f'Registration error: {str(e)}')
            print(f"Registration error for {email}: {str(e)}")  # Debug
            return redirect(url_for('register'))
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = c.fetchone()
    conn.close()
    
    if user:
        print(f"Login attempt for {email}, stored hash: {user[2]}")  # Debug
        try:
            if bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
                session['user_id'] = user[0]
                flash('Login successful!')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid password!')
                print(f"Invalid password for {email}")  # Debug
        except ValueError as e:
            flash(f'Login error: {str(e)}. Please re-register.')
            print(f"Login error for {email}: {str(e)}, Hash: {user[2]}")  # Debug
    else:
        flash('User not found!')
        print(f"User not found: {email}")  # Debug
    return redirect(url_for('home'))

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('home'))

@app.route('/reset_request', methods=['GET', 'POST'])
def reset_request():
    if request.method == 'POST':
        email = request.form['email']
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = c.fetchone()
        
        if user:
            # Generate a reset token and set expiry (1 hour from now)
            token = str(uuid.uuid4())
            expiry = (datetime.now() + timedelta(hours=1)).isoformat()
            c.execute('UPDATE users SET reset_token = %s, token_expiry = %s WHERE email = %s', 
                      (token, expiry, email))
            conn.commit()
            # Send the reset token via email
            if send_reset_email(email, token):
                flash('A password reset link has been sent to your email. Please check your inbox (and spam/junk folder).')
            else:
                flash('Failed to send the reset email. Please try again later.')
            return redirect(url_for('reset_request'))
        else:
            flash('Email not found!')
        
        conn.close()
    
    return render_template('reset_request.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE reset_token = %s', (token,))
    user = c.fetchone()
    
    if not user:
        flash('Invalid or expired token!')
        conn.close()
        return redirect(url_for('home'))
    
    # Check token expiry
    expiry = datetime.fromisoformat(user[5]) if user[5] else datetime.now()
    if datetime.now() > expiry:
        flash('Token has expired!')
        c.execute('UPDATE users SET reset_token = NULL, token_expiry = NULL WHERE reset_token = %s', (token,))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match!')
            conn.close()
            return redirect(url_for('reset_password', token=token))
        
        try:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            c.execute('UPDATE users SET password_hash = %s, reset_token = NULL, token_expiry = NULL WHERE reset_token = %s', 
                      (password_hash, token))
            conn.commit()
            flash('Password reset successfully! Please login.')
            conn.close()
            return redirect(url_for('home'))
        except Exception as e:
            flash(f'Error resetting password: {str(e)}')
            conn.close()
            return redirect(url_for('reset_password', token=token))
    
    conn.close()
    return render_template('reset_password.html', token=token)

@app.route('/marks', methods=['GET', 'POST'])
@login_required
def marks():
    conn = get_db_connection()
    c = conn.cursor()
    
    if request.method == 'POST':
        if 'delete' in request.form:
            # Handle delete request
            student_id = request.form['student_id']
            try:
                c.execute('DELETE FROM subject_marks WHERE student_id = %s', (student_id,))
                c.execute('DELETE FROM students WHERE student_id = %s', (student_id,))
                conn.commit()
                flash('Student and their marks deleted successfully!')
            except Exception as e:
                flash(f'Error deleting student: {str(e)}')
        else:
            # Handle add request
            name = request.form['name']
            course_id = request.form['course_id']
            math_mark = request.form['math_mark']
            physics_mark = request.form['physics_mark']
            chemistry_mark = request.form['chemistry_mark']
            try:
                c.execute('INSERT INTO students (name, course_id) VALUES (%s, %s) RETURNING student_id', (name, course_id))
                student_id = c.fetchone()[0]
                c.execute('INSERT INTO subject_marks (student_id, subject, mark) VALUES (%s, %s, %s)', 
                          (student_id, 'Math', math_mark))
                c.execute('INSERT INTO subject_marks (student_id, subject, mark) VALUES (%s, %s, %s)', 
                          (student_id, 'Physics', physics_mark))
                c.execute('INSERT INTO subject_marks (student_id, subject, mark) VALUES (%s, %s, %s)', 
                          (student_id, 'Chemistry', chemistry_mark))
                conn.commit()
                flash('Student and marks added successfully!')
            except Exception as e:
                flash(f'Error adding student: {str(e)}')
                conn.rollback()
    
    # Fetch students and their marks
    c.execute('''SELECT s.student_id, s.name, s.course_id, 
                        MAX(CASE WHEN sm.subject = 'Math' THEN sm.mark END) as math_mark,
                        MAX(CASE WHEN sm.subject = 'Physics' THEN sm.mark END) as physics_mark,
                        MAX(CASE WHEN sm.subject = 'Chemistry' THEN sm.mark END) as chemistry_mark
                 FROM students s
                 LEFT JOIN subject_marks sm ON s.student_id = sm.student_id
                 GROUP BY s.student_id''')
    students = c.fetchall()
    c.execute('SELECT course_id, name FROM courses')
    courses = c.fetchall()
    conn.close()
    return render_template('marks.html', students=students, courses=courses)

@app.route('/courses', methods=['GET', 'POST'])
@login_required
def courses():
    conn = get_db_connection()
    c = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        c.execute('INSERT INTO courses (name, description) VALUES (%s, %s)', 
                  (name, description))
        conn.commit()
        flash('Course added successfully!')
    c.execute('SELECT * FROM courses')
    courses = c.fetchall()
    conn.close()
    return render_template('courses.html', courses=courses)

@app.route('/fees', methods=['GET', 'POST'])
@login_required
def fees():
    conn = get_db_connection()
    c = conn.cursor()
    if request.method == 'POST':
        student_id = request.form['student_id']
        amount_paid = request.form['amount_paid']
        balance_due = request.form['balance_due']
        c.execute('INSERT INTO fees (student_id, amount_paid, balance_due) VALUES (%s, %s, %s)', 
                  (student_id, amount_paid, balance_due))
        conn.commit()
        flash('Fee record added successfully!')
    c.execute('SELECT * FROM fees')
    fees = c.fetchall()
    c.execute('SELECT student_id, name FROM students')
    students = c.fetchall()
    conn.close()
    return render_template('fees.html', fees=fees, students=students)

if __name__ == '__main__':
    init_db()
    port = int(os.getenv('PORT', 5000))  # Use PORT env variable for Heroku
    app.run(host='0.0.0.0', port=port, debug=False)