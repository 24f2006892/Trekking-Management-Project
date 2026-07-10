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
                 mobile TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL,
                 role TEXT NOT NULL DEFAULT 'user')
                 """)
    
    admin = conn.execute(" SELECT * FROM users WHERE role = 'admin' ").fetchone()
    if not admin:
        conn.execute(""" INSERT INTO users (username, email, password, role ) VALUEs (?, ?, ?, ?) 
                    """,("admin", "admin@gmail.com", generate_password_hash("admin@123"), "admin") )
    conn.execute("""
                CREATE TABLE IF NOT EXISTS treks(
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 location TEXT NOT NULL,
                 price INTEGER NOT NULL,
                 slots INTEGER NOT NULL,
                 difficulty TEXT NOT NULL,
                 duration INTEGER NOT NULL,
                 status TEXT NOT NULL DEFAULT 'Open',
                 assigned_staffID INTEGER NOT NULL,
                 start_date DATE ,
                 end_date DATE ,
                 description TEXT ,
                 FOREIGN KEY (assigned_staffID) REFERENCES staff_profiles(id)
                 ) """)
    conn.execute(""" 
                CREATE TABLE IF NOT EXISTS bookings(
                 user_id INTEGER PRIMARY KEY ,
                 username TEXT NOT NULL,
                 trek_id INTEGER,
                 booking_date DATE ,
                 status TEXT NOT NULL,
                 FOREIGN KEY(trek_id) REFERENCES treks(id)),
                 FOREIGN KEY(user_id) REFERENCES users(id)
                 
                 ) """)
    conn.execute(""" 
                CREATE TABLE IF NOT EXISTS staff(
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 mobile INTEGER,
                 assigned_trek TEXT ,
                 status TEXT NOT NULL)
                  """)
    
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
    bookings = conn.execute("""
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
        session["role"] = user["role"]
        session["mobile"] = user["mobile"]
    if user["role"] == "admin":
            return redirect("/admin_dashboard")

    elif user["role"] == "staff":
        conn = get_db_connnection()
        staff = conn.execute("""
                                SELECT * FROM staff WHERE mobile = ?""", (user["mobile"],)).fetchone()

        conn.close()

        if not staff:
            flash("Staff record not found.")
            return redirect("/login")

        if staff["status"] != "Approved":
            flash("Your account is waiting for Admin approval.")
            return redirect("/login")

        return redirect("/staff_dashboard")

    else:
        return redirect("/view_treks")

    return render_template("login.html", msg=msg)
    
        
# Register 
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        password = request.form["password"]
        role = request.form["role"]

        hashed_password = generate_password_hash(password)
        
        conn = get_db_connnection()
        try:
            conn.execute(
                "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                (username, email, hashed_password, role)
            )
            if role == "staff":
                conn.execute("""
                            INSERT INTO staff (name, mobile, assigned_trek, status)
                            VALUES (?, ?, ?, ?)""", (username,mobile,"Not Assigned","Pending"))
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
    conn = get_db_connnection()
    search = request.args.get("search", "")
    difficulty = request.args.get("difficulty", "")
    location = request.args.get("location", "")
    query = """
        SELECT *
        FROM treks
        WHERE status='Open'
    """
    values = []
    if search:
        query += " AND name LIKE ?"
        values.append("%" + search + "%")
    if difficulty:
        query += " AND difficulty = ?"
        values.append(difficulty)
    if location:
        query += " AND location LIKE ?"
        values.append("%" + location + "%")
    treks = conn.execute(query, values).fetchall()
    conn.close()
    return render_template( "view_treks.html",treks=treks)


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
    # Get logged-in user
    user = conn.execute("SELECT * FROM users WHERE username = ?",(username,)).fetchone()

    # Insert booking
    conn.execute("""
    INSERT INTO bookings
    (user_id, username, trek_id, booking_date, status)
    VALUES (?, ?, ?, DATE('now'), ?)
    """,
    (user["id"],username,trek_id,"Booked"))
    # Update slots
    conn.execute(
        " UPDATE treks SET slots = slots - 1 WHERE id = ? AND slots > 0",
        (trek_id,))
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

    
#Admin dashboard
@app.route("/admin_dashboard")
def dashboard():
    if "user" not in session or session["user"] != "admin":
        return "Access Denied"
    conn = get_db_connnection()

    users_count = conn.execute(""" 
                SELECT COUNT(*) FROM users """).fetchone()[0]
    bookings_count = conn.execute(""" 
                SELECT COUNT(*) FROM bookings """).fetchone()[0]
    trek_count = conn.execute(""" 
                SELECT COUNT(*) FROM treks """).fetchone()[0]
    staff_count = conn.execute(""" 
                SELECT COUNT(*) FROM staff """).fetchone()[0]

    bookings = conn.execute("""SELECT bookings.username, treks.name, treks.location, treks.price, bookings.status
                    FROM bookings 
                    JOIN treks ON bookings.trek_id = treks.id
                  """).fetchall()
    
    staff = conn.execute(""" 
                        SELECT * FROM staff """).fetchall()
    conn.close()
    return render_template("admin_dashboard.html",bookings=bookings,user_count=users_count,bookings_count=bookings_count,trek_count=trek_count,staff_count=staff_count,staff=staff)
