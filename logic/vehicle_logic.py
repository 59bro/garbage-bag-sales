# ============================================================
# logic/vehicle_logic.py  —  차량, 폐기물 반입처, 운행일지 CRUD
# ============================================================

from database.db_manager import DBManager


class VehicleLogic:
    def __init__(self):
        self.db = DBManager()

    # ── 차량 관리 (Vehicles) ─────────────────────────────────
    def get_all_vehicles(self, include_inactive=False, vehicle_type: str = None) -> list:
        clauses = ["1=1"]
        params = []
        if not include_inactive:
            clauses.append("is_active = 1")
        if vehicle_type:
            clauses.append("vehicle_type = ?")
            params.append(vehicle_type)
        where = " AND ".join(clauses)
        return self.db.fetchall(
            f"SELECT * FROM vehicles WHERE {where} ORDER BY vehicle_type, vehicle_number",
            tuple(params)
        )

    def get_vehicle_by_id(self, vid: int) -> dict | None:
        return self.db.fetchone("SELECT * FROM vehicles WHERE id=?", (vid,))

    def add_vehicle(self, vehicle_number: str, vehicle_type: str, crew_count: int,
                    crew_names: str, default_start_time: str, default_end_time: str) -> int:
        if not vehicle_number.strip():
            raise ValueError("차량 번호를 입력해주세요.")
        return self.db.execute(
            """INSERT INTO vehicles (vehicle_number, vehicle_type, crew_count, crew_names,
                                     default_start_time, default_end_time)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (vehicle_number.strip(), vehicle_type, crew_count, crew_names.strip(),
             default_start_time.strip(), default_end_time.strip())
        )

    def update_vehicle(self, vid: int, vehicle_number: str, vehicle_type: str, crew_count: int,
                       crew_names: str, default_start_time: str, default_end_time: str):
        if not vehicle_number.strip():
            raise ValueError("차량 번호를 입력해주세요.")
        self.db.execute(
            """UPDATE vehicles SET vehicle_number=?, vehicle_type=?, crew_count=?, crew_names=?,
                                   default_start_time=?, default_end_time=? WHERE id=?""",
            (vehicle_number.strip(), vehicle_type, crew_count, crew_names.strip(),
             default_start_time.strip(), default_end_time.strip(), vid)
        )

    def deactivate_vehicle(self, vid: int):
        self.db.execute("UPDATE vehicles SET is_active=0 WHERE id=?", (vid,))

    def activate_vehicle(self, vid: int):
        self.db.execute("UPDATE vehicles SET is_active=1 WHERE id=?", (vid,))

    # ── 폐기물 반입처 관리 (Disposal Sites) ─────────────────────
    def get_all_disposal_sites(self, include_inactive=False) -> list:
        where = "1=1" if include_inactive else "is_active = 1"
        return self.db.fetchall(f"SELECT * FROM disposal_sites WHERE {where} ORDER BY name")

    def get_disposal_site_by_id(self, sid: int) -> dict | None:
        return self.db.fetchone("SELECT * FROM disposal_sites WHERE id=?", (sid,))

    def add_disposal_site(self, name: str, address: str = '', memo: str = '') -> int:
        if not name.strip():
            raise ValueError("반입처/거래처명을 입력해주세요.")
        return self.db.execute(
            "INSERT INTO disposal_sites (name, address, memo) VALUES (?, ?, ?)",
            (name.strip(), address.strip(), memo.strip())
        )

    def update_disposal_site(self, sid: int, name: str, address: str = '', memo: str = ''):
        if not name.strip():
            raise ValueError("반입처/거래처명을 입력해주세요.")
        self.db.execute(
            "UPDATE disposal_sites SET name=?, address=?, memo=? WHERE id=?",
            (name.strip(), address.strip(), memo.strip(), sid)
        )

    def deactivate_disposal_site(self, sid: int):
        self.db.execute("UPDATE disposal_sites SET is_active=0 WHERE id=?", (sid,))

    def activate_disposal_site(self, sid: int):
        self.db.execute("UPDATE disposal_sites SET is_active=1 WHERE id=?", (sid,))

    # ── 차량별 운행 및 폐기물 반입 일지 (Vehicle Logs) ─────────────
    def add_log(self, record_date: str, vehicle_id: int, start_time: str, end_time: str,
                absent_crew: str = '', disposal_site_id: int | None = None,
                disposal_amount: float = 0, memo: str = '') -> int:
        return self.db.execute(
            """INSERT INTO vehicle_logs (record_date, vehicle_id, start_time, end_time,
                                         absent_crew, disposal_site_id, disposal_amount, memo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (record_date, vehicle_id, start_time.strip(), end_time.strip(),
             absent_crew.strip(), disposal_site_id, disposal_amount, memo.strip())
        )

    def update_log(self, log_id: int, record_date: str, vehicle_id: int, start_time: str, end_time: str,
                   absent_crew: str = '', disposal_site_id: int | None = None,
                   disposal_amount: float = 0, memo: str = ''):
        self.db.execute(
            """UPDATE vehicle_logs SET record_date=?, vehicle_id=?, start_time=?, end_time=?,
                                       absent_crew=?, disposal_site_id=?, disposal_amount=?, memo=?
               WHERE id=?""",
            (record_date, vehicle_id, start_time.strip(), end_time.strip(),
             absent_crew.strip(), disposal_site_id, disposal_amount, memo.strip(), log_id)
        )

    def delete_log(self, log_id: int):
        self.db.execute("DELETE FROM vehicle_logs WHERE id=?", (log_id,))

    def get_logs(self, start_date: str = None, end_date: str = None,
                 vehicle_id: int = None, vehicle_type: str = None,
                 disposal_site_id: int = None) -> list:
        sql = """
        SELECT vl.*,
               v.vehicle_number,
               v.vehicle_type,
               v.crew_count,
               v.crew_names,
               v.default_start_time,
               v.default_end_time,
               ds.name AS disposal_site_name
          FROM vehicle_logs vl
          JOIN vehicles v ON vl.vehicle_id = v.id
     LEFT JOIN disposal_sites ds ON vl.disposal_site_id = ds.id
         WHERE 1=1
        """
        params = []
        if start_date:
            sql += " AND vl.record_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND vl.record_date <= ?"
            params.append(end_date)
        if vehicle_id:
            sql += " AND vl.vehicle_id = ?"
            params.append(vehicle_id)
        if vehicle_type:
            sql += " AND v.vehicle_type = ?"
            params.append(vehicle_type)
        if disposal_site_id:
            sql += " AND vl.disposal_site_id = ?"
            params.append(disposal_site_id)

        sql += " ORDER BY vl.record_date DESC, v.vehicle_type, v.vehicle_number"
        return self.db.fetchall(sql, tuple(params))
