# ============================================================
# database/models.py  —  테이블 스키마 정의
# ============================================================

CREATE_CUSTOMERS = """
CREATE TABLE IF NOT EXISTS customers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    district    TEXT    DEFAULT '',
    phone       TEXT    DEFAULT '',
    address     TEXT    DEFAULT '',
    memo        TEXT    DEFAULT '',
    initial_ar  INTEGER DEFAULT 0,
    is_active   INTEGER DEFAULT 1,
    created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
)
"""

CREATE_PRODUCT_TYPES = """
CREATE TABLE IF NOT EXISTS product_types (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL UNIQUE
)
"""

CREATE_PRODUCT_SPECS = """
CREATE TABLE IF NOT EXISTS product_specs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    type_id       INTEGER NOT NULL,
    spec_name     TEXT    NOT NULL,
    product_code  TEXT    DEFAULT '',
    unit_price    INTEGER DEFAULT 0,
    is_active     INTEGER DEFAULT 1,
    created_at    TEXT    DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (type_id) REFERENCES product_types(id)
)
"""

CREATE_SALES = """
CREATE TABLE IF NOT EXISTS sales (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_date       TEXT    NOT NULL,
    customer_id     INTEGER NOT NULL,
    spec_id         INTEGER NOT NULL,
    quantity        INTEGER NOT NULL,
    unit_price      INTEGER NOT NULL,
    total_amount    INTEGER NOT NULL,
    payment_method  TEXT    NOT NULL CHECK(payment_method IN ('현금', '미수', '카드')),
    memo            TEXT    DEFAULT '',
    created_at      TEXT    DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (spec_id)     REFERENCES product_specs(id)
)
"""

CREATE_INVENTORY = """
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    spec_id          INTEGER NOT NULL,
    transaction_date TEXT    NOT NULL,
    transaction_type TEXT    NOT NULL CHECK(transaction_type IN ('초기재고', '입고', '출고')),
    quantity         INTEGER NOT NULL,
    reference_id     INTEGER DEFAULT NULL,
    memo             TEXT    DEFAULT '',
    created_at       TEXT    DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (spec_id) REFERENCES product_specs(id)
)
"""

# ── 미수 수금 테이블 (판매 없이 수금만 처리) ─────────────────
CREATE_AR_COLLECTIONS = """
CREATE TABLE IF NOT EXISTS ar_collections (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_date  TEXT    NOT NULL,
    customer_id      INTEGER NOT NULL,
    amount           INTEGER NOT NULL,
    payment_method   TEXT    NOT NULL CHECK(payment_method IN ('현금', '카드', '계좌이체')),
    memo             TEXT    DEFAULT '',
    created_at       TEXT    DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
)
"""

# ── 차량 및 폐기물 반입 관리 테이블 ──────────────────────────
CREATE_DISPOSAL_SITES = """
CREATE TABLE IF NOT EXISTS disposal_sites (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    address     TEXT    DEFAULT '',
    memo        TEXT    DEFAULT '',
    is_active   INTEGER DEFAULT 1,
    created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
)
"""

CREATE_VEHICLES = """
CREATE TABLE IF NOT EXISTS vehicles (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_number     TEXT    NOT NULL UNIQUE,
    vehicle_type       TEXT    NOT NULL CHECK(vehicle_type IN ('생활', '재활용', '음식물')),
    crew_count         INTEGER DEFAULT 1,
    crew_names         TEXT    DEFAULT '',
    default_start_time TEXT    NOT NULL,
    default_end_time   TEXT    NOT NULL,
    is_active          INTEGER DEFAULT 1,
    created_at         TEXT    DEFAULT (datetime('now', 'localtime'))
)
"""

CREATE_VEHICLE_LOGS = """
CREATE TABLE IF NOT EXISTS vehicle_logs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    record_date      TEXT    NOT NULL,
    vehicle_id       INTEGER NOT NULL,
    start_time       TEXT    NOT NULL,
    end_time         TEXT    NOT NULL,
    absent_crew      TEXT    DEFAULT '',
    disposal_site_id INTEGER DEFAULT NULL,
    disposal_amount  REAL    DEFAULT 0,
    memo             TEXT    DEFAULT '',
    created_at       TEXT    DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (vehicle_id)       REFERENCES vehicles(id),
    FOREIGN KEY (disposal_site_id) REFERENCES disposal_sites(id)
)
"""

CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    name          TEXT    NOT NULL,
    role          TEXT    DEFAULT 'admin',
    is_active     INTEGER DEFAULT 1,
    created_at    TEXT    DEFAULT (datetime('now', 'localtime'))
)
"""

CREATE_SUPPLIER_CONTRACTS = """
CREATE TABLE IF NOT EXISTS supplier_contracts (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id       INTEGER NOT NULL,
    spec_id           INTEGER NOT NULL,
    contract_quantity INTEGER NOT NULL DEFAULT 0,
    created_at        TEXT    DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (supplier_id) REFERENCES customers(id),
    FOREIGN KEY (spec_id)     REFERENCES product_specs(id)
)
"""

ALL_TABLES = [
    CREATE_CUSTOMERS,
    CREATE_PRODUCT_TYPES,
    CREATE_PRODUCT_SPECS,
    CREATE_SALES,
    CREATE_INVENTORY,
    CREATE_AR_COLLECTIONS,
    CREATE_DISPOSAL_SITES,
    CREATE_VEHICLES,
    CREATE_VEHICLE_LOGS,
    CREATE_USERS,
    CREATE_SUPPLIER_CONTRACTS,
]

DEFAULT_PRODUCT_TYPES = [
    '생활용 봉투', '음식물용 봉투', '업소용 필증', '가정용 필증', '특수마대', '재사용봉투',
]

PAYMENT_METHODS = ['현금', '미수', '카드']
COLLECTION_METHODS = ['현금', '카드', '계좌이체']
VEHICLE_TYPES = ['생활', '재활용', '음식물']

DISTRICTS = ['번1동', '번2동', '번3동', '삼양동', '삼각산동', '송천동', '송중동', '기타']

