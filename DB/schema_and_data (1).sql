-- ============================================================
--  ForceSight Intern Task – Sample Database: Customer Orders
--  Database: SQLite / MySQL (candidate's choice)
--  Created: 2026-06-30
-- ============================================================

-- ─── TABLE: users ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(150) UNIQUE NOT NULL,
    age         INTEGER,
    city        VARCHAR(80),
    joined_date DATE
);

-- ─── TABLE: products ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    product_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(150) NOT NULL,
    category    VARCHAR(80),
    price       DECIMAL(10, 2),
    stock       INTEGER DEFAULT 0
);

-- ─── TABLE: orders ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    order_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    product_id  INTEGER NOT NULL,
    quantity    INTEGER DEFAULT 1,
    total_amount DECIMAL(10, 2),
    order_date  DATE,
    status      VARCHAR(30) DEFAULT 'pending',
    FOREIGN KEY (user_id)    REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- ─── TABLE: support_tickets ──────────────────────────────────
CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    subject     VARCHAR(200),
    priority    VARCHAR(20) DEFAULT 'medium',
    status      VARCHAR(30) DEFAULT 'open',
    created_at  DATE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);


-- ============================================================
--  SAMPLE DATA DUMP
-- ============================================================

-- ─── users ───────────────────────────────────────────────────
INSERT INTO users (name, email, age, city, joined_date) VALUES
('Alice Johnson',   'alice@example.com',   29, 'Mumbai',    '2023-01-15'),
('Bob Sharma',      'bob@example.com',     35, 'Delhi',     '2023-03-22'),
('Carol Nair',      'carol@example.com',   27, 'Bangalore', '2023-05-10'),
('David Menon',     'david@example.com',   42, 'Chennai',   '2022-11-01'),
('Eva Pillai',      'eva@example.com',     31, 'Hyderabad', '2024-01-08'),
('Frank Reddy',     'frank@example.com',   26, 'Pune',      '2024-02-14'),
('Grace Kumar',     'grace@example.com',   38, 'Mumbai',    '2022-08-30'),
('Hank Verma',      'hank@example.com',    45, 'Kolkata',   '2023-07-19'),
('Isla Thomas',     'isla@example.com',    23, 'Jaipur',    '2024-04-01'),
('Jack Iyer',       'jack@example.com',    33, 'Bangalore', '2023-09-25');

-- ─── products ─────────────────────────────────────────────────
INSERT INTO products (name, category, price, stock) VALUES
('Wireless Headphones',  'Electronics',   2499.00, 150),
('Yoga Mat',             'Fitness',        799.00, 300),
('Python Programming Book', 'Books',       599.00, 500),
('Mechanical Keyboard',  'Electronics',  4999.00,  80),
('Running Shoes',        'Footwear',     3499.00, 200),
('Coffee Maker',         'Appliances',   2999.00,  60),
('Backpack 30L',         'Travel',       1799.00, 120),
('Noise Cancelling Earbuds', 'Electronics', 5999.00, 90),
('Water Bottle 1L',      'Fitness',        349.00, 400),
('Desk Lamp LED',        'Home Decor',     899.00, 175);

-- ─── orders ──────────────────────────────────────────────────
INSERT INTO orders (user_id, product_id, quantity, total_amount, order_date, status) VALUES
(1,  1,  1,  2499.00, '2024-03-01', 'delivered'),
(1,  3,  2,  1198.00, '2024-03-15', 'delivered'),
(2,  4,  1,  4999.00, '2024-04-02', 'delivered'),
(3,  2,  1,   799.00, '2024-04-10', 'shipped'),
(3,  9,  2,   698.00, '2024-04-18', 'delivered'),
(4,  6,  1,  2999.00, '2024-05-05', 'delivered'),
(5,  8,  1,  5999.00, '2024-05-12', 'cancelled'),
(5,  5,  1,  3499.00, '2024-05-20', 'delivered'),
(6,  7,  1,  1799.00, '2024-06-01', 'shipped'),
(7,  10, 2,  1798.00, '2024-06-08', 'delivered'),
(8,  1,  1,  2499.00, '2024-06-15', 'pending'),
(9,  3,  1,   599.00, '2024-06-20', 'delivered'),
(10, 4,  1,  4999.00, '2024-06-22', 'shipped'),
(2,  9,  3,  1047.00, '2024-06-25', 'delivered'),
(4,  2,  2,  1598.00, '2024-06-28', 'pending');

-- ─── support_tickets ─────────────────────────────────────────
INSERT INTO support_tickets (user_id, subject, priority, status, created_at) VALUES
(1,  'Order not received after 7 days',        'high',   'open',     '2024-03-10'),
(2,  'Keyboard keys not working properly',     'high',   'resolved', '2024-04-05'),
(3,  'Wrong item delivered',                   'medium', 'open',     '2024-04-20'),
(5,  'Request refund for cancelled order',     'high',   'open',     '2024-05-15'),
(6,  'Coffee maker leaked on first use',       'high',   'resolved', '2024-05-10'),
(7,  'Desk lamp flickering intermittently',    'low',    'open',     '2024-06-09'),
(8,  'Headphones not delivered yet',           'medium', 'open',     '2024-06-17'),
(9,  'Book cover was torn on arrival',         'low',    'resolved', '2024-06-22');
