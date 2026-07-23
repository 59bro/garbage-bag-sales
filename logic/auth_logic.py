# ============================================================
# logic/auth_logic.py  —  로그인 및 사용자 계정 관리 비즈니스 로직
# ============================================================

import hashlib
from database.db_manager import DBManager


class AuthLogic:
    current_user: dict | None = None  # 전역 현재 로그인 사용자 정보

    def __init__(self):
        self.db = DBManager()

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def login(self, username: str, password: str) -> dict | None:
        username = username.strip()
        pwd_hash = self.hash_password(password)
        user = self.db.fetchone(
            """
            SELECT id, username, name, role, is_active
            FROM users
            WHERE username = ? AND password_hash = ? AND is_active = 1
            """,
            (username, pwd_hash)
        )
        if user:
            AuthLogic.current_user = user
            return user
        return None

    def logout(self):
        AuthLogic.current_user = None

    def get_all_users(self) -> list:
        return self.db.fetchall(
            """
            SELECT id, username, name, role, is_active, created_at
            FROM users
            ORDER BY id
            """
        )

    def register_user(self, username: str, password: str, name: str, role: str = 'admin') -> int:
        username = username.strip()
        name = name.strip()
        if not username or not password or not name:
            raise ValueError("아이디, 비밀번호, 이름을 모두 입력해주세요.")
        
        existing = self.db.fetchone("SELECT id FROM users WHERE username = ?", (username,))
        if existing:
            raise ValueError(f"이미 존재하는 아이디입니다: '{username}'")

        pwd_hash = self.hash_password(password)
        return self.db.execute(
            """
            INSERT INTO users (username, password_hash, name, role, is_active)
            VALUES (?, ?, ?, ?, 1)
            """,
            (username, pwd_hash, name, role)
        )

    def update_user(self, user_id: int, name: str, role: str, password: str = None):
        name = name.strip()
        if not name:
            raise ValueError("이름을 입력해주세요.")
        
        if password and password.strip():
            pwd_hash = self.hash_password(password.strip())
            self.db.execute(
                "UPDATE users SET name = ?, role = ?, password_hash = ? WHERE id = ?",
                (name, role, pwd_hash, user_id)
            )
        else:
            self.db.execute(
                "UPDATE users SET name = ?, role = ? WHERE id = ?",
                (name, role, user_id)
            )

    def deactivate_user(self, user_id: int):
        if AuthLogic.current_user and AuthLogic.current_user['id'] == user_id:
            raise ValueError("현재 로그인된 본인 계정은 비활성화할 수 없습니다.")
        self.db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))

    def activate_user(self, user_id: int):
        self.db.execute("UPDATE users SET is_active = 1 WHERE id = ?", (user_id,))
