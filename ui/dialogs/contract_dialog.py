# ============================================================
# ui/dialogs/contract_dialog.py
# ============================================================

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from logic.customer_logic import CustomerLogic
from logic.product_logic import ProductLogic
from logic.contract_logic import ContractLogic

class ContractDialog(QDialog):
    def __init__(self, parent=None, supplier_id: int = None, spec_id: int = None, current_qty: int = 0):
        super().__init__(parent)
        self.supplier_id = supplier_id
        self.spec_id = spec_id
        self.current_qty = current_qty

        title = "입고처 계약 수량 수정" if supplier_id and spec_id else "입고처 계약 수량 등록"
        self.setWindowTitle(title)
        self.setFixedSize(400, 250)
        
        self.customer_logic = CustomerLogic()
        self.product_logic = ProductLogic()
        self.contract_logic = ContractLogic()

        self._build_ui()
        if supplier_id and spec_id:
            self._load_edit_data()

    def _build_ui(self):
        v = QVBoxLayout(self)
        v.setSpacing(12)
        v.setContentsMargins(20, 20, 20, 20)

        # 입고처
        h1 = QHBoxLayout()
        lbl1 = QLabel("입고처:")
        lbl1.setFixedWidth(80)
        self.combo_supplier = QComboBox()
        for c in self.customer_logic.get_all(include_inactive=False):
            if c.get('customer_type') == '입고처':
                self.combo_supplier.addItem(c['name'], c['id'])
        h1.addWidget(lbl1)
        h1.addWidget(self.combo_supplier)
        v.addLayout(h1)

        # 품목 규격
        h2 = QHBoxLayout()
        lbl2 = QLabel("계약 품목:")
        lbl2.setFixedWidth(80)
        self.combo_spec = QComboBox()
        for s in self.product_logic.get_all_specs():
            self.combo_spec.addItem(f"{s['type_name']} - {s['spec_name']}", s['id'])
        h2.addWidget(lbl2)
        h2.addWidget(self.combo_spec)
        v.addLayout(h2)

        # 계약 수량
        h3 = QHBoxLayout()
        lbl3 = QLabel("총 예정수량:")
        lbl3.setFixedWidth(80)
        self.txt_qty = QLineEdit()
        self.txt_qty.setPlaceholderText("예: 100000")
        h3.addWidget(lbl3)
        h3.addWidget(self.txt_qty)
        v.addLayout(h3)

        v.addStretch()

        btn_h = QHBoxLayout()
        btn_text = "수정" if self.supplier_id and self.spec_id else "등록"
        btn_save = QPushButton(btn_text)
        btn_save.setObjectName("btn_primary")
        btn_save.setFixedHeight(40)
        btn_save.clicked.connect(self._save)

        btn_cancel = QPushButton("취소")
        btn_cancel.setObjectName("btn_ghost")
        btn_cancel.setFixedHeight(40)
        btn_cancel.clicked.connect(self.reject)

        btn_h.addWidget(btn_cancel)
        btn_h.addWidget(btn_save)
        v.addLayout(btn_h)

    def _load_edit_data(self):
        idx_sup = self.combo_supplier.findData(self.supplier_id)
        if idx_sup >= 0:
            self.combo_supplier.setCurrentIndex(idx_sup)

        idx_spec = self.combo_spec.findData(self.spec_id)
        if idx_spec >= 0:
            self.combo_spec.setCurrentIndex(idx_spec)

        self.txt_qty.setText(str(self.current_qty))

    def _save(self):
        sup_id = self.combo_supplier.currentData()
        spec_id = self.combo_spec.currentData()
        qty_str = self.txt_qty.text().strip().replace(',', '')
        
        if not sup_id:
            QMessageBox.warning(self, "경고", "입고처를 선택해주세요.")
            return
        if not spec_id:
            QMessageBox.warning(self, "경고", "품목을 선택해주세요.")
            return
        if not qty_str.isdigit():
            QMessageBox.warning(self, "경고", "예정수량을 올바른 숫자로 입력해주세요.")
            return
            
        qty = int(qty_str)
        if qty <= 0:
            QMessageBox.warning(self, "경고", "예정수량은 1 이상이어야 합니다.")
            return

        try:
            if self.supplier_id and self.spec_id:
                self.contract_logic.update_contract(
                    sup_id, spec_id, qty,
                    old_supplier_id=self.supplier_id,
                    old_spec_id=self.spec_id
                )
            else:
                self.contract_logic.add_contract(sup_id, spec_id, qty)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 중 오류가 발생했습니다:\n{str(e)}")
