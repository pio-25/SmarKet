import os
import bcrypt
from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId
import datetime

# Load environment variables from a .env file
load_dotenv()

app = Flask(__name__)

# --- MongoDB Connectivity ---
try:
    MONGO_URI = os.getenv("MONGO_URI")
    client = MongoClient(MONGO_URI)
    db = client['smarket_db']
    users_collection = db['users']
    products_collection = db['products']
    orders_collection = db['orders']
    carts_collection = db['carts']
    print("✅ Successfully connected to MongoDB.")
except Exception as e:
    print(f"❌ Could not connect to MongoDB: {e}")

# --- API Endpoints ---

# Endpoint for user registration
@app.route('/api/auth/register', methods=['POST'])
def register_user():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'buyer') # Default role is 'buyer'

    if not all([username, email, password]):
        return jsonify({"error": "Missing required fields"}), 400

    # Hash the password for security
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Check if user already exists
    if users_collection.find_one({"email": email}):
        return jsonify({"error": "User with this email already exists"}), 409

    user_data = {
        "username": username,
        "email": email,
        "password": hashed_password.decode('utf-8'),
        "role": role,
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }

    try:
        result = users_collection.insert_one(user_data)
        return jsonify({
            "message": "User registered successfully",
            "user_id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint for user login
@app.route('/api/auth/login', methods=['POST'])
def login_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({"error": "Missing required fields"}), 400

    user = users_collection.find_one({"email": email})

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({
            "message": "Login successful",
            "user_id": str(user['_id']),
            "role": user.get('role', 'buyer')
        }), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401

# Endpoint to get all products for home page
@app.route('/api/products', methods=['GET'])
def get_products():
    products = list(products_collection.find())
    for product in products:
        product['_id'] = str(product['_id'])
        # Add seller name to product data
        if 'seller_id' in product:
            seller = users_collection.find_one({"_id": ObjectId(product['seller_id'])})
            product['seller_name'] = seller['username'] if seller else 'Unknown'
        else:
            product['seller_name'] = 'Unknown'
    return jsonify(products)

# Endpoint for sellers to add a product
@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    name = data.get('name')
    price = data.get('price')
    description = data.get('description')
    image = data.get('image')
    # Use a placeholder seller ID for now
    seller_id = "60c72b2f9b1e8a001c8a0d78" # Example ObjectId

    if not all([name, price, description, image]):
        return jsonify({"error": "Missing required product data"}), 400

    product_data = {
        "name": name,
        "price": price,
        "description": description,
        "image": image,
        "seller_id": ObjectId(seller_id),
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }

    try:
        result = products_collection.insert_one(product_data)
        return jsonify({
            "message": "Product added successfully",
            "product_id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint to manage all sellers (admin view)
@app.route('/api/admin/sellers', methods=['GET'])
def get_all_sellers():
    # In a real application, add authentication check for admin role
    sellers = list(users_collection.find({"role": "seller"}))
    for seller in sellers:
        seller['_id'] = str(seller['_id'])
        # For demonstration, we'll just return the name and a mock status
        seller['status'] = 'Active' if str(seller['_id']) != "60c72b2f9b1e8a001c8a0d79" else 'Pending'
    return jsonify(sellers)

# Endpoint to manage all products
@app.route('/api/admin/products', methods=['GET'])
def get_all_products():
    # In a real application, add authentication check for admin role
    products = list(products_collection.find())
    for product in products:
        product['_id'] = str(product['_id'])
        product['seller_id'] = str(product['seller_id'])
    return jsonify(products)

# Endpoint for processing a payment (cart_payment.html)
@app.route('/api/checkout', methods=['POST'])
def checkout():
    data = request.json
    buyer_id_str = data.get('buyer_id')
    cart_items = data.get('cart')
    total_price = data.get('total_price')

    if not all([buyer_id_str, cart_items, total_price is not None]):
        return jsonify({"error": "Missing required checkout data"}), 400

    try:
        buyer_id = ObjectId(buyer_id_str)
    except Exception:
        return jsonify({"error": "Invalid buyer ID format"}), 400

    order_data = {
        "buyer_id": buyer_id,
        "items": cart_items,
        "total_price": total_price,
        "status": "Pending",
        "order_date": datetime.datetime.now(datetime.timezone.utc)
    }

    try:
        orders_collection.insert_one(order_data)
        # Clear the cart after a successful checkout
        carts_collection.delete_one({"user_id": buyer_id})
        return jsonify({"message": "Checkout successful", "order_id": str(order_data['_id'])}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Cart API Endpoints ---
@app.route('/api/cart', methods=['GET'])
def get_cart():
    # Placeholder user ID for this example
    user_id_str = "60c72b2f9b1e8a001c8a0d78"
    try:
        user_id = ObjectId(user_id_str)
    except Exception:
        return jsonify({"error": "Invalid user ID"}), 400

    cart_document = carts_collection.find_one({"user_id": user_id})

    if cart_document:
        cart_items = cart_document.get('items', [])
        return jsonify(cart_items)
    else:
        # Return an empty list if the cart doesn't exist
        return jsonify([])

@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    data = request.json
    product = data.get('product')
    quantity = data.get('quantity', 1)

    if not product or not product.get('id'):
        return jsonify({"error": "Missing product data"}), 400

    # Placeholder user ID for this example
    user_id_str = "60c72b2f9b1e8a001c8a0d78"
    try:
        user_id = ObjectId(user_id_str)
    except Exception:
        return jsonify({"error": "Invalid user ID"}), 400

    cart_document = carts_collection.find_one({"user_id": user_id})

    if not cart_document:
        # Create a new cart for the user
        cart_document = {
            "user_id": user_id,
            "items": []
        }
        carts_collection.insert_one(cart_document)

    items = cart_document['items']
    existing_item = next((item for item in items if item['id'] == product['id']), None)

    if existing_item:
        # Update quantity if the item already exists
        existing_item['quantity'] = quantity
    else:
        # Add a new item to the cart
        items.append({
            "id": product['id'],
            "name": product['name'],
            "price": product['price'],
            "image": product['image'],
            "quantity": quantity
        })

    # Update the cart document in the database
    carts_collection.update_one(
        {"user_id": user_id},
        {"$set": {"items": items}}
    )

    return jsonify({"message": "Cart updated successfully"}), 200

@app.route('/api/cart/<product_id>', methods=['DELETE'])
def remove_from_cart(product_id):
    # Placeholder user ID for this example
    user_id_str = "60c72b2f9b1e8a001c8a0d78"
    try:
        user_id = ObjectId(user_id_str)
    except Exception:
        return jsonify({"error": "Invalid user ID"}), 400

    cart_document = carts_collection.find_one({"user_id": user_id})

    if not cart_document:
        return jsonify({"error": "Cart not found"}), 404

    items = cart_document.get('items', [])
    updated_items = [item for item in items if item['id'] != product_id]

    carts_collection.update_one(
        {"user_id": user_id},
        {"$set": {"items": updated_items}}
    )

    return jsonify({"message": "Product removed from cart successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)
