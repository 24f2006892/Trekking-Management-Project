from flask import Flask , render_template , redirect
import sqlite3

app = Flask(__name__)
def get_db_connnection():
    conn = sqlite3.connect("database.db")
    conn.row_factory =sqlite3.Row
    return conn

@app.route("/init_db")
def init_db():
    conn = get_db_connnection()
    conn.execute("""
                CREATE TABLE IF NOT EXISTS users(
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 email TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL
                 role TEXT NOT NULL)
                 """)
    conn.execute("""
                CREATE TABLE IF NOT EXISTS treks(
                 id INTEGER PRIMARY KEY AUTOINCEREMENT
                 name TEXT NOT NULL,
                 location TEXT NOT NULL
                 price INTEGER NOT NULL,
                 slots INTEGER NOT NULL
                 ) """)
    conn.execute(""" 
                CREATE TABLE IF NOT EXISTS bookings(
                 id INTEGER PRIMARY KEY AUTOINCEREMENT
                 username TEXT NOT NULL,
                 trek_id INTEGER
                 ) """)
    conn.execute()
    conn.commit()
    conn.close()
    return redirect("/")
    
@app.route('/')
def home():
    return "Trekking project"
# Login
@app.route("/login")
def login():
    return "Login"

@app.route("/register")
def login():
    return "Register"

if __name__ == '__main__' :
    app.run(debug=True)
