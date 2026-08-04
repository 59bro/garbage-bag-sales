# ============================================================
# logic/ar_logic.py  —  미수 / 수금 관리 로직
# ============================================================

from database.db_manager import DBManager


class ARLogic:
    def __init__(self):
        self.db = DBManager()

    # ── 미수 잔액 ────────────────────────────────────────────
    def _get_last_reset_info(self, customer_id: int):
        """
        특정 거래처의 미수 잔액 흐름을 추적하여, 
        잔액이 0원(완납) 이하가 된 마지막 리셋 포인트 이후의 활성 미수/수금 내역을 반환.
        """
        cust = self.db.fetchone("SELECT id, name, district, COALESCE(initial_ar, 0) AS initial_ar FROM customers WHERE id=?", (customer_id,))
        if not cust:
            return None

        init_ar = cust['initial_ar']
        c_sales = self.db.fetchall("SELECT id, sale_date, total_amount FROM sales WHERE customer_id=? AND payment_method='미수' ORDER BY sale_date, id", (customer_id,))
        c_cols  = self.db.fetchall("SELECT id, collection_date, amount FROM ar_collections WHERE customer_id=? ORDER BY collection_date, id", (customer_id,))

        events = []
        if init_ar != 0:
            events.append({'type': 'init', 'date': '0000-00-00', 'id': 0, 'amount': init_ar, 'ref_id': 0})
        for s in c_sales:
            events.append({'type': 'sale', 'date': s['sale_date'], 'id': s['id'], 'amount': s['total_amount'], 'ref_id': s['id']})
        for col in c_cols:
            events.append({'type': 'col', 'date': col['collection_date'], 'id': col['id'], 'amount': -col['amount'], 'ref_id': col['id']})

        # 수금(col)이 신규 판매(sale)보다 동일 날짜에 먼저 처리되도록 정렬
        events.sort(key=lambda x: (x['date'], 0 if x['type']=='init' else (1 if x['type']=='col' else 2), x['id']))

        running = 0
        last_reset_idx = -1
        for idx, ev in enumerate(events):
            running += ev['amount']
            if running <= 0:
                last_reset_idx = idx

        start_idx = last_reset_idx + 1 if last_reset_idx >= 0 else 0
        
        active_events = events[start_idx:]
        last_reset_date = events[last_reset_idx]['date'] if last_reset_idx >= 0 else None

        active_init_ar = sum(ev['amount'] for ev in active_events if ev['type'] == 'init')
        active_sales = sum(ev['amount'] for ev in active_events if ev['type'] == 'sale')
        active_cols = sum(-ev['amount'] for ev in active_events if ev['type'] == 'col')
        outstanding = active_init_ar + active_sales - active_cols

        return {
            'customer_id': customer_id,
            'customer_name': cust['name'],
            'district': cust['district'] or '',
            'initial_ar': active_init_ar,
            'sales_credit': active_sales,
            'total_credit': active_init_ar + active_sales,
            'total_collected': active_cols,
            'outstanding': outstanding,
            'last_reset_date': last_reset_date,
            'active_sale_ids': [ev['ref_id'] for ev in active_events if ev['type'] == 'sale'],
            'active_col_ids': [ev['ref_id'] for ev in active_events if ev['type'] == 'col']
        }

    def get_outstanding_summary(self, include_zero: bool = False) -> list:
        """
        거래처별 미수 잔액 집계.
        전체 데이터를 단 3번의 쿼리로 일괄 조회(Batch Fetch)하여
        인터넷 클라우드 DB 연동 시 GUI 프리징(다운) 현상을 완벽하게 방지합니다.
        """
        customers = self.db.fetchall("SELECT id, name, district, COALESCE(initial_ar, 0) AS initial_ar FROM customers WHERE is_active=1 ORDER BY name")
        all_sales = self.db.fetchall("SELECT id, customer_id, sale_date, total_amount FROM sales WHERE payment_method='미수' ORDER BY sale_date, id")
        all_cols  = self.db.fetchall("SELECT id, customer_id, collection_date, amount FROM ar_collections ORDER BY collection_date, id")

        sales_by_cust = {}
        for s in all_sales:
            sales_by_cust.setdefault(s['customer_id'], []).append(s)

        cols_by_cust = {}
        for col in all_cols:
            cols_by_cust.setdefault(col['customer_id'], []).append(col)

        result = []
        for cust in customers:
            cid = cust['id']
            init_ar = cust['initial_ar']
            c_sales = sales_by_cust.get(cid, [])
            c_cols  = cols_by_cust.get(cid, [])

            events = []
            if init_ar != 0:
                events.append({'type': 'init', 'date': '0000-00-00', 'id': 0, 'amount': init_ar, 'ref_id': 0})
            for s in c_sales:
                events.append({'type': 'sale', 'date': s['sale_date'], 'id': s['id'], 'amount': s['total_amount'], 'ref_id': s['id']})
            for col in c_cols:
                events.append({'type': 'col', 'date': col['collection_date'], 'id': col['id'], 'amount': -col['amount'], 'ref_id': col['id']})

            if not events:
                if include_zero:
                    result.append({
                        'customer_id': cid,
                        'customer_name': cust['name'],
                        'district': cust['district'] or '',
                        'initial_ar': 0,
                        'sales_credit': 0,
                        'total_credit': 0,
                        'total_collected': 0,
                        'outstanding': 0,
                        'last_reset_date': None,
                        'active_sale_ids': [],
                        'active_col_ids': []
                    })
                continue

            events.sort(key=lambda x: (x['date'], 0 if x['type']=='init' else (1 if x['type']=='col' else 2), x['id']))

            running = 0
            last_reset_idx = -1
            for idx, ev in enumerate(events):
                running += ev['amount']
                if running <= 0:
                    last_reset_idx = idx

            start_idx = last_reset_idx + 1 if last_reset_idx >= 0 else 0
            active_events = events[start_idx:]
            last_reset_date = events[last_reset_idx]['date'] if last_reset_idx >= 0 else None

            active_init_ar = sum(ev['amount'] for ev in active_events if ev['type'] == 'init')
            active_sales = sum(ev['amount'] for ev in active_events if ev['type'] == 'sale')
            active_cols = sum(-ev['amount'] for ev in active_events if ev['type'] == 'col')
            outstanding = active_init_ar + active_sales - active_cols

            if not include_zero and outstanding == 0:
                continue

            result.append({
                'customer_id': cid,
                'customer_name': cust['name'],
                'district': cust['district'] or '',
                'initial_ar': active_init_ar,
                'sales_credit': active_sales,
                'total_credit': active_init_ar + active_sales,
                'total_collected': active_cols,
                'outstanding': outstanding,
                'last_reset_date': last_reset_date,
                'active_sale_ids': [ev['ref_id'] for ev in active_events if ev['type'] == 'sale'],
                'active_col_ids': [ev['ref_id'] for ev in active_events if ev['type'] == 'col']
            })

        result.sort(key=lambda x: (-x['outstanding'], x['customer_name']))
        return result

    def get_outstanding_total(self) -> int:
        summary = self.get_outstanding_summary(include_zero=False)
        return sum(s['outstanding'] for s in summary)

    def get_credit_sales_by_customer(self, customer_id: int,
                                      start_date: str = None,
                                      end_date: str = None,
                                      only_active_cycle: bool = True) -> list:
        """
        특정 거래처의 미수 판매 내역.
        only_active_cycle=True인 경우 이전 완납 포인트 이후의 활성 미수 판매건만 조회합니다.
        """
        info = self._get_last_reset_info(customer_id)
        if not info:
            return []

        clauses = ["s.customer_id = ?", "s.payment_method = '미수'"]
        params  = [customer_id]

        if only_active_cycle and info['active_sale_ids']:
            placeholders = ",".join(["?"] * len(info['active_sale_ids']))
            clauses.append(f"s.id IN ({placeholders})")
            params.extend(info['active_sale_ids'])
        elif only_active_cycle and not info['active_sale_ids']:
            return []

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
            ORDER BY s.sale_date DESC, s.id DESC
        """, tuple(params))

    def get_credit_by_date_grouped(self, customer_id: int, only_active_cycle: bool = True) -> list:
        """거래처별 미수 판매를 날짜별로 그룹핑하여 반환."""
        info = self._get_last_reset_info(customer_id)
        if not info:
            return []

        clauses = ["s.customer_id = ?", "s.payment_method = '미수'"]
        params  = [customer_id]

        if only_active_cycle and info['active_sale_ids']:
            placeholders = ",".join(["?"] * len(info['active_sale_ids']))
            clauses.append(f"s.id IN ({placeholders})")
            params.extend(info['active_sale_ids'])
        elif only_active_cycle and not info['active_sale_ids']:
            return []

        return self.db.fetchall(f"""
            SELECT s.sale_date,
                   COUNT(*) AS item_count,
                   SUM(s.quantity) AS total_qty,
                   SUM(s.total_amount) AS total_amount
            FROM sales s
            WHERE {' AND '.join(clauses)}
            GROUP BY s.sale_date
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
