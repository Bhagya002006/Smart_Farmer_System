from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os

app = Flask(__name__)

# ---------------- DATABASE CONNECTION ----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",                  # change if different
    password=os.environ.get("DB_PASSWORD", "Bhagya@123"),  # 🔴 put your MySQL password here
    database="smart_farmer_system"
)
cursor = db.cursor()

# ---------------- HOME ----------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------- FARMER ----------------
@app.route("/farmer", methods=["GET", "POST"])
def farmer():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        address = request.form["address"]

        cursor.execute(
            "INSERT INTO farmer (name, phone, address) VALUES (%s,%s,%s)",
            (name, phone, address)
        )
        db.commit()
        return redirect(url_for("index"))

    return render_template("farmer.html")

# ---------------- LAND ----------------
@app.route("/land", methods=["GET", "POST"])
def land():
    if request.method == "POST":
        farmer_id = request.form["farmer_id"]
        area = request.form["area"]
        location = request.form["location"]
        soil_type = request.form["soil_type"]

        cursor.execute(
            "INSERT INTO land (farmer_id, area, location, soil_type) VALUES (%s,%s,%s,%s)",
            (farmer_id, area, location, soil_type)
        )
        db.commit()
        return redirect(url_for("index"))

    return render_template("land.html")

# ---------------- CROP ----------------
@app.route("/crop", methods=["GET", "POST"])
def crop():
    if request.method == "POST":
        farmer_id = request.form["farmer_id"]
        crop_name = request.form["crop_name"]
        price = request.form["price_per_kg"]
        quantity = request.form["quantity_kg"]
        season = request.form["season"]

        cursor.execute(
            "INSERT INTO crop (farmer_id, crop_name, price_per_kg, quantity_kg, season) VALUES (%s,%s,%s,%s,%s)",
            (farmer_id, crop_name, price, quantity, season)
        )
        db.commit()
        return redirect(url_for("index"))

    return render_template("crop.html")

# ---------------- CONSUMER ----------------
@app.route("/consumer", methods=["GET", "POST"])
def consumer():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]

        cursor.execute(
            "INSERT INTO consumer (name, phone) VALUES (%s,%s)",
            (name, phone)
        )
        db.commit()
        return redirect(url_for("index"))

    return render_template("consumer.html")


# ---------------- RECORD / ADD SALES ----------------
@app.route("/sales", methods=["GET", "POST"])
def sales():

    if request.method == "POST":

        try:
            crop_id = int(request.form["crop_id"])
            quantity_sold = int(request.form["quantity_sold"])
            income = float(request.form["income"])

            if crop_id <= 0 or quantity_sold <= 0 or income <= 0:
                return "Please enter valid positive values."

            # Check whether crop exists
            cursor.execute(
                "SELECT crop_id FROM crop WHERE crop_id = %s",
                (crop_id,)
            )

            crop = cursor.fetchone()

            if not crop:
                return "Crop ID does not exist. Please enter a valid Crop ID."

            # Insert sales record
            cursor.execute("""
                INSERT INTO sales
                (crop_id, quantity_sold, income)
                VALUES (%s, %s, %s)
            """, (crop_id, quantity_sold, income))

            db.commit()

            return redirect(url_for("sales_analytics"))

        except ValueError:
            db.rollback()
            return "Please enter valid numeric values."

        except Exception as error:
            db.rollback()
            return f"Unable to save sales: {error}"

    return render_template("sales.html")


