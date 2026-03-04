import redis
import csv
import random
from collections import defaultdict

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# load cart account mappings
cart_to_account = {}
active_accounts = set()

with open('out/cart.csv', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cart_id = row['CartID']
        account_id = row['AccountID']
        cart_to_account[cart_id] = account_id
        active_accounts.add(account_id)

# load some carts into Redis
with open('out/cart_product.csv', newline='') as f:
    reader = csv.DictReader(f)

    for row in reader:
        cart_id = row['CartID']
        product_id = row['ProductID']
        quantity = row['Quantity']

        if cart_id in cart_to_account:
            account_id = cart_to_account[cart_id]

            redis_key = f"cart:{account_id}"
            r.hset(redis_key, product_id, quantity)

# set 24 hour expiration for carts
for account_id in active_accounts:
    r.expire(f"cart:{account_id}", 86400)

print(f"Loaded {len(active_accounts)} carts into Redis.")

# generate search histories for active accounts
search_terms_pool = [
    "wireless headphones",
    "noise cancelling headphones",
    "blue summer dress",
    "aqua dress",
    "large dress",
    "ceramic vase",
    "home decor vase",
    "fashion sale",
    "tablet accessories",
    "home essentials"
]

for account_id in active_accounts:
    num_searches = random.randint(3, 10)

    for _ in range(num_searches):
        term = random.choice(search_terms_pool)
        r.lpush(f"search:{account_id}", term)

    # keep only last 10 searches
    r.ltrim(f"search:{account_id}", 0, 9)

    # expire after 7 days
    r.expire(f"search:{account_id}", 604800)

print("Search histories generated.")
print("Redis population complete.")
