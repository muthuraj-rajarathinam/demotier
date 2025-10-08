import sqlite3
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from contextlib import contextmanager
from flask import Flask, send_from_directory, request, jsonify

# --- Flask App Configuration ---
app = Flask(__name__)
DATABASE = '/app/data/elegance_chocolat.db'
import os
os.makedirs(os.path.dirname(DATABASE), exist_ok=True)

# --- Database Utilities ---

@contextmanager
def get_db():
    """Context manager for database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initializes the database structure and inserts dummy product data."""
    with get_db() as db:
        cursor = db.cursor()

        # 1. Product Catalog (Static Data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                flavor TEXT,
                img TEXT
            );
        """)

        # 2. Orders (Transactional Data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                order_date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT NOT NULL
            );
        """)
        
        # 3. Order Items (Detailed Transactional Data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (order_id)
            );
        """)
        
        # Insert initial product data (must match the frontend's product IDs for calculation)
        products_data = [
            ('prod-001', '70% Dark Cacao Bar', 8.00, 'Intense, deep, pure', 'https://images.pexels.com/photos/6167328/pexels-photo-6167328.jpeg'),
            ('prod-002', 'Sea Salt Dark Squares', 12.00, 'Dark chocolate, sea salt flakes', 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?ixid=M3w5MTc5fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=facearea&w=400&q=80'),
            ('prod-003', 'Espresso Milk Bar', 10.00, 'Smooth milk chocolate, espresso', 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?ixid=M3w5MTc5fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=facearea&w=400&q=80'),
            ('prod-004', 'White Raspberry Truffle', 14.00, 'White chocolate, raspberry', 'https://images.unsplash.com/photo-1527515637462-cff94eecc1ac?ixid=M3w5MTc5fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=facearea&w=400&q=80'),
            ('prod-005', 'Champagne Truffle', 17.00, 'Milk chocolate, champagne', 'https://images.pexels.com/photos/4399753/pexels-photo-4399753.jpeg'),
            ('prod-006', 'Salted Caramel Praline', 16.00, 'Milk chocolate, salted caramel', 'https://images.pexels.com/photos/7676087/pexels-photo-7676087.jpeg')
        ]
        
        for p_id, name, price, flavor, img in products_data:
            # Using INSERT OR REPLACE for easy data resets during testing
            cursor.execute("INSERT OR REPLACE INTO products (id, name, price, flavor, img) VALUES (?, ?, ?, ?, ?)", 
                           (p_id, name, price, flavor, img))

        db.commit()

# Initialize the database on application start
with app.app_context():
    init_db()


# --- 3. Frontend Serving Route ---

@app.route('/')
def serve_index():
    """Serves the main HTML file to the client."""
    # Assumes index.html is in the same directory as app.py
    try:
        return send_from_directory("static", "index.html")
    except FileNotFoundError:
        return "Error: index.html not found. Make sure both files are in the same directory.", 404


# --- 4. API Endpoints ---

@app.route('/api/products', methods=['GET'])
def get_products():
    """
    Returns the product catalog and categories.
    """
    with get_db() as db:
        products_db = db.execute("SELECT id, name, price, flavor, img FROM products").fetchall()
    
    # Convert DB rows to list of dictionaries
    products = [dict(row) for row in products_db]
    
    # Static category data (can also be moved to DB if dynamic)
    categories = [
        {"id": 1, "name": "Dark Chocolate", "img": "https://images.pexels.com/photos/65882/chocolate-dark-coffee-confiserie-65882.jpeg", "flavors": ["70% Cacao", "Espresso", "Sea Salt", "Orange Zest"]},
        {"id": 2, "name": "Milk Chocolate", "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?ixid=M3w5MTc5fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=facearea&w=400&q=80", "flavors": ["Classic", "Hazelnut", "Caramel", "Almond"]},
        {"id": 3, "name": "Truffles & Pralines", "img": "https://images.pexels.com/photos/19121798/pexels-photo-19121798.jpeg", "flavors": ["Champagne", "Salted Caramel", "Tiramisu", "Rum"]}
    ]
    
    response = {
        "categories": categories,
        "products": products
    }
    
    return jsonify(response)


@app.route('/api/checkout', methods=['POST'])
def checkout():
    """
    Processes the order, calculates the total based on DB prices,
    stores the order details in SQL, and returns a confirmation.
    """
    data = request.get_json()
    cart_items = data.get('items', [])
    
    if not cart_items:
        return jsonify({"message": "Cart is empty."}), 400

    with get_db() as db:
        cursor = db.cursor()
        
        # 1. Fetch current product prices for security and validation
        product_ids = [item['id'] for item in cart_items]
        # Use SET to remove duplicates from product_ids before querying
        unique_product_ids = list(set(product_ids))
        
        placeholders = ','.join('?' for _ in unique_product_ids)
        
        product_details = cursor.execute(
            f"SELECT id, name, price FROM products WHERE id IN ({placeholders})", 
            unique_product_ids
        ).fetchall()
        
        # Convert to dictionary for quick lookup: {'prod-001': RowObject, ...}
        product_lookup = {p['id']: p for p in product_details}
        
        # 2. Calculate final total and validate
        total_amount = 0.0
        order_items_to_save = []

        for item in cart_items:
            product_id = item.get('id')
            quantity = item.get('qty', 0)
            
            # Basic validation
            if product_id not in product_lookup or not isinstance(quantity, int) or quantity <= 0:
                return jsonify({"message": f"Invalid item or quantity found in cart."}), 400
                
            product = product_lookup[product_id]
            unit_price = product['price']
            total_amount += unit_price * quantity
            
            order_items_to_save.append({
                "product_id": product_id,
                "product_name": product['name'],
                "quantity": quantity,
                "unit_price": unit_price
            })

        # 3. Store Order in SQL
        try:
            order_id = str(uuid.uuid4())
            order_date = datetime.now().isoformat()
            status = "Processing"
            
            # Save to orders table
            cursor.execute(
                "INSERT INTO orders (order_id, order_date, total_amount, status) VALUES (?, ?, ?, ?)",
                (order_id, order_date, total_amount, status)
            )
            
            # Save to order_items table
            for item in order_items_to_save:
                cursor.execute(
                    "INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price) VALUES (?, ?, ?, ?, ?)",
                    (order_id, item['product_id'], item['product_name'], item['quantity'], item['unit_price'])
                )
                
            db.commit()
            
        except sqlite3.Error as e:
            db.rollback()
            print(f"Database error during checkout: {e}")
            return jsonify({"message": "Server encountered a database error. Please try again."}), 500

        # 4. Return Confirmation
        return jsonify({
            "orderId": order_id,
            "status": status,
            "total": round(total_amount, 2),
            "message": "Order placed successfully!"
        }), 200

if __name__ == '__main__':
    # Running on port 5000 is standard for Flask
    app.run(debug=True, port=5000)
