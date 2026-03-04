import csv
import random
import uuid
from datetime import datetime, timedelta

NUM_EVENTS = 500000
SEARCH_TERMS = ["headphones", "blue dress", "ceramic vase", "summer fashion", "home decor"]
DEVICE_TYPES = ["laptop", "tablet", "mobile"]


# Load IDs from existing CSVs
def load_column(filename, column_name):
    with open(filename, newline='') as f:
        reader = csv.DictReader(f)
        return [row[column_name] for row in reader]

account_ids = load_column("out/account.csv", "AccountID")
product_ids = load_column("out/product.csv", "ProductID")

# Generate events
start_date = datetime.now() - timedelta(days=180)

with open("out/user_events.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        "eventId", "accountId",
        "eventType", "productId",
        "searchTerm", "deviceType",
        "timestamp", "timeOnPageSeconds"
    ])

    for _ in range(NUM_EVENTS):
        event_type = random.choice(["product_view", "search"])

        account_id = random.choice(account_ids)
        device = random.choice(DEVICE_TYPES)

        timestamp = start_date + timedelta(
            seconds=random.randint(0, 180 * 24 * 60 * 60)
        )

        if event_type == "product_view":
            product_id = random.choice(product_ids)
            search_term = ""
            time_spent = random.randint(5, 300)
        else:
            product_id = ""
            search_term = random.choice(SEARCH_TERMS)
            time_spent = ""

        writer.writerow([
            str(uuid.uuid4()),
            account_id,
            event_type,
            product_id,
            search_term,
            device,
            timestamp.isoformat(),
            time_spent
        ])
