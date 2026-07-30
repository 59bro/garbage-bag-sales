# ============================================================
# database/db_manager.py  —  DB 연결 싱글톤 + 마이그레이션
# SQLite (로컬) 및 PostgreSQL (Supabase 클라우드) 양쪽 지원
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

        # ── 환경변수 DATABASE_URL 우선 (Render 클라우드 배포용) ──
        db_url = os.environ.get('DATABASE_URL', '')
        if db_url:
            self.db_mode = 'postgres'
            self._pg_dsn = db_url
            self.pg_host = ''
            self.pg_port = 6543
            self.pg_db   = 'postgres'
            self.pg_user = ''
            self.pg_pass = ''
            self.db_path = None
            self._initialized = True
            return

        from utils.db_config_manager import get_db_config
        cfg = get_db_config()

        self.db_mode = cfg.get('db_mode', 'sqlite')
        self._pg_dsn = ''  # 환경변수 없을 때는 빈 값

        if self.db_mode == 'postgres':
            self.pg_host = cfg.get('cloud_host', '')
            self.pg_port = cfg.get('cloud_port', 6543)
            self.pg_db   = cfg.get('cloud_dbname', 'postgres')
            self.pg_user = cfg.get('cloud_user', 'postgres')
            self.pg_pass = cfg.get('cloud_password', '')
            self.db_path = None
        else:
            self.pg_host = None
            custom_path = cfg.get('sqlite_path', '').strip()
            if custom_path and os.path.exists(os.path.dirname(custom_path)):
                self.db_path = custom_path
            elif custom_path and not os.path.exists(os.path.dirname(custom_path)):
                self.db_path = DB_PATH
            else:
                self.db_path = DB_PATH
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        self._initialized = True

        if self.db_mode == 'sqlite':
            self._initialize_db()
            self._migrate()

    def reload_config(self):
        from utils.db_config_manager import get_db_config
        cfg = get_db_config()
        self.db_mode = cfg.get('db_mode', 'sqlite')

        if self.db_mode == 'postgres':
            self.pg_host = cfg.get('cloud_host', '')
            self.pg_port = cfg.get('cloud_port', 6543)
            self.pg_db   = cfg.get('cloud_dbname', 'postgres')
            self.pg_user = cfg.get('cloud_user', 'postgres')
            self.pg_pass = cfg.get('cloud_password', '')
        else:
            custom_path = cfg.get('sqlite_path', '').strip()
            if custom_path and os.path.exists(os.path.dirname(custom_path)):
                self.db_path = custom_path
            else:
                self.db_path = DB_PATH
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self._initialize_db()
            self._migrate()

    def get_connection(self):
        if self.db_mode == 'postgres':
            return self._get_pg_connection()
        else:
            return self._get_sqlite_connection()

    def _get_sqlite_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _get_pg_connection(self):
        import psycopg2
        import psycopg2.extras
        # ── 커넥션 풀링: 기존 연결이 살아있으면 재사용 ──
        if hasattr(self, '_pg_conn') and self._pg_conn and not self._pg_conn.closed:
            try:
                # 연결 상태 확인 (끊어졌으면 재연결)
                self._pg_conn.cursor().execute("SELECT 1")
                return self._pg_conn
            except Exception:
                try:
                    self._pg_conn.close()
                except Exception:
                    pass

        # DATABASE_URL 환경변수로 설정된 DSN 우선 사용
        if getattr(self, '_pg_dsn', ''):
            dsn = self._pg_dsn
        else:
            import urllib.parse
            pw = urllib.parse.quote(self.pg_pass, safe='')
            dsn = f"postgresql://{self.pg_user}:{pw}@{self.pg_host}:{self.pg_port}/{self.pg_db}?sslmode=require"
        conn = psycopg2.connect(dsn)
        conn.autocommit = False
        self._pg_conn = conn
        return conn

    def _close_pg_connection(self):
        """PostgreSQL 연결 명시적 종료 (앱 종료 시 호출)."""
        if hasattr(self, '_pg_conn') and self._pg_conn and not self._pg_conn.closed:
            try:
                self._pg_conn.close()
            except Exception:
                pass
            self._pg_conn = None

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
        """기존 DB에 컬럼/테이블 추가 마이그레이션 (SQLite 전용)."""
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

            # sales 테이블에 cash_amount / card_amount 컬럼 추가 (복합결제 지원)
            sale_cols = [r[1] for r in conn.execute("PRAGMA table_info(sales)")]
            if 'cash_amount' not in sale_cols:
                conn.execute("ALTER TABLE sales ADD COLUMN cash_amount INTEGER DEFAULT 0")
            if 'card_amount' not in sale_cols:
                conn.execute("ALTER TABLE sales ADD COLUMN card_amount INTEGER DEFAULT 0")

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

    # ── 헬퍼 (SQLite ? → PostgreSQL %s 자동 변환) ─────────────
    def _convert_sql(self, sql: str) -> str:
        """SQLite의 ? 플레이스홀더를 PostgreSQL의 %s로 변환."""
        if self.db_mode == 'postgres':
            return sql.replace('?', '%s')
        return sql

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        sql = self._convert_sql(sql)
        if self.db_mode == 'postgres':
            import psycopg2.extras
            conn = self.get_connection()
            try:
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur.execute(sql, params)
                result = [dict(row) for row in cur.fetchall()]
                cur.close()
                return result
            except Exception as e:
                conn.rollback()
                # 연결 끊김이면 재연결 시도
                if 'closed' in str(e).lower() or 'connection' in str(e).lower():
                    self._pg_conn = None
                    return self.fetchall(self._convert_sql(sql.replace('%s', '?')), params)
                raise
        else:
            with self.get_connection() as conn:
                cur = conn.execute(sql, params)
                return [dict(row) for row in cur.fetchall()]

    def fetchone(self, sql: str, params: tuple = ()) -> dict | None:
        sql = self._convert_sql(sql)
        if self.db_mode == 'postgres':
            import psycopg2.extras
            conn = self.get_connection()
            try:
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur.execute(sql, params)
                row = cur.fetchone()
                cur.close()
                return dict(row) if row else None
            except Exception as e:
                conn.rollback()
                if 'closed' in str(e).lower() or 'connection' in str(e).lower():
                    self._pg_conn = None
                    return self.fetchone(self._convert_sql(sql.replace('%s', '?')), params)
                raise
        else:
            with self.get_connection() as conn:
                cur = conn.execute(sql, params)
                row = cur.fetchone()
                return dict(row) if row else None

    def execute(self, sql: str, params: tuple = ()) -> int:
        sql = self._convert_sql(sql)
        if self.db_mode == 'postgres':
            conn = self.get_connection()
            try:
                cur = conn.cursor()
                cur.execute(sql + " RETURNING id" if "INSERT" in sql.upper() and "RETURNING" not in sql.upper() else sql, params)
                conn.commit()
                if cur.description:
                    row = cur.fetchone()
                    result = row[0] if row else 0
                else:
                    result = cur.rowcount
                cur.close()
                return result
            except Exception:
                conn.rollback()
                raise
        else:
            with self.get_connection() as conn:
                cur = conn.execute(sql, params)
                conn.commit()
                return cur.lastrowid

    def executemany(self, sql: str, params_list: list):
        sql = self._convert_sql(sql)
        if self.db_mode == 'postgres':
            conn = self.get_connection()
            try:
                cur = conn.cursor()
                for params in params_list:
                    cur.execute(sql, params)
                conn.commit()
                cur.close()
            except Exception:
                conn.rollback()
                raise
        else:
            with self.get_connection() as conn:
                conn.executemany(sql, params_list)
                conn.commit()

