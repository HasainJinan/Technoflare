#Imports
from flask import Flask, render_template, request, redirect, flash, abort
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


##Special Account
admin = conf.sp_username


##User Login Manager
login_manager = login.LoginManager()
login_manager.init_app(app)
login_manager.login_view=("/login")


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
    return render_template("homepage.html.jinja", admin = admin)


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
    
    cursor.execute(f"""
        SELECT
            `review`,
            `rating_stars`,
            `Review`.`timestamp`,
            `username`
        FROM `Review`
        JOIN `Customer` ON `customer_id` = `Customer`.`id`
    ;""")
    
    reviews = cursor.fetchall()

    ##Close Connections
    cursor.close()
    conn.close()

    if result is None:
        abort(404)

    return render_template("product.html.jinja", product = result, reviews = reviews)
        

##Add to Cart Functionality
@app.route("/product/<product_id>/cart", methods=["POST"])
@login.login_required
def add_to_cart(product_id):
    quantity = request.form["quantity"]

    customer_id = login.current_user.id

    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute(f"""
        INSERT INTO `Cart`
            (`customer_id`, `product_id`, `quantity`)
        VALUES
            ({customer_id}, {product_id}, {quantity})
        ON DUPLICATE KEY UPDATE
            `quantity` = `quantity` + {quantity}
        ;""")

    cursor.close()
    conn.close()

    return redirect("/cart")


##Sign Up Page
@app.route("/signup", methods=["POST", "GET"])
def signup_page():
    if login.current_user.is_authenticated:
        return redirect("/")
    
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

        if len(username.strip()) > 20:
            flash("Username must be 20 characters or less.")

        else:
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
    if login.current_user.is_authenticated:
        return redirect("/")
    if request.method == "POST":
        username = request.form["userVer"].strip()
        password = request.form["passVer"]

        conn = connect_db()

        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM `Customer` WHERE `username` = '{username}';")
        
        result = cursor.fetchone()

        #Close Connections
        cursor.close()
        conn.close()

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


##Cart Page
@app.route("/cart", methods=["GET"])
@login.login_required
def cart_page():
    conn = connect_db()

    cursor = conn.cursor()

    customer_id = login.current_user.id

    cursor.execute(f"""
        SELECT
            `name`,
            `price`,
            `quantity`,
            `image`,
            `product_id`,
            `Cart`.`id`
        FROM `Cart` 
        JOIN `Product` ON `product_id` = `Product`.`id` 
        WHERE `customer_id` = {customer_id};
    """)

    results = cursor.fetchall()

    total = 0

    if len(results) > 0:
        for item in results:
            total += (item["price"] * item["quantity"])
        total = round(total, 2)

    #Close Connections
    cursor.close()
    conn.close()
    return render_template("cart.html.jinja", cartContents = results, sum = total)


##Remove from Cart
@app.route("/cart/remove_cart", methods=["POST"])
@login.login_required
def remove_cart():
    conn = connect_db()

    cursor = conn.cursor()

    customer_id = login.current_user.id

    cart_id = request.form["id"]

    cursor.execute(f"""
    DELETE FROM `Cart`
    WHERE
        `customer_id` = {customer_id}
    AND
        `Cart`.`id` = {cart_id};
    """)

    #Close Connections
    cursor.close()
    conn.close()

    return redirect("/cart")


##Update Item Quantity in Cart
@app.route("/cart/<cart_id>/update", methods=["POST"])
@login.login_required
def update_cart(cart_id):
    conn = connect_db()

    cursor = conn.cursor()

    new_qty = request.form["upd_quantity"]

    cursor.execute(f"""
    UPDATE `Cart`
    SET `quantity` = {new_qty}
    WHERE `id` = {cart_id}
    ;""")

    #Close Connections
    cursor.close()
    conn.close()

    return redirect("/cart")


##Checkout Page
@app.route("/checkout", methods=["GET"])
@login.login_required
def checkout():
    conn = connect_db()

    cursor = conn.cursor()

    customer_id = login.current_user.id

    cursor.execute(f"""
        SELECT
            `name`,
            `price`,
            `quantity`,
            `image`,
            `product_id`,
            `Cart`.`id`
        FROM `Cart` 
        JOIN `Product` on `product_id` = `Product`.`id` 
        WHERE `customer_id` = {customer_id};
    """)

    #Cart Item Fetch
    results = cursor.fetchall()

    if len(results) == 0:
        return redirect("/browse")
    
    else:
        total = 0

        for item in results:
            total += (item["price"] * item["quantity"])
        total = round(total, 2)
    
    #User Information Fetch
    cursor.execute(f"""
        SELECT * FROM `Customer`
        WHERE `id` = {customer_id}
    ;""")

    consumer = cursor.fetchone()

    #Close Connections
    cursor.close()
    conn.close()

    return render_template("checkout.html.jinja", cartContents = results, sum = total, customer = consumer)


#Update Information
@app.route("/account/update", methods=["POST"])
@login.login_required
def update_account():
    conn = connect_db()

    cursor = conn.cursor()

    customer_id = login.current_user.id
    
    new_email = request.form["upd_email"]

    new_address = request.form["upd_address"]

    if len(new_email) != 0:
        try:
            cursor.execute(f"""
                UPDATE `Customer`
                SET `email` = '{new_email}'
                WHERE `id` = {customer_id}
            ;""")
        except:
            return redirect("/checkout")
    
    if len(new_address) != 0:
        try:
            cursor.execute(f"""
                UPDATE `Customer`
                SET `address` = '{new_address}'
                WHERE `id` = {customer_id}
            ;""")
        except:
            return redirect("/checkout")

    #Close Connections
    cursor.close()
    conn.close()

    return redirect("/checkout")


##Create Sale
@app.route("/checkout/sale")
@login.login_required
def create_sale():
    conn = connect_db()

    cursor = conn.cursor()

    customer_id = login.current_user.id
    
    cursor.execute(f"SELECT `address` FROM `Customer` WHERE `id` = {customer_id};")
    
    address = cursor.fetchone()

    cursor.execute(f"""
        INSERT INTO `Sale`
            (`customer_id`, `address`, `status`)
        VALUES
            ('{customer_id}', '{address["address"]}', 'Pending');
    """)

    sale_id = cursor.lastrowid
    
    cursor.execute(f"""
        SELECT * FROM `Cart` WHERE `customer_id` = {customer_id};
    ;""")
    
    products = cursor.fetchall()

    for product in products:
        cursor.execute(f"""
            INSERT INTO `SaleProduct`
                (`sale_id`, `product_id`, `quantity`)
            VALUES
                ({sale_id}, {product['product_id']}, {product['quantity']})
        ;""")
    
    return redirect("/thankyou")


##Empty Cart
@app.route("/thankyou")
@login.login_required
def empty():
    conn = connect_db()
    
    cursor = conn.cursor()
    
    customer_id = login.current_user.id

    cursor.execute(f"DELETE FROM `Cart` WHERE `customer_id` = {customer_id};")
    
    return render_template("thankyou.html.jinja")


#Add Review Function
@app.route("/add_review/<product_id>", methods=["POST"])
@login.login_required
def add_review(product_id):
    customer_id = login.current_user.id
    
    comment = request.form["comment"]
    
    rating = request.form["rating"]

    conn = connect_db()
    
    cursor = conn.cursor()
    
    cursor.execute(f"""
        INSERT INTO `Review`
            (`customer_id`, `product_id`, `review`, `rating_stars`)
        VALUES
            ({customer_id}, {product_id}, '{comment}', {rating})
    ;""")
    
    return redirect(f"/product/{product_id}")