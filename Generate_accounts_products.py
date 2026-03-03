import csv
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple


# ============================================================
# Config
# ============================================================

SEED = 42
OUT_DIR = Path("out")

N_ACCOUNTS = 10_000
N_PRODUCTS_TOTAL = 5_100
N_PER_CATEGORY = 1_700  # tech/fashion/home each

# We will explicitly assign IDs so downstream joins are deterministic.
ACCOUNT_ID_START = 1
SHIPPING_ID_START = 1
PRODUCT_ID_START = 1

UTC = timezone.utc


# ============================================================
# Helpers
# ============================================================

def utc_now() -> datetime:
    return datetime.now(tz=UTC)

def rand_dt_within_days(days_back: int) -> datetime:
    """Random datetime in the last `days_back` days."""
    end = utc_now()
    start = end - timedelta(days=days_back)
    delta_seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, delta_seconds))

def money(x: float) -> str:
    """Format as 2-decimal string for DECIMAL(10,2) CSV."""
    return f"{x:.2f}"

def slugify_simple(s: str) -> str:
    """Simple slug for usernames/emails (no external libs)."""
    out = []
    for ch in s.lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_"):
            out.append("_")
    return "".join(out).strip("_")

def write_csv(path: Path, header: List[str], rows: List[List[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

def choose_weighted(options: List[Tuple[object, float]]):
    """options = [(value, weight), ...]"""
    vals = [v for v, _ in options]
    weights = [w for _, w in options]
    return random.choices(vals, weights=weights, k=1)[0]


# ============================================================
# Phase 2A: Accounts
# ============================================================

FIRST_NAMES = [
    "Sarah", "Emma", "Olivia", "Ava", "Mia", "Sophia", "Isabella", "Amelia",
    "Noah", "Liam", "Elijah", "James", "Benjamin", "Lucas", "Henry", "Leo",
    "Ryan", "Aria", "Layla", "Ethan", "Jack", "Mason", "Chloe", "Zoe"
]
LAST_NAMES = [
    "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson",
    "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"
]
EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com", "proton.me"]

def gen_accounts(n: int) -> List[List[object]]:
    """
    Output rows matching MySQL table:
    Account(AccountID, Name, Email, Phone, Username)
    Requirement: first account username must be "sarah".
    """
    rows: List[List[object]] = []

    used_usernames = set()
    used_emails = set()

    # 1) First account is Sarah
    account_id = ACCOUNT_ID_START
    name = "Sarah Johnson"
    username = "sarah"
    email = "sarah.johnson@example.com"  # you can pick anything; must be unique
    phone = "312-555-0100"

    used_usernames.add(username)
    used_emails.add(email)
    rows.append([account_id, name, email, phone, username])

    # 2) Other accounts
    for i in range(2, n + 1):
        account_id = ACCOUNT_ID_START + (i - 1)

        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        name = f"{fn} {ln}"

        base = slugify_simple(f"{fn}.{ln}")
        # ensure unique username
        suffix = 1
        username = base
        while username in used_usernames:
            suffix += 1
            username = f"{base}{suffix}"
        used_usernames.add(username)

        domain = random.choice(EMAIL_DOMAINS)
        email = f"{username}@{domain}"
        # ensure unique email (mostly redundant due to username uniqueness)
        while email in used_emails:
            email = f"{username}{random.randint(100,999)}@{domain}"
        used_emails.add(email)

        # simple US-like phone; allow NULL occasionally
        if random.random() < 0.05:
            phone = None
        else:
            phone = f"{random.randint(200, 999)}-555-{random.randint(1000, 9999)}"

        rows.append([account_id, name, email, phone, username])

    return rows


# ============================================================
# Phase 2B: Shipping Options
# ============================================================

def gen_shipping_options() -> List[List[object]]:
    """
    ShippingOption(ShippingOptionID, Name, Cost, TimeToDelivery)
    Small, realistic set.
    """
    options = [
        (SHIPPING_ID_START + 0, "Standard Shipping", money(5.99), "3-5 business days"),
        (SHIPPING_ID_START + 1, "Expedited Shipping", money(12.99), "2-3 business days"),
        (SHIPPING_ID_START + 2, "Overnight Shipping", money(24.99), "1 business day"),
        (SHIPPING_ID_START + 3, "Free Shipping (Orders $50+)", money(0.00), "5-7 business days"),
        (SHIPPING_ID_START + 4, "In-Store Pickup", money(0.00), "Same day"),
    ]
    return [[sid, name, cost, ttd] for (sid, name, cost, ttd) in options]


# ============================================================
# Phase 2C: Products (base concept + variants)
# ============================================================

@dataclass
class VariantPlan:
    """How to create variants for a base product concept."""
    dim1_name: str
    dim1_values: List[str]
    dim2_name: str
    dim2_values: List[str]

@dataclass
class ProductTemplate:
    """A base concept for a product (before variant expansion)."""
    category: str  # "TECH" | "FASHION" | "HOME"
    base_name: str
    base_desc: str
    price_range: Tuple[float, float]
    variant_plan: VariantPlan

# Variant catalogs (kept simple; you can expand later)
COLORS_FASHION = ["Black", "White", "Navy", "Aqua Blue", "Red", "Green", "Pink", "Beige"]
SIZES_APPAREL = ["XS", "S", "M", "L", "XL"]
MATERIALS_FASHION = ["Cotton", "Linen", "Polyester", "Silk", "Denim"]

COLORS_TECH = ["Black", "White", "Silver", "Space Gray", "Blue", "Red"]
STORAGE = ["64GB", "128GB", "256GB", "512GB"]
SCREEN_SIZES = ["13-inch", "14-inch", "15-inch", "16-inch"]
TV_SIZES = ["43-inch", "50-inch", "55-inch", "65-inch"]

COLORS_HOME = ["White", "Black", "Beige", "Walnut", "Oak", "Ceramic Blue", "Terracotta"]
SIZES_HOME = ["Small", "Medium", "Large"]
ROOMS = ["Living Room", "Bedroom", "Kitchen", "Office"]

def build_templates() -> List[ProductTemplate]:
    """
    A pool of base product concepts by category.
    Each base concept will expand into variants based on the VariantPlan.
    """
    templates: List[ProductTemplate] = []

    # TECH
    templates += [
        ProductTemplate(
            category="TECH",
            base_name="Wireless Headphones",
            base_desc="Premium wireless headphones with comfortable fit and immersive sound.",
            price_range=(79.99, 349.99),
            variant_plan=VariantPlan("Color", COLORS_TECH, "Connectivity", ["Bluetooth", "Bluetooth+Wired"])
        ),
        ProductTemplate(
            category="TECH",
            base_name="Smartphone",
            base_desc="High-performance smartphone with fast processor and sharp display.",
            price_range=(399.99, 1299.99),
            variant_plan=VariantPlan("Color", COLORS_TECH, "Storage", STORAGE)
        ),
        ProductTemplate(
            category="TECH",
            base_name="Laptop",
            base_desc="Lightweight laptop built for productivity and everyday computing.",
            price_range=(549.99, 2199.99),
            variant_plan=VariantPlan("ScreenSize", SCREEN_SIZES, "Color", ["Silver", "Space Gray", "Black"])
        ),
        ProductTemplate(
            category="TECH",
            base_name="4K Television",
            base_desc="Ultra HD 4K TV with vibrant colors and smooth motion.",
            price_range=(299.99, 1799.99),
            variant_plan=VariantPlan("TVSize", TV_SIZES, "Color", ["Black", "Silver"])
        ),
        ProductTemplate(
            category="TECH",
            base_name="Smartwatch",
            base_desc="Fitness and notifications on your wrist with long battery life.",
            price_range=(99.99, 599.99),
            variant_plan=VariantPlan("Color", COLORS_TECH, "Band", ["Silicone", "Leather"])
        ),
    ]

    # FASHION
    templates += [
        ProductTemplate(
            category="FASHION",
            base_name="Summer Dress",
            base_desc="Breathable summer dress designed for warm weather comfort.",
            price_range=(29.99, 119.99),
            variant_plan=VariantPlan("Size", SIZES_APPAREL, "Color", COLORS_FASHION)
        ),
        ProductTemplate(
            category="FASHION",
            base_name="T-Shirt",
            base_desc="Soft everyday t-shirt with a classic fit.",
            price_range=(9.99, 39.99),
            variant_plan=VariantPlan("Size", SIZES_APPAREL, "Color", COLORS_FASHION)
        ),
        ProductTemplate(
            category="FASHION",
            base_name="Hoodie",
            base_desc="Cozy hoodie with warm fleece lining for daily wear.",
            price_range=(24.99, 89.99),
            variant_plan=VariantPlan("Size", SIZES_APPAREL, "Color", ["Black", "Gray", "Navy", "White"])
        ),
        ProductTemplate(
            category="FASHION",
            base_name="Sneakers",
            base_desc="Comfort sneakers built for walking and everyday use.",
            price_range=(39.99, 159.99),
            variant_plan=VariantPlan("Size", [str(x) for x in range(6, 13)], "Color", ["Black", "White", "Gray"])
        ),
        ProductTemplate(
            category="FASHION",
            base_name="Skirt",
            base_desc="Versatile skirt suitable for casual and semi-formal looks.",
            price_range=(19.99, 89.99),
            variant_plan=VariantPlan("Size", SIZES_APPAREL, "Color", ["Black", "Navy", "Red", "Beige"])
        ),
    ]

    # HOME DECOR
    templates += [
        ProductTemplate(
            category="HOME",
            base_name="Ceramic Vase",
            base_desc="Decorative ceramic vase with a smooth glazed finish.",
            price_range=(14.99, 129.99),
            variant_plan=VariantPlan("Size", SIZES_HOME, "Color", ["White", "Ceramic Blue", "Terracotta", "Black"])
        ),
        ProductTemplate(
            category="HOME",
            base_name="Table Lamp",
            base_desc="Modern table lamp that adds warm lighting to your space.",
            price_range=(19.99, 199.99),
            variant_plan=VariantPlan("Room", ROOMS, "Color", ["Black", "White", "Brass"])
        ),
        ProductTemplate(
            category="HOME",
            base_name="Sofa",
            base_desc="Comfortable sofa with durable fabric and supportive cushions.",
            price_range=(399.99, 2499.99),
            variant_plan=VariantPlan("Size", ["Loveseat", "3-Seater", "Sectional"], "Color", ["Gray", "Beige", "Navy"])
        ),
        ProductTemplate(
            category="HOME",
            base_name="Dining Table",
            base_desc="Sturdy dining table designed for daily use and gatherings.",
            price_range=(199.99, 1799.99),
            variant_plan=VariantPlan("Material", ["Oak", "Walnut", "Glass"], "Size", ["4-Person", "6-Person", "8-Person"])
        ),
        ProductTemplate(
            category="HOME",
            base_name="Wall Art Print",
            base_desc="High-quality art print to elevate your room’s aesthetic.",
            price_range=(9.99, 149.99),
            variant_plan=VariantPlan("Size", ["8x10", "12x16", "18x24", "24x36"], "Style", ["Modern", "Boho", "Minimalist", "Traditional"])
        ),
    ]

    return templates


def sample_price(lo: float, hi: float) -> float:
    """Bias toward lower prices but allow high end (log-ish)."""
    # Generate u in [0,1], bias it (square) then scale
    u = random.random() ** 2
    return lo + (hi - lo) * u


def gen_products_with_variants(
    n_tech: int, n_fashion: int, n_home: int
) -> Tuple[List[List[object]], List[List[object]]]:
    """
    Generates:
      - Product rows: [ProductID, Name, Description, Price]
      - Variant map rows (NOT a DB table): helps generate Attribute/ProductAttribute later.

    Variant map columns:
      ProductID, Category, BaseKey, BaseName, VariantDim1Name, VariantDim1Value, VariantDim2Name, VariantDim2Value
    """
    templates = build_templates()

    # Pick templates by category
    by_cat: Dict[str, List[ProductTemplate]] = {"TECH": [], "FASHION": [], "HOME": []}
    for t in templates:
        by_cat[t.category].append(t)

    targets = {"TECH": n_tech, "FASHION": n_fashion, "HOME": n_home}

    product_rows: List[List[object]] = []
    variant_map_rows: List[List[object]] = []

    next_product_id = PRODUCT_ID_START
    base_counter = {"TECH": 0, "FASHION": 0, "HOME": 0}

    for cat in ["TECH", "FASHION", "HOME"]:
        remaining = targets[cat]

        while remaining > 0:
            base_counter[cat] += 1
            base_key = f"{cat}_BASE_{base_counter[cat]:06d}"

            tmpl = random.choice(by_cat[cat])
            vp = tmpl.variant_plan

            # Decide how many values to use from each dimension to control variant count
            # (keeps variety so not every base concept explodes into 40 variants)
            def pick_subset(values: List[str], min_k: int, max_k: int) -> List[str]:
                k = random.randint(min_k, min(max_k, len(values)))
                return random.sample(values, k)

            if cat == "FASHION":
                dim1_vals = pick_subset(vp.dim1_values, 3, 5)  # sizes
                dim2_vals = pick_subset(vp.dim2_values, 2, 4)  # colors
            elif cat == "TECH":
                dim1_vals = pick_subset(vp.dim1_values, 2, 4)
                dim2_vals = pick_subset(vp.dim2_values, 1, 3)
            else:  # HOME
                dim1_vals = pick_subset(vp.dim1_values, 1, 3)
                dim2_vals = pick_subset(vp.dim2_values, 1, 3)

            variants = [(a, b) for a in dim1_vals for b in dim2_vals]

            # If too many variants, truncate; if too few, still ok.
            # Also cap by remaining needed for category.
            if len(variants) > remaining:
                variants = variants[:remaining]

            # Create a stable base name that can repeat with numbering
            # Example: "Summer Dress 0412"
            base_name = f"{tmpl.base_name} {base_counter[cat]:04d}"
            base_desc = tmpl.base_desc
            base_price = sample_price(*tmpl.price_range)

            for (v1, v2) in variants:
                product_id = next_product_id
                next_product_id += 1

                # Product table itself stays generic (attributes captured later).
                # Name can stay base-like; optional add short variant hint to reduce duplicates.
                # Keep it mostly base to match your story (variants are via Attribute table).
                name = base_name
                desc = base_desc
                price = base_price

                product_rows.append([product_id, name, desc, money(price)])

                variant_map_rows.append([
                    product_id,
                    cat,
                    base_key,
                    base_name,
                    vp.dim1_name, v1,
                    vp.dim2_name, v2
                ])

            remaining -= len(variants)

    # Sanity check
    assert len(product_rows) == (n_tech + n_fashion + n_home), \
        f"Expected {n_tech+n_fashion+n_home} products, got {len(product_rows)}"
    assert len(variant_map_rows) == len(product_rows)

    return product_rows, variant_map_rows


# ============================================================
# Main
# ============================================================

def main():
    random.seed(SEED)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Accounts
    accounts = gen_accounts(N_ACCOUNTS)
    write_csv(
        OUT_DIR / "account.csv",
        header=["AccountID", "Name", "Email", "Phone", "Username"],
        rows=accounts
    )
    print(f"Wrote {len(accounts):,} accounts -> out/account.csv")

    # 2) Shipping options
    shipping = gen_shipping_options()
    write_csv(
        OUT_DIR / "shipping_option.csv",
        header=["ShippingOptionID", "Name", "Cost", "TimeToDelivery"],
        rows=shipping
    )
    print(f"Wrote {len(shipping):,} shipping options -> out/shipping_option.csv")

    # 3) Products + variant map (for later Attribute/ProductAttribute generation)
    products, variant_map = gen_products_with_variants(
        n_tech=N_PER_CATEGORY,
        n_fashion=N_PER_CATEGORY,
        n_home=N_PER_CATEGORY
    )
    write_csv(
        OUT_DIR / "product.csv",
        header=["ProductID", "Name", "Description", "Price"],
        rows=products
    )
    print(f"Wrote {len(products):,} products -> out/product.csv")

    write_csv(
        OUT_DIR / "product_variant_map.csv",
        header=[
            "ProductID", "Category", "BaseKey", "BaseName",
            "VariantDim1Name", "VariantDim1Value",
            "VariantDim2Name", "VariantDim2Value"
        ],
        rows=variant_map
    )
    print(f"Wrote {len(variant_map):,} variant-map rows -> out/product_variant_map.csv")

    print("\nNext step (Phase 2 continuation):")
    print(" - Use product_variant_map.csv to generate Attribute.csv, ProductAttribute.csv, Inventory.csv")
    print(" - Then Phase 3: generate facts (Cart/Order/...) using ProductID/AccountID ranges")


if __name__ == "__main__":
    main()