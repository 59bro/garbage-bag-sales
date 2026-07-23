# ============================================================
# logic/report_logic.py
# 보고서 / 통계 조회 로직
# ============================================================

from database.db_manager import DBManager


class ReportLogic:
    def __init__(self):
        self.db = DBManager()

    # ── 일별 거래처별 현황 ────────────────────────────────────
    def get_daily_by_customer(self, date: str) -> list:
        """특정 날짜의 거래처별 판매 집계."""
        return self.db.fetchall(
            """
            SELECT
                c.name AS customer_name,
                SUM(s.quantity)     AS total_qty,
                SUM(s.total_amount) AS total_amount,
                SUM(CASE WHEN s.payment_method='현금' THEN s.total_amount ELSE 0 END) AS cash,
                SUM(CASE WHEN s.payment_method='미수' THEN s.total_amount ELSE 0 END) AS credit,
                SUM(CASE WHEN s.payment_method='카드' THEN s.total_amount ELSE 0 END) AS card
            FROM sales s
            JOIN customers c ON s.customer_id = c.id
            WHERE s.sale_date = ?
            GROUP BY c.id
            ORDER BY c.name
            """,
            (date,)
        )

    # ── 기간별 거래처별 현황 ──────────────────────────────────
    def get_period_by_customer(self, start_date: str, end_date: str,
                               customer_id: int = None) -> list:
        params = [start_date, end_date]
        cust_filter = ""
        if customer_id:
            cust_filter = "AND s.customer_id = ?"
            params.append(customer_id)

        return self.db.fetchall(
            f"""
            SELECT
                s.sale_date,
                c.name AS customer_name,
                pt.name AS type_name,
                ps.spec_name,
                s.quantity,
                s.unit_price,
                s.total_amount,
                s.payment_method,
                s.memo
            FROM sales s
            JOIN customers c      ON s.customer_id = c.id
            JOIN product_specs ps ON s.spec_id     = ps.id
            JOIN product_types pt ON ps.type_id    = pt.id
            WHERE s.sale_date BETWEEN ? AND ?
            {cust_filter}
            ORDER BY s.sale_date, c.name, pt.id, ps.spec_name
            """,
            tuple(params)
        )

    # ── 기간 종합 집계 ────────────────────────────────────────
    def get_period_summary(self, start_date: str, end_date: str) -> dict:
        """기간 종합. 건수 = 고유 (날짜, 거래처) 단위."""
        row = self.db.fetchone(
            """
            SELECT
                COUNT(DISTINCT sale_date || '|' || customer_id) AS sale_count,
                COALESCE(SUM(quantity), 0)                      AS total_qty,
                COALESCE(SUM(total_amount), 0)                  AS total_amount,
                COALESCE(SUM(CASE WHEN payment_method='현금' THEN total_amount ELSE 0 END), 0) AS cash,
                COALESCE(SUM(CASE WHEN payment_method='미수'  THEN total_amount ELSE 0 END), 0) AS credit,
                COALESCE(SUM(CASE WHEN payment_method='카드' THEN total_amount ELSE 0 END), 0) AS card
            FROM sales
            WHERE sale_date BETWEEN ? AND ?
            """,
            (start_date, end_date)
        )
        return row or {}

    # ── 월별 거래처별 판매 집계 ───────────────────────────────
    def get_monthly_customer_summary(self, year: int, month: int) -> list:
        ym = f"{year:04d}-{month:02d}"
        return self.db.fetchall(
            """
            SELECT
                c.name AS customer_name,
                SUM(s.quantity)     AS total_qty,
                SUM(s.total_amount) AS total_amount
            FROM sales s
            JOIN customers c ON s.customer_id = c.id
            WHERE s.sale_date LIKE ?
            GROUP BY c.id
            ORDER BY total_amount DESC
            """,
            (f"{ym}%",)
        )

    # ── 규격별 판매 집계 ──────────────────────────────────────
    def get_period_by_spec(self, start_date: str, end_date: str) -> list:
        return self.db.fetchall(
            """
            SELECT
                pt.name AS type_name,
                ps.spec_name,
                SUM(s.quantity)     AS total_qty,
                SUM(s.total_amount) AS total_amount
            FROM sales s
            JOIN product_specs ps ON s.spec_id  = ps.id
            JOIN product_types pt ON ps.type_id = pt.id
            WHERE s.sale_date BETWEEN ? AND ?
            GROUP BY ps.id
            ORDER BY pt.id, total_amount DESC
            """,
            (start_date, end_date)
        )

    # ── 연도별 월별 집계 ──────────────────────────────────────
    def get_yearly_monthly_summary(self, year: int) -> list:
        """연도 그룹별 월별 집계. 건수 = 해당 월 고유 납품 단위."""
        return self.db.fetchall(
            """
            SELECT
                SUBSTR(sale_date, 1, 7) AS ym,
                COUNT(DISTINCT sale_date || '|' || customer_id) AS sale_count,
                SUM(quantity)           AS total_qty,
                SUM(total_amount)       AS total_amount
            FROM sales
            WHERE sale_date LIKE ?
            GROUP BY ym
            ORDER BY ym
            """,
            (f"{year:04d}%",)
        )
