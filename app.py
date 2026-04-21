from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pymysql
import pymysql.cursors
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mysecretkey2026')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

DB_CONFIG = {
    'host': os.environ.get('MYSQLHOST', 'shinkansen.proxy.rlwy.net'),
    'port': int(os.environ.get('MYSQLPORT', 29655)),
    'user': os.environ.get('MYSQLUSER', 'root'),
    'password': os.environ.get('MYSQLPASSWORD', 'gIkrfNobviTrJZkTqqIOBEinnlzsrbJb'),
    'database': os.environ.get('MYSQLDATABASE', 'railway'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'connect_timeout': 10,
    'read_timeout': 30,
    'write_timeout': 30,
}

def get_db():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database error: {e}")
        return None

def query(sql, params=None, fetch_one=False, fetch_all=False):
    conn = get_db()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params) if params else cursor.execute(sql)
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                conn.commit()
                return True
    except Exception as e:
        print(f"Query error: {e}")
        return None
    finally:
        conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    products = query('SELECT * FROM products ORDER BY created_at DESC', fetch_all=True)
    return render_template('index.html', products=products or [])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        error = None

        if not username:
            error = 'Username is required'
        elif not email:
            error = 'Email is required'
        elif not password:
            error = 'Password is required'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters'

        if error is None:
            hashed = generate_password_hash(password)
            try:
                query('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
                      (username, email, hashed))
                return redirect(url_for('login'))
            except:
                error = 'Username or email already exists'

        return render_template('register.html', error=error)
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = query('SELECT * FROM users WHERE username = %s', (username,), fetch_one=True)
        error = None

        if user is None:
            error = 'Invalid username'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = bool(user['is_admin'])
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))

        return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))



@app.route('/cart')
@login_required
def cart():
    cart_items = session.get('cart', {})
    items = []
    total = 0
    for product_id, quantity in cart_items.items():
        try:
            product = query('SELECT * FROM products WHERE id = %s', (int(product_id),), fetch_one=True)
            if product:
                subtotal = float(product['price']) * quantity
                items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
                total += subtotal
        except:
            continue
    return render_template('cart.html', items=items, total=total)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    try:
        quantity = int(request.form.get('quantity', 1))
        if quantity < 1:
            quantity = 1
    except:
        quantity = 1

    if 'cart' not in session:
        session['cart'] = {}

    product_id_str = str(product_id)
    if product_id_str in session['cart']:
        session['cart'][product_id_str] += quantity
    else:
        session['cart'][product_id_str] = quantity
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST', 'GET'])
@login_required
def remove_from_cart(product_id):
    if 'cart' in session and str(product_id) in session['cart']:
        del session['cart'][str(product_id)]
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/checkout')
@login_required
def checkout():
    if not session.get('cart'):
        return redirect(url_for('cart'))
    return render_template('payment.html')

