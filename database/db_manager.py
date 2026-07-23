# ============================================================
# database/db_manager.py  —  DB 연결 싱글톤 + 마이그레이션
# ============================================================

import sqlite3
import os
from database.models import ALL_TABLES, DEFAULT_PRODUCT_TYPES

from utils.db_config_manager import get_root_dir

_ROOT   = get_root_dir()
DB_PATH = os.path.join(_ROOT, 'data', 'sales.db')


class DBManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        from utils.db_config_manager import get_db_config
        cfg = get_db_config()
        custom_path = cfg.get('sqlite_path', '').strip()
        if custom_path and os.path.exists(os.path.dirname(custom_path)):
            self.db_path = custom_path
        elif custom_path and not os.path.exists(os.path.dirname(custom_path)):
            # 만약 구글 드라이브나 지정 폴더가 없으면 기본 경로(실행 파일 옆 data/sales.db) 사용
            self.db_path = DB_PATH
        else:
            self.db_path = DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._initialized = True
        self._initialize_db()
        self._migrate()

    def reload_config(self):
        from utils.db_config_manager import get_db_config
        cfg = get_db_config()
        custom_path = cfg.get('sqlite_path', '').strip()
        if custom_path and os.path.exists(os.path.dirname(custom_path)):
            self.db_path = custom_path
        else:
            self.db_path = DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._initialize_db()
        self._migrate()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _initialize_db(self):
        with self.get_connection() as conn:
            for sql in ALL_TABLES:
                conn.execute(sql)
            for name in DEFAULT_PRODUCT_TYPES:
                conn.execute(
                    "INSERT OR IGNORE INTO product_types (name) VALUES (?)", (name,)
                )
            conn.commit()

    def _migrate(self):
        """기존 DB에 컬럼/테이블 추가 마이그레이션."""
        with self.get_connection() as conn:
            # customers 테이블에 district 컬럼 추가
            cols = [r[1] for r in conn.execute("PRAGMA table_info(customers)")]
            if 'district' not in cols:
                conn.execute("ALTER TABLE customers ADD COLUMN district TEXT DEFAULT ''")
            if 'customer_type' not in cols:
                conn.execute("ALTER TABLE customers ADD COLUMN customer_type TEXT DEFAULT '출고처'")
            if 'initial_ar' not in cols:
                conn.execute("ALTER TABLE customers ADD COLUMN initial_ar INTEGER DEFAULT 0")
                
            # product_specs 테이블에 product_code 컬럼 추가
            spec_cols = [r[1] for r in conn.execute("PRAGMA table_info(product_specs)")]
            if 'product_code' not in spec_cols:
                conn.execute("ALTER TABLE product_specs ADD COLUMN product_code TEXT DEFAULT ''")
            
            # 재사용봉투 품목 추가
            conn.execute(
                "INSERT OR IGNORE INTO product_types (name) VALUES ('재사용봉투')"
            )
            
            # 신규 테이블 생성 (차량, 반입, 사용자 관리, 입고 계약)
            from database.models import CREATE_DISPOSAL_SITES, CREATE_VEHICLES, CREATE_VEHICLE_LOGS, CREATE_USERS, CREATE_SUPPLIER_CONTRACTS
            conn.execute(CREATE_DISPOSAL_SITES)
            conn.execute(CREATE_VEHICLES)
            conn.execute(CREATE_VEHICLE_LOGS)
            conn.execute(CREATE_USERS)
            conn.execute(CREATE_SUPPLIER_CONTRACTS)

            # 관리자 계정이 없으면 자동 등록 ('admin' / 'admin1234')
            import hashlib
            default_hash = hashlib.sha256('admin1234'.encode('utf-8')).hexdigest()
            conn.execute(
                "INSERT OR IGNORE INTO users (username, password_hash, name, role) VALUES (?, ?, ?, ?)",
                ('admin', default_hash, '최고관리자', 'admin')
            )
            conn.commit()

    # ── 헬퍼 ────────────────────────────────────────────────
    def fetchall(self, sql: str, params: tuple = ()) -> list:
        with self.get_connection() as conn:
            cur = conn.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]

    def fetchone(self, sql: str, params: tuple = ()) -> dict | None:
        with self.get_connection() as conn:
            cur = conn.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None

    def execute(self, sql: str, params: tuple = ()) -> int:
        with self.get_connection() as conn:
            cur = conn.execute(sql, params)
            conn.commit()
            return cur.lastrowid

    def executemany(self, sql: str, params_list: list):
        with self.get_connection() as conn:
            conn.executemany(sql, params_list)
            conn.commit()
