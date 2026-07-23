# ============================================================
# ui/dialogs/ar_dialog.py  —  수금 등록 다이얼로그
# ============================================================

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QComboBox, QDateEdit,
    QPushButton, QLabel, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, QDate
from logic.customer_logic import CustomerLogic
from logic.ar_logic import ARLogic
from database.models import COLLECTION_METHODS
from utils.format_utils import fmt_currency
from ui.widgets import NoScrollDateEdit


class ARCollectionDialog(QDialog):
    """미수 수금 등록 다이얼로그."""

    def __init__(self, parent=None, customer_id: int = None):
        super().__init__(parent)
        self.preset_customer_id = customer_id
        self.customer_logic = CustomerLogic()
        self.ar_logic       = ARLogic()
        self._build_ui()
        if customer_id:
            self._set_customer(customer_id)

    def _build_ui(self):
        self.setWindowTitle("수금 등록")
        self.setMinimumWidth(420)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(24, 20, 24, 20)

        lbl = QLabel("미수 수금 등록")
        lbl.setStyleSheet(
            "color:#818cf8; font-size:14pt; font-weight:bold; "
            "background:transparent; border:none;"
        )
        lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(lbl)

        # 잔액 표시 카드
        balance_frame = QFrame()
        balance_frame.setStyleSheet(
            "background:#fefce8; border:1px solid #fde047; border-radius:8px; padding:4px;"
        )
        bf = QHBoxLayout(balance_frame)
        bf.setContentsMargins(14, 8, 14, 8)
        lbl_bl = QLabel("현재 미수 잔액")
        lbl_bl.setStyleSheet("color:#92400e; font-size:9pt; font-weight:bold; background:transparent; border:none;")
        self.lbl_balance = QLabel("—")
        self.lbl_balance.setStyleSheet(
            "color:#d97706; font-size:14pt; font-weight:bold; background:transparent; border:none;"
        )
        bf.addWidget(lbl_bl)
        bf.addStretch()
        bf.addWidget(self.lbl_balance)
        root.addWidget(balance_frame)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        def fl(t):
            l = QLabel(t)
            l.setObjectName("form_label")
            return l

        # 거래처
        self.combo_cust = QComboBox()
        for c in self.customer_logic.get_all():
            self.combo_cust.addItem(
                f"{c['name']}  [{c.get('district','')}]" if c.get('district') else c['name'],
                c['id']
            )
        self.combo_cust.currentIndexChanged.connect(self._update_balance)
        form.addRow(fl("거래처 *"), self.combo_cust)

        # 수금일
        self.date_edit = NoScrollDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        form.addRow(fl("수금일 *"), self.date_edit)

        # 수금액
        self.spin_amount = QSpinBox()
        self.spin_amount.setRange(1, 999_999_999)
        self.spin_amount.setSuffix("  원")
        self.spin_amount.setSingleStep(10000)
        form.addRow(fl("수금액 *"), self.spin_amount)

        # 수금방법
        self.combo_method = QComboBox()
        for m in COLLECTION_METHODS:
            self.combo_method.addItem(m, m)
        form.addRow(fl("수금방법 *"), self.combo_method)

        # 메모
        self.edit_memo = QLineEdit()
        self.edit_memo.setPlaceholderText("메모 (선택)")
        form.addRow(fl("메모"), self.edit_memo)

        root.addLayout(form)

        bh = QHBoxLayout()
        bh.setSpacing(10)
        btn_cancel = QPushButton("취소")
        btn_cancel.setObjectName("btn_ghost")
        btn_cancel.setFixedHeight(38)
        btn_save   = QPushButton("수금 저장")
        btn_save.setObjectName("btn_success")
        btn_save.setFixedHeight(38)
        btn_cancel.clicked.connect(self.reject)
        btn_save.clicked.connect(self._save)
        bh.addWidget(btn_cancel)
        bh.addWidget(btn_save)
        root.addLayout(bh)

        self._update_balance()

    def _set_customer(self, cid: int):
        for i in range(self.combo_cust.count()):
            if self.combo_cust.itemData(i) == cid:
                self.combo_cust.setCurrentIndex(i)
                break

    def _update_balance(self):
        cid     = self.combo_cust.currentData()
        if cid is None:
            return
        balance = self.ar_logic.get_customer_outstanding(cid)
        self.lbl_balance.setText(fmt_currency(balance))
        color = "#ef4444" if balance > 0 else "#10b981"
        self.lbl_balance.setStyleSheet(
            f"color:{color}; font-size:14pt; font-weight:bold; background:transparent; border:none;"
        )

    def _save(self):
        cid    = self.combo_cust.currentData()
        date   = self.date_edit.date().toString("yyyy-MM-dd")
        amount = self.spin_amount.value()
        method = self.combo_method.currentData()
        memo   = self.edit_memo.text().strip()
        try:
            self.ar_logic.add_collection(date, cid, amount, method, memo)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "입력 오류", str(e))
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패: {e}")


