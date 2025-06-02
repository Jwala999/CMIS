# College Management Information System (CMIS)

A simple web-based system to manage college operations, including user registration/login, student marks, courses, and fees.

## Setup Instructions

1. **Install Python**:
   - Download and install Python 3.8+ from [python.org](https://www.python.org/downloads/).
   - Verify: `python --version`.

2. **Install Git**:
   - Download from [git-scm.com](https://git-scm.com/downloads).
   - Verify: `git --version`.

3. **Create Virtual Environment**:
   - Navigate to the project folder: `cd CMIS`.
   - Run: `python -m venv venv`.
   - Activate:
     - Windows: `.\venv\Scripts\activate`
     - Mac/Linux: `source venv/bin/activate`

4. **Install Dependencies**:
   - Run: `pip install -r requirements.txt`.

5. **Download Bootstrap**:
   - Download Bootstrap 5 CSS from [getbootstrap.com](https://getbootstrap.com/docs/5.3/getting-started/download/).
   - Place `bootstrap.min.css` in `static/css/`.

6. **Run the Application**:
   - Run: `python app.py`.
   - Open `http://localhost:5000` in a browser.

7. **Run Tests**:
   - Run: `python tests.py`.

## Usage
- **Login**: Access at `/`.
- **Register**: Click "New User? Create Account".
- **Marks**: View at `/marks` after login.
- **Courses**: View at `/courses`.
- **Fees**: View at `/fees`.

## Notes
- Sample data is pre-loaded in `database.db`.
- Use `test@example.com` and `password` to test login after registration.