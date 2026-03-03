import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional

SEED = 42
OUT_DIR = Path("out")

VARIANT_MAP_PATH = OUT_DIR / "product_variant_map.csv"
PRODUCT_PATH = OUT_DIR / "product.csv"

ATTRIBUTE_OUT = OUT_DIR / "attribute.csv"
PRODUCT_ATTRIBUTE_OUT = OUT_DIR / "product_attribute.csv"
INVENTORY_OUT = OUT_DIR / "inventory.csv"

UTC = timezone.utc


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

def write_csv(path: Path, header: List[str], rows: List[List[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

def choose_weighted(options: List[Tuple[object, float]]):
    vals = [v for v, _ in options]
    weights = [w for _, w in options]
    return random.choices(vals, weights=weights, k=1)[0]


# ----------------------------
# Load inputs
# ----------------------------

def load_products(product_csv: Path) -> Dict[int, Dict[str, str]]:
    """
    product.csv header:
      ProductID, Name, Description, Price
    """
    products: Dict[int, Dict[str, str]] = {}
    with product_csv.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            pid = int(row["ProductID"])
            products[pid] = row
    return products

def load_variant_map(variant_csv: Path) -> List[Dict[str, str]]:
    """
    product_variant_map.csv header:
      ProductID, Category, BaseKey, BaseName,
      VariantDim1Name, VariantDim1Value,
      VariantDim2Name, VariantDim2Value
    """
    rows: List[Dict[str, str]] = []
    with variant_csv.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows


# ----------------------------
# Attribute logic
# ----------------------------

FASHION_MATERIALS = ["Cotton", "Linen", "Polyester", "Silk", "Denim", "Rayon"]
CERAMIC_MATERIALS = ["Stoneware", "Porcelain", "Earthenware", "Bone China"]
CARE_INSTRUCTIONS = [
    "Hand wash only",
    "Wipe clean with damp cloth",
    "Dishwasher safe (top rack)",
    "Avoid abrasive cleaners",
    "Not microwave safe",
]

def is_headphones(base_name: str) -> bool:
    return base_name.startswith("Wireless Headphones")

def is_summer_dress(base_name: str) -> bool:
    return base_name.startswith("Summer Dress")

def is_ceramic_vase(base_name: str) -> bool:
    return base_name.startswith("Ceramic Vase")

def derive_vase_dimensions(size_label: str) -> str:
    # Use simple, consistent mapping; string fits Attribute.Value
    mapping = {
        "Small":  "15cm x 10cm x 10cm",
        "Medium": "25cm x 14cm x 14cm",
        "Large":  "35cm x 18cm x 18cm",
    }
    return mapping.get(size_label, "25cm x 14cm x 14cm")

def derive_vase_weight_kg(size_label: str) -> str:
    mapping = {
        "Small":  (0.6, 1.2),
        "Medium": (1.0, 2.0),
        "Large":  (1.8, 3.5),
    }
    lo, hi = mapping.get(size_label, (1.0, 2.0))
    w = lo + (hi - lo) * random.random()
    return f"{w:.2f}"  # store numeric as string in Attribute.Value

def gen_headphone_battery_hours() -> str:
    # common battery life bands
    return str(choose_weighted([
        (20, 2.0),
        (25, 3.0),
        (30, 5.0),
        (35, 3.0),
        (40, 2.0),
        (50, 1.0),
        (60, 0.5),
    ]))

def gen_headphone_weight_grams() -> str:
    # typical headphone weights 180-380g
    w = 180 + int((380 - 180) * (random.random() ** 0.8))
    return str(w)

def derive_connectivity_type(variant_dims: Dict[str, str]) -> str:
    """
    If the product's variant includes Connectivity, use that.
    Else fallback.
    """
    if variant_dims.get("VariantDim1Name") == "Connectivity":
        return variant_dims.get("VariantDim1Value")
    if variant_dims.get("VariantDim2Name") == "Connectivity":
        return variant_dims.get("VariantDim2Value")
    return "Bluetooth"


# ----------------------------
# Build Attribute + ProductAttribute
# ----------------------------

def build_attributes_and_links(variant_rows: List[Dict[str, str]]) -> Tuple[List[List[object]], List[List[object]]]:
    """
    Produces:
      Attribute.csv rows: [AttributeID, Name, Value]
      ProductAttribute.csv rows: [ProductAttributeID, ProductID, AttributeID]

    Strategy:
      - collect all (Name, Value) pairs into a set
      - assign AttributeID deterministically
      - create product->attribute links
    """

    # product_id -> list of (name, value)
    prod_attrs: Dict[int, List[Tuple[str, str]]] = {}

    all_pairs: set[Tuple[str, str]] = set()

    for row in variant_rows:
        pid = int(row["ProductID"])
        cat = row["Category"]  # TECH/FASHION/HOME
        base_name = row["BaseName"]

        dim1n, dim1v = row["VariantDim1Name"], row["VariantDim1Value"]
        dim2n, dim2v = row["VariantDim2Name"], row["VariantDim2Value"]

        attrs: List[Tuple[str, str]] = []

        # 1) universal attributes
        attrs.append(("Category", cat))
        attrs.append((dim1n, dim1v))
        attrs.append((dim2n, dim2v))

        # 2) “common sense” extras for specific base concepts
        if is_headphones(base_name):
            # battery life, connectivity type, weight
            attrs.append(("BatteryLifeHours", gen_headphone_battery_hours()))
            attrs.append(("ConnectivityType", derive_connectivity_type(row)))
            attrs.append(("WeightGrams", gen_headphone_weight_grams()))

        if is_summer_dress(base_name):
            # material only (size/color already in variants)
            attrs.append(("Material", random.choice(FASHION_MATERIALS)))

        if is_ceramic_vase(base_name):
            # dimensions, material, weight, care
            # derive based on Size if present; otherwise default
            size_label: Optional[str] = None
            if dim1n == "Size":
                size_label = dim1v
            elif dim2n == "Size":
                size_label = dim2v

            if size_label is None:
                size_label = "Medium"

            attrs.append(("Dimensions", derive_vase_dimensions(size_label)))
            attrs.append(("Material", random.choice(CERAMIC_MATERIALS)))
            attrs.append(("WeightKg", derive_vase_weight_kg(size_label)))
            attrs.append(("CareInstructions", random.choice(CARE_INSTRUCTIONS)))

        # de-dupe per product (avoid repeated pairs if something overlaps)
        attrs_unique = list(dict.fromkeys(attrs))

        prod_attrs[pid] = attrs_unique
        for pair in attrs_unique:
            all_pairs.add(pair)

    # Assign AttributeIDs in deterministic order for repeatability
    pairs_sorted = sorted(all_pairs, key=lambda x: (x[0], x[1]))
    pair_to_id: Dict[Tuple[str, str], int] = {}
    attribute_rows: List[List[object]] = []
    next_attr_id = 1
    for (name, value) in pairs_sorted:
        pair_to_id[(name, value)] = next_attr_id
        attribute_rows.append([next_attr_id, name, value])
        next_attr_id += 1

    # Build ProductAttribute rows
    product_attribute_rows: List[List[object]] = []
    next_pa_id = 1
    for pid in sorted(prod_attrs.keys()):
        for (name, value) in prod_attrs[pid]:
            aid = pair_to_id[(name, value)]
            product_attribute_rows.append([next_pa_id, pid, aid])
            next_pa_id += 1

    return attribute_rows, product_attribute_rows


# ----------------------------
# Inventory
# ----------------------------

def gen_inventory(product_ids: List[int]) -> List[List[object]]:
    """
    Inventory(ProductID, QuantityAvailable, LastUpdate)
    Use a realistic skew:
      - some out of stock
      - most modest stock
      - few large stock
    """
    rows: List[List[object]] = []
    for pid in product_ids:
        qty = choose_weighted([
            (0,   1.0),   # out of stock
            (1,   2.0),
            (2,   3.0),
            (5,   5.0),
            (10,  6.0),
            (25,  4.0),
            (50,  2.0),
            (100, 1.0),
            (200, 0.3),
        ])
        # add small jitter for non-zero quantities
        if qty > 0:
            qty = max(0, qty + random.randint(-2, 8))

        last_update = fmt_dt(rand_dt_within_days(30))
        rows.append([pid, int(qty), last_update])
    return rows


# ----------------------------
# Main
# ----------------------------

def main():
    random.seed(SEED)

    # Load base files
    products = load_products(PRODUCT_PATH)
    variant_rows = load_variant_map(VARIANT_MAP_PATH)

    # 1) Attribute + ProductAttribute
    attribute_rows, product_attribute_rows = build_attributes_and_links(variant_rows)

    write_csv(
        ATTRIBUTE_OUT,
        header=["AttributeID", "Name", "Value"],
        rows=attribute_rows
    )
    print(f"Wrote {len(attribute_rows):,} Attribute rows -> {ATTRIBUTE_OUT}")

    write_csv(
        PRODUCT_ATTRIBUTE_OUT,
        header=["ProductAttributeID", "ProductID", "AttributeID"],
        rows=product_attribute_rows
    )
    print(f"Wrote {len(product_attribute_rows):,} ProductAttribute rows -> {PRODUCT_ATTRIBUTE_OUT}")

    # 2) Inventory
    product_ids = sorted(products.keys())
    inv_rows = gen_inventory(product_ids)

    write_csv(
        INVENTORY_OUT,
        header=["ProductID", "QuantityAvailable", "LastUpdate"],
        rows=inv_rows
    )
    print(f"Wrote {len(inv_rows):,} Inventory rows -> {INVENTORY_OUT}")

    # Quick sanity checks
    n_products_variant = len({int(r["ProductID"]) for r in variant_rows})
    assert n_products_variant == len(product_ids), \
        f"Variant map product count {n_products_variant} != product.csv count {len(product_ids)}"
    print("Sanity OK: product.csv and product_variant_map.csv align.")


if __name__ == "__main__":
    main()