# ============================================================
# logic/customer_logic.py  —  거래처 CRUD + 지역 필터
# ============================================================

from database.db_manager import DBManager


class CustomerLogic:
    def __init__(self):
        self.db = DBManager()

    def get_all(self, include_inactive=False, district: str = None, customer_type: str = None) -> list:
        clauses = ["1=1"]
        params  = []
        if not include_inactive:
            clauses.append("is_active = 1")
        if district:
            clauses.append("district = ?")
            params.append(district)
        if customer_type:
            clauses.append("customer_type = ?")
            params.append(customer_type)
        where = " AND ".join(clauses)
        return self.db.fetchall(
            f"SELECT * FROM customers WHERE {where} ORDER BY customer_type DESC, district, name",
            tuple(params)
        )

    def get_by_id(self, cid: int) -> dict | None:
        return self.db.fetchone("SELECT * FROM customers WHERE id=?", (cid,))

    def add(self, name: str, district: str = '', phone: str = '',
            address: str = '', memo: str = '', customer_type: str = '출고처', initial_ar: int = 0) -> int:
        if not name.strip():
            raise ValueError("거래처명을 입력해주세요.")
        return self.db.execute(
            "INSERT INTO customers (name, district, phone, address, memo, customer_type, initial_ar) VALUES (?,?,?,?,?,?,?)",
            (name.strip(), district, phone.strip(), address.strip(), memo.strip(), customer_type, initial_ar)
        )

    def update(self, cid: int, name: str, district: str = '', phone: str = '',
               address: str = '', memo: str = '', customer_type: str = '출고처', initial_ar: int = None):
        if not name.strip():
            raise ValueError("거래처명을 입력해주세요.")
        if initial_ar is not None:
            self.db.execute(
                "UPDATE customers SET name=?, district=?, phone=?, address=?, memo=?, customer_type=?, initial_ar=? WHERE id=?",
                (name.strip(), district, phone.strip(), address.strip(), memo.strip(), customer_type, initial_ar, cid)
            )
        else:
            self.db.execute(
                "UPDATE customers SET name=?, district=?, phone=?, address=?, memo=?, customer_type=? WHERE id=?",
                (name.strip(), district, phone.strip(), address.strip(), memo.strip(), customer_type, cid)
            )

    def update_initial_ar(self, cid: int, initial_ar: int):
        self.db.execute("UPDATE customers SET initial_ar=? WHERE id=?", (initial_ar, cid))

    def deactivate(self, cid: int):
        self.db.execute("UPDATE customers SET is_active=0 WHERE id=?", (cid,))

    def activate(self, cid: int):
        self.db.execute("UPDATE customers SET is_active=1 WHERE id=?", (cid,))

    def has_references(self, cid: int) -> dict:
        row = self.db.fetchone("""
            SELECT 
                (SELECT COUNT(*) FROM sales WHERE customer_id=?) AS sales_cnt,
                (SELECT COUNT(*) FROM ar_collections WHERE customer_id=?) AS ar_cnt,
                (SELECT COUNT(*) FROM supplier_contracts WHERE supplier_id=?) AS contract_cnt
        """, (cid, cid, cid))
        s = row['sales_cnt'] if row else 0
        a = row['ar_cnt'] if row else 0
        c = row['contract_cnt'] if row else 0
        total = s + a + c
        return {
            'has_ref': total > 0,
            'sales_cnt': s,
            'ar_cnt': a,
            'contract_cnt': c,
            'total_cnt': total
        }

    def delete(self, cid: int, check_ref: bool = True):
        if check_ref:
            ref = self.has_references(cid)
            if ref['has_ref']:
                raise ValueError("기존 거래/수금/계약 내역이 존재하는 거래처는 완전 삭제할 수 없습니다. 대신 비활성화 기능을 이용하세요.")
        self.db.execute("DELETE FROM customers WHERE id=?", (cid,))

    def get_names_dict(self) -> dict:
        return {r['id']: r['name'] for r in self.get_all()}

