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

    def get_remaining_contracts(self, supplier_id: int = None) -> list:
        """
        입고처별/규격별 총 계약수량, 총 입고(납품)수량, 잔여수량 조회
        """
        where_clause = ""
        params = []
        if supplier_id:
            where_clause = "WHERE sc.supplier_id = ?"
            params.append(supplier_id)

        sql = f"""
            SELECT 
                sc.supplier_id,
                c.name AS supplier_name,
                pt.name AS type_name,
                ps.spec_name,
                sc.spec_id,
                SUM(sc.contract_quantity) AS total_contract_quantity,
                COALESCE((
                    SELECT SUM(it.quantity)
                    FROM inventory_transactions it
                    WHERE it.reference_id = sc.supplier_id 
                      AND it.spec_id = sc.spec_id 
                      AND it.transaction_type = '입고'
                ), 0) AS total_delivered_quantity,
                (SUM(sc.contract_quantity) - COALESCE((
                    SELECT SUM(it.quantity)
                    FROM inventory_transactions it
                    WHERE it.reference_id = sc.supplier_id 
                      AND it.spec_id = sc.spec_id 
                      AND it.transaction_type = '입고'
                ), 0)) AS remaining_quantity
            FROM supplier_contracts sc
            JOIN customers c ON sc.supplier_id = c.id
            JOIN product_specs ps ON sc.spec_id = ps.id
            JOIN product_types pt ON ps.type_id = pt.id
            {where_clause}
            GROUP BY sc.supplier_id, sc.spec_id, c.name, pt.name, ps.spec_name
            ORDER BY c.name, pt.name, ps.spec_name
        """
        return self.db.fetchall(sql, tuple(params))
