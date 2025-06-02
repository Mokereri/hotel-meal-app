CREATE DATABASE IF NOT EXISTS hotel_app_db;

USE hotel_app_db;

-- Users table (for basic login, still not fully secure without hashing)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL -- In a real app, hash this password!
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(255) PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    order_date DATETIME NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending',
    personalization_name VARCHAR(255),
    personalization_phone VARCHAR(255),
    personalization_message TEXT
);

-- Order Items table
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(255) NOT NULL,
    meal_id INT NOT NULL,
    meal_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    price_per_item DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
ALTER TABLE orders
ADD COLUMN checkout_request_id VARCHAR(255) UNIQUE NULL AFTER status;

ALTER TABLE orders
ADD COLUMN mpesa_receipt_number VARCHAR(255) NULL AFTER checkout_request_id;

ALTER TABLE orders
ADD COLUMN mpesa_transaction_date DATETIME NULL AFTER mpesa_receipt_number;

USE hotel_app_db;

-- 1. Add the 'role' column to the 'users' table
-- This column is crucial for Role-Based Access Control (RBAC).
-- It will store 'user' or 'admin'.
-- Run this ONLY if the 'role' column does not exist in your 'users' table.
ALTER TABLE users
ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'user';

-- Optional: Update existing users to 'user' role if they were created before this column was added.
-- If you have an existing 'admin@kitchen.com' user, you'll need to manually set their role to 'admin'
-- after adding the column, as the `create_user` function in the Streamlit app will handle this for new registrations.
-- For example:
-- UPDATE users SET role = 'admin' WHERE email = 'admin@kitchen.com';


-- M-Pesa Callback Related Columns for 'orders' table
-- These should already exist if your M-Pesa integration was set up previously.
-- Run these ONLY if the respective columns do not exist in your 'orders' table.

-- Add 'checkout_request_id' to track M-Pesa STK Push requests
ALTER TABLE orders
ADD COLUMN checkout_request_id VARCHAR(255) UNIQUE NULL AFTER status;

-- Add 'mpesa_receipt_number' to store the unique M-Pesa transaction ID
ALTER TABLE orders
ADD COLUMN mpesa_receipt_number VARCHAR(255) NULL AFTER checkout_request_id;

-- Add 'mpesa_transaction_date' to record when the M-Pesa payment occurred
ALTER TABLE orders
ADD COLUMN mpesa_transaction_date DATETIME NULL AFTER mpesa_receipt_number;

-- Modify the default status for new orders (if not already set)
-- This updates existing orders' status if you ran this before, but primarily affects new inserts.
ALTER TABLE orders
MODIFY COLUMN status VARCHAR(50) DEFAULT 'Pending Payment Confirmation';

---

## Data Truncation (Use with Extreme Caution!)

**WARNING:** The following `TRUNCATE TABLE` commands will **PERMANENTLY DELETE ALL DATA** from the specified tables. Only run these if you are in a development environment and are absolutely certain you want to clear all existing orders, order items, and users.

```sql
-- Disable foreign key checks temporarily, which is necessary before truncating tables
-- that have relationships with other tables.
SET FOREIGN_KEY_CHECKS = 0;

-- Delete all data from the 'orders' table
TRUNCATE TABLE hotel_app_db.orders;

-- Delete all data from the 'order_items' table
TRUNCATE TABLE hotel_app_db.order_items;

-- Delete all data from the 'users' table (Optional: Run if you want to clear all user accounts)
-- TRUNCATE TABLE hotel_app_db.users;

-- Re-enable foreign key checks after truncation is complete
SET FOREIGN_KEY_CHECKS = 1;



SELECT * 
FROM orders