# ============================================================
# logic/product_logic.py
# 규격 / 단가 CRUD 비즈니스 로직
# ============================================================

from database.db_manager import DBManager


class ProductLogic:
    def __init__(self):
        self.db = DBManager()

    # ── 품목 종류 ────────────────────────────────────────────
    def get_types(self) -> list:
        return self.db.fetchall("SELECT * FROM product_types ORDER BY id")

    def get_type_by_id(self, type_id: int) -> dict | None:
        return self.db.fetchone("SELECT * FROM product_types WHERE id = ?", (type_id,))

    def add_type(self, name: str) -> int:
        name = name.strip()
        if not name:
            raise ValueError("품목 종류명을 입력해주세요.")
        # Check duplicate
        existing = self.db.fetchone("SELECT id FROM product_types WHERE name = ?", (name,))
        if existing:
            raise ValueError(f"이미 존재하는 품목 종류입니다: '{name}'")
        return self.db.execute("INSERT INTO product_types (name) VALUES (?)", (name,))

    def update_type(self, type_id: int, name: str):
        name = name.strip()
        if not name:
            raise ValueError("품목 종류명을 입력해주세요.")
        existing = self.db.fetchone("SELECT id FROM product_types WHERE name = ? AND id != ?", (name, type_id))
        if existing:
            raise ValueError(f"이미 존재하는 품목 종류명입니다: '{name}'")
        self.db.execute("UPDATE product_types SET name = ? WHERE id = ?", (name, type_id))

    def delete_type(self, type_id: int):
        # Check if any product_specs belong to this type
        specs = self.db.fetchone("SELECT COUNT(*) AS cnt FROM product_specs WHERE type_id = ?", (type_id,))
        if specs and specs['cnt'] > 0:
            raise ValueError(f"이 품목 종류에 소속된 규격이 {specs['cnt']}개 있습니다.\n먼저 소속 규격을 비활성화하거나 삭제해주세요.")
        self.db.execute("DELETE FROM product_types WHERE id = ?", (type_id,))

    # ── 규격 ─────────────────────────────────────────────────
    def get_specs_by_type(self, type_id: int, include_inactive: bool = False) -> list:
        if include_inactive:
            sql = """
                SELECT ps.*, pt.name AS type_name
                FROM product_specs ps
                JOIN product_types pt ON ps.type_id = pt.id
                WHERE ps.type_id = ?
                ORDER BY CAST(ps.spec_name AS INTEGER), ps.spec_name
            """
        else:
            sql = """
                SELECT ps.*, pt.name AS type_name
                FROM product_specs ps
                JOIN product_types pt ON ps.type_id = pt.id
                WHERE ps.type_id = ? AND ps.is_active = 1
                ORDER BY CAST(ps.spec_name AS INTEGER), ps.spec_name
            """
        return self.db.fetchall(sql, (type_id,))

    def get_all_specs(self, include_inactive: bool = False) -> list:
        where = "" if include_inactive else "WHERE ps.is_active = 1"
        sql = f"""
            SELECT ps.*, pt.name AS type_name
            FROM product_specs ps
            JOIN product_types pt ON ps.type_id = pt.id
            {where}
            ORDER BY pt.id, CAST(ps.spec_name AS INTEGER), ps.spec_name
        """
        return self.db.fetchall(sql)

    def get_spec_by_id(self, spec_id: int) -> dict | None:
        return self.db.fetchone(
            """
            SELECT ps.*, pt.name AS type_name
            FROM product_specs ps
            JOIN product_types pt ON ps.type_id = pt.id
            WHERE ps.id = ?
            """,
            (spec_id,)
        )

    def add_spec(self, type_id: int, spec_name: str, product_code: str, unit_price: int) -> int:
        if not spec_name.strip():
            raise ValueError("규격명을 입력해주세요.")
        if unit_price < 0:
            raise ValueError("단가는 0 이상이어야 합니다.")
        return self.db.execute(
            "INSERT INTO product_specs (type_id, spec_name, product_code, unit_price) VALUES (?, ?, ?, ?)",
            (type_id, spec_name.strip(), product_code.strip(), unit_price)
        )

    def update_spec(self, spec_id: int, type_id: int, spec_name: str, product_code: str, unit_price: int):
        if not spec_name.strip():
            raise ValueError("규격명을 입력해주세요.")
        self.db.execute(
            "UPDATE product_specs SET type_id=?, spec_name=?, product_code=?, unit_price=? WHERE id=?",
            (type_id, spec_name.strip(), product_code.strip(), unit_price, spec_id)
        )

    def deactivate_spec(self, spec_id: int):
        self.db.execute(
            "UPDATE product_specs SET is_active = 0 WHERE id = ?", (spec_id,)
        )

    def activate_spec(self, spec_id: int):
        self.db.execute(
            "UPDATE product_specs SET is_active = 1 WHERE id = ?", (spec_id,)
        )

    def get_spec_display_name(self, spec_id: int) -> str:
        """'생활용 봉투 - 10L' 형태 반환."""
        row = self.get_spec_by_id(spec_id)
        if row:
            return f"{row['type_name']} - {row['spec_name']}"
        return ''

    def get_specs_for_combo(self) -> list:
        """콤보박스용: [(id, '종류 - 규격', unit_price), ...]"""
        rows = self.get_all_specs()
        return [(r['id'], f"{r['type_name']} - {r['spec_name']}", r['unit_price']) for r in rows]
