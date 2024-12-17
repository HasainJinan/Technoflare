from flask import Flask, render_template, request, redirect, flash
import pymysql
from dynaconf import Dynaconf

app = Flask(__name__)

conf = Dynaconf(
    settings_file = ["settings.toml"]
)

app.secret_key = conf.secret_key

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

@app.route("/")
def index():
    return render_template("homepage.html.jinja")

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

    #Close Connections
    cursor.close()
    conn.close()

    return render_template("browse.html.jinja", products = results)

@app.route("/product/<product_id>")
def product_page(product_id):
    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM `Product` WHERE `id` = {product_id};")

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("product.html.jinja", product = result)

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
                    cursor.close()
                    conn.close()

    return render_template("signup.html.jinja")

@app.route("/login")
def login_page():
    return render_template("login.html.jinja")