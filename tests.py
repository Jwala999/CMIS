import unittest
from app import app
import sqlite3
import bcrypt

class CMISTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('DELETE FROM users')
        c.execute('DELETE FROM students')
        c.execute('DELETE FROM courses')
        c.execute('DELETE FROM fees')
        conn.commit()
        conn.close()

    def test_register_new_user(self):
        response = self.client.post('/register', data={
            'email': 'test@example.com',
            'password': 'password',
            'confirm_password': 'password'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', ('test@example.com',))
        user = c.fetchone()
        conn.close()
        self.assertIsNotNone(user)

    def test_duplicate_email(self):
        self.client.post('/register', data={
            'email': 'test@example.com',
            'password': 'password',
            'confirm_password': 'password'
        })
        response = self.client.post('/register', data={
            'email': 'test@example.com',
            'password': 'password',
            'confirm_password': 'password'
        }, follow_redirects=True)
        self.assertIn(b'User is already registered', response.data)

    def test_login_success(self):
        password = 'password'
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)', 
                 ('test@example.com', password_hash, 'User'))
        conn.commit()
        conn.close()
        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password'
        }, follow_redirects=True)
        self.assertIn(b'Login successful!', response.data)

    def test_login_failure(self):
        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'wrong'
        }, follow_redirects=True)
        self.assertIn(b'Invalid credentials!', response.data)

    def test_add_student(self):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('INSERT INTO courses (name, description) VALUES (?, ?)', ('CS101', 'Intro'))
        conn.commit()
        conn.close()
        response = self.client.post('/marks', data={
            'name': 'Jane Doe',
            'course_id': '1',
            'marks': '80,85,90'
        }, follow_redirects=True)
        self.assertIn(b'Student added successfully!', response.data)

    def test_add_course(self):
        response = self.client.post('/courses', data={
            'name': 'CS102',
            'description': 'Advanced CS'
        }, follow_redirects=True)
        self.assertIn(b'Course added successfully!', response.data)

    def test_add_fee(self):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('INSERT INTO students (name, course_id, marks) VALUES (?, ?, ?)', 
                 ('Jane Doe', 1, '80,85,90'))
        conn.commit()
        conn.close()
        response = self.client.post('/fees', data={
            'student_id': '1',
            'amount_paid': '6000',
            'balance_due': '1500'
        }, follow_redirects=True)
        self.assertIn(b'Fee record added successfully!', response.data)

if __name__ == '__main__':
    unittest.main()