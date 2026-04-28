USE railway;

CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(100) UNIQUE NOT NULL,
    email       VARCHAR(100) UNIQUE NOT NULL,
    password    VARCHAR(500) NOT NULL,
    is_admin    INT DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS products (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(255) UNIQUE NOT NULL,
    description    TEXT,
    price          DECIMAL(10,2) NOT NULL,
    quantity       INT DEFAULT 0,
    image_filename VARCHAR(255),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS orders (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status       VARCHAR(50) DEFAULT 'pending',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS order_items (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    order_id   INT NOT NULL,
    product_id INT NOT NULL,
    quantity   INT NOT NULL,
    price      DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id)   REFERENCES orders(id)   ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS revenue (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    amount   DECIMAL(10,2) NOT NULL,
    date     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT IGNORE INTO users (username, email, password, is_admin)
VALUES (
    'admin',
    'admin@example.com',
    'scrypt:32768:8:1$MgtouXgUKja9w3fi$0e1678ca1bfc689dc26215c8c475a66c3496efb5a4a3225ddaefe1f80fb30b464dcf8cf596d3fb536e1025376bff8b22f2b7fc39f5765e89b77bf35829e6adc0',
    1
);

INSERT IGNORE INTO products (name, description, price, quantity) VALUES
('Pen',        'High quality writing pen', 50.00,  100),
('Book',       'Educational book set',     150.00,  50),
('Notebook',   'A4 size notebook',          80.00,  75),
('Pencil',     'HB pencil pack',            30.00, 200),
('Eraser',     'Eraser set',                25.00, 150),
('Calculator', 'Calculator',               25.00,  150);

select* from products;