#Admin_side to manage users
@app.route("/manage_users")
def manage_users():
    if "user" not in session or session["user"] != "admin":
        return "Access Denied"
    conn = get_db_connnection()
    search = request.args.get("search","")

    if search:
        users = conn.execute("""
                             SELECT * FROM users vWHERE username LIKE ? OR id LIKE ?""",("%"+search+"%","%"+search+"%")).fetchall()

    else:
        users = conn.execute(""" SELECT *FROM users""").fetchall()
    conn.close()
    return render_template("manage_users.html", users=users)


@app.route("/manage_staff")
def manage_staff():

    if "user" not in session or session["user"] != "admin":
        return "Access Denied"
    conn = get_db_connnection()
    search = request.args.get("search", "")
    if search:
        staff = conn.execute("""
            SELECT *
            FROM staff
            WHERE name LIKE ?
            OR CAST(id AS TEXT) LIKE ?
        """, ("%" + search + "%", "%" + search + "%")).fetchall()
    else:
        staff = conn.execute("""
            SELECT *
            FROM staff
        """).fetchall()
    conn.close()
    return render_template("manage_staff.html", staff=staff)


@app.route("/manage_treks")
def manage_treks():

    if "user" not in session or session["user"]!="admin":
        return redirect("/login")

    conn=get_db_connnection()

    treks=conn.execute("""

    SELECT *

    FROM treks

    """).fetchall()

    conn.close()

    return render_template("manage_treks.html",treks=treks)

@app.route("/approve_staff/<int:id>")
def approve_staff(id):

    conn=get_db_connnection()

    conn.execute("""

    UPDATE staff

    SET status='Approved'

    WHERE id=?

    """,(id,))

    conn.commit()

    conn.close()

    return redirect("/admin_dashboard")

@app.route("/blacklist_staff/<int:id>")
def blacklist_staff(id):

    conn=get_db_connnection()

    conn.execute("""

    UPDATE staff

    SET status='Blacklist'

    WHERE id=?

    """,(id,))

    conn.commit()

    conn.close()

    return redirect("/admin_dashboard")

@app.route("/assign_staff/<int:trek_id>",methods=["GET","POST"])
def assign_staff(trek_id):

    conn=get_db_connnection()

    if request.method=="POST":

        staff_id=request.form["staff_id"]

        conn.execute("""

        UPDATE treks

        SET assigned_staffID=?

        WHERE id=?

        """,(staff_id,trek_id))

        conn.commit()

        conn.close()

        return redirect("/view_treks")

    staff=conn.execute("""

    SELECT *

    FROM staff

    WHERE status='Approved'

    """).fetchall()

    conn.close()

    return render_template("assign_staff.html",staff=staff)
#staff_dashboard
@app.route("/staff_dashboard")
def staff_dashboard():

    if "user" not in session or session["role"] != "staff":
        return redirect("/login")

    conn = get_db_connnection()

    staff = conn.execute("""
        SELECT *
        FROM staff
        WHERE mobile = ?
    """, (session["mobile"],)).fetchone()

    trek = None

    if staff:
        trek = conn.execute("""SELECT * FROM treksWHERE assigned_staffID = ?
        """, (staff["id"],)).fetchone()

    conn.close()

    return render_template("staff_dashboard.html",staff=staff,trek=trek)

@app.route("/update_trek_status", methods=["GET", "POST"])
def update_trek_status():

    if "user" not in session or session["role"] != "staff":
        return redirect("/login")

    conn = get_db_connnection()

    staff = conn.execute("""
        SELECT *
        FROM staff
        WHERE mobile=?
    """, (session["mobile"],)).fetchone()

    trek = conn.execute("""
        SELECT *
        FROM treks
        WHERE assigned_staffID=?
    """, (staff["id"],)).fetchone()

    if request.method == "POST":

        status = request.form["status"]

        conn.execute("""
            UPDATE treks
            SET status=?
            WHERE id=?
        """, (status, trek["id"]))

        conn.commit()
        conn.close()

        flash("Trek status updated.")
        return redirect("/staff_dashboard")

    conn.close()

    return render_template("update_trek_status.html", trek=trek)

@app.route("/update_slots", methods=["GET", "POST"])
def update_slots():

    if "user" not in session or session["role"] != "staff":
        return redirect("/login")

    conn = get_db_connnection()

    # Get logged-in staff
    staff = conn.execute("""
        SELECT * FROM staff
        WHERE mobile = ?
    """, (session["mobile"],)).fetchone()

    # Get assigned trek
    trek = conn.execute("""
        SELECT * FROM treks
        WHERE assigned_staffID = ?
    """, (staff["id"],)).fetchone()

    if request.method == "POST":

        slots = request.form["slots"]

        conn.execute("""
            UPDATE treks
            SET slots = ?
            WHERE id = ?
        """, (slots, trek["id"]))

        conn.commit()
        conn.close()

        flash("Slots updated successfully.")
        return redirect("/staff_dashboard")

    conn.close()

    return render_template("update_slots.html", trek=trek)

@app.route("/staff_bookings")
def staff_bookings():

    if "user" not in session or session["role"] != "staff":
        return redirect("/login")

    conn = get_db_connnection()

    # Get logged-in staff
    staff = conn.execute("""
        SELECT * FROM staff WHERE mobile = ?
    """, (session["mobile"],)).fetchone()

    bookings = []

    if staff:

        bookings = conn.execute("""
            SELECT
                bookings.username,
                bookings.booking_date,
                bookings.status,
                treks.name
            FROM bookings JOIN treks ON bookings.trek_id = treks.id
            WHERE treks.assigned_staffID = ?
        """, (staff["id"],)).fetchall()

    conn.close()

    return render_template(
        "staff_bookings.html",
        bookings=bookings
    )
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