# ---------------- ORDERS ----------------
@app.route("/orders", methods=["GET", "POST"])
def orders():
    if request.method == "POST":
        consumer_id = request.form["consumer_id"]
        crop_id = request.form["crop_id"]
        quantity = int(request.form["quantity_kg"])

        # 1️⃣ Get price per kg from crop table
        cursor.execute(
            "SELECT price_per_kg, quantity_kg FROM crop WHERE crop_id = %s",
            (crop_id,)
        )
        crop = cursor.fetchone()

        if not crop:
            return "Invalid Crop ID"

        price_per_kg = crop[0]
        available_qty = crop[1]

        if quantity > available_qty:
            return "Not enough crop quantity available"

        # 2️⃣ Calculate total price
        total_price = price_per_kg * quantity

        # 3️⃣ Insert order
        cursor.execute(
            "INSERT INTO orders (consumer_id, crop_id, quantity_kg, total_price) VALUES (%s,%s,%s,%s)",
            (consumer_id, crop_id, quantity, total_price)
        )

        # 4️⃣ Update crop quantity
        cursor.execute(
            "UPDATE crop SET quantity_kg = quantity_kg - %s WHERE crop_id = %s",
            (quantity, crop_id)
        )

        # 5️⃣ Insert into sales table
        cursor.execute(
            "INSERT INTO sales (crop_id, quantity_sold, income) VALUES (%s,%s,%s)",
            (crop_id, quantity, total_price)
        )

        db.commit()
        return redirect(url_for("index"))

    return render_template("orders.html")
# ---------------- FARMERS & AVAILABLE CROPS ----------------
@app.route("/farmers-crops")
def farmers_crops():

    # Get all farmers and their available crops
    cursor.execute("""
        SELECT
            f.farmer_id,
            f.name,
            f.phone,
            f.address,
            c.crop_id,
            c.crop_name,
            c.price_per_kg,
            c.quantity_kg,
            c.season
        FROM farmer f
        LEFT JOIN crop c
            ON f.farmer_id = c.farmer_id
            AND c.quantity_kg > 0
        ORDER BY f.farmer_id, c.crop_id
    """)

    records = cursor.fetchall()

    # Group crops under their respective farmers
    farmers = {}

    for row in records:

        farmer_id = row[0]

        if farmer_id not in farmers:
            farmers[farmer_id] = {
                "farmer_id": row[0],
                "name": row[1],
                "phone": row[2],
                "address": row[3],
                "crops": []
            }

        if row[4] is not None:
            farmers[farmer_id]["crops"].append({
                "crop_id": row[4],
                "crop_name": row[5],
                "price": row[6],
                "quantity": row[7],
                "season": row[8]
            })

    # Get registered consumers for ordering
    cursor.execute("""
        SELECT consumer_id, name
        FROM consumer
        ORDER BY consumer_id
    """)

    consumers = cursor.fetchall()

    return render_template(
        "farmers_crops.html",
        farmers=farmers.values(),
        consumers=consumers
    )

# ---------------- FARMER DASHBOARD ----------------
@app.route("/farmer-dashboard/<int:farmer_id>")
def farmer_dashboard(farmer_id):

    # Get farmer details
    cursor.execute(
        "SELECT * FROM farmer WHERE farmer_id = %s",
        (farmer_id,)
    )
    farmer_data = cursor.fetchone()

    if not farmer_data:
        return "Farmer not found", 404

    # Total crops
    cursor.execute("""
        SELECT COUNT(*)
        FROM crop
        WHERE farmer_id = %s
    """, (farmer_id,))

    total_crops = cursor.fetchone()[0]

    # Available stock
    cursor.execute("""
        SELECT COALESCE(SUM(quantity_kg), 0)
        FROM crop
        WHERE farmer_id = %s
    """, (farmer_id,))

    available_stock = cursor.fetchone()[0]

     # Total orders received
    cursor.execute("""
        SELECT COUNT(*)
        FROM orders o
        JOIN crop c ON o.crop_id = c.crop_id
        WHERE c.farmer_id = %s
    """, (farmer_id,))

    total_orders = cursor.fetchone()[0]

    # Pending orders
    cursor.execute("""
        SELECT COUNT(*)
        FROM orders o
        JOIN crop c ON o.crop_id = c.crop_id
        WHERE c.farmer_id = %s
        AND o.order_status IN ('Placed', 'Accepted', 'Packed')
    """, (farmer_id,))

    pending_orders = cursor.fetchone()[0]

    # Delivered sales revenue
    cursor.execute("""
        SELECT COALESCE(SUM(o.total_price), 0)
        FROM orders o
        JOIN crop c ON o.crop_id = c.crop_id
        WHERE c.farmer_id = %s
        AND o.order_status = 'Delivered'
    """, (farmer_id,))

    total_earnings = cursor.fetchone()[0]

    # Farmer's crops
    cursor.execute("""
        SELECT *
        FROM crop
        WHERE farmer_id = %s
    """, (farmer_id,))

    crops = cursor.fetchall()

    # Farmer's orders
    cursor.execute("""
        SELECT
            o.order_id,
            o.crop_id,
            o.quantity_kg,
            o.total_price,
            o.order_status,
            con.name
        FROM orders o
        JOIN crop c ON o.crop_id = c.crop_id
        JOIN consumer con ON o.consumer_id = con.consumer_id
        WHERE c.farmer_id = %s
        ORDER BY o.order_id DESC
    """, (farmer_id,))

    farmer_orders = cursor.fetchall()

    return render_template(
        "farmer_dashboard.html",
        farmer=farmer_data,
        total_crops=total_crops,
        available_stock=available_stock,
        total_orders=total_orders,
        pending_orders=pending_orders,
        total_earnings=total_earnings,
        crops=crops,
        farmer_orders=farmer_orders
    )
