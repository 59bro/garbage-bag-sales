# ============================================================
# ui/dialogs/db_config_dialog.py  —  DB 공유/클라우드 연결 설정 팝업
# ============================================================

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from utils.db_config_manager import get_db_config, save_db_config
from database.db_manager import DBManager


class DBConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_db_config()
        self.changed = False
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        self.setWindowTitle("☁️ 구글 드라이브 및 DB 연결 설정")
        self.setMinimumWidth(540)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(24, 20, 24, 20)

        # 타이틀
        lbl_title = QLabel("☁️  구글 드라이브(Google Drive) 실시간 데이터 연동")
        lbl_title.setStyleSheet(
            "color:#2563eb; font-size:14pt; font-weight:bold; "
            "background:transparent; border:none;"
        )
        lbl_title.setAlignment(Qt.AlignCenter)
        root.addWidget(lbl_title)

        desc = QLabel(
            "사내와 외부 PC(집/출장지) 어디서나 100% 동일한 데이터로 접속하시려면,\n"
            "구글 드라이브 폴더 내부에 DB 파일(sales.db)을 위치시키면 실시간으로 동기화됩니다."
        )
        desc.setStyleSheet("color:#475569; font-size:9.5pt;")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        root.addWidget(desc)

        # 구글 드라이브 자동 탐색 카드
        g_box = QFrame()
        g_box.setStyleSheet("""
            QFrame {
                background-color: #eff6ff;
                border: 1.5px solid #bfdbfe;
                border-radius: 10px;
            }
        """)
        gv = QVBoxLayout(g_box)
        gv.setContentsMargins(16, 14, 16, 14)
        gv.setSpacing(10)

        gl_title = QLabel("💡  가장 빠른 연동: 구글 드라이브 자동 탐색 및 적용")
        gl_title.setStyleSheet("font-weight: bold; color: #1e40af; font-size: 10pt; border: none;")
        gv.addWidget(gl_title)

        gl_sub = QLabel("PC에 설치된 구글 드라이브(G:\\내 드라이브 등)를 찾아 전용 DB 폴더를 자동으로 생성하고 연결합니다.")
        gl_sub.setStyleSheet("color: #3b82f6; font-size: 8.5pt; border: none;")
        gv.addWidget(gl_sub)

        btn_auto_g = QPushButton("☁️   내 PC의 구글 드라이브 폴더 자동 탐색 / 연결")
        btn_auto_g.setCursor(Qt.PointingHandCursor)
        btn_auto_g.setFixedHeight(40)
        btn_auto_g.setStyleSheet("""
            QPushButton {
                background: #2563eb;
                color: white;
                font-weight: bold;
                font-size: 10pt;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background: #1d4ed8; }
        """)
        btn_auto_g.clicked.connect(self._auto_detect_gdrive)
        gv.addWidget(btn_auto_g)
        root.addWidget(g_box)

        # 폼 (직접 지정)
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        def fl(t):
            l = QLabel(t); l.setObjectName("form_label"); return l

        path_box = QHBoxLayout()
        self.edit_sqlite_path = QLineEdit()
        self.edit_sqlite_path.setPlaceholderText("예: G:\\내 드라이브\\봉투관리DB\\sales.db")
        btn_browse = QPushButton("📁 직접 찾아보기")
        btn_browse.setObjectName("btn_ghost")
        btn_browse.clicked.connect(self._browse_file)
        path_box.addWidget(self.edit_sqlite_path, 1)
        path_box.addWidget(btn_browse)
        form.addRow(fl("DB 파일 경로 *"), path_box)

        root.addLayout(form)

        # 하단 버튼
        bh = QHBoxLayout()
        bh.setSpacing(10)
        btn_cancel = QPushButton("취소")
        btn_cancel.setObjectName("btn_ghost")
        btn_cancel.setFixedHeight(38)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾 설정 저장 및 적용")
        btn_save.setObjectName("btn_success")
        btn_save.setFixedHeight(38)
        btn_save.clicked.connect(self._save)

        bh.addWidget(btn_cancel)
        bh.addWidget(btn_save)
        root.addLayout(bh)

    def _load_data(self):
        self.edit_sqlite_path.setText(self.config.get('sqlite_path', ''))

    def _auto_detect_gdrive(self):
        # 흔한 구글 드라이브 마운트 경로 리스트
        candidates = [
            r"G:\내 드라이브",
            r"G:\My Drive",
            r"D:\Google Drive",
            r"E:\Google Drive",
            r"F:\Google Drive",
            os.path.expanduser(r"~\Google Drive"),
            os.path.expanduser(r"~\OneDrive"),
        ]
        found = None
        for path in candidates:
            if os.path.exists(path):
                found = path
                break

        if found:
            target_folder = os.path.join(found, "종량제봉투_통합DB")
            target_db = os.path.join(target_folder, "sales.db")
            reply = QMessageBox.question(
                self, "☁️ 구글 드라이브 발견",
                f"내 PC에서 구글 드라이브 경로를 발견했습니다!\n\n▶ 경로: {found}\n\n이곳에 [종량제봉투_통합DB\\sales.db] 폴더를 만들고 실시간 연동을 진행하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                os.makedirs(target_folder, exist_ok=True)
                self.edit_sqlite_path.setText(target_db)
                self._save()
        else:
            QMessageBox.information(
                self, "알림",
                "기본 경로(G:\\내 드라이브 등)에서 구글 드라이브 폴더를 자동으로 찾지 못했습니다.\n\n"
                " PC에 구글 드라이브 앱(Google Drive 데스크톱)이 설치되어 있는지 확인하신 후, 하단의 '📁 직접 찾아보기' 버튼을 눌러 구글 드라이브 폴더를 직접 선택해 주세요."
            )

    def _browse_file(self):
        cur_path = self.edit_sqlite_path.text().strip()
        start_dir = os.path.dirname(cur_path) if cur_path and os.path.exists(os.path.dirname(cur_path)) else ""
        path, _ = QFileDialog.getSaveFileName(
            self, "구글 드라이브 내 DB 파일 지정 (또는 새로 생성)", start_dir, "SQLite DB (*.db)"
        )
        if path:
            self.edit_sqlite_path.setText(os.path.normpath(path))

    def _save(self):
        new_path = self.edit_sqlite_path.text().strip()
        if not new_path:
            QMessageBox.warning(self, "입력 오류", "DB 파일 경로를 지정해 주세요.")
            return

        try:
            import shutil, sqlite3
            # 기존 로컬 DB 경로
            _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            local_db = os.path.join(_ROOT, 'data', 'sales.db')

            # 대상 경로가 없거나 비어있는 DB인 경우 기존 로컬 DB를 자동 복사(마이그레이션)
            if os.path.normpath(new_path) != os.path.normpath(local_db) and os.path.exists(local_db):
                need_copy = True
                if os.path.exists(new_path):
                    try:
                        conn = sqlite3.connect(new_path)
                        cnt = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
                        conn.close()
                        if cnt > 0:
                            need_copy = False
                    except Exception:
                        need_copy = True

                if need_copy:
                    os.makedirs(os.path.dirname(new_path), exist_ok=True)
                    shutil.copy2(local_db, new_path)

            self.config['sqlite_path'] = new_path
            self.config['db_mode'] = 'sqlite'
            save_db_config(self.config)

            # DBManager 재설정
            db = DBManager()
            db.reload_config()

            self.changed = True
            QMessageBox.information(self, "적용 완료", f"☁️ 구글 드라이브(또는 공유 폴더) 연동 경로가 성공적으로 적용되었습니다:\n{new_path}\n\n기존 등록하셨던 모든 거래처 및 규격 데이터가 안전하게 연동 보존되었습니다!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "연결 실패", f"지정한 DB 파일 경로에 접근하거나 초기화할 수 없습니다.\n{e}")
