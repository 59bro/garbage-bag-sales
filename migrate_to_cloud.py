# ============================================================
# migrate_to_cloud.py  —  SQLite → Supabase PostgreSQL 데이터 마이그레이션
# ============================================================

import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from psycopg2.extras import execute_values

# ── Supabase PostgreSQL 연결 정보 (Transaction Pooler - IPv4) ──
PG_HOST     = "aws-0-ap-northeast-1.pooler.supabase.com"
PG_PORT     = 6543
PG_DB       = "postgres"
PG_USER     = "postgres.ycvmncbcudgxlemmkgtb"
PG_PASSWORD = "Wndudwns6813"

# ── SQLite 경로 (구글 드라이브 실제 경로) ────────────────────
SQLITE_PATH = r"G:\내 드라이브\data\sales.db"

print(f"[INFO] SQLite DB 경로: {SQLITE_PATH}")
if not os.path.exists(SQLITE_PATH):
    print("[ERROR] SQLite DB 파일을 찾을 수 없습니다!")
    sys.exit(1)


def get_pg_conn():
    import urllib.parse
    password_encoded = urllib.parse.quote(PG_PASSWORD, safe='')
    dsn = f"postgresql://{PG_USER}:{password_encoded}@{PG_HOST}:{PG_PORT}/{PG_DB}?sslmode=require"
    return psycopg2.connect(dsn)


def get_sqlite_conn():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── PostgreSQL 테이블 생성 ──────────────────────────────────
PG_TABLES = [
    """
    CREATE TABLE IF NOT EXISTS customers (
        id          SERIAL PRIMARY KEY,
        name        TEXT    NOT NULL,
        district    TEXT    DEFAULT '',
        phone       TEXT    DEFAULT '',
        address     TEXT    DEFAULT '',
        memo        TEXT    DEFAULT '',
        customer_type TEXT  DEFAULT '출고처',
        initial_ar  INTEGER DEFAULT 0,
        is_active   INTEGER DEFAULT 1,
        created_at  TEXT    DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS')
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS product_types (
        id   SERIAL PRIMARY KEY,
        name TEXT    NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS product_specs (
        id            SERIAL PRIMARY KEY,
        type_id       INTEGER NOT NULL REFERENCES product_types(id),
        spec_name     TEXT    NOT NULL,
        product_code  TEXT    DEFAULT '',
        unit_price    INTEGER DEFAULT 0,
        is_active     INTEGER DEFAULT 1,
        created_at    TEXT    DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS')
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sales (
        id              SERIAL PRIMARY KEY,
        sale_date       TEXT    NOT NULL,
        customer_id     INTEGER NOT NULL REFERENCES customers(id),
        spec_id         INTEGER NOT NULL REFERENCES product_specs(id),
        quantity        INTEGER NOT NULL,
        unit_price      INTEGER NOT NULL,
        total_amount    INTEGER NOT NULL,
        payment_method  TEXT    NOT NULL,
        cash_amount     INTEGER DEFAULT 0,
        card_amount     INTEGER DEFAULT 0,
        memo            TEXT    DEFAULT '',
        created_at      TEXT    DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS')
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS inventory_transactions (
        id               SERIAL PRIMARY KEY,
        spec_id          INTEGER NOT NULL REFERENCES product_specs(id),
        transaction_date TEXT    NOT NULL,
        transaction_type TEXT    NOT NULL,
        quantity         INTEGER NOT NULL,
        reference_id     INTEGER DEFAULT NULL,
        memo             TEXT    DEFAULT '',
        created_at       TEXT    DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS')
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ar_collections (
        id               SERIAL PRIMARY KEY,
        collection_date  TEXT    NOT NULL,
        customer_id      INTEGER NOT NULL REFERENCES customers(id),
        amount           INTEGER NOT NULL,
        payment_method   TEXT    NOT NULL,
        memo             TEXT    DEFAULT '',
        created_at       TEXT    DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS')
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
        id            SERIAL PRIMARY KEY,
        username      TEXT    NOT NULL UNIQUE,
        password_hash TEXT    NOT NULL,
        name          TEXT    NOT NULL,
        role          TEXT    DEFAULT 'admin',
        is_active     INTEGER DEFAULT 1,
        created_at    TEXT    DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS')
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS disposal_sites (
        id          SERIAL PRIMARY KEY,
        name        TEXT    NOT NULL UNIQUE,
        address     TEXT    DEFAULT '',
        memo        TEXT    DEFAULT '',
        is_active   INTEGER DEFAULT 1,
        created_at  TEXT    DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS')
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS vehicles (
        id                 SERIAL PRIMARY KEY,
        vehicle_number     TEXT    NOT NULL UNIQUE,
        vehicle_type       TEXT    NOT NULL,
        crew_count         INTEGER DEFAULT 1,
        crew_names         TEXT    DEFAULT '',
        default_start_time TEXT    NOT NULL,
        default_end_time   TEXT    NOT NULL,
        is_active          INTEGER DEFAULT 1,
        created_at         TEXT    DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS')
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS vehicle_logs (
        id               SERIAL PRIMARY KEY,
        record_date      TEXT    NOT NULL,
        vehicle_id       INTEGER NOT NULL REFERENCES vehicles(id),
        start_time       TEXT    NOT NULL,
        end_time         TEXT    NOT NULL,
        absent_crew      TEXT    DEFAULT '',
        disposal_site_id INTEGER DEFAULT NULL,
        disposal_amount  REAL    DEFAULT 0,
        memo             TEXT    DEFAULT '',
        created_at       TEXT    DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS')
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS supplier_contracts (
        id                SERIAL PRIMARY KEY,
        supplier_id       INTEGER NOT NULL REFERENCES customers(id),
        spec_id           INTEGER NOT NULL REFERENCES product_specs(id),
        contract_quantity INTEGER NOT NULL DEFAULT 0,
        created_at        TEXT    DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS')
    )
    """,
]


