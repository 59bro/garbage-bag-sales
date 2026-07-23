# ============================================================
# ui/dialogs/initial_stock_dialog.py
# 초기재고 / 입고 등록 다이얼로그
# ============================================================

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QSpinBox, QComboBox, QDateEdit, QLineEdit,
    QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from logic.product_logic import ProductLogic
from logic.stock_logic import StockLogic
from logic.customer_logic import CustomerLogic


class StockInDialog(QDialog):
    """초기재고 설정 또는 입고 등록 다이얼로그."""

    def __init__(self, parent=None, mode: str = 'inbound', spec_id: int = None):
        """
        mode: 'initial' = 초기재고 설정
              'inbound'  = 입고 등록
        """
        super().__init__(parent)
        self.mode = mode
        self.preset_spec_id = spec_id
        self.product_logic = ProductLogic()
        self.stock_logic = StockLogic()
        self.customer_logic = CustomerLogic()
        self._build_ui()

    def _build_ui(self):
        title = "초기재고 설정" if self.mode == 'initial' else "입고 등록"
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        lbl = QLabel(title)
        lbl.setObjectName("label_title")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

        form = QFormLayout()
        form.setSpacing(10)

        # 규격 선택
        self.combo_spec = QComboBox()
        self.combo_spec.setMinimumWidth(220)
        specs = self.product_logic.get_specs_for_combo()
        for spec_id, display, price in specs:
            self.combo_spec.addItem(display, spec_id)
        if self.preset_spec_id:
            for i in range(self.combo_spec.count()):
                if self.combo_spec.itemData(i) == self.preset_spec_id:
                    self.combo_spec.setCurrentIndex(i)
                    break
        form.addRow("규격 *", self.combo_spec)
        
        # 거래처 선택 (입고 모드인 경우)
        if self.mode == 'inbound':
            self.combo_supplier = QComboBox()
            self.combo_supplier.addItem("선택 안함", None)
            # 입고처만 가져오기
            suppliers = self.customer_logic.get_all(include_inactive=False, customer_type="입고처")
            for sup in suppliers:
                self.combo_supplier.addItem(sup['name'], sup['id'])
            form.addRow("입고처", self.combo_supplier)

        # 날짜
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        form.addRow("날짜 *", self.date_edit)

        # 수량
        self.spin_qty = QSpinBox()
        self.spin_qty.setRange(1, 9_999_999)
        self.spin_qty.setSuffix(" 개")
        form.addRow("수량 *", self.spin_qty)

        # 메모
        self.edit_memo = QLineEdit()
        self.edit_memo.setPlaceholderText("메모 (선택)")
        form.addRow("메모", self.edit_memo)

        layout.addLayout(form)

        # 버튼
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("저장")
        self.btn_save.setObjectName("btn_success")
        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.setObjectName("btn_secondary")

        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def _save(self):
        spec_id = self.combo_spec.currentData()
        date = self.date_edit.date().toString("yyyy-MM-dd")
        qty = self.spin_qty.value()
        memo = self.edit_memo.text().strip()

        try:
            if self.mode == 'initial':
                self.stock_logic.set_initial_stock(spec_id, qty, date, memo)
            else:
                supplier_id = self.combo_supplier.currentData() if hasattr(self, 'combo_supplier') else None
                self.stock_logic.add_inbound(spec_id, qty, date, memo, supplier_id)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "입력 오류", str(e))
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패: {e}")