# ---------------- CONSUMER DASHBOARD ----------------
@app.route("/consumer-dashboard/<int:consumer_id>")
def consumer_dashboard(consumer_id):

    cursor.execute(
        "SELECT * FROM consumer WHERE consumer_id = %s",
        (consumer_id,)
    )

    consumer_data = cursor.fetchone()

    if not consumer_data:
        return "Consumer not found", 404

    cursor.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE consumer_id = %s
    """, (consumer_id,))

    total_orders = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE consumer_id = %s
        AND order_status NOT IN ('Delivered', 'Cancelled')
    """, (consumer_id,))

    active_orders = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(total_price), 0)
        FROM orders
        WHERE consumer_id = %s
        AND order_status != 'Cancelled'
    """, (consumer_id,))

    total_spent = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            o.order_id,
            c.crop_name,
            f.name,
            o.quantity_kg,
            o.total_price,
            o.order_status
        FROM orders o
        JOIN crop c ON o.crop_id = c.crop_id
        JOIN farmer f ON c.farmer_id = f.farmer_id
        WHERE o.consumer_id = %s
        ORDER BY o.order_id DESC
    """, (consumer_id,))

    orders_data = cursor.fetchall()

    return render_template(
        "consumer_dashboard.html",
        consumer=consumer_data,
        total_orders=total_orders,
        active_orders=active_orders,
        total_spent=total_spent,
        orders=orders_data
    )
# ---------------- VIEW ALL DATA ----------------
@app.route("/view")
def view():
    cursor.execute("SELECT * FROM farmer")
    farmers = cursor.fetchall()

    cursor.execute("SELECT * FROM land")
    lands = cursor.fetchall()

    cursor.execute("SELECT * FROM crop")
    crops = cursor.fetchall()

    cursor.execute("SELECT * FROM consumer")
    consumers = cursor.fetchall()

    cursor.execute("SELECT * FROM sales")
    sales_data = cursor.fetchall()

    cursor.execute("SELECT * FROM orders")
    orders_data = cursor.fetchall()

    return render_template(
        "view.html",
        farmers=farmers,
        lands=lands,
        crops=crops,
        consumers=consumers,
        sales=sales_data,
        orders=orders_data
    )

# ---------------- CROP PRICE COMPARISON ----------------
@app.route("/price-comparison")
def price_comparison():

    crop_name = request.args.get("crop_name", "").strip()

    query = """
        SELECT
            c.crop_name,
            f.name,
            f.address,
            c.price_per_kg,
            c.quantity_kg,
            c.season
        FROM crop c
        JOIN farmer f
            ON c.farmer_id = f.farmer_id
        WHERE c.quantity_kg > 0
    """

    values = []

    if crop_name:
        query += " AND c.crop_name LIKE %s"
        values.append("%" + crop_name + "%")

    query += " ORDER BY c.crop_name, c.price_per_kg ASC"

    cursor.execute(query, tuple(values))
    records = cursor.fetchall()

    # Find the lowest available price for each crop.
    lowest_prices = {}
    for row in records:
        normalized_crop_name = row[0].strip().lower()

        if normalized_crop_name not in lowest_prices:
            lowest_prices[normalized_crop_name] = row[3]

    crops = []

    for row in records:
        normalized_crop_name = row[0].strip().lower()

        crops.append({
            "crop_name": row[0],
            "farmer_name": row[1],
            "location": row[2],
            "price_per_kg": row[3],
            "quantity_kg": row[4],
            "season": row[5],
            "is_lowest": row[3] == lowest_prices[normalized_crop_name]
        })

    return render_template(
        "price_comparision.html",
        crops=crops
    )


@app.route("/sales-analytics")
def sales_analytics():

    # Overall sales statistics
    cursor.execute("""
        SELECT
            COALESCE(SUM(income), 0),
            COALESCE(SUM(quantity_sold), 0),
            COUNT(*),
            COALESCE(AVG(income), 0)
        FROM sales
    """)

    summary = cursor.fetchone()

    total_revenue = summary[0]
    total_quantity = summary[1]
    total_transactions = summary[2]
    average_sale = round(float(summary[3]), 2)

    # Crop-wise sales performance
    cursor.execute("""
        SELECT
            c.crop_name,
            SUM(s.quantity_sold),
            SUM(s.income)
        FROM sales s
        JOIN crop c ON s.crop_id = c.crop_id
        GROUP BY c.crop_id, c.crop_name
        ORDER BY SUM(s.income) DESC
    """)

    crop_records = cursor.fetchall()

    crop_sales = []

    for row in crop_records:
        crop_sales.append({
            "crop_name": row[0],
            "total_quantity": row[1],
            "total_revenue": row[2]
        })

    # Sales history
    cursor.execute("""
        SELECT
            s.sale_id,
            c.crop_name,
            s.quantity_sold,
            s.income
        FROM sales s
        JOIN crop c ON s.crop_id = c.crop_id
        ORDER BY s.sale_id DESC
    """)

    sales_records = cursor.fetchall()

    sales_data = []

    for row in sales_records:
        sales_data.append({
            "sale_id": row[0],
            "crop_name": row[1],
            "quantity_sold": row[2],
            "income": row[3]
        })

    return render_template(
        "sales_analytics.html",
        total_revenue=total_revenue,
        total_quantity=total_quantity,
        total_transactions=total_transactions,
        average_sale=average_sale,
        crop_sales=crop_sales,
        sales_data=sales_data
    )



# ---------------- SOIL TESTING ----------------
@app.route("/soil-test", methods=["GET", "POST"])
def soil_test():

    message = None
    message_type = None

    if request.method == "POST":
        try:
            land_id = int(request.form["land_id"])
            ph_value = float(request.form["ph_value"])

            if not 0 <= ph_value <= 14:
                raise ValueError("Soil pH must be between 0 and 14.")

            cursor.execute(
                "SELECT land_id FROM land WHERE land_id = %s",
                (land_id,)
            )

            if not cursor.fetchone():
                raise ValueError("Selected land does not exist.")

            cursor.execute("""
                INSERT INTO soil_test (land_id, ph_value)
                VALUES (%s, %s)
            """, (land_id, ph_value))

            db.commit()
            message = "Soil test result saved successfully!"
            message_type = "success"

        except ValueError as error:
            db.rollback()
            message = str(error)
            message_type = "error"

        except Exception as error:
            db.rollback()
            message = "Unable to save soil test: " + str(error)
            message_type = "error"

    # Get land records with farmer names
    cursor.execute("""
        SELECT l.land_id, f.name, l.location, l.soil_type
        FROM land l
        JOIN farmer f ON l.farmer_id = f.farmer_id
        ORDER BY l.land_id
    """)

    lands = cursor.fetchall()

    # Get previous soil test records
    cursor.execute("""
        SELECT
            st.test_id,
            f.name,
            l.location,
            l.soil_type,
            st.ph_value
        FROM soil_test st
        JOIN land l ON st.land_id = l.land_id
        JOIN farmer f ON l.farmer_id = f.farmer_id
        ORDER BY st.test_id DESC
    """)

    soil_records = cursor.fetchall()

    return render_template(
        "soil_test.html",
        lands=lands,
        soil_records=soil_records,
        message=message,
        message_type=message_type
    )