def migrate_table(sqlite_conn, pg_conn, table_name, columns):
    """SQLite 테이블의 모든 데이터를 PostgreSQL로 복사."""
    cur_s = sqlite_conn.cursor()
    cur_p = pg_conn.cursor()

    col_list = ", ".join(columns)
    cur_s.execute(f"SELECT {col_list} FROM {table_name}")
    rows = cur_s.fetchall()

    if not rows:
        print(f"  [{table_name}] 데이터 없음 (스킵)")
        return 0

    placeholders = ", ".join(["%s"] * len(columns))
    insert_sql = f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

    count = 0
    for row in rows:
        values = tuple(row[col] if row[col] is not None else None for col in columns)
        try:
            cur_p.execute(insert_sql, values)
            count += 1
        except Exception as e:
            print(f"  [WARNING] {table_name} row skip: {e}")
            pg_conn.rollback()
            continue

    pg_conn.commit()

    # 시퀀스(auto increment) 동기화
    try:
        cur_p.execute(f"SELECT MAX(id) FROM {table_name}")
        max_id = cur_p.fetchone()[0]
        if max_id:
            cur_p.execute(f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), {max_id})")
            pg_conn.commit()
    except Exception:
        pass

    print(f"  [{table_name}] {count}건 마이그레이션 완료")
    return count


def main():
    print("=" * 60)
    print("  SQLite → Supabase PostgreSQL 데이터 마이그레이션 시작")
    print("=" * 60)

    # 1. PostgreSQL 테이블 생성
    print("\n[1/3] PostgreSQL 테이블 생성 중...")
    pg = get_pg_conn()
    cur = pg.cursor()
    for sql in PG_TABLES:
        cur.execute(sql)
    pg.commit()
    print("  테이블 생성 완료!")

    # 2. SQLite 데이터 읽기 및 마이그레이션
    print("\n[2/3] SQLite 데이터 마이그레이션 중...")
    sl = get_sqlite_conn()

    tables_config = [
        ("product_types", ["id", "name"]),
        ("customers", ["id", "name", "district", "phone", "address", "memo", "customer_type", "initial_ar", "is_active", "created_at"]),
        ("product_specs", ["id", "type_id", "spec_name", "product_code", "unit_price", "is_active", "created_at"]),
        ("sales", ["id", "sale_date", "customer_id", "spec_id", "quantity", "unit_price", "total_amount", "payment_method", "memo", "created_at"]),
        ("inventory_transactions", ["id", "spec_id", "transaction_date", "transaction_type", "quantity", "reference_id", "memo", "created_at"]),
        ("ar_collections", ["id", "collection_date", "customer_id", "amount", "payment_method", "memo", "created_at"]),
        ("users", ["id", "username", "password_hash", "name", "role", "is_active", "created_at"]),
    ]

    total = 0
    for tbl, cols in tables_config:
        try:
            total += migrate_table(sl, pg, tbl, cols)
        except Exception as e:
            print(f"  [ERROR] {tbl}: {e}")

    sl.close()

    # 3. 기본 데이터 확인
    print(f"\n[3/3] 마이그레이션 완료! 총 {total}건 이관됨")

    cur = pg.cursor()
    cur.execute("SELECT COUNT(*) FROM customers")
    print(f"  거래처: {cur.fetchone()[0]}건")
    cur.execute("SELECT COUNT(*) FROM sales")
    print(f"  판매내역: {cur.fetchone()[0]}건")
    cur.execute("SELECT COUNT(*) FROM product_specs")
    print(f"  품목규격: {cur.fetchone()[0]}건")
    cur.execute("SELECT COUNT(*) FROM ar_collections")
    print(f"  수금내역: {cur.fetchone()[0]}건")
    cur.execute("SELECT COUNT(*) FROM inventory_transactions")
    print(f"  재고거래: {cur.fetchone()[0]}건")

    pg.close()
    print("\n" + "=" * 60)
    print("  마이그레이션이 성공적으로 완료되었습니다!")
    print("=" * 60)


if __name__ == "__main__":
    main()
