from flask import Flask , render_template , redirect,request,session
from werkzeug.security import generate_password_hash , check_password_hash
import sqlite3
import os


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
                 role TEXT NOT NULl)
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
@app.route("/login" , methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        conn = get_db_connnection()
        user = conn.execute("""
                SELECT * FROM users WHERE username = ?
                            """ (username,) ).fetchone
        conn.close()
        if user and check_password_hash(user["password"],password):
            session["user"]=username
            return("Login Successful")
        else:
            return("Invalid Details")

        

@app.route("/register" , methods=["GET", "POST"])
def register():
    if request.method=="POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)
        conn = get_db_connnection()
        conn.execute(""" 
                    INSERT INTO users (username, email, password) VALUES (?, ?, ?)""",(username, email, hashed_password))
        conn.commit()
        conn.close()
    return "User Registered Successfully"

# View treks backend 
@app.route("view_treks")
def view_treks():
    return "This is a trek"
#Book trek - user side
@app.route("/book/<int:trek_id>", methods=["POST"])
def book_trek(trek_id):
    username = session["user"]
    conn = get_db_connnection()
    #check trek
    trek = conn.execute(""" 
                        SELECT * FROM treks WHERE  id=?   """,(trek_id)).fetchone
    if not trek or trek["slots"]<=0:
        conn.close()
        return "No treks Available"
    # insert bookings
    conn.execute(" INSERT INTO bookings (username, trek_id) VALUES (?, ?)",
                 (username, trek_id))
    # Update slots
    conn.execute(
        " UPDATE treks SET slots = slots - 1 WHERE id = ? AND slots > 0",
        (trek_id,)
    )
    conn.commit()
    conn.close()




if __name__ == '__main__' :
    app.run(debug=True)
