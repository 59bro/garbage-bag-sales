"""
SQLite -> PostgreSQL(Supabase) 데이터 마이그레이션 스크립트
구글 드라이브의 로컬 SQLite 데이터를 클라우드 DB로 이전합니다.
"""
import sqlite3
import psycopg2
import psycopg2.extras
import sys
import os

# ── 설정 ──
SQLITE_PATH = r"G:\내 드라이브\data\sales.db"
PG_DSN = "postgresql://postgres.ycvmncbcudgxlemmkgtb:Wndudwns6813@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def migrate():
    print("=" * 60)
    print(" SQLite → PostgreSQL 마이그레이션 시작")
    print("=" * 60)

    if not os.path.exists(SQLITE_PATH):
        print(f"[ERROR] SQLite 파일 없음: {SQLITE_PATH}")
        sys.exit(1)

    # SQLite 연결
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row

    # PostgreSQL 연결
    pg_conn = psycopg2.connect(PG_DSN)
    pg_cur = pg_conn.cursor()

    try:
        # ── 1. customers 마이그레이션 ──
        print("\n[1/4] customers 마이그레이션...")
        rows = sqlite_conn.execute("SELECT * FROM customers").fetchall()
        migrated = 0
        skipped = 0
        for r in rows:
            try:
                pg_cur.execute("""
                    INSERT INTO customers (id, name, phone, address, memo, is_active, district, customer_type, initial_ar)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (
                    r['id'], r['name'], r['phone'], r['address'], r['memo'],
                    r['is_active'],
                    r['district'] if 'district' in r.keys() else '',
                    r['customer_type'] if 'customer_type' in r.keys() else '출고처',
                    r['initial_ar'] if 'initial_ar' in r.keys() else 0
                ))
                if pg_cur.rowcount > 0:
                    migrated += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"  [WARN] customer {r['name']}: {e}")
                skipped += 1
        pg_conn.commit()
        print(f"  → 신규 {migrated}건, 스킵(이미존재) {skipped}건")

        # ── 2. product_types & product_specs 마이그레이션 ──
        print("\n[2/4] product_types & product_specs 마이그레이션...")
        types = sqlite_conn.execute("SELECT * FROM product_types").fetchall()
        for t in types:
            pg_cur.execute("""
                INSERT INTO product_types (id, name)
                VALUES (%s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (t['id'], t['name']))
        pg_conn.commit()
        print(f"  → product_types: {len(types)}건 처리")

        specs = sqlite_conn.execute("SELECT * FROM product_specs").fetchall()
        spec_migrated = 0
        for s in specs:
            try:
                pg_cur.execute("""
                    INSERT INTO product_specs (id, type_id, spec_name, unit_price, is_active, product_code)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (
                    s['id'], s['type_id'], s['spec_name'], s['unit_price'],
                    s['is_active'],
                    s['product_code'] if 'product_code' in s.keys() else ''
                ))
                if pg_cur.rowcount > 0:
                    spec_migrated += 1
            except Exception as e:
                print(f"  [WARN] spec {s['spec_name']}: {e}")
        pg_conn.commit()
        print(f"  → product_specs: 신규 {spec_migrated}건")

        # ── 3. sales 마이그레이션 ──
        print("\n[3/4] sales 마이그레이션...")
        sales = sqlite_conn.execute("SELECT * FROM sales").fetchall()
        sale_migrated = 0
        sale_skipped = 0
        for s in sales:
            try:
                pg_cur.execute("""
                    INSERT INTO sales (id, sale_date, customer_id, spec_id, quantity, unit_price, total_amount, payment_method, memo, cash_amount, card_amount)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (
                    s['id'], s['sale_date'], s['customer_id'], s['spec_id'],
                    s['quantity'], s['unit_price'], s['total_amount'],
                    s['payment_method'], s['memo'],
                    s['cash_amount'] if 'cash_amount' in s.keys() else 0,
                    s['card_amount'] if 'card_amount' in s.keys() else 0
                ))
                if pg_cur.rowcount > 0:
                    sale_migrated += 1
                else:
                    sale_skipped += 1
            except Exception as e:
                print(f"  [WARN] sale id={s['id']}: {e}")
                sale_skipped += 1
        pg_conn.commit()
        print(f"  → 신규 {sale_migrated}건, 스킵 {sale_skipped}건")

        # ── 4. ar_collections & stock_inbound 마이그레이션 ──
        print("\n[4/4] ar_collections & stock_inbound 마이그레이션...")
        
        # ar_collections
        try:
            ar_rows = sqlite_conn.execute("SELECT * FROM ar_collections").fetchall()
            ar_migrated = 0
            for r in ar_rows:
                pg_cur.execute("""
                    INSERT INTO ar_collections (id, collection_date, customer_id, amount, payment_method, memo)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (r['id'], r['collection_date'], r['customer_id'], r['amount'], r['payment_method'], r['memo']))
                if pg_cur.rowcount > 0:
                    ar_migrated += 1
            pg_conn.commit()
            print(f"  → ar_collections: 신규 {ar_migrated}건")
        except Exception as e:
            print(f"  → ar_collections 없거나 오류: {e}")

        # stock_inbound
        try:
            stock_rows = sqlite_conn.execute("SELECT * FROM stock_inbound").fetchall()
            stock_migrated = 0
            for r in stock_rows:
                pg_cur.execute("""
                    INSERT INTO stock_inbound (id, spec_id, quantity, transaction_date, memo)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (r['id'], r['spec_id'], r['quantity'], r['transaction_date'], r['memo']))
                if pg_cur.rowcount > 0:
                    stock_migrated += 1
            pg_conn.commit()
            print(f"  → stock_inbound: 신규 {stock_migrated}건")
        except Exception as e:
            print(f"  → stock_inbound 없거나 오류: {e}")

        # ── 시퀀스 갱신 (PostgreSQL ID 충돌 방지) ──
        print("\n[SEQ] PostgreSQL 시퀀스 갱신...")
        for table in ['customers', 'product_types', 'product_specs', 'sales', 'ar_collections', 'stock_inbound']:
            try:
                pg_cur.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1))")
            except Exception:
                pg_conn.rollback()
        pg_conn.commit()
        print("  → 시퀀스 갱신 완료")

        print("\n" + "=" * 60)
        print(" ✅ 마이그레이션 완료!")
        print("=" * 60)

    except Exception as e:
        pg_conn.rollback()
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        sqlite_conn.close()
        pg_cur.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