# ---------------- FARMER REVIEWS & RATINGS ----------------
@app.route("/farmer-reviews", methods=["GET", "POST"])
def farmer_reviews():

    message = None
    message_type = None

    # ---------------- SUBMIT REVIEW ----------------
    if request.method == "POST":

        try:
            order_id = int(request.form["order_id"])
            rating = int(request.form["rating"])
            review_text = request.form.get("review", "").strip()

            if rating < 1 or rating > 5:
                raise ValueError("Rating must be between 1 and 5.")

            # Check order and retrieve farmer and consumer
            cursor.execute("""
                SELECT
                    o.order_id,
                    o.consumer_id,
                    c.farmer_id,
                    o.order_status
                FROM orders o
                JOIN crop c ON o.crop_id = c.crop_id
                WHERE o.order_id = %s
            """, (order_id,))

            order = cursor.fetchone()

            if not order:
                raise ValueError("Order not found.")

            if not order[3] or order[3].strip().lower() != "delivered":
                raise ValueError("Only delivered orders can be reviewed.")

            # Insert review
            cursor.execute("""
                INSERT INTO farmer_reviews
                (farmer_id, consumer_id, order_id, rating, review)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                order[2],
                order[1],
                order[0],
                rating,
                review_text
            ))

            db.commit()

            message = "Your review has been submitted successfully!"
            message_type = "success"

        except ValueError as error:
            db.rollback()
            message = str(error)
            message_type = "error"

        except mysql.connector.IntegrityError:
            db.rollback()
            message = "A review has already been submitted for this order."
            message_type = "error"

        except Exception as error:
            db.rollback()
            message = "Unable to submit review: " + str(error)
            message_type = "error"

    # ---------------- FETCH EXISTING REVIEWS ----------------
    cursor.execute("""
        SELECT
            fr.review_id,
            f.name,
            con.name,
            fr.order_id,
            fr.rating,
            fr.review,
            fr.created_at
        FROM farmer_reviews fr
        JOIN farmer f
            ON fr.farmer_id = f.farmer_id
        JOIN consumer con
            ON fr.consumer_id = con.consumer_id
        ORDER BY fr.created_at DESC
    """)

    reviews = cursor.fetchall()

    # ---------------- FETCH DELIVERED ORDERS AVAILABLE FOR REVIEW ----------------
    cursor.execute("""
        SELECT
            o.order_id,
            con.name,
            f.name,
            c.crop_name
        FROM orders o
        JOIN consumer con
            ON o.consumer_id = con.consumer_id
        JOIN crop c
            ON o.crop_id = c.crop_id
        JOIN farmer f
            ON c.farmer_id = f.farmer_id
        WHERE LOWER(TRIM(o.order_status)) = 'delivered'
          AND NOT EXISTS (
              SELECT 1
              FROM farmer_reviews fr
              WHERE fr.order_id = o.order_id
          )
        ORDER BY o.order_id DESC
    """)

    available_orders = cursor.fetchall()

    print("Available orders for reviews:", available_orders)
    print("Existing farmer reviews:", reviews)

    # ---------------- DISPLAY PAGE ----------------
    return render_template(
        "farmer_reviews.html",
        available_orders=available_orders,
        reviews=reviews,
        message=message,
        message_type=message_type
    )



# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)