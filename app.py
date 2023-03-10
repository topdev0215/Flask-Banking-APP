import sqlite3
from flask import Flask, g, render_template, request, redirect, flash, url_for, session
import re
import random
import locale
import datetime
import json
import pandas as pd

locale.setlocale(locale.LC_ALL, '')

app = Flask(__name__)
app.secret_key = 'abcdef12345!@#$%'
DATABASE = 'bank.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()      

@app.errorhandler(sqlite3.Error)
def handle_database_error(error):
    return 'A database error occurred: ' + str(error), 500

@app.route('/')
def index():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                email TEXT UNIQUE,
                username TEXT UNIQUE,
                password TEXT,
                balance NUMERIC(10, 2) DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                t_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount NUMERIC(10, 2),
                memo TEXT,
                time DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        db.commit()
        cursor.close()
        return render_template('index.html')
    except sqlite3.Error as e:
        return 'A database error occurred: ' + str(e), 500

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Forgot Password Page
    # Send Email to verify identity

def valid_username(string):
    pattern = re.compile(r'^(?=.*[a-zA-Z])(?=.*\d).+$')
    return bool(pattern.match(string) and len(string) >= 8)

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_password(password):
    if len(password) < 8:
        return False
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#]).+$'
    if not bool(re.match(pattern, password)):
        return False
    return True

def generate_id():
    return random.randint(10000000, 99999999)

@app.route('/create_account', methods=['POST'])
def create_user():
    db = get_db()
    cursor = db.cursor()
    unique_id = False
    while not unique_id:
        id = generate_id()
        cursor.execute('SELECT user_id FROM users WHERE user_id=?', (id,))
        id_exists = cursor.fetchone()
        if not id_exists:
            unique_id=True

    first_name = request.form['first_name']
    last_name = request.form['last_name']

    email = request.form['email']
    if not is_valid_email(email):
        flash('Invalid Email, "error')
        return render_template('index.html')
    
    username = request.form['username']
    if not valid_username(username):
        flash('Username Must Contain 8+ Characters (Numbers and Letters)', "error")
        return render_template('index.html')
    
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    if password != confirm_password:
        flash('Passwords do not match', 'error')
        return render_template('index.html')
    if not is_valid_password(password):
        flash("Password must contain at least one uppercase letter, one lowercase letter, one digit and one special character", "error")
        return render_template('index.html')

    cursor.execute('SELECT email FROM users WHERE email=?', (email,))
    email_exists = cursor.fetchone()
    if email_exists:
        cursor.close()
        flash('Email already in use', 'error')
        return render_template('index.html')
    
    cursor.execute('SELECT username FROM users WHERE username=?', (username,))
    username_exists = cursor.fetchone()
    if username_exists:
        cursor.close()
        flash('Username already exists', 'error')
        return render_template('index.html')

    cursor.execute('''INSERT INTO users (user_id,
                                         first_name,
                                         last_name,
                                         email,
                                         username,
                                         password, 
                                         balance) VALUES (?, ?, ?, ?, ?, ?, ?)''', (id, first_name, last_name, email, username, password, 0))
    db.commit()
    cursor.close()
    flash('User created successfully', 'success')   
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor()
        username = str(request.form['username'])
        password = request.form['password']
        cursor.execute('SELECT email FROM users WHERE username=? AND password=?', (username, password))
        valid_user = cursor.fetchone()
        if valid_user:
            session['username'] = username
            session['password'] = password
            cursor.close()
            return redirect(f'dashboard/{username}')
        else:
            flash('Invalid login credentials', 'error')
            return render_template('index.html')

@app.route('/dashboard/<string:username>', methods=["GET", "POST"])
def dashboard(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT balance FROM users WHERE username=?', (username,))
    balance = float(cursor.fetchone()[0])
    cursor.execute('SELECT user_id FROM users WHERE username=?', (username,))
    user_id = int(cursor.fetchone()[0])
    cursor.execute('SELECT * FROM transactions WHERE user_id=?',(user_id,))
    t_rows = cursor.fetchall()
    user_transactions = []
    for row in t_rows:
        transaction = {
            'time': row[5],
            'type': row[2],
            'amount': row[3],
            'memo': row[4]
        }
        user_transactions.append(transaction)
    user_transactions_df = pd.DataFrame(user_transactions)
    cursor.close()
    return render_template('account.html', username=username, balance=balance, transactions=user_transactions_df)

@app.route('/deposit', methods=['POST'])
def deposit():
    amount = request.form['amount']
    memo = request.form['memo']
    username = session['username']
    password = session['password']

    with sqlite3.connect('bank.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE username=? AND password=?', (amount, username, password))
        conn.commit()
        cursor.execute('SELECT user_id FROM users WHERE username=? AND password=?', (username, password))
        user_id = int(cursor.fetchone()[0])
        cursor.execute('''INSERT INTO transactions (user_id,
                                                    type,
                                                    amount,
                                                    memo) VALUES (?, ?, ?, ?)''', (user_id, "deposit", float(amount), str(memo)))
        conn.commit()
        cursor.close()
    flash(f'Successful Deposit of {locale.currency(float(amount), grouping=True)} at {datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")}', 'success')
    return redirect(f'dashboard/{username}')

@app.route('/withdraw', methods=['POST'])
def withdraw():
    amount = request.form['amount']
    memo = request.form['memo']
    username = session['username']
    password = session['password']
    with sqlite3.connect('bank.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE username=? AND password=?', (username, password))
        balance = float(cursor.fetchone()[0])
        cursor.execute('SELECT user_id FROM users WHERE username=? AND password=?', (username, password))
        user_id = int(cursor.fetchone()[0])
        if float(amount) > balance:
            flash(f'Error: Insufficient balance for withdrawal', 'error')
        else:
            cursor.execute('UPDATE users SET balance = balance - ? WHERE username=? AND password=?', (amount, username, password))
            conn.commit()
            cursor.execute('''INSERT INTO transactions (user_id,
                                                        type,
                                                        amount,
                                                        memo) VALUES (?, ?, ?, ?)''', (user_id, "withdraw", float(amount), str(memo)))
            conn.commit()
            flash(f'Successful Withdrawal of {locale.currency(float(amount), grouping=True)} at {datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")}', 'success')
        cursor.close()
        amount=0
        return redirect(f'dashboard/{username}')

if __name__ == '__main__':
    app.run(debug=True)