import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple

SEED = 42
OUT_DIR = Path("out")

# Inputs from earlier phases
ACCOUNT_CSV = OUT_DIR / "account.csv"
PRODUCT_CSV = OUT_DIR / "product.csv"
VARIANT_MAP_CSV = OUT_DIR / "product_variant_map.csv"
SHIPPING_CSV = OUT_DIR / "shipping_option.csv"

# Outputs for Phase 3
CART_OUT = OUT_DIR / "cart.csv"
CART_PRODUCT_OUT = OUT_DIR / "cart_product.csv"
ORDER_OUT = OUT_DIR / "order.csv"
ORDER_ITEM_OUT = OUT_DIR / "order_item.csv"
PAYMENT_OUT = OUT_DIR / "payment.csv"
RETURN_OUT = OUT_DIR / "return.csv"
RETURN_ITEM_OUT = OUT_DIR / "return_item.csv"

UTC = timezone.utc

N_ORDERS = 100_000

# Return probabilities by category (Category attribute values in your variant map)
RETURN_PROB = {
    "FASHION": 0.12,
    "HOME": 0.06,
    "TECH": 0.04,
}

# Shipping option selection probabilities (roughly realistic).
# These IDs assume you used the earlier script's ShippingOptionIDs 1..5.
# If your shipping IDs differ, the code falls back safely.
SHIPPING_WEIGHTS = [
    (1, 0.35),  # Standard
    (2, 0.18),  # Expedited
    (3, 0.04),  # Overnight
    (4, 0.38),  # Free 50+
    (5, 0.05),  # Pickup
]

DEVICE_WEIGHTS = [
    ("MOBILE", 0.42),
    ("TABLET", 0.18),
    ("LAPTOP", 0.25),
    ("DESKTOP", 0.13),
    ("UNKNOWN", 0.02),
]


# ----------------------------
# Helpers
# ----------------------------

def utc_now() -> datetime:
    return datetime.now(tz=UTC)

def fmt_dt(dt: datetime) -> str:
    # MySQL DATETIME: "YYYY-MM-DD HH:MM:SS"
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def rand_dt_within_days(days_back: int) -> datetime:
    end = utc_now()
    start = end - timedelta(days=days_back)
    delta_seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, delta_seconds))

def choose_weighted(options: List[Tuple[object, float]]):
    vals = [v for v, _ in options]
    weights = [w for _, w in options]
    return random.choices(vals, weights=weights, k=1)[0]

def write_csv(path: Path, header: List[str], rows: List[List[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

def money_str_to_float(s: str) -> float:
    return float(s)

def money(x: float) -> str:
    return f"{x:.2f}"


# ----------------------------
# Load dimensions
# ----------------------------

def load_account_ids(path: Path) -> List[int]:
    ids = []
    with path.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            ids.append(int(row["AccountID"]))
    return ids

def load_products(path: Path) -> Dict[int, Dict[str, str]]:
    """
    product.csv: ProductID, Name, Description, Price
    """
    products: Dict[int, Dict[str, str]] = {}
    with path.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            pid = int(row["ProductID"])
            products[pid] = row
    return products

def load_product_category(variant_map_csv: Path) -> Dict[int, str]:
    """
    product_variant_map.csv has Category per ProductID
    """
    cat: Dict[int, str] = {}
    with variant_map_csv.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            cat[int(row["ProductID"])] = row["Category"]
    return cat

def load_shipping_ids(path: Path) -> List[int]:
    ids = []
    with path.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            ids.append(int(row["ShippingOptionID"]))
    return ids


# ----------------------------
# Sampling logic
# ----------------------------

def sample_items_per_order() -> int:
    # Most orders are small (1-3 items); some 4-6
    return choose_weighted([(1, 0.45), (2, 0.30), (3, 0.15), (4, 0.06), (5, 0.03), (6, 0.01)])

def sample_quantity_per_line() -> int:
    # Most quantities are 1, sometimes 2-3
    return choose_weighted([(1, 0.82), (2, 0.13), (3, 0.04), (4, 0.01)])

def choose_order_status() -> str:
    # Status distribution; kept simple and consistent with payment
    return choose_weighted([
        ("DELIVERED", 0.72),
        ("SHIPPED",   0.12),
        ("PAID",      0.06),
        ("PLACED",    0.04),
        ("CANCELLED", 0.06),
    ])

def payment_method() -> str:
    return choose_weighted([
        ("CREDIT_CARD",   0.78),
        ("DEBIT_CARD",    0.12),
        ("BANK_TRANSFER", 0.10),
    ])

def payment_status_for_order(order_status: str) -> str:
    if order_status == "CANCELLED":
        return "DECLINED"
    if order_status == "PLACED":
        return "PENDING"
    return "APPROVED"

def maybe_mark_returned(order_status: str, order_item_pids: List[int], pid_to_cat: Dict[int, str]) -> bool:
    """
    Returns happen only if delivered (or later marked returned).
    Probability is basket-driven by categories in the basket.
    """
    if order_status not in ("DELIVERED", "RETURNED"):
        return False

    # Basket return probability: 1 - product of (1 - p_cat)
    p_no = 1.0
    for pid in order_item_pids:
        cat = pid_to_cat.get(pid, "TECH")
        p = RETURN_PROB.get(cat, 0.05)
        p_no *= (1 - p)
    p_return = 1 - p_no

    return random.random() < p_return

def choose_return_status() -> str:
    return choose_weighted([
        ("REFUNDED",   0.55),
        ("RECEIVED",   0.20),
        ("IN_TRANSIT", 0.15),
        ("INITIATED",  0.08),
        ("REJECTED",   0.02),
    ])

def compute_returned_quantity(qty_ordered: int) -> int:
    # Usually return all of the line; sometimes partial
    if qty_ordered <= 1:
        return 1
    return choose_weighted([
        (qty_ordered, 0.70),
        (max(1, qty_ordered - 1), 0.25),
        (1, 0.05),
    ])

def gen_last_update_for_cart(created: datetime, placed: datetime) -> datetime:
    # last update between created and placed
    if placed <= created:
        return created
    delta = placed - created
    return created + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


# ----------------------------
# Extra carts (ACTIVE + ABANDONED)
# ----------------------------

def sample_cart_items_noncheckout() -> int:
    # Many non-checkout carts have 1-3 items; some are empty
    return choose_weighted([(0, 0.10), (1, 0.40), (2, 0.25), (3, 0.15), (4, 0.06), (5, 0.03), (6, 0.01)])

def cart_status_counts(n_accounts: int) -> Tuple[int, int]:
    """
    Returns (n_active, n_abandoned) additional carts to generate.

    With 10k accounts:
      active ~15% => 1500
      abandoned ~0.6 per account => 6000
    """
    n_active = int(0.15 * n_accounts)
    n_abandoned = int(0.60 * n_accounts)
    return n_active, n_abandoned

def gen_extra_carts_and_items(
    account_ids: List[int],
    products: Dict[int, Dict[str, str]],
    start_cart_id: int,
    start_cart_product_id: int
) -> Tuple[List[List[object]], List[List[object]], int, int]:
    """
    Generate additional ACTIVE and ABANDONED carts not tied to orders.

    Returns:
      extra_carts, extra_cart_products, next_cart_id, next_cart_product_id
    """
    product_ids = list(products.keys())
    n_active, n_abandoned = cart_status_counts(len(account_ids))

    extra_carts: List[List[object]] = []
    extra_cart_products: List[List[object]] = []

    next_cart_id = start_cart_id
    next_cart_product_id = start_cart_product_id

    # ACTIVE carts (recent)
    for _ in range(n_active):
        account_id = random.choice(account_ids)
        created = utc_now() - timedelta(days=random.randint(1, 7), minutes=random.randint(0, 60 * 24))
        last_update = utc_now() - timedelta(hours=random.randint(0, 48))
        if last_update < created:
            last_update = created

        device = choose_weighted(DEVICE_WEIGHTS)

        cart_id = next_cart_id
        next_cart_id += 1

        extra_carts.append([cart_id, account_id, "ACTIVE", fmt_dt(created), fmt_dt(last_update), device])

        k = sample_cart_items_noncheckout()
        if k > 0:
            chosen = random.sample(product_ids, k=min(k, len(product_ids)))
            for pid in chosen:
                qty = sample_quantity_per_line()
                price = money_str_to_float(products[pid]["Price"])
                extra_cart_products.append([next_cart_product_id, cart_id, pid, qty, money(price)])
                next_cart_product_id += 1

    # ABANDONED carts (older; last update not recent)
    for _ in range(n_abandoned):
        account_id = random.choice(account_ids)
        created = rand_dt_within_days(365)

        # last update generally within a few days of creation, but ensure it's at least 14 days ago
        last_update = created + timedelta(hours=random.randint(0, 72))
        cutoff = utc_now() - timedelta(days=14)
        if last_update > cutoff:
            last_update = cutoff - timedelta(hours=random.randint(1, 48))

        device = choose_weighted(DEVICE_WEIGHTS)

        cart_id = next_cart_id
        next_cart_id += 1

        extra_carts.append([cart_id, account_id, "ABANDONED", fmt_dt(created), fmt_dt(last_update), device])

        k = sample_cart_items_noncheckout()
        if k > 0:
            chosen = random.sample(product_ids, k=min(k, len(product_ids)))
            for pid in chosen:
                qty = sample_quantity_per_line()
                price = money_str_to_float(products[pid]["Price"])
                extra_cart_products.append([next_cart_product_id, cart_id, pid, qty, money(price)])
                next_cart_product_id += 1

    return extra_carts, extra_cart_products, next_cart_id, next_cart_product_id


# ----------------------------
# Main generator
# ----------------------------

def generate_facts(
    account_ids: List[int],
    products: Dict[int, Dict[str, str]],
    pid_to_cat: Dict[int, str],
    shipping_ids: List[int],
):
    product_ids = list(products.keys())

    # Output rows
    carts: List[List[object]] = []
    cart_products: List[List[object]] = []
    orders: List[List[object]] = []
    order_items: List[List[object]] = []
    payments: List[List[object]] = []
    returns: List[List[object]] = []
    return_items: List[List[object]] = []

    # Sequential IDs (explicit IDs are OK with MySQL AUTO_INCREMENT tables)
    next_cart_id = 1
    next_cart_product_id = 1
    next_order_id = 1
    next_order_item_id = 1
    next_payment_id = 1
    next_return_id = 1
    next_return_item_id = 1

    for _ in range(N_ORDERS):
        account_id = random.choice(account_ids)

        # Cart and order times
        time_placed = rand_dt_within_days(365)
        cart_created = time_placed - timedelta(minutes=random.randint(5, 60 * 24 * 7))  # up to 7 days before
        cart_last_update = gen_last_update_for_cart(cart_created, time_placed)

        device = choose_weighted(DEVICE_WEIGHTS)

        # Cart (always converted because it's 1 cart per order)
        cart_id = next_cart_id
        next_cart_id += 1
        carts.append([
            cart_id,
            account_id,
            "CONVERTED",
            fmt_dt(cart_created),
            fmt_dt(cart_last_update),
            device,
        ])

        # Choose shipping
        shipping_id = choose_weighted(SHIPPING_WEIGHTS)
        if shipping_id not in shipping_ids:
            shipping_id = shipping_ids[0]

        # Order status
        ostatus = choose_order_status()

        # Choose items (products) for this order
        n_lines = sample_items_per_order()
        chosen_pids = random.sample(product_ids, k=min(n_lines, len(product_ids)))

        this_order_item_pid_qty_price = []

        # Build cart_product and order_item rows
        for pid in chosen_pids:
            qty = sample_quantity_per_line()
            price = money_str_to_float(products[pid]["Price"])

            cart_products.append([next_cart_product_id, cart_id, pid, qty, money(price)])
            next_cart_product_id += 1

            order_item_id = next_order_item_id
            order_items.append([order_item_id, next_order_id, pid, qty, money(price)])
            next_order_item_id += 1

            this_order_item_pid_qty_price.append((order_item_id, pid, qty, price))

        # Decide return
        will_return = maybe_mark_returned(ostatus, chosen_pids, pid_to_cat)
        if will_return and ostatus == "DELIVERED" and random.random() < 0.75:
            ostatus = "RETURNED"

        # Order row
        order_id = next_order_id
        next_order_id += 1
        orders.append([order_id, account_id, cart_id, ostatus, fmt_dt(time_placed), shipping_id])

        # Payment row
        pmethod = payment_method()
        pstatus = payment_status_for_order(ostatus)

        pay_date = None
        if pstatus in ("APPROVED", "REFUNDED"):
            pay_date = fmt_dt(time_placed + timedelta(minutes=random.randint(0, 180)))

        payments.append([next_payment_id, order_id, pmethod, pstatus, pay_date])
        next_payment_id += 1

        # Return + ReturnItems
        if will_return:
            rstatus = choose_return_status()
            return_id = next_return_id
            next_return_id += 1

            returns.append([return_id, order_id, account_id, rstatus])

            # Select 1..k items from this order to return
            k = choose_weighted([(1, 0.60), (2, 0.25), (3, 0.10), (4, 0.05)])
            k = min(k, len(this_order_item_pid_qty_price))
            returned_lines = random.sample(this_order_item_pid_qty_price, k=k)

            for (oi_id, pid, qty_ordered, price) in returned_lines:
                qty_returned = compute_returned_quantity(qty_ordered)
                refund_amount = qty_returned * price

                return_items.append([next_return_item_id, return_id, oi_id, qty_returned, money(refund_amount)])
                next_return_item_id += 1

            # If refunded, mark payment refunded (update last payment row)
            if rstatus == "REFUNDED":
                payments[-1][3] = "REFUNDED"

    # Add extra ACTIVE + ABANDONED carts not tied to orders
    extra_carts, extra_cart_products, next_cart_id, next_cart_product_id = gen_extra_carts_and_items(
        account_ids=account_ids,
        products=products,
        start_cart_id=next_cart_id,
        start_cart_product_id=next_cart_product_id
    )
    carts.extend(extra_carts)
    cart_products.extend(extra_cart_products)

    return carts, cart_products, orders, order_items, payments, returns, return_items


def main():
    random.seed(SEED)

    account_ids = load_account_ids(ACCOUNT_CSV)
    products = load_products(PRODUCT_CSV)
    pid_to_cat = load_product_category(VARIANT_MAP_CSV)
    shipping_ids = load_shipping_ids(SHIPPING_CSV)

    carts, cart_products, orders, order_items, payments, returns, return_items = generate_facts(
        account_ids, products, pid_to_cat, shipping_ids
    )

    write_csv(
        CART_OUT,
        header=["CartID", "AccountID", "Status", "CreatedTime", "LastUpdate", "DeviceType"],
        rows=carts
    )
    write_csv(
        CART_PRODUCT_OUT,
        header=["CartProductID", "CartID", "ProductID", "Quantity", "Price"],
        rows=cart_products
    )
    write_csv(
        ORDER_OUT,
        header=["OrderID", "AccountID", "CartID", "Status", "TimePlaced", "ShippingOptionID"],
        rows=orders
    )
    write_csv(
        ORDER_ITEM_OUT,
        header=["OrderItemID", "OrderID", "ProductID", "Quantity", "Price"],
        rows=order_items
    )
    write_csv(
        PAYMENT_OUT,
        header=["PaymentID", "OrderID", "Method", "Status", "PayDate"],
        rows=payments
    )
    write_csv(
        RETURN_OUT,
        header=["ReturnID", "OrderID", "AccountID", "Status"],
        rows=returns
    )
    write_csv(
        RETURN_ITEM_OUT,
        header=["ReturnItemID", "ReturnID", "OrderItemID", "Quantity", "RefundAmount"],
        rows=return_items
    )

    print(f"Wrote {len(carts):,} carts -> {CART_OUT}")
    print(f"Wrote {len(cart_products):,} cart products -> {CART_PRODUCT_OUT}")
    print(f"Wrote {len(orders):,} orders -> {ORDER_OUT}")
    print(f"Wrote {len(order_items):,} order items -> {ORDER_ITEM_OUT}")
    print(f"Wrote {len(payments):,} payments -> {PAYMENT_OUT}")
    print(f"Wrote {len(returns):,} returns -> {RETURN_OUT}")
    print(f"Wrote {len(return_items):,} return items -> {RETURN_ITEM_OUT}")

    # Sanity checks
    assert len(orders) == N_ORDERS, "orders count mismatch"
    assert len(payments) == N_ORDERS, "payments count mismatch"
    assert len(order_items) >= N_ORDERS, "each order should have >=1 item"
    assert len(carts) >= N_ORDERS, "should have at least one cart per order"

    print("Sanity OK.")


if __name__ == "__main__":
    main()