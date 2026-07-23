# ============================================================
# ui/dialogs/login_dialog.py  —  모던 로그인 팝업 (Rich Aesthetics)
# ============================================================

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from logic.auth_logic import AuthLogic
from ui.dialogs.db_config_dialog import DBConfigDialog


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth = AuthLogic()
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("🔒 종량제 봉투 판매 관리 시스템 — 로그인")
        self.setMinimumWidth(440)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }
            QLineEdit {
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 11pt;
                background-color: #ffffff;
                color: #1e293b;
            }
            QLineEdit:focus {
                border: 2px solid #6366f1;
                background-color: #ffffff;
            }
        """)

        root = QVBoxLayout(self)
        root.setSpacing(20)
        root.setContentsMargins(32, 28, 32, 24)

        # 헤더 카드
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #6366f1);
                border-radius: 12px;
            }
        """)
        header_v = QVBoxLayout(header_frame)
        header_v.setContentsMargins(20, 20, 20, 20)
        header_v.setSpacing(6)

        title_lbl = QLabel("🔒  시스템 로그인")
        title_lbl.setStyleSheet("color: #ffffff; font-size: 16pt; font-weight: bold; background: transparent; border: none;")
        title_lbl.setAlignment(Qt.AlignCenter)
        header_v.addWidget(title_lbl)

        sub_lbl = QLabel("종량제 봉투 및 폐기물 통합 관리 플랫폼")
        sub_lbl.setStyleSheet("color: #e0e7ff; font-size: 9.5pt; background: transparent; border: none;")
        sub_lbl.setAlignment(Qt.AlignCenter)
        header_v.addWidget(sub_lbl)
        root.addWidget(header_frame)

        # 안내 문구
        hint_lbl = QLabel("아이디와 비밀번호를 입력해 주세요.\n(최초 실행 시 아이디: admin / 비밀번호: admin1234)")
        hint_lbl.setStyleSheet("color: #64748b; font-size: 9pt; background: transparent;")
        hint_lbl.setAlignment(Qt.AlignCenter)
        hint_lbl.setWordWrap(True)
        root.addWidget(hint_lbl)

        # 로그인 폼
        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        def fl(t):
            l = QLabel(t)
            l.setStyleSheet("color: #334155; font-size: 10.5pt; font-weight: 600; background: transparent;")
            return l

        self.edit_id = QLineEdit()
        self.edit_id.setPlaceholderText("아이디 (예: admin)")
        self.edit_id.setText("admin")  # 편의를 위해 기본값 세팅
        form.addRow(fl("아이디"), self.edit_id)

        self.edit_pw = QLineEdit()
        self.edit_pw.setEchoMode(QLineEdit.Password)
        self.edit_pw.setPlaceholderText("비밀번호 (기본값: admin1234)")
        self.edit_pw.returnPressed.connect(self._login)
        form.addRow(fl("비밀번호"), self.edit_pw)

        root.addLayout(form)

        # 로그인 버튼
        btn_login = QPushButton("🔑   로그 인")
        btn_login.setCursor(Qt.PointingHandCursor)
        btn_login.setFixedHeight(46)
        btn_login.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #4338ca);
                color: #ffffff;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: #4338ca;
            }
            QPushButton:pressed {
                background: #3730a3;
            }
        """)
        btn_login.clicked.connect(self._login)
        root.addWidget(btn_login)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #e2e8f0; background: #e2e8f0; border: none; max-height: 1px;")
        root.addWidget(line)

        # 하단 DB 연결 설정 바
        bh = QHBoxLayout()
        btn_db = QPushButton("🌐  DB 연결 및 네트워크 공유 설정")
        btn_db.setObjectName("btn_ghost")
        btn_db.setCursor(Qt.PointingHandCursor)
        btn_db.setStyleSheet("""
            QPushButton {
                color: #6366f1;
                font-size: 9pt;
                background: transparent;
                border: 1px solid #c7d2fe;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #e0e7ff;
            }
        """)
        btn_db.clicked.connect(self._open_db_config)
        bh.addStretch()
        bh.addWidget(btn_db)
        bh.addStretch()
        root.addLayout(bh)

    def _login(self):
        uid = self.edit_id.text().strip()
        pwd = self.edit_pw.text().strip()
        if not uid or not pwd:
            QMessageBox.warning(self, "입력 오류", "아이디와 비밀번호를 모두 입력해주세요.")
            return

        user = self.auth.login(uid, pwd)
        if user:
            self.accept()
        else:
            QMessageBox.warning(self, "로그인 실패", "아이디 또는 비밀번호가 일치하지 않거나 비활성화된 계정입니다.")
            self.edit_pw.clear()
            self.edit_pw.setFocus()

    def _open_db_config(self):
        if DBConfigDialog(self).exec_():
            # DB가 바뀌었을 수 있으므로 AuthLogic 재연결
            self.auth = AuthLogic()