class InitialARDialog(QDialog):
    """초기 미수(이월 미수) 강제 입력/조정 다이얼로그."""

    def __init__(self, parent=None, customer_id: int = None):
        super().__init__(parent)
        self.preset_customer_id = customer_id
        self.customer_logic = CustomerLogic()
        self.ar_logic       = ARLogic()
        self._cur_init_ar   = 0
        self._cur_total_ar  = 0
        self._build_ui()
        if customer_id:
            self._set_customer(customer_id)

    def _build_ui(self):
        self.setWindowTitle("초기 미수(이월 미수) 강제 입력 / 조정")
        self.setMinimumWidth(440)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(24, 20, 24, 20)

        lbl = QLabel("초기(이월) 미수금 조정")
        lbl.setStyleSheet(
            "color:#f59e0b; font-size:14pt; font-weight:bold; "
            "background:transparent; border:none;"
        )
        lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(lbl)

        info_lbl = QLabel(
            "프로그램 도입 이전 기 거래처에 존재하던 미수금을 입력합니다.\n"
            "입력된 초기 미수금은 해당 거래처의 총 미수 잔액에 반영됩니다."
        )
        info_lbl.setStyleSheet("color:#64748b; font-size:9pt; background:transparent; border:none;")
        info_lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(info_lbl)

        # 현재 상태 표시 카드
        balance_frame = QFrame()
        balance_frame.setStyleSheet(
            "background:#fff7ed; border:1px solid #ffedd5; border-radius:8px; padding:4px;"
        )
        bf = QVBoxLayout(balance_frame)
        bf.setContentsMargins(14, 10, 14, 10)
        bf.setSpacing(6)

        h1 = QHBoxLayout()
        lbl_cur_init = QLabel("현재 설정된 초기 미수:")
        lbl_cur_init.setStyleSheet("color:#9a3412; font-size:9pt; font-weight:bold; background:transparent; border:none;")
        self.lbl_init_ar = QLabel("0 원")
        self.lbl_init_ar.setStyleSheet("color:#ea580c; font-size:11pt; font-weight:bold; background:transparent; border:none;")
        h1.addWidget(lbl_cur_init)
        h1.addStretch()
        h1.addWidget(self.lbl_init_ar)
        bf.addLayout(h1)

        h2 = QHBoxLayout()
        lbl_tot = QLabel("현재 거래처 총 잔여 미수:")
        lbl_tot.setStyleSheet("color:#9a3412; font-size:9pt; font-weight:bold; background:transparent; border:none;")
        self.lbl_total_ar = QLabel("0 원")
        self.lbl_total_ar.setStyleSheet("color:#dc2626; font-size:12pt; font-weight:bold; background:transparent; border:none;")
        h2.addWidget(lbl_tot)
        h2.addStretch()
        h2.addWidget(self.lbl_total_ar)
        bf.addLayout(h2)

        root.addWidget(balance_frame)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        def fl(t):
            l = QLabel(t)
            l.setObjectName("form_label")
            return l

        # 거래처
        self.combo_cust = QComboBox()
        for c in self.customer_logic.get_all():
            self.combo_cust.addItem(
                f"{c['name']}  [{c.get('district','')}]" if c.get('district') else c['name'],
                c['id']
            )
        self.combo_cust.currentIndexChanged.connect(self._update_balance)
        form.addRow(fl("거래처 *"), self.combo_cust)

        # 초기 미수금액 입력
        self.spin_initial_ar = QSpinBox()
        self.spin_initial_ar.setRange(-999_999_999, 999_999_999)
        self.spin_initial_ar.setSuffix("  원")
        self.spin_initial_ar.setSingleStep(10000)
        self.spin_initial_ar.setStyleSheet("QSpinBox { font-weight: bold; color: #dc2626; font-size: 11pt; }")
        self.spin_initial_ar.valueChanged.connect(self._preview_total)
        form.addRow(fl("변경할 초기 미수 *"), self.spin_initial_ar)

        root.addLayout(form)

        bh = QHBoxLayout()
        bh.setSpacing(10)
        btn_cancel = QPushButton("취소")
        btn_cancel.setObjectName("btn_ghost")
        btn_cancel.setFixedHeight(38)
        btn_save   = QPushButton("초기 미수 저장")
        btn_save.setObjectName("btn_warning")
        btn_save.setFixedHeight(38)
        btn_cancel.clicked.connect(self.reject)
        btn_save.clicked.connect(self._save)
        bh.addWidget(btn_cancel)
        bh.addWidget(btn_save)
        root.addLayout(bh)

        self._update_balance()

    def _set_customer(self, cid: int):
        for i in range(self.combo_cust.count()):
            if self.combo_cust.itemData(i) == cid:
                self.combo_cust.setCurrentIndex(i)
                break

    def _update_balance(self):
        cid = self.combo_cust.currentData()
        if cid is None:
            return
        cust = self.customer_logic.get_by_id(cid)
        init_ar = int((cust or {}).get('initial_ar', 0) or 0)
        total_ar = self.ar_logic.get_customer_outstanding(cid)
        self._cur_init_ar = init_ar
        self._cur_total_ar = total_ar

        self.spin_initial_ar.blockSignals(True)
        self.spin_initial_ar.setValue(init_ar)
        self.spin_initial_ar.blockSignals(False)

        self.lbl_init_ar.setText(fmt_currency(init_ar))
        self.lbl_total_ar.setText(fmt_currency(total_ar))

    def _preview_total(self, new_init: int):
        diff = new_init - getattr(self, '_cur_init_ar', 0)
        preview_tot = getattr(self, '_cur_total_ar', 0) + diff
        self.lbl_total_ar.setText(fmt_currency(preview_tot) + " (변경 예상)")

    def _save(self):
        cid = self.combo_cust.currentData()
        if cid is None:
            return
        new_init = self.spin_initial_ar.value()
        try:
            self.customer_logic.update_initial_ar(cid, new_init)
            QMessageBox.information(self, "완료", "초기 미수금이 성공적으로 반영되었습니다.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패: {e}")
