# ============================================================
# logic/sales_logic.py
# 판매 내역 CRUD + 재고 자동 반영
# ============================================================

from database.db_manager import DBManager


class SalesLogic:
    def __init__(self):
        self.db = DBManager()

    def _get_spec_info(self, spec_id: int):
        if not hasattr(self, '_spec_cache'):
            self._spec_cache = {}
        if spec_id not in self._spec_cache:
            row = self.db.fetchone("""
                SELECT ps.spec_name, pt.name AS type_name 
                FROM product_specs ps
                JOIN product_types pt ON ps.type_id = pt.id
                WHERE ps.id = ?
            """, (spec_id,))
            self._spec_cache[spec_id] = row
        return self._spec_cache[spec_id]

    def _get_home_spec_id(self, spec_name: str):
        if not hasattr(self, '_home_spec_cache'):
            self._home_spec_cache = {}
        if spec_name not in self._home_spec_cache:
            row = self.db.fetchone("""
                SELECT ps.id 
                FROM product_specs ps
                JOIN product_types pt ON ps.type_id = pt.id
                WHERE pt.name = '가정용 필증' AND ps.spec_name = ?
            """, (spec_name,))
            self._home_spec_cache[spec_name] = row['id'] if row else None
        return self._home_spec_cache[spec_name]

    # ── 판매 등록 ────────────────────────────────────────────
    def add_sale(self, sale_date: str, customer_id: int, spec_id: int,
                 quantity: int, unit_price: int, payment_method: str,
                 memo: str = '', cash_amount: int = 0, card_amount: int = 0) -> int:
        """판매 등록 + 재고 출고 자동 반영."""
        # [아파트 필증] 특별 처리 로직 (캐시 사용)
        spec_info = self._get_spec_info(spec_id)

        if spec_info and spec_info['type_name'].strip() == '아파트 필증':
            # "아파트 필증"인 경우: 판매 테이블에는 기록하지 않고 "가정용 필증" 재고에서 차감
            home_spec_id = self._get_home_spec_id(spec_info['spec_name'])
            target_spec_id = home_spec_id if home_spec_id else spec_id
            memo_str = f"아파트 필증({spec_info['spec_name']}) 배부 차감" + (f" - {memo}" if memo else "")
            
            # 재고 출고만 기록 (판매 기록 안 함)
            self.db.execute(
                """
                INSERT INTO inventory_transactions
                    (spec_id, transaction_date, transaction_type, quantity, memo)
                VALUES (?, ?, '출고', ?, ?)
                """,
                (target_spec_id, sale_date, quantity, memo_str)
            )
            return -1  # 판매 기록이 없음을 의미

        total = quantity * unit_price

        # 일반 판매 내역 저장
        sale_id = self.db.execute(
            """
            INSERT INTO sales
                (sale_date, customer_id, spec_id, quantity, unit_price,
                 total_amount, payment_method, cash_amount, card_amount, memo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (sale_date, customer_id, spec_id, quantity, unit_price,
             total, payment_method, cash_amount, card_amount, memo)
        )

        # 일반 재고 출고 자동 기록
        self.db.execute(
            """
            INSERT INTO inventory_transactions
                (spec_id, transaction_date, transaction_type, quantity, reference_id, memo)
            VALUES (?, ?, '출고', ?, ?, '판매 출고')
            """,
            (spec_id, sale_date, quantity, sale_id)
        )
        return sale_id

    def add_sales_batch(self, rows: list) -> list:
        """
        다중 행 일괄 저장.
        rows: [dict(sale_date, customer_id, spec_id, quantity, unit_price,
                    payment_method, memo, cash_amount, card_amount), ...]
        반환: 저장된 sale_id 목록
        """
        ids = []
        for r in rows:
            sid = self.add_sale(
                r['sale_date'], r['customer_id'], r['spec_id'],
                r['quantity'], r['unit_price'], r['payment_method'],
                r.get('memo', ''), r.get('cash_amount', 0), r.get('card_amount', 0)
            )
            ids.append(sid)
        return ids

    # ── 판매 수정 / 삭제 ─────────────────────────────────────
    def update_sale(self, sale_id: int, quantity: int, unit_price: int,
                    payment_method: str, memo: str = ''):
        """판매 수정 (수량/단가 변경 시 재고 출고량도 보정)."""
        old = self.get_sale_by_id(sale_id)
        if not old:
            raise ValueError(f"판매 ID {sale_id}를 찾을 수 없습니다.")

        total = quantity * unit_price

        self.db.execute(
            """
            UPDATE sales
               SET quantity=?, unit_price=?, total_amount=?,
                   payment_method=?, memo=?
             WHERE id=?
            """,
            (quantity, unit_price, total, payment_method, memo, sale_id)
        )

        # 재고 출고량 보정: 기존 출고 레코드 업데이트
        self.db.execute(
            """
            UPDATE inventory_transactions
               SET quantity=?
             WHERE reference_id=? AND transaction_type='출고'
            """,
            (quantity, sale_id)
        )

    def delete_sale(self, sale_id: int):
        """판매 삭제 + 연결된 재고 출고 레코드 삭제."""
        self.db.execute(
            "DELETE FROM inventory_transactions WHERE reference_id=? AND transaction_type='출고'",
            (sale_id,)
        )
        self.db.execute("DELETE FROM sales WHERE id=?", (sale_id,))

    # ── 조회 ─────────────────────────────────────────────────
    def get_sale_by_id(self, sale_id: int) -> dict | None:
        return self.db.fetchone("SELECT * FROM sales WHERE id=?", (sale_id,))

    def get_sales_by_date(self, date: str) -> list:
        """특정 날짜 전체 판매."""
        return self.db.fetchall(
            """
            SELECT s.*,
                   c.name AS customer_name,
                   pt.name AS type_name,
                   ps.spec_name,
                   ps.product_code
            FROM sales s
            JOIN customers c         ON s.customer_id = c.id
            JOIN product_specs ps    ON s.spec_id     = ps.id
            JOIN product_types pt    ON ps.type_id    = pt.id
            WHERE s.sale_date = ?
            ORDER BY c.name, pt.id, ps.spec_name
            """,
            (date,)
        )

    def get_sales_by_customer_period(self, customer_id: int,
                                     start_date: str, end_date: str) -> list:
        """거래처별 기간 판매 조회."""
        return self.db.fetchall(
            """
            SELECT s.*,
                   c.name AS customer_name,
                   pt.name AS type_name,
                   ps.spec_name,
                   ps.product_code
            FROM sales s
            JOIN customers c         ON s.customer_id = c.id
            JOIN product_specs ps    ON s.spec_id     = ps.id
            JOIN product_types pt    ON ps.type_id    = pt.id
            WHERE s.customer_id = ?
              AND s.sale_date BETWEEN ? AND ?
            ORDER BY s.sale_date, pt.id, ps.spec_name
            """,
            (customer_id, start_date, end_date)
        )

    def get_sales_by_period(self, start_date: str, end_date: str,
                            customer_id: int = None) -> list:
        """기간 판매 조회 (거래처 선택 가능)."""
        if customer_id:
            return self.get_sales_by_customer_period(customer_id, start_date, end_date)
        return self.db.fetchall(
            """
            SELECT s.*,
                   c.name AS customer_name,
                   pt.name AS type_name,
                   ps.spec_name,
                   ps.product_code
            FROM sales s
            JOIN customers c         ON s.customer_id = c.id
            JOIN product_specs ps    ON s.spec_id     = ps.id
            JOIN product_types pt    ON ps.type_id    = pt.id
            WHERE s.sale_date BETWEEN ? AND ?
            ORDER BY s.sale_date, c.name, pt.id
            """,
            (start_date, end_date)
        )

    def get_daily_summary(self, date: str) -> dict:
        """해당 날짜 종합 판매 현황. 건수 = 납품 거래처 수 (품목 수 아님)."""
        row = self.db.fetchone(
            """
            SELECT
                COUNT(DISTINCT customer_id)                     AS sale_count,
                COALESCE(SUM(quantity), 0)                      AS total_qty,
                COALESCE(SUM(total_amount), 0)                  AS total_amount,
                COALESCE(SUM(CASE WHEN payment_method='현금' THEN total_amount
                                  WHEN payment_method='현금+카드' THEN COALESCE(cash_amount, 0)
                                  ELSE 0 END), 0) AS cash,
                COALESCE(SUM(CASE WHEN payment_method='미수'  THEN total_amount ELSE 0 END), 0) AS credit,
                COALESCE(SUM(CASE WHEN payment_method='카드' THEN total_amount
                                  WHEN payment_method='현금+카드' THEN COALESCE(card_amount, 0)
                                  ELSE 0 END), 0) AS card
            FROM sales
            WHERE sale_date = ?
            """,
            (date,)
        )
        return row or {}

    def get_monthly_summary(self, year: int, month: int) -> list:
        """월별 일자별 판매 집계. 건수 = 해당 일 납품 거래처 수."""
        ym = f"{year:04d}-{month:02d}"
        return self.db.fetchall(
            """
            SELECT sale_date,
                   COUNT(DISTINCT customer_id) AS sale_count,
                   SUM(quantity)               AS total_qty,
                   SUM(total_amount)           AS total_amount
            FROM sales
            WHERE sale_date LIKE ?
            GROUP BY sale_date
            ORDER BY sale_date
            """,
            (f"{ym}%",)
        )
