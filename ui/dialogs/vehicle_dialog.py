# ============================================================
# ui/dialogs/vehicle_dialog.py  —  차량 등록 / 수정 다이얼로그
# ============================================================

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QSpinBox, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt
from logic.vehicle_logic import VehicleLogic
from database.models import VEHICLE_TYPES


class VehicleDialog(QDialog):
    def __init__(self, parent=None, vehicle_id: int = None):
        super().__init__(parent)
        self.vehicle_id = vehicle_id
        self.logic = VehicleLogic()
        self._build_ui()
        if vehicle_id:
            self._load_data()
        else:
            self._on_type_changed()

    def _build_ui(self):
        title = "차량 정보 수정" if self.vehicle_id else "신규 차량 등록"
        self.setWindowTitle(title)
        self.setMinimumWidth(440)
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

        self.edit_number = QLineEdit()
        self.edit_number.setPlaceholderText("예: 12가3456 (필수)")
        form.addRow(fl("차량 번호 *"), self.edit_number)

        self.combo_type = QComboBox()
        for vt in VEHICLE_TYPES:
            self.combo_type.addItem(vt, vt)
        self.combo_type.currentIndexChanged.connect(self._on_type_changed)
        form.addRow(fl("차량 분류 *"), self.combo_type)

        self.spin_crew = QSpinBox()
        self.spin_crew.setRange(1, 20)
        self.spin_crew.setValue(3)
        form.addRow(fl("탑승 인원 수"), self.spin_crew)

        self.edit_names = QLineEdit()
        self.edit_names.setPlaceholderText("예: 홍길동, 김철수, 이영희 (쉼표로 구분)")
        form.addRow(fl("탑승인원 명단"), self.edit_names)

        time_h = QHBoxLayout()
        time_h.setSpacing(6)
        self.edit_start_time = QLineEdit()
        self.edit_start_time.setPlaceholderText("00:00")
        self.edit_start_time.setFixedWidth(80)
        self.edit_start_time.setAlignment(Qt.AlignCenter)

        lbl_tilde = QLabel("~")
        lbl_tilde.setAlignment(Qt.AlignCenter)
        lbl_tilde.setFixedWidth(20)

        self.edit_end_time = QLineEdit()
        self.edit_end_time.setPlaceholderText("08:00")
        self.edit_end_time.setFixedWidth(80)
        self.edit_end_time.setAlignment(Qt.AlignCenter)

        time_h.addWidget(self.edit_start_time)
        time_h.addWidget(lbl_tilde)
        time_h.addWidget(self.edit_end_time)
        time_h.addStretch()
        form.addRow(fl("기본 작업시간"), time_h)

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

    def _on_type_changed(self):
        if self.vehicle_id:  # 수정 시에는 자동 변경 안 함 (초기 로드 후 사용자가 임의 설정)
            return
        vtype = self.combo_type.currentData()
        if vtype == '생활':
            self.edit_start_time.setText("00:00")
            self.edit_end_time.setText("08:00")
        elif vtype == '재활용':
            self.edit_start_time.setText("04:00")
            self.edit_end_time.setText("12:00")
        elif vtype == '음식물':
            self.edit_start_time.setText("00:00")
            self.edit_end_time.setText("08:00")

    def _load_data(self):
        d = self.logic.get_vehicle_by_id(self.vehicle_id)
        if d:
            self.edit_number.setText(d['vehicle_number'])
            idx = self.combo_type.findData(d['vehicle_type'])
            if idx >= 0:
                self.combo_type.setCurrentIndex(idx)
            self.spin_crew.setValue(d.get('crew_count', 1))
            self.edit_names.setText(d.get('crew_names', ''))
            self.edit_start_time.setText(d.get('default_start_time', '00:00'))
            self.edit_end_time.setText(d.get('default_end_time', '08:00'))

    def _save(self):
        vnum  = self.edit_number.text().strip()
        vtype = self.combo_type.currentData()
        ccount = self.spin_crew.value()
        cnames = self.edit_names.text().strip()
        stime  = self.edit_start_time.text().strip()
        etime  = self.edit_end_time.text().strip()

        if not vnum:
            QMessageBox.warning(self, "입력 오류", "차량 번호를 입력해주세요.")
            return
        if not stime or not etime:
            QMessageBox.warning(self, "입력 오류", "기본 작업시간(시작/종료)을 입력해주세요.")
            return

        try:
            if self.vehicle_id:
                self.logic.update_vehicle(self.vehicle_id, vnum, vtype, ccount, cnames, stime, etime)
            else:
                self.vehicle_id = self.logic.add_vehicle(vnum, vtype, ccount, cnames, stime, etime)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "입력 오류", str(e))
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패: {e}")
