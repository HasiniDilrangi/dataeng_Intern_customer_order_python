import pandas as pd
import mysql.connector

# Load CSV files
customers_df = pd.read_csv(r"C:\Users\DILRANGI\Downloads\customers.csv")
orders_df = pd.read_csv(r"C:\Users\DILRANGI\Downloads\order.csv")

# ---- Data Preprocessing part ----

# Remove duplicates / Data Cleaning
customers_df = customers_df.drop_duplicates()
orders_df = orders_df.drop_duplicates()

# Handle missing values / Data Cleaning
customers_df = customers_df.dropna()
orders_df = orders_df.dropna()

# Filter the orders with customer_id
valid_customer_ids = customers_df['customer_id'].unique()
orders_df = orders_df[orders_df['customer_id'].isin(valid_customer_ids)]

# MySQL Database connection
db_connection = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='datatest'
)

cursor = db_connection.cursor()

# ---- Create Tables in Mysql----

# Create customers table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INT PRIMARY KEY,
        customer_name VARCHAR(255)
    )
''')

# Create orders table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id INT PRIMARY KEY,
        customer_id INT,
        total_amount DECIMAL(10, 2),
        order_date DATETIME,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    )
''')

# Insert customers data
for index, row in customers_df.iterrows():
    cursor.execute('''
        INSERT INTO customers (customer_id, customer_name) 
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE customer_name = VALUES(customer_name)
    ''', (row['customer_id'], row['name']))

# Insert orders data
for index, row in orders_df.iterrows():
    cursor.execute('''
        INSERT INTO orders (order_id, customer_id, total_amount, order_date) 
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE total_amount = VALUES(total_amount), order_date = VALUES(order_date)
    ''', (row['id'], row['customer_id'], row['total_amount'], row['created_at']))


# Commit the transactions
db_connection.commit()

# Close cursor and connection
cursor.close()
db_connection.close()
