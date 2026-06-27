import psycopg2
from faker import Faker
import random

fake = Faker()

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="planviz",
    user="visualizer",
    password="localdevpassword"
)
cur = conn.cursor()

NUM_CUSTOMERS = 5000
NUM_PRODUCTS = 200
NUM_ORDERS = 200000
MAX_ITEMS_PER_ORDER = 4

CATEGORIES = ["Electronics", "Clothing", "Home & Garden", "Books", "Toys", "Sports", "Beauty", "Groceries"]
STATUSES = ["pending", "shipped", "delivered", "cancelled", "refunded"]

print("Inserting customers...")
customers = []
for _ in range(NUM_CUSTOMERS):
    customers.append((
        fake.name(),
        fake.email(),
        fake.city(),
        fake.country()
    ))
cur.executemany(
    "INSERT INTO customers (full_name, email, city, country) VALUES (%s, %s, %s, %s)",
    customers
)
conn.commit()
print(f"Inserted {NUM_CUSTOMERS} customers.")

print("Inserting products...")
products = []
for _ in range(NUM_PRODUCTS):
    products.append((
        fake.word().capitalize() + " " + fake.word().capitalize(),
        random.choice(CATEGORIES),
        round(random.uniform(5, 500), 2)
    ))
cur.executemany(
    "INSERT INTO products (product_name, category, price) VALUES (%s, %s, %s)",
    products
)
conn.commit()
print(f"Inserted {NUM_PRODUCTS} products.")

print("Fetching IDs...")
cur.execute("SELECT customer_id FROM customers")
customer_ids = [row[0] for row in cur.fetchall()]

cur.execute("SELECT product_id, price FROM products")
product_rows = cur.fetchall()

print("Inserting orders...")
order_ids = []
batch = []
for i in range(NUM_ORDERS):
    batch.append((
        random.choice(customer_ids),
        random.choice(STATUSES)
    ))
    if len(batch) >= 5000:
        cur.executemany(
            "INSERT INTO orders (customer_id, order_status) VALUES (%s, %s) RETURNING order_id",
            batch
        )
        batch = []
        if i % 50000 == 0:
            print(f"  {i} orders inserted...")

# executemany doesn't support RETURNING well across rows, so we insert then fetch all IDs after commit
conn.commit()

cur.execute("SELECT order_id FROM orders")
order_ids = [row[0] for row in cur.fetchall()]
print(f"Inserted {len(order_ids)} orders.")

print("Inserting order_items...")
item_batch = []
count = 0
for oid in order_ids:
    num_items = random.randint(1, MAX_ITEMS_PER_ORDER)
    for _ in range(num_items):
        pid, price = random.choice(product_rows)
        qty = random.randint(1, 5)
        item_batch.append((oid, pid, qty, price))
        count += 1
    if len(item_batch) >= 5000:
        cur.executemany(
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
            item_batch
        )
        conn.commit()
        item_batch = []
        if count % 50000 < 5000:
            print(f"  ~{count} order_items inserted...")

if item_batch:
    cur.executemany(
        "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
        item_batch
    )
    conn.commit()

print(f"Inserted ~{count} order_items.")
print("Done!")

cur.close()
conn.close()
