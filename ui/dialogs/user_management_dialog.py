# ============================================================
# ui/dialogs/user_management_dialog.py  —  사용자 계정 관리 대화창
# ============================================================

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QComboBox, QFrame, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from logic.auth_logic import AuthLogic


class UserManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth = AuthLogic()
        self._build_ui()
        self._load_users()

    def _build_ui(self):
        self.setWindowTitle("👥  시스템 사용자 계정 관리")
        self.resize(750, 520)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(24, 20, 24, 20)

        # 타이틀
        th = QHBoxLayout()
        lbl_title = QLabel("👥  시스템 사용자 및 로그인 권한 관리")
        lbl_title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #1e293b;")
        th.addWidget(lbl_title)
        th.addStretch()

        btn_add = QPushButton("➕  신규 사용자 등록")
        btn_add.setObjectName("btn_success")
        btn_add.setFixedHeight(38)
        btn_add.clicked.connect(self._add_user)
        th.addWidget(btn_add)
        root.addLayout(th)

        # 안내
        lbl_desc = QLabel("등록된 사용자는 동일한 아이디와 비밀번호로 이 시스템(또는 연결된 DB 폴더/서버)에 로그인하여 작업할 수 있습니다.")
        lbl_desc.setStyleSheet("color: #64748b; font-size: 9pt;")
        root.addWidget(lbl_desc)

        # 테이블
        self.tbl = QTableWidget(0, 6)
        self.tbl.setHorizontalHeaderLabels(['ID', '아이디', '사용자 이름', '권한', '계정 상태', '등록일시'])
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)

        hh = self.tbl.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        root.addWidget(self.tbl)

        # 하단 액션
        bh = QHBoxLayout()
        btn_edit = QPushButton("✏  선택 계정 수정 / 암호 초기화")
        btn_edit.setObjectName("btn_primary")
        btn_edit.setFixedHeight(38)
        btn_edit.clicked.connect(self._edit_user)

        btn_toggle = QPushButton("🔄  계정 활성 / 비활성화 전환")
        btn_toggle.setObjectName("btn_warning")
        btn_toggle.setFixedHeight(38)
        btn_toggle.clicked.connect(self._toggle_user)

        btn_close = QPushButton("닫기")
        btn_close.setObjectName("btn_ghost")
        btn_close.setFixedHeight(38)
        btn_close.clicked.connect(self.accept)

        bh.addWidget(btn_edit)
        bh.addWidget(btn_toggle)
        bh.addStretch()
        bh.addWidget(btn_close)
        root.addLayout(bh)

    def _load_users(self):
        users = self.auth.get_all_users()
        self.tbl.setRowCount(len(users))
        for r, u in enumerate(users):
            vals = [
                u['id'], u['username'], u['name'],
                "관리자(Admin)" if u['role'] == 'admin' else "일반 사용자",
                "🟢 활성" if u['is_active'] else "🔴 비활성",
                u['created_at'] or ''
            ]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                if c == 4:
                    item.setForeground(QColor('#10b981' if u['is_active'] else '#ef4444'))
                self.tbl.setItem(r, c, item)

    def _get_selected_user_id(self) -> int | None:
        row = self.tbl.currentRow()
        if row < 0:
            QMessageBox.warning(self, "선택 알림", "목록에서 사용자 계정을 선택해 주세요.")
            return None
        return int(self.tbl.item(row, 0).text())

    def _add_user(self):
        dlg = UserEditDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_users()

    def _edit_user(self):
        uid = self._get_selected_user_id()
        if not uid:
            return
        # 기존 정보 가져오기
        row = self.tbl.currentRow()
        username = self.tbl.item(row, 1).text()
        name = self.tbl.item(row, 2).text()
        role = 'admin' if 'Admin' in self.tbl.item(row, 3).text() else 'user'

        dlg = UserEditDialog(self, user_id=uid, username=username, name=name, role=role)
        if dlg.exec_() == QDialog.Accepted:
            self._load_users()

    def _toggle_user(self):
        uid = self._get_selected_user_id()
        if not uid:
            return
        row = self.tbl.currentRow()
        is_active = ("🟢 활성" in self.tbl.item(row, 4).text())
        try:
            if is_active:
                if QMessageBox.question(self, "비활성화 확인", "해당 계정의 로그인을 차단(비활성화)하시겠습니까?",
                                        QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                    self.auth.deactivate_user(uid)
            else:
                self.auth.activate_user(uid)
            self._load_users()
        except ValueError as ve:
            QMessageBox.warning(self, "처리 오류", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "오류", f"상태 변경 중 오류: {e}")


class UserEditDialog(QDialog):
    def __init__(self, parent=None, user_id: int = None, username: str = "", name: str = "", role: str = "user"):
        super().__init__(parent)
        self.auth = AuthLogic()
        self.user_id = user_id
        self.init_username = username
        self.init_name = name
        self.init_role = role
        self._build_ui()

    def _build_ui(self):
        is_edit = self.user_id is not None
        self.setWindowTitle("✏ 사용자 계정 수정" if is_edit else "➕ 신규 사용자 등록")
        self.setMinimumWidth(400)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(24, 20, 24, 20)

        form = QFormLayout()
        form.setSpacing(12)

        def fl(t):
            l = QLabel(t); l.setStyleSheet("font-weight:bold; color:#334155;"); return l

        self.edit_id = QLineEdit(self.init_username)
        if is_edit:
            self.edit_id.setEnabled(False)
            self.edit_id.setStyleSheet("background:#f1f5f9; color:#64748b;")
        form.addRow(fl("아이디 *"), self.edit_id)

        self.edit_pw = QLineEdit()
        self.edit_pw.setEchoMode(QLineEdit.Password)
        self.edit_pw.setPlaceholderText("변경 시에만 입력 (빈칸 시 기존 암호 유지)" if is_edit else "비밀번호 입력")
        form.addRow(fl("비밀번호 *"), self.edit_pw)

        self.edit_name = QLineEdit(self.init_name)
        form.addRow(fl("사용자 이름 *"), self.edit_name)

        self.combo_role = QComboBox()
        self.combo_role.addItem("일반 사용자 (조회 및 입력)", "user")
        self.combo_role.addItem("최고 관리자 (모든 권한 및 설정)", "admin")
        idx = self.combo_role.findData(self.init_role)
        if idx >= 0:
            self.combo_role.setCurrentIndex(idx)
        form.addRow(fl("권한 설정"), self.combo_role)

        root.addLayout(form)

        bh = QHBoxLayout()
        btn_cancel = QPushButton("취소")
        btn_cancel.setObjectName("btn_ghost")
        btn_cancel.setFixedHeight(38)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾 저장하기")
        btn_save.setObjectName("btn_success")
        btn_save.setFixedHeight(38)
        btn_save.clicked.connect(self._save)

        bh.addWidget(btn_cancel)
        bh.addWidget(btn_save)
        root.addLayout(bh)

    def _save(self):
        uid_str = self.edit_id.text().strip()
        pwd_str = self.edit_pw.text().strip()
        name_str = self.edit_name.text().strip()
        role_str = self.combo_role.currentData()

        try:
            if self.user_id is None:
                # 신규
                self.auth.register_user(uid_str, pwd_str, name_str, role_str)
            else:
                # 수정
                self.auth.update_user(self.user_id, name_str, role_str, pwd_str if pwd_str else None)
            QMessageBox.information(self, "완료", "사용자 정보가 성공적으로 저장되었습니다.")
            self.accept()
        except ValueError as ve:
            QMessageBox.warning(self, "입력 오류", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"처리 중 오류가 발생했습니다: {e}")
