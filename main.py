#Imports
from flask import Flask, render_template, request, redirect, flash
import pymysql
from dynaconf import Dynaconf
import flask_login as login
#Imports


##Application
app = Flask(__name__)


##Settings Configuration
conf = Dynaconf(
    settings_file = ["settings.toml"]
)


##Secret Key
app.secret_key = conf.secret_key


##User Login Manager
login_manager = login.LoginManager()
login_manager.init_app(app)


##Classes
class User:
    is_authenticated = True
    is_anonymous = False
    is_active = True

    def __init__(self, user_id, username, email, first_name, last_name):
        self.id = user_id
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name

    def get_id(self):
        return str(self.id)
##Classes


##Load User Session
@login_manager.user_loader
def load_user(user_id):
    conn = connect_db()
    
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM `Customer` WHERE `id` = {user_id};")

    result = cursor.fetchone()
    
    ##Close Connections
    cursor.close()
    conn.close

    if result is not None:
        return User(result["id"], result["username"], result["email"], result["first_name"], result["last_name"])


##Connecting To Database Function
def connect_db():
    conn = pymysql.connect(
        host = "10.100.34.80",
        database = "hjinan_technoflare",
        user = "hjinan",
        password = conf.password,
        autocommit = True,
        cursorclass = pymysql.cursors.DictCursor
    )

    return conn


##Homepage
@app.route("/")
def index():
    return render_template("homepage.html.jinja")


##Product Browsing Page
@app.route("/browse")
def product_browse():
    query = request.args.get("query")

    conn = connect_db()

    cursor = conn.cursor()

    if query is None:
        cursor.execute("SELECT * FROM `Product`;")

    else:
        cursor.execute(f"SELECT * FROM `Product` WHERE `name` LIKE '%{query}%' OR `description` LIKE '%{query}%' OR `price` LIKE '%{query}%' OR `type` LIKE '%{query}%';")

    results = cursor.fetchall()

    ##Close Connections
    cursor.close()
    conn.close()

    return render_template("browse.html.jinja", products = results)


##Individual Product Page
@app.route("/product/<product_id>")
def product_page(product_id):
    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM `Product` WHERE `id` = {product_id};")

    result = cursor.fetchone()

    ##Close Connections
    cursor.close()
    conn.close()

    return render_template("product.html.jinja", product = result)


##ign Up Page
@app.route("/signup", methods=["POST", "GET"])
def signup_page():
    if request.method == "POST":
        first_name = request.form["fname"]
        last_name = request.form["lname"]

        email = request.form["email"]
        address = request.form["address"]

        username = request.form["username"]
        password = request.form["pass"]
        confirm_password = request.form["confpass"]

        conn = connect_db()

        cursor = conn.cursor()
        
        if len(password.strip()) < 8:
            flash("Password must be 8 characters or longer.")
        
        else:
            if password != confirm_password:
                flash("Passwords do not match.")

            else:
                try:
                    cursor.execute(f"""
                        INSERT INTO `Customer`
                            (`username`, `password`, `first_name`, `last_name`, `email`, `address`)
                        VALUES
                            ('{username}', '{password}', '{first_name}', '{last_name}', '{email}', '{address}');
                    """)

                except pymysql.err.IntegrityError:
                    flash("Username or email is already in use.")
                
                else:
                    return redirect("/login")

                finally:
                    ##Close Connections
                    cursor.close()
                    conn.close()

    return render_template("signup.html.jinja")


##Log In Page
@app.route("/login", methods=["POST", "GET"])
def login_page():
    if request.method == "POST":
        username = request.form["userVer"].strip()
        password = request.form["passVer"]

        conn = connect_db()

        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM `Customer` WHERE `username` = '{username}';")
        
        result = cursor.fetchone()

        if result is None:
            flash("Your username and/or password is incorrect.")
        
        elif password != result["password"]:
            flash("Your username and/or password is incorrect.")
        
        else:
            user = User(result["id"], result["username"], result["email"], result["first_name"], result["last_name"])

            #Loging In
            login.login_user(user)

            return redirect("/")

    return render_template("login.html.jinja")


##Log Out "Button" Code
@app.route("/logout")
def logout():
    login.logout_user()
    return redirect("/")