# ============================================================
# ui/dialogs/disposal_site_dialog.py  —  폐기물 반입처/거래처 등록·수정
# ============================================================

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt
from logic.vehicle_logic import VehicleLogic


class DisposalSiteDialog(QDialog):
    def __init__(self, parent=None, site_id: int = None):
        super().__init__(parent)
        self.site_id = site_id
        self.logic = VehicleLogic()
        self._build_ui()
        if site_id:
            self._load_data()

    def _build_ui(self):
        title = "폐기물 반입처 수정" if self.site_id else "신규 반입처 등록"
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(24, 20, 24, 20)

        lbl = QLabel(title)
        lbl.setStyleSheet(
            "color:#818cf8; font-size:14pt; font-weight:bold; "
            "background:transparent; border:none;"
        )
        lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(lbl)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        def fl(t):
            l = QLabel(t)
            l.setObjectName("form_label")
            return l

        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("반입처/거래처명 (필수)")
        form.addRow(fl("반입처명 *"), self.edit_name)

        self.edit_address = QLineEdit()
        self.edit_address.setPlaceholderText("주소")
        form.addRow(fl("주소"), self.edit_address)

        self.edit_memo = QTextEdit()
        self.edit_memo.setMaximumHeight(70)
        self.edit_memo.setPlaceholderText("메모")
        form.addRow(fl("메모"), self.edit_memo)

        root.addLayout(form)

        bh = QHBoxLayout()
        bh.setSpacing(10)
        btn_cancel = QPushButton("취소")
        btn_cancel.setObjectName("btn_ghost")
        btn_cancel.setFixedHeight(38)
        btn_save = QPushButton("저장")
        btn_save.setObjectName("btn_success")
        btn_save.setFixedHeight(38)
        btn_cancel.clicked.connect(self.reject)
        btn_save.clicked.connect(self._save)
        bh.addWidget(btn_cancel)
        bh.addWidget(btn_save)
        root.addLayout(bh)

    def _load_data(self):
        d = self.logic.get_disposal_site_by_id(self.site_id)
        if d:
            self.edit_name.setText(d['name'])
            self.edit_address.setText(d.get('address', ''))
            self.edit_memo.setPlainText(d.get('memo', ''))

    def _save(self):
        name    = self.edit_name.text().strip()
        address = self.edit_address.text().strip()
        memo    = self.edit_memo.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "입력 오류", "반입처명을 입력해주세요.")
            return

        try:
            if self.site_id:
                self.logic.update_disposal_site(self.site_id, name, address, memo)
            else:
                self.site_id = self.logic.add_disposal_site(name, address, memo)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "입력 오류", str(e))
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패: {e}")
