-- ==================== পুরানো ডাটাবেস মুছুন ====================

DROP DATABASE IF EXISTS ecommerce_db;

-- ==================== নতুন ডাটাবেস তৈরি করুন ====================

CREATE DATABASE ecommerce_db;
USE ecommerce_db;

-- ==================== USERS TABLE ====================

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(500) NOT NULL,
    is_admin INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== PRODUCTS TABLE ====================

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    quantity INT DEFAULT 0,
    image_filename VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== ORDERS TABLE ====================

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== ORDER ITEMS TABLE ====================

CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== REVENUE TABLE ====================

CREATE TABLE revenue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== INSERT DATA ====================

-- Admin User
INSERT INTO users (username, email, password, is_admin) 
VALUES ('admin', 'admin@example.com', 'scrypt:32768:8:1$MgtouXgUKja9w3fi$0e1678ca1bfc689dc26215c8c475a66c3496efb5a4a3225ddaefe1f80fb30b464dcf8cf596d3fb536e1025376bff8b22f2b7fc39f5765e89b77bf35829e6adc0', 1);

-- Products
INSERT INTO products (name, description, price, quantity) VALUES
('পেন', 'উচ্চমানের লেখার পেন', 50.00, 100),
('বই', 'শিক্ষামূলক বই সেট', 150.00, 50),
('নোটবুক', 'এ৪ সাইজ নোটবুক', 80.00, 75),
('পেন্সিল', 'এইচবি পেন্সিল প্যাক', 30.00, 200),
('রাবার', 'ইরেজার সেট', 25.00, 150);

-- ==================== যাচাই ====================

SELECT * FROM users;
SELECT * FROM products;

SHOW TABLE STATUS;