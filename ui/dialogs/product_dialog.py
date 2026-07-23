# ============================================================
# ui/dialogs/product_dialog.py  —  규격 / 단가 등록 / 수정
# ============================================================

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QComboBox, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt
from logic.product_logic import ProductLogic


class ProductDialog(QDialog):
    def __init__(self, parent=None, spec_id: int = None, default_type_id: int = None):
        super().__init__(parent)
        self.spec_id        = spec_id
        self.default_type_id = default_type_id
        self.logic          = ProductLogic()
        self._build_ui()
        if spec_id:
            self._load_data()

    def _build_ui(self):
        title = "규격 수정" if self.spec_id else "규격 등록"
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
            l = QLabel(t); l.setObjectName("form_label"); return l

        # 품목 종류
        type_box = QHBoxLayout()
        type_box.setSpacing(6)
        self.combo_type = QComboBox()
        for t in self.logic.get_types():
            self.combo_type.addItem(t['name'], t['id'])
        if self.default_type_id:
            for i in range(self.combo_type.count()):
                if self.combo_type.itemData(i) == self.default_type_id:
                    self.combo_type.setCurrentIndex(i)
                    break
        type_box.addWidget(self.combo_type, 1)

        btn_add_type = QPushButton("➕ 종류 추가")
        btn_add_type.setObjectName("btn_ghost")
        btn_add_type.setToolTip("새로운 봉투 종류(대분류)를 등록하거나 관리합니다")
        btn_add_type.clicked.connect(self._open_type_dialog)
        type_box.addWidget(btn_add_type)
        form.addRow(fl("품목 종류 *"), type_box)

        # 규격명
        self.edit_spec_name = QLineEdit()
        self.edit_spec_name.setPlaceholderText("예: 10L, 20L, 50kg ...")
        form.addRow(fl("규격명 *"), self.edit_spec_name)

        # 상품코드
        self.edit_product_code = QLineEdit()
        self.edit_product_code.setPlaceholderText("예: 0301 (선택사항)")
        form.addRow(fl("상품코드"), self.edit_product_code)

        # 단가
        self.spin_price = QSpinBox()
        self.spin_price.setRange(0, 99_999_999)
        self.spin_price.setSuffix("  원")
        self.spin_price.setSingleStep(100)
        form.addRow(fl("단가 *"), self.spin_price)

        root.addLayout(form)

        bh = QHBoxLayout(); bh.setSpacing(10)
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
        data = self.logic.get_spec_by_id(self.spec_id)
        if data:
            for i in range(self.combo_type.count()):
                if self.combo_type.itemData(i) == data['type_id']:
                    self.combo_type.setCurrentIndex(i)
                    break
            self.edit_spec_name.setText(data['spec_name'])
            self.edit_product_code.setText(data.get('product_code', ''))
            self.spin_price.setValue(data['unit_price'])

    def _save(self):
        type_id      = self.combo_type.currentData()
        spec_name    = self.edit_spec_name.text().strip()
        product_code = self.edit_product_code.text().strip()
        unit_price   = self.spin_price.value()
        try:
            if self.spec_id:
                self.logic.update_spec(self.spec_id, type_id, spec_name, product_code, unit_price)
            else:
                self.logic.add_spec(type_id, spec_name, product_code, unit_price)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "입력 오류", str(e))
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패: {e}")

    def _open_type_dialog(self):
        from ui.dialogs.product_type_dialog import ProductTypeDialog
        dlg = ProductTypeDialog(self)
        dlg.exec_()
        if dlg.changed_any:
            current = self.combo_type.currentData()
            self.combo_type.clear()
            types = self.logic.get_types()
            for t in types:
                self.combo_type.addItem(t['name'], t['id'])
            # Try reselecting previous or last
            for i in range(self.combo_type.count()):
                if self.combo_type.itemData(i) == current:
                    self.combo_type.setCurrentIndex(i)
                    return
            if self.combo_type.count() > 0:
                self.combo_type.setCurrentIndex(self.combo_type.count() - 1)
