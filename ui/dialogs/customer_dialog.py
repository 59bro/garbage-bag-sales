# ============================================================
# ui/dialogs/customer_dialog.py  —  거래처 등록 / 수정 (지역 추가)
# ============================================================

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QPushButton, QLabel, QMessageBox, QSpinBox
)
from PyQt5.QtCore import Qt
from logic.customer_logic import CustomerLogic
from database.models import DISTRICTS


class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer_id: int = None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.logic = CustomerLogic()
        self._build_ui()
        if customer_id:
            self._load_data()

    def _build_ui(self):
        title = "거래처 수정" if self.customer_id else "거래처 등록"
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
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
        self.edit_name.setPlaceholderText("거래처명 (필수)")
        form.addRow(fl("거래처명 *"), self.edit_name)

        self.combo_type = QComboBox()
        self.combo_type.addItem("출고처", "출고처")
        self.combo_type.addItem("입고처", "입고처")
        form.addRow(fl("거래처 구분"), self.combo_type)

        self.combo_district = QComboBox()
        self.combo_district.addItem("선택 안함", "")
        for d in DISTRICTS:
            self.combo_district.addItem(d, d)
        form.addRow(fl("지역(동)"), self.combo_district)

        self.edit_phone = QLineEdit()
        self.edit_phone.setPlaceholderText("000-0000-0000")
        form.addRow(fl("전화번호"), self.edit_phone)

        self.edit_address = QLineEdit()
        self.edit_address.setPlaceholderText("주소")
        form.addRow(fl("주소"), self.edit_address)

        self.spin_initial_ar = QSpinBox()
        self.spin_initial_ar.setRange(-999999999, 999999999)
        self.spin_initial_ar.setSingleStep(10000)
        self.spin_initial_ar.setAlignment(Qt.AlignRight)
        self.spin_initial_ar.setSuffix(" 원")
        self.spin_initial_ar.setStyleSheet("QSpinBox { font-weight: bold; color: #dc2626; }")
        form.addRow(fl("초기 미수(이월)"), self.spin_initial_ar)

        self.edit_memo = QTextEdit()
        self.edit_memo.setMaximumHeight(70)
        self.edit_memo.setPlaceholderText("메모")
        form.addRow(fl("메모"), self.edit_memo)

        root.addLayout(form)

        bh = QHBoxLayout()
        bh.setSpacing(10)

        if self.customer_id:
            btn_delete = QPushButton("삭제")
            btn_delete.setObjectName("btn_danger")
            btn_delete.setFixedHeight(38)
            btn_delete.clicked.connect(self._delete)
            bh.addWidget(btn_delete)

        bh.addStretch()

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
        d = self.logic.get_by_id(self.customer_id)
        if d:
            self.edit_name.setText(d['name'])
            self.edit_phone.setText(d.get('phone', ''))
            self.edit_address.setText(d.get('address', ''))
            self.edit_memo.setPlainText(d.get('memo', ''))
            self.spin_initial_ar.setValue(int(d.get('initial_ar', 0) or 0))
            
            idx = self.combo_district.findData(d.get('district', ''))
            if idx >= 0:
                self.combo_district.setCurrentIndex(idx)
                
            type_idx = self.combo_type.findData(d.get('customer_type', '출고처'))
            if type_idx >= 0:
                self.combo_type.setCurrentIndex(type_idx)

    def _save(self):
        name     = self.edit_name.text().strip()
        district = self.combo_district.currentData()
        ctype    = self.combo_type.currentData()
        phone    = self.edit_phone.text().strip()
        address  = self.edit_address.text().strip()
        memo     = self.edit_memo.toPlainText().strip()
        init_ar  = self.spin_initial_ar.value()
        try:
            if self.customer_id:
                self.logic.update(self.customer_id, name, district, phone, address, memo, ctype, initial_ar=init_ar)
            else:
                self.customer_id = self.logic.add(name, district, phone, address, memo, ctype, initial_ar=init_ar)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "입력 오류", str(e))
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패: {e}")

    def _delete(self):
        if not self.customer_id:
            return
        cust = self.logic.get_by_id(self.customer_id)
        cust_name = cust['name'] if cust else "거래처"

        ref = self.logic.has_references(self.customer_id)
        if ref['has_ref']:
            msg = (
                f"'{cust_name}' 거래처는 기존 거래/수금/계약 내역(총 {ref['total_cnt']}건)이 존재하여 완전 삭제할 수 없습니다.\n\n"
                f"• 판매 내역: {ref['sales_cnt']}건\n"
                f"• 수금 내역: {ref['ar_cnt']}건\n"
                f"• 입고 계약: {ref['contract_cnt']}건\n\n"
                "대신 '비활성화' 처리를 진행하시겠습니까?"
            )
            reply = QMessageBox.warning(
                self, "완전 삭제 불가", msg,
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.logic.deactivate(self.customer_id)
                self.accept()
            return

        if QMessageBox.question(
            self, "거래처 완전 삭제",
            f"'{cust_name}' 거래처를 정말로 완전 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.Yes:
            try:
                self.logic.delete(self.customer_id)
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "오류", f"거래처 삭제 실패: {e}")

