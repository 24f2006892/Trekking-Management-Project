from flask import Flask , render_template , redirect,request,session
from werkzeug.security import generate_password_hash , check_password_hash
import sqlite3
from flask import flash
import os


app = Flask(__name__)
app.secret_key = "your_secret_key"
def get_db_connnection():
    conn = sqlite3.connect("database.db")
    conn.row_factory =sqlite3.Row
    return conn
# Initializing Database
@app.route("/init_db")
def init_db():
    conn = get_db_connnection()
    conn.execute("""
                CREATE TABLE IF NOT EXISTS users(
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 email TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL,
                 role TEXT NOT NULL)
                 """)
    conn.execute("""
                CREATE TABLE IF NOT EXISTS treks(
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 location TEXT NOT NULL,
                 price INTEGER NOT NULL,
                 slots INTEGER NOT NULL,
                 difficulty TEXT NOT NULL,
                 duration INTEGER NOT NULL,
                 assigned_staffID INTEGER NOT NULL,
                 start_date DATE ,
                 end_date DATE ,
                 description TEXT ,
                 FOREIGN KEY (assigned_staffID) REFERENCES staff_profiles(id)
                 ) """)
    conn.execute(""" 
                CREATE TABLE IF NOT EXISTS bookings(
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT NOT NULL,
                 trek_id INTEGER
                 booking_date DATE ,
                 status TEXT NOT NULL 
                 ) """)
    conn.execute(""" 
                CREATE TABLE IF NOT EXISTS staff(
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 mobile INTEGER,
                 assigned_trek TEXT ,
                 status TEXT NOT NULL 
                 ) """)
    conn.execute()
    conn.commit()
    conn.close()
    flash("Database Initialized Successfully")
    return redirect("/")
    
@app.route('/')
def home():
    return "Trekking project"

# Show Bookings 
@app.route("/my_bookings")
def my_bookings():
    if "user" not in session:
        return redirect("/login")
    username = session["user"]
    conn = get_db_connnection()
    conn.execute("""
                 SELECT treks.name, treks.location , treks.price
                 FROM bookings 
                 JOIN treks ON bookings.trek_id = treks.id
                 WHERE bookings.username = ?""",(username,)).fetchall()
    conn.close()
    return render_template("my_bookings.html", bookings=bookings)
#Book Treks (USER)
app.route("/book/<int:trek_id>",methods=["POST"])
def book_trek(trek_id):
    if "user" not in session:
        return redirect("/login")
    username = session["user"]
    conn = get_db_connnection()

    #Check duplicate
    existing = conn.execute("SELECT * FROM bookings WHERE username = ? AND trek_id = ?",
                            (username, trek_id)).fetchone()
    if existing:
        conn.close()
        flash("Already Booked")
    #Check trek
    trek = conn.execute(
        "SELECT * FROM treks where id = ?",(trek_id)
    ).fetchone()

    if not trek or trek["slots"]<=0:
        conn.close()
        flash("No slots remaining")
        return redirect("/view_treks")
    # Insert bookings
    conn.execute("INSERT INTO bookings (username, trek_id) VALUES (?, ?)",
                 (username, trek_id))
    #update treks
    conn.execute("UPDATE treks SET slots = slots - 1 WHERE id = ? AND slots > 0",
                 (trek_id))
    conn.commit()
    conn.close()

    flash ("trek booked successfully")
    return redirect("/view_treks")


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        conn = get_db_connnection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = username
            return "Login Successful"
        else:
            msg = "Invalid Credentials"

    return render_template("login.html", msg=msg)
    
        
# Register 
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)
        
        conn = get_db_connnection()
        try:
            conn.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, hashed_password)
            )
            conn.commit()
        except:
            conn.close()
            flash("User already exists")
            return redirect("/register")
        flash("Registration Done , Please Login")
        conn.close()
        return redirect("/login")
        
    return render_template("register.html")


# View treks backend 
@app.route("/view_treks")
def view_treks():
    return "This is a trek"
#Book trek - user side
@app.route("/book/<int:trek_id>", methods=["POST"])
def book_trek(trek_id):
    if "user" not in session:
        return redirect("/login")
    username = session["user"]
    conn = get_db_connnection()
    #check trek
    trek = conn.execute(""" 
                        SELECT * FROM treks WHERE  id=?   """,(trek_id)).fetchone()
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
#Delete treks
@app.route("/delete_trek/<int:trek_id>",methods=["POST"])
def delete_trek(trek_id):
    conn = get_db_connnection()
    conn.execute("DELETE FROM treks WHERE id = ?",(trek_id))
    conn.commit()
    conn.close()
    return redirect("/view_treks")
#Update treks 
@app.route("/update_trek/<int:trek_id>",methods=["GET","POST"])
def update_trek(trek_id):
    if session["user"]!="admin":
        return redirect("/login")
    conn = get_db_connnection()
    if request.method=="POST":
        name = request.form["name"]
        location = request.form["location"]
        price = request.form["price"]
        slots = request.form["slots"]

    conn.execute("""
                UPDATE treks SET name = ?, location = ?, price = ?, slots = ?
                WHERE id = ? """, (name, location, price, slots, trek_id))
    conn.commit()
    conn.close()
    return redirect("/view_treks")

@app.route("/logout")
def logout():
    session.pop("user",None)
    return redirect("/login")

@app.route("/about")
def about():
    if "user" not in session:
        return redirect("/login")
    return render_template("about.html")
@app.route("/contact")
def contact():
    if "user" not in session:
        return redirect("/login")
    return render_template("contact.html")
@app.route("/services")
def services():
    if "user" not in session:
        return redirect("/login")
    return render_template("services.html")

# Admin
@app.route("/admin/users")
def view_users():
    if "user" not in session or session["user"]!="admin":
        return redirect("/login")
    
    conn = get_db_connnection()
    bookings = conn.execute("""
                            SELECT bookings.username, treks.name, treks.location
                            FROM bookings
                            JOIN treks on bookings.trek_id = treks.id
                                 """).fetchall()
    conn.close()
    return render_template("admin_bookings.html", bookings=bookings)
    
# Bookings show to admin
@app.route("/admin/bookings")
def view_bookings():
    if "user" not in session or session["user"] != "admin":
        return "Access Denied"
    conn = get_db_connnection()
    bookings = conn.execute("""SELECT bookings.username, treks.name, treks.location
                    FROM bookings 
                    JOIN treks ON bookings.id = treks.id
                  """).fetchall()
    conn.close()
    return render_template("admin_bookings.html",bookings=bookings)

#Add treks
@app.route("/treks", methods=["GET","POST"])
def trek():
    
    if session["user"] != "admin":
        flash("Access Denied")
        return redirect("/login")
    
    if request.method == "POST":
        name = request.form["name"]
        location = request.form["location"]
        price = request.form["price"]
        slots = request.fprm["slots"]

        conn = get_db_connnection()
        conn.execute(
            "INSERT INTO treks (name, location, price, slots) VALUES (?, ?, ?, ?)",
            (name,location,price,slots)
        )
        conn.commit()
        conn.close()

        return redirect("/view_treks")



    




if __name__ == '__main__' :
    app.run(debug=True)