@app.route('/process_payment', methods=['POST'])
@login_required
def process_payment():
    cart_items = session.get('cart', {})
    if not cart_items:
        return jsonify({'success': False, 'message': 'Cart is empty'})

    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection error'})

    try:
        with conn.cursor() as cursor:
            total = 0
            order_details = []

            for product_id, quantity in cart_items.items():
                cursor.execute('SELECT id, price, quantity FROM products WHERE id = %s', (int(product_id),))
                product = cursor.fetchone()
                if product:
                    if product['quantity'] < quantity:
                        return jsonify({'success': False, 'message': 'Insufficient stock'})
                    subtotal = float(product['price']) * quantity
                    total += subtotal
                    order_details.append({
                        'product_id': int(product_id),
                        'quantity': quantity,
                        'price': float(product['price'])
                    })

            cursor.execute('INSERT INTO orders (user_id, total_amount, status) VALUES (%s, %s, %s)',
                           (session['user_id'], total, 'completed'))
            order_id = cursor.lastrowid

            for detail in order_details:
                cursor.execute('INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)',
                               (order_id, detail['product_id'], detail['quantity'], detail['price']))
                cursor.execute('UPDATE products SET quantity = quantity - %s WHERE id = %s',
                               (detail['quantity'], detail['product_id']))

            cursor.execute('INSERT INTO revenue (order_id, amount) VALUES (%s, %s)', (order_id, total))
            conn.commit()

            session['cart'] = {}
            session.modified = True
            return jsonify({'success': True, 'message': 'Payment successful!', 'order_id': order_id})

    except Exception as e:
        print(f"Payment error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        conn.close()



@app.route('/admin')
@admin_required
def admin_dashboard():
    try:
        all_users = query('SELECT COUNT(*) as count FROM users', fetch_one=True)
        customers = query('SELECT COUNT(*) as count FROM users WHERE is_admin = 0', fetch_one=True)
        products = query('SELECT COUNT(*) as count FROM products', fetch_one=True)
        orders = query('SELECT COUNT(*) as count FROM orders', fetch_one=True)
        revenue = query('SELECT SUM(amount) as total FROM revenue', fetch_one=True)
        return render_template('admin.html',
                               total_users=all_users['count'] if all_users else 0,
                               customers=customers['count'] if customers else 0,
                               products=products['count'] if products else 0,
                               orders=orders['count'] if orders else 0,
                               revenue=revenue['total'] if revenue and revenue['total'] else 0)
    except Exception as e:
        return f"<h2>Dashboard Error: {str(e)}</h2>", 500

@app.route('/admin/products')
@admin_required
def admin_products():
    try:
        products = query('SELECT * FROM products ORDER BY created_at DESC', fetch_all=True)
        return render_template('products_list.html', products=products or [])
    except Exception as e:
        return f"<h2>Products Error: {str(e)}</h2><a href='/admin'>Back</a>", 500

@app.route('/admin/add_product', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price_str = request.form.get('price', '')
        quantity_str = request.form.get('quantity', '')
        error = None

        if not name:
            error = 'Product name is required'
        try:
            price = float(price_str) if price_str else 0
            if price <= 0:
                error = 'Price must be greater than 0'
        except ValueError:
            error = 'Price must be a number'
        try:
            quantity = int(quantity_str) if quantity_str else 0
            if quantity < 0:
                error = 'Quantity cannot be negative'
        except ValueError:
            error = 'Quantity must be a number'

        if error:
            return render_template('add_product.html', error=error)

        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{int(datetime.now().timestamp())}_{filename}"
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_filename = filename

        query('INSERT INTO products (name, description, price, quantity, image_filename) VALUES (%s, %s, %s, %s, %s)',
              (name, description, price, quantity, image_filename))
        return redirect(url_for('admin_products'))
    return render_template('add_product.html')

@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price_str = request.form.get('price', '')
        quantity_str = request.form.get('quantity', '')
        error = None

        if not name:
            error = 'Product name is required'
        try:
            price = float(price_str) if price_str else 0
            if price <= 0:
                error = 'Price must be greater than 0'
        except ValueError:
            error = 'Price must be a number'
        try:
            quantity = int(quantity_str) if quantity_str else 0
            if quantity < 0:
                error = 'Quantity cannot be negative'
        except ValueError:
            error = 'Quantity must be a number'

        if error:
            product = query('SELECT * FROM products WHERE id = %s', (product_id,), fetch_one=True)
            return render_template('edit_product.html', product=product, error=error)

        product = query('SELECT image_filename FROM products WHERE id = %s', (product_id,), fetch_one=True)
        image_filename = product['image_filename'] if product else None

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{int(datetime.now().timestamp())}_{filename}"
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_filename = filename

        query('UPDATE products SET name = %s, description = %s, price = %s, quantity = %s, image_filename = %s WHERE id = %s',
              (name, description, price, quantity, image_filename, product_id))
        return redirect(url_for('admin_products'))

    product = query('SELECT * FROM products WHERE id = %s', (product_id,), fetch_one=True)
    if not product:
        return redirect(url_for('admin_products'))
    return render_template('edit_product.html', product=product)

@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    query('DELETE FROM products WHERE id = %s', (product_id,))
    return redirect(url_for('admin_products'))

@app.route('/admin/customers')
@admin_required
def admin_customers():
    try:
        customers = query('SELECT id, username, email, created_at FROM users WHERE is_admin = 0 ORDER BY created_at DESC', fetch_all=True)
        return render_template('customers.html', customers=customers or [])
    except Exception as e:
        return f"<h2>Customers Error: {str(e)}</h2><a href='/admin'>Back</a>", 500

@app.route('/admin/orders')
@admin_required
def admin_orders():
    try:
        orders = query('''SELECT o.id, o.user_id, o.total_amount, o.status, o.created_at, u.username
                          FROM orders o JOIN users u ON o.user_id = u.id
                          ORDER BY o.created_at DESC''', fetch_all=True)
        return render_template('orders.html', orders=orders or [])
    except Exception as e:
        return f"<h2>Orders Error: {str(e)}</h2><a href='/admin'>Back</a>", 500

@app.route('/admin/order_details/<int:order_id>')
@admin_required
def order_details(order_id):
    try:
        order = query('''SELECT o.id, o.total_amount, o.status, o.created_at, u.id as user_id, u.username, u.email
                         FROM orders o JOIN users u ON o.user_id = u.id WHERE o.id = %s''',
                      (order_id,), fetch_one=True)
        if not order:
            return redirect(url_for('admin_orders'))
        items = query('''SELECT oi.id, oi.quantity, oi.price, p.id as product_id, p.name
                         FROM order_items oi JOIN products p ON oi.product_id = p.id
                         WHERE oi.order_id = %s''', (order_id,), fetch_all=True)
        return render_template('order_details.html', order=order, items=items or [])
    except Exception as e:
        return f"<h2>Order Detail Error: {str(e)}</h2><a href='/admin/orders'>Back</a>", 500

@app.route('/admin/update_order_status/<int:order_id>/<status>', methods=['POST'])
@admin_required
def update_order_status(order_id, status):
    valid_statuses = ['pending', 'processing', 'completed', 'cancelled']
    if status not in valid_statuses:
        return jsonify({'success': False, 'message': 'Invalid status'})
    query('UPDATE orders SET status = %s WHERE id = %s', (status, order_id))
    return jsonify({'success': True, 'message': 'Status updated successfully'})

@app.route('/admin/revenue')
@admin_required
def admin_revenue():
    try:
        revenue_data = query('SELECT r.id, r.order_id, r.amount, r.date FROM revenue r ORDER BY r.date DESC', fetch_all=True)
        total_revenue = query('SELECT SUM(amount) as total FROM revenue', fetch_one=True)
        total_orders = query('SELECT COUNT(*) as count FROM orders', fetch_one=True)
        return render_template('revenue.html',
                               revenue_data=revenue_data or [],
                               total=total_revenue['total'] if total_revenue and total_revenue['total'] else 0,
                               orders=total_orders['count'] if total_orders else 0)
    except Exception as e:
        return f"<h2>Revenue Error: {str(e)}</h2><a href='/admin'>Back</a>", 500



@app.errorhandler(404)
def page_not_found(e):
    return "<h2 style='text-align:center;margin-top:100px'>404 - Page Not Found</h2><p style='text-align:center'><a href='/'>Go Home</a></p>", 404

@app.errorhandler(500)
def internal_error(e):
    return "<h2 style='text-align:center;margin-top:100px'>500 - Internal Server Error</h2><p style='text-align:center'><a href='/'>Go Home</a></p>", 500



if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)