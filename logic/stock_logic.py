# ============================================================
# logic/stock_logic.py
# 재고 관리 (초기재고 / 입고 / 출고 / 현재고 계산)
# ============================================================

from database.db_manager import DBManager


class StockLogic:
    def __init__(self):
        self.db = DBManager()

    # ── 초기재고 ─────────────────────────────────────────────
    def has_initial_stock(self, spec_id: int) -> bool:
        row = self.db.fetchone(
            "SELECT id FROM inventory_transactions WHERE spec_id=? AND transaction_type='초기재고'",
            (spec_id,)
        )
        return row is not None

    def set_initial_stock(self, spec_id: int, quantity: int, date: str, memo: str = ''):
        """최초 1회 초기재고 설정. 이미 있으면 업데이트."""
        existing = self.db.fetchone(
            "SELECT id FROM inventory_transactions WHERE spec_id=? AND transaction_type='초기재고'",
            (spec_id,)
        )
        if existing:
            self.db.execute(
                """
                UPDATE inventory_transactions
                   SET quantity=?, transaction_date=?, memo=?
                 WHERE id=?
                """,
                (quantity, date, memo, existing['id'])
            )
        else:
            self.db.execute(
                """
                INSERT INTO inventory_transactions
                    (spec_id, transaction_date, transaction_type, quantity, memo)
                VALUES (?, ?, '초기재고', ?, ?)
                """,
                (spec_id, date, quantity, memo)
            )

    # ── 입고 ─────────────────────────────────────────────────
    def add_inbound(self, spec_id: int, quantity: int, date: str, memo: str = '', supplier_id: int = None) -> int:
        if quantity <= 0:
            raise ValueError("입고 수량은 1 이상이어야 합니다.")
        return self.db.execute(
            """
            INSERT INTO inventory_transactions
                (spec_id, transaction_date, transaction_type, quantity, memo, reference_id)
            VALUES (?, ?, '입고', ?, ?, ?)
            """,
            (spec_id, date, quantity, memo, supplier_id)
        )

    def update_inbound(self, transaction_id: int, quantity: int, date: str, memo: str = ''):
        self.db.execute(
            """
            UPDATE inventory_transactions
               SET quantity=?, transaction_date=?, memo=?
             WHERE id=? AND transaction_type='입고'
            """,
            (quantity, date, memo, transaction_id)
        )

    def delete_inbound(self, transaction_id: int):
        self.db.execute(
            "DELETE FROM inventory_transactions WHERE id=? AND transaction_type='입고'",
            (transaction_id,)
        )

    # ── 현재고 계산 ──────────────────────────────────────────
    def get_current_stock(self, spec_id: int) -> int:
        """
        현재고 = (가장 최근 설정된) 초기재고 + (초기재고일 이후의) 입고 합계 - (초기재고일 이후의) 출고 합계
        """
        row = self.db.fetchone(
            """
            SELECT 
                COALESCE(init.quantity, 0)
                + COALESCE(SUM(CASE WHEN it.transaction_type = '입고' THEN it.quantity ELSE 0 END), 0)
                - COALESCE(SUM(CASE WHEN it.transaction_type = '출고' THEN it.quantity ELSE 0 END), 0)
                AS current_stock
            FROM product_specs ps
            LEFT JOIN inventory_transactions init 
                   ON init.spec_id = ps.id AND init.transaction_type = '초기재고'
            LEFT JOIN inventory_transactions it 
                   ON it.spec_id = ps.id 
                  AND it.transaction_type != '초기재고'
                  AND (init.transaction_date IS NULL OR it.transaction_date >= init.transaction_date)
            WHERE ps.id = ?
            GROUP BY ps.id, init.quantity
            """,
            (spec_id,)
        )
        return int(row['current_stock']) if row else 0

    def get_all_current_stocks(self) -> list:
        """모든 규격의 현재고 목록."""
        return self.db.fetchall(
            """
            SELECT
                ps.id AS spec_id,
                pt.name AS type_name,
                ps.spec_name,
                ps.unit_price,
                COALESCE(init.quantity, 0)
                + COALESCE(SUM(CASE WHEN it.transaction_type = '입고' THEN it.quantity ELSE 0 END), 0)
                - COALESCE(SUM(CASE WHEN it.transaction_type = '출고' THEN it.quantity ELSE 0 END), 0)
                AS current_stock
            FROM product_specs ps
            JOIN product_types pt ON ps.type_id = pt.id
            LEFT JOIN inventory_transactions init 
                   ON init.spec_id = ps.id AND init.transaction_type = '초기재고'
            LEFT JOIN inventory_transactions it 
                   ON it.spec_id = ps.id 
                  AND it.transaction_type != '초기재고'
                  AND (init.transaction_date IS NULL OR it.transaction_date >= init.transaction_date)
            WHERE ps.is_active = 1
            GROUP BY ps.id, pt.name, ps.spec_name, ps.unit_price, init.quantity
            ORDER BY pt.id, ps.spec_name
            """
        )

    # ── 재고 이동 내역 조회 ───────────────────────────────────
    def get_transactions(self, spec_id: int = None,
                         start_date: str = None, end_date: str = None,
                         trans_type: str = None) -> list:
        """재고 이동 내역 조회 (조건 선택적)."""
        where_clauses = []
        params = []

        if spec_id:
            where_clauses.append("it.spec_id = ?")
            params.append(spec_id)
        if start_date:
            where_clauses.append("it.transaction_date >= ?")
            params.append(start_date)
        if end_date:
            where_clauses.append("it.transaction_date <= ?")
            params.append(end_date)
        if trans_type:
            where_clauses.append("it.transaction_type = ?")
            params.append(trans_type)

        where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        sql = f"""
            SELECT it.*,
                   pt.name AS type_name,
                   ps.spec_name,
                   c.name AS supplier_name
            FROM inventory_transactions it
            JOIN product_specs ps ON it.spec_id = ps.id
            JOIN product_types pt ON ps.type_id = pt.id
            LEFT JOIN customers c ON it.reference_id = c.id AND it.transaction_type = '입고'
            {where}
            ORDER BY it.transaction_date DESC, it.id DESC
        """
        return self.db.fetchall(sql, tuple(params))

    def get_inbound_by_period(self, spec_id: int = None,
                              start_date: str = None, end_date: str = None) -> list:
        return self.get_transactions(spec_id, start_date, end_date, '입고')
