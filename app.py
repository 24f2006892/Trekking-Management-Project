from flask import Flask , render_template


app = Flask(__name__)

@app.route('/')
def home():
    return "Trekking project"

@app.route("/login")
def login():
    return "Login"

@app.route("/register")
def login():
    return "Register"

if __name__ == '__main__' :
    app.run(debug=True)
