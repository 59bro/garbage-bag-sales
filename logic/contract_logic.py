# ============================================================
# logic/contract_logic.py
# 입고 계약 및 잔여수량 조회 로직
# ============================================================

from database.db_manager import DBManager

class ContractLogic:
    def __init__(self):
        self.db = DBManager()

    def add_contract(self, supplier_id: int, spec_id: int, contract_quantity: int) -> int:
        """새로운 계약 수량 추가 (동일 업체의 동일 규격이 여러 개일 수도 있지만, 
           일단 단순 합산 방식으로 처리하거나 건별로 저장).
           여기서는 새로운 계약 건을 추가합니다."""
        return self.db.execute(
            """
            INSERT INTO supplier_contracts (supplier_id, spec_id, contract_quantity)
            VALUES (?, ?, ?)
            """,
            (supplier_id, spec_id, contract_quantity)
        )

    def delete_contract(self, contract_id: int):
        """계약 삭제"""
        self.db.execute("DELETE FROM supplier_contracts WHERE id=?", (contract_id,))

    def delete_contract_by_supplier_spec(self, supplier_id: int, spec_id: int):
        """특정 입고처 및 규격의 모든 계약 삭제"""
        self.db.execute(
            "DELETE FROM supplier_contracts WHERE supplier_id=? AND spec_id=?",
            (supplier_id, spec_id)
        )

    def update_contract(self, supplier_id: int, spec_id: int, contract_quantity: int,
                        old_supplier_id: int = None, old_spec_id: int = None):
        """
        계약 수량 및 입고처/규격 수정.
        old_supplier_id / old_spec_id가 지정되면 기존 레코드를 삭제 후 새 계약 정보로 재등록합니다.
        """
        orig_sup  = old_supplier_id if old_supplier_id is not None else supplier_id
        orig_spec = old_spec_id if old_spec_id is not None else spec_id

        # 기존 계약 내역 삭제 후 1건으로 갱신
        self.delete_contract_by_supplier_spec(orig_sup, orig_spec)
        self.add_contract(supplier_id, spec_id, contract_quantity)

    def get_remaining_contracts(self, supplier_id: int = None) -> list:
        """
        입고처별/규격별 총 계약수량, 총 입고(납품)수량, 잔여수량 조회.
        계약 내역이 없더라도 등록된 모든 활성 입고처(customer_type='입고처') 목록을 포함하여 반환합니다.
        """
        where_clause = ""
        params = []
        if supplier_id:
            where_clause = "AND c.id = ?"
            params.append(supplier_id)

        sql = f"""
            SELECT 
                c.id AS supplier_id,
                c.name AS supplier_name,
                COALESCE(pt.name, '-') AS type_name,
                COALESCE(ps.spec_name, '-') AS spec_name,
                sc.spec_id,
                COALESCE(SUM(sc.contract_quantity), 0) AS total_contract_quantity,
                COALESCE((
                    SELECT SUM(it.quantity)
                    FROM inventory_transactions it
                    WHERE it.reference_id = c.id 
                      AND (sc.spec_id IS NULL OR it.spec_id = sc.spec_id)
                      AND it.transaction_type = '입고'
                ), 0) AS total_delivered_quantity,
                (COALESCE(SUM(sc.contract_quantity), 0) - COALESCE((
                    SELECT SUM(it.quantity)
                    FROM inventory_transactions it
                    WHERE it.reference_id = c.id 
                      AND (sc.spec_id IS NULL OR it.spec_id = sc.spec_id)
                      AND it.transaction_type = '입고'
                ), 0)) AS remaining_quantity
            FROM customers c
            LEFT JOIN supplier_contracts sc ON sc.supplier_id = c.id
            LEFT JOIN product_specs ps ON sc.spec_id = ps.id
            LEFT JOIN product_types pt ON ps.type_id = pt.id
            WHERE c.customer_type = '입고처' AND c.is_active = 1 {where_clause}
            GROUP BY c.id, c.name, sc.spec_id, pt.name, ps.spec_name
            ORDER BY c.name, pt.name, ps.spec_name
        """
        return self.db.fetchall(sql, tuple(params))
