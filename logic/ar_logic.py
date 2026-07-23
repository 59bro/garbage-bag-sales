# ============================================================
# logic/ar_logic.py  —  미수 / 수금 관리 로직
# ============================================================

from database.db_manager import DBManager


class ARLogic:
    def __init__(self):
        self.db = DBManager()

    # ── 미수 잔액 ────────────────────────────────────────────
    def get_outstanding_summary(self) -> list:
        """거래처별 미수 잔액 집계 (초기 미수 + 판매 미수 - 수금액)."""
        return self.db.fetchall("""
            SELECT
                c.id AS customer_id,
                c.name AS customer_name,
                c.district,
                COALESCE(c.initial_ar, 0) AS initial_ar,
                COALESCE(s.sales_credit, 0) AS sales_credit,
                COALESCE(c.initial_ar, 0) + COALESCE(s.sales_credit, 0) AS total_credit,
                COALESCE(col.total_collected, 0) AS total_collected,
                COALESCE(c.initial_ar, 0) + COALESCE(s.sales_credit, 0) - COALESCE(col.total_collected, 0) AS outstanding
            FROM customers c
            LEFT JOIN (
                SELECT customer_id, SUM(total_amount) AS sales_credit
                FROM sales WHERE payment_method = '미수'
                GROUP BY customer_id
            ) s ON c.id = s.customer_id
            LEFT JOIN (
                SELECT customer_id, SUM(amount) AS total_collected
                FROM ar_collections
                GROUP BY customer_id
            ) col ON c.id = col.customer_id
            WHERE c.is_active = 1
              AND (COALESCE(c.initial_ar, 0) != 0 OR COALESCE(s.sales_credit, 0) > 0 OR COALESCE(col.total_collected, 0) > 0)
            ORDER BY outstanding DESC, c.name
        """)

    def get_outstanding_total(self) -> int:
        row = self.db.fetchone("""
            SELECT
                COALESCE((SELECT SUM(initial_ar) FROM customers WHERE is_active=1), 0) +
                COALESCE((SELECT SUM(total_amount) FROM sales WHERE payment_method = '미수'), 0) -
                COALESCE((SELECT SUM(amount) FROM ar_collections), 0) AS total
        """)
        return int(row['total']) if row else 0

    def get_credit_sales_by_customer(self, customer_id: int,
                                      start_date: str = None,
                                      end_date: str = None) -> list:
        """특정 거래처의 미수 판매 내역."""
        clauses = ["s.customer_id = ?", "s.payment_method = '미수'"]
        params  = [customer_id]
        if start_date:
            clauses.append("s.sale_date >= ?"); params.append(start_date)
        if end_date:
            clauses.append("s.sale_date <= ?");  params.append(end_date)
        return self.db.fetchall(f"""
            SELECT s.*, pt.name AS type_name, ps.spec_name
            FROM sales s
            JOIN product_specs ps ON s.spec_id  = ps.id
            JOIN product_types pt ON ps.type_id = pt.id
            WHERE {' AND '.join(clauses)}
            ORDER BY s.sale_date DESC
        """, tuple(params))

    # ── 수금 ─────────────────────────────────────────────────
    def add_collection(self, collection_date: str, customer_id: int,
                       amount: int, payment_method: str, memo: str = '') -> int:
        if amount <= 0:
            raise ValueError("수금액은 1원 이상이어야 합니다.")
        return self.db.execute("""
            INSERT INTO ar_collections
                (collection_date, customer_id, amount, payment_method, memo)
            VALUES (?, ?, ?, ?, ?)
        """, (collection_date, customer_id, amount, payment_method, memo))

    def delete_collection(self, col_id: int):
        self.db.execute("DELETE FROM ar_collections WHERE id=?", (col_id,))

    def get_collections(self, customer_id: int = None,
                         start_date: str = None, end_date: str = None) -> list:
        clauses = ["1=1"]
        params  = []
        if customer_id:
            clauses.append("col.customer_id = ?"); params.append(customer_id)
        if start_date:
            clauses.append("col.collection_date >= ?"); params.append(start_date)
        if end_date:
            clauses.append("col.collection_date <= ?");  params.append(end_date)
        return self.db.fetchall(f"""
            SELECT col.*, c.name AS customer_name, c.district
            FROM ar_collections col
            JOIN customers c ON col.customer_id = c.id
            WHERE {' AND '.join(clauses)}
            ORDER BY col.collection_date DESC, col.id DESC
        """, tuple(params))

    def get_monthly_collection_total(self, year: int, month: int) -> int:
        ym = f"{year:04d}-{month:02d}"
        row = self.db.fetchone(
            "SELECT COALESCE(SUM(amount),0) AS total FROM ar_collections WHERE collection_date LIKE ?",
            (f"{ym}%",)
        )
        return int(row['total']) if row else 0

    def get_customer_outstanding(self, customer_id: int) -> int:
        """단일 거래처 현재 미수 잔액."""
        cust = self.db.fetchone("SELECT COALESCE(initial_ar, 0) AS init_ar FROM customers WHERE id=?", (customer_id,))
        init_ar = int((cust or {}).get('init_ar', 0))
        credit = self.db.fetchone(
            "SELECT COALESCE(SUM(total_amount),0) AS t FROM sales WHERE customer_id=? AND payment_method='미수'",
            (customer_id,)
        )
        collected = self.db.fetchone(
            "SELECT COALESCE(SUM(amount),0) AS t FROM ar_collections WHERE customer_id=?",
            (customer_id,)
        )
        return init_ar + int((credit or {}).get('t', 0)) - int((collected or {}).get('t', 0))
