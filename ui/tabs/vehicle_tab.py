# ============================================================
# ui/tabs/vehicle_tab.py  —  차량 운행 및 폐기물 반입 관리 탭 (통합 등록 + 가로 2단 쾌적 레이아웃)
# ============================================================

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QTabWidget, QFrame, QLineEdit, QCheckBox, QScrollArea
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from datetime import date as dt

from logic.vehicle_logic import VehicleLogic
from ui.dialogs.vehicle_dialog import VehicleDialog
from ui.dialogs.disposal_site_dialog import DisposalSiteDialog
from ui.widgets import StatCard, SectionCard, NoScrollDateEdit
from utils.format_utils import fmt_number
from database.models import VEHICLE_TYPES


class VehicleTab(QWidget):
    """차량 운행일지 및 폐기물 반입량 통합 관리 탭."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logic = VehicleLogic()
        self._reg_log_ids = []
        self._search_log_ids = []
        self._vehicle_ids = []
        self._site_ids = []
        self._crew_checkboxes = []  # [(이름, QCheckBox)]
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(14)

        # ══ 요약 카드 ════════════════════════════════════════
        cards_h = QHBoxLayout(); cards_h.setSpacing(12)
        self.sc_total_logs   = StatCard("🚚", "이번 달 총 운행일수", "—", "#818cf8")
        self.sc_total_amount = StatCard("⚖", "이번 달 총 반입량", "—", "#10b981")
        self.sc_active_veh   = StatCard("🚍", "등록된 운영 차량", "—", "#f59e0b")
        for sc in (self.sc_total_logs, self.sc_total_amount, self.sc_active_veh):
            cards_h.addWidget(sc)
        cards_h.addStretch()
        root.addLayout(cards_h)

        # ══ 내부 탭 ══════════════════════════════════════════
        inner = QTabWidget()
        inner.addTab(self._registration_tab(), "📋  일지 · 반입량 통합 등록")
        inner.addTab(self._search_tab(),       "📊  운행 및 반입 내역 조회")
        inner.addTab(self._management_tab(),   "⚙  차량 및 반입처 등록 관리")
        root.addWidget(inner)

        self._load_all()

    # ── 1. 일지 · 반입량 통합 등록 탭 (이중 입력 방지 + 가로 2단 쾌적 레이아웃) ──
    def _registration_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(14)

        # ── 상단: 좌/우 2열 분할로 쾌적하게 펼쳐진 입력 폼 카드 ──
        card_form = SectionCard("🚛 일별 차량 운행 일지 및 폐기물 반입 종합 입력")
        
        form_h = QHBoxLayout()
        form_h.setSpacing(28)

        # [좌측 1열 패널: 🕒 차량 및 근무 · 출결 설정]
        left_panel = QWidget()
        left_form = QFormLayout(left_panel)
        left_form.setSpacing(12)
        left_form.setContentsMargins(0, 4, 0, 4)
        left_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        def fl(t):
            l = QLabel(t); l.setObjectName("form_label"); return l

        self.date_reg = NoScrollDateEdit(QDate.currentDate())
        self.date_reg.setCalendarPopup(True)
        self.date_reg.setDisplayFormat("yyyy-MM-dd")
        self.date_reg.setFixedWidth(140)
        self.date_reg.dateChanged.connect(self._load_reg_logs)
        left_form.addRow(fl("운행 일자 *"), self.date_reg)

        self.combo_reg_veh = QComboBox()
        self.combo_reg_veh.setMinimumWidth(240)
        self.combo_reg_veh.currentIndexChanged.connect(self._on_reg_vehicle_selected)
        left_form.addRow(fl("차량 선택 *"), self.combo_reg_veh)

        time_box = QHBoxLayout(); time_box.setSpacing(6)
        self.edit_reg_start = QLineEdit()
        self.edit_reg_start.setPlaceholderText("00:00")
        self.edit_reg_start.setFixedWidth(75)
        self.edit_reg_start.setAlignment(Qt.AlignCenter)
        lbl_tilde = QLabel("~"); lbl_tilde.setAlignment(Qt.AlignCenter); lbl_tilde.setFixedWidth(16)
        self.edit_reg_end = QLineEdit()
        self.edit_reg_end.setPlaceholderText("08:00")
        self.edit_reg_end.setFixedWidth(75)
        self.edit_reg_end.setAlignment(Qt.AlignCenter)
        time_box.addWidget(self.edit_reg_start); time_box.addWidget(lbl_tilde); time_box.addWidget(self.edit_reg_end)
        time_box.addStretch()
        left_form.addRow(fl("작업 시간 *"), time_box)

        # 탑승인원 출결 (3열 그리드로 깔끔하게 나열)
        self.crew_grid_widget = QWidget()
        self.crew_grid_layout = QGridLayout(self.crew_grid_widget)
        self.crew_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.crew_grid_layout.setSpacing(8)
        left_form.addRow(fl("탑승인원 출결\n(해제 시 결근)"), self.crew_grid_widget)

        self.edit_absent_extra = QLineEdit()
        self.edit_absent_extra.setPlaceholderText("기타 결근자 이름 (없으면 비워둠)")
        left_form.addRow(fl("기타 결근자"), self.edit_absent_extra)

        form_h.addWidget(left_panel, 5)

        # [우측 2열 패널: ⚖ 폐기물 반입처 · 수량 및 비고]
        right_panel = QWidget()
        right_form = QFormLayout(right_panel)
        right_form.setSpacing(14)
        right_form.setContentsMargins(0, 4, 0, 4)
        right_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.combo_reg_site = QComboBox()
        self.combo_reg_site.setMinimumWidth(240)
        right_form.addRow(fl("폐기물 반입처"), self.combo_reg_site)

        self.spin_reg_amount = QDoubleSpinBox()
        self.spin_reg_amount.setRange(0, 999999)
        self.spin_reg_amount.setDecimals(1)
        self.spin_reg_amount.setSuffix(" kg/톤")
        self.spin_reg_amount.setStyleSheet("font-size:13pt; font-weight:bold; color:#10b981;")
        self.spin_reg_amount.setMinimumWidth(180)
        right_form.addRow(fl("반입 수량"), self.spin_reg_amount)

        self.edit_reg_memo = QLineEdit()
        self.edit_reg_memo.setPlaceholderText("특이사항 및 비고 입력")
        right_form.addRow(fl("비고 / 메모"), self.edit_reg_memo)

        # 우측 패널 하단에 여백 추가
        right_form.addRow(QLabel(""), QLabel(""))

        form_h.addWidget(right_panel, 5)
        card_form.add_layout(form_h)

        btn_save = QPushButton("  ✓  차량 운행 일지 및 폐기물 반입 기록 한 번에 저장")
        btn_save.setObjectName("btn_success")
        btn_save.setFixedHeight(46)
        btn_save.setStyleSheet("font-size: 12pt; font-weight: bold;")
        btn_save.clicked.connect(self._save_reg_log)
        card_form.add_widget(btn_save)

        v.addWidget(card_form)

        # ── 하단: 선택 일자 종합 기록 내역 표 (화면 전체 가로 폭 사용) ──
        card_list = SectionCard("선택 일자 운행 및 폐기물 반입 종합 기록 내역")
        self.tbl_reg_logs = self._tbl(
            ['일자', '차량번호', '차종', '작업시간', '탑승인원 (결근자)', '폐기물 반입처', '반입량 (kg/톤)', '비고']
        )
        hh = self.tbl_reg_logs.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.Stretch)
        hh.setSectionResizeMode(5, QHeaderView.Stretch)
        hh.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(7, QHeaderView.Stretch)
        card_list.add_widget(self.tbl_reg_logs)

        bh = QHBoxLayout(); bh.addStretch()
        btn_del = QPushButton("선택 기록 삭제")
        btn_del.setObjectName("btn_danger")
        btn_del.clicked.connect(self._delete_reg_log)
        bh.addWidget(btn_del)
        card_list.add_layout(bh)

        v.addWidget(card_list, 1)
        return w

    def _on_reg_vehicle_selected(self):
        idx = self.combo_reg_veh.currentIndex()
        if idx < 0 or not self._vehicle_ids:
            return
        vid = self.combo_reg_veh.currentData()
        if not vid:
            return
        veh = self.logic.get_vehicle_by_id(vid)
        if not veh:
            return

        self.edit_reg_start.setText(veh.get('default_start_time', '00:00'))
        self.edit_reg_end.setText(veh.get('default_end_time', '08:00'))

        # 기존 체크박스 제거
        for i in reversed(range(self.crew_grid_layout.count())):
            item = self.crew_grid_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        self._crew_checkboxes.clear()

        names_str = veh.get('crew_names', '').strip()
        if names_str:
            names = [n.strip() for n in names_str.split(',') if n.strip()]
            for idx_n, name in enumerate(names):
                chk = QCheckBox(f"{name} (출근)")
                chk.setChecked(True)
                chk.stateChanged.connect(lambda state, c=chk, n=name: c.setText(
                    f"{n} (출근)" if state == Qt.Checked else f"{n} (❌ 결근)"
                ))
                self._crew_checkboxes.append((name, chk))
                row = idx_n // 3
                col = idx_n % 3
                self.crew_grid_layout.addWidget(chk, row, col)
        else:
            lbl_no_crew = QLabel("등록된 탑승인원 명단이 없습니다.")
            lbl_no_crew.setStyleSheet("color:#94a3b8; font-size:10pt;")
            self.crew_grid_layout.addWidget(lbl_no_crew, 0, 0)

    def _save_reg_log(self):
        vid = self.combo_reg_veh.currentData()
        if not vid:
            QMessageBox.warning(self, "입력 오류", "차량을 선택해주세요.")
            return

        record_date = self.date_reg.date().toString("yyyy-MM-dd")
        stime = self.edit_reg_start.text().strip()
        etime = self.edit_reg_end.text().strip()
        if not stime or not etime:
            QMessageBox.warning(self, "입력 오류", "작업시간(시작/종료)을 입력해주세요.")
            return

        absents = []
        for name, chk in self._crew_checkboxes:
            if not chk.isChecked():
                absents.append(name)
        extra_abs = self.edit_absent_extra.text().strip()
        if extra_abs:
            absents.append(extra_abs)
        absent_str = ", ".join(absents)

        sid = self.combo_reg_site.currentData()
        amount = self.spin_reg_amount.value()
        memo = self.edit_reg_memo.text().strip()

        try:
            # 운행 일지 및 반입 기록 한 번에 통합 저장
            self.logic.add_log(record_date, vid, stime, etime, absent_str, sid, amount, memo)
            self._load_reg_logs()
            self._load_summary()
            self.spin_reg_amount.setValue(0)
            self.edit_reg_memo.clear()
            self.edit_absent_extra.clear()
            for name, chk in self._crew_checkboxes:
                chk.setChecked(True)
            QMessageBox.information(self, "저장 완료", f"[{record_date}] 차량 운행 및 폐기물 반입 기록이 저장되었습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"기록 저장 실패: {e}")

    def _load_reg_logs(self):
        sel_date = self.date_reg.date().toString("yyyy-MM-dd")
        rows = self.logic.get_logs(start_date=sel_date, end_date=sel_date)
        
        self._reg_log_ids.clear()
        self.tbl_reg_logs.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self._reg_log_ids.append(row['id'])
            time_str = f"{row['start_time']} ~ {row['end_time']}" if row['start_time'] else "-"
            crew_str = f"{row['crew_count']}명"
            if row['absent_crew']:
                crew_str += f" (결근: {row['absent_crew']})"
            else:
                crew_str += " (전원출근)"
            
            site_name = row['disposal_site_name'] or "-"
            amount_str = fmt_number(row['disposal_amount']) if row['disposal_amount'] > 0 else "-"

            vals = [row['record_date'], row['vehicle_number'], row['vehicle_type'],
                    time_str, crew_str, site_name, amount_str, row.get('memo', '')]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                if c == 4 and row['absent_crew']:
                    item.setForeground(QColor('#ef4444'))
                if c == 6 and row['disposal_amount'] > 0:
                    item.setForeground(QColor('#10b981'))
                self.tbl_reg_logs.setItem(r, c, item)

    def _delete_reg_log(self):
        sel = sorted(set(i.row() for i in self.tbl_reg_logs.selectedItems()))
        if not sel:
            QMessageBox.information(self, "알림", "삭제할 기록을 선택해주세요.")
            return
        if QMessageBox.question(self, "삭제 확인", f"{len(sel)}건의 운행 및 반입 기록을 삭제하시겠습니까?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        for r in sorted(sel, reverse=True):
            self.logic.delete_log(self._reg_log_ids[r])
        self._load_reg_logs()
        self._load_summary()

    # ── 2. 운행 및 반입 종합 내역 조회 탭 ─────────────────────
    def _search_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(12)

        fh = QHBoxLayout(); fh.setSpacing(8)

        def fl(t):
            l = QLabel(t); l.setObjectName("form_label"); return l

        fh.addWidget(fl("시작일"))
        self.date_search_s = NoScrollDateEdit(QDate.currentDate().addDays(-30))
        self.date_search_s.setCalendarPopup(True)
        self.date_search_s.setDisplayFormat("yyyy-MM-dd")
        self.date_search_s.setFixedWidth(130)
        fh.addWidget(self.date_search_s)

        fh.addWidget(fl("종료일"))
        self.date_search_e = NoScrollDateEdit(QDate.currentDate())
        self.date_search_e.setCalendarPopup(True)
        self.date_search_e.setDisplayFormat("yyyy-MM-dd")
        self.date_search_e.setFixedWidth(130)
        fh.addWidget(self.date_search_e)

        fh.addWidget(fl("차량"))
        self.combo_search_veh = QComboBox()
        self.combo_search_veh.setFixedWidth(150)
        fh.addWidget(self.combo_search_veh)

        fh.addWidget(fl("차종"))
        self.combo_search_type = QComboBox()
        self.combo_search_type.addItem("전체 차종", "")
        for vt in VEHICLE_TYPES:
            self.combo_search_type.addItem(vt, vt)
        fh.addWidget(self.combo_search_type)

        fh.addWidget(fl("반입처"))
        self.combo_search_site = QComboBox()
        self.combo_search_site.setFixedWidth(150)
        fh.addWidget(self.combo_search_site)

        btn_q = QPushButton("조회")
        btn_q.setObjectName("btn_ghost")
        btn_q.setFixedWidth(80)
        btn_q.clicked.connect(self._load_search_logs)
        fh.addWidget(btn_q)
        fh.addStretch()

        v.addLayout(fh)

        c = SectionCard("차량 운행 및 폐기물 반입 종합 내역 조회")
        self.tbl_search_logs = self._tbl(
            ['일자', '차량번호', '차종', '작업시간', '탑승/결근', '폐기물 반입처', '반입량', '비고']
        )
        hh = self.tbl_search_logs.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.Stretch)
        hh.setSectionResizeMode(5, QHeaderView.Stretch)
        hh.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(7, QHeaderView.Stretch)
        c.add_widget(self.tbl_search_logs)

        dh = QHBoxLayout(); dh.addStretch()
        btn_del_s = QPushButton("선택 기록 삭제")
        btn_del_s.setObjectName("btn_danger")
        btn_del_s.clicked.connect(self._delete_search_log)
        dh.addWidget(btn_del_s)
        c.add_layout(dh)

        v.addWidget(c, 1)
        return w

    def _load_search_logs(self):
        s_date = self.date_search_s.date().toString("yyyy-MM-dd")
        e_date = self.date_search_e.date().toString("yyyy-MM-dd")
        vid = self.combo_search_veh.currentData()
        vtype = self.combo_search_type.currentData()
        sid = self.combo_search_site.currentData()

        rows = self.logic.get_logs(s_date, e_date, vid, vtype, sid)

        self._search_log_ids.clear()
        self.tbl_search_logs.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self._search_log_ids.append(row['id'])
            time_str = f"{row['start_time']} ~ {row['end_time']}" if row['start_time'] else "-"
            crew_str = f"{row['crew_count']}명 ({row['absent_crew'] or '전원출근'})" if row['start_time'] else "-"
            site_name = row['disposal_site_name'] or "-"
            amount_str = fmt_number(row['disposal_amount']) if row['disposal_amount'] > 0 else "-"

            vals = [row['record_date'], row['vehicle_number'], row['vehicle_type'],
                    time_str, crew_str, site_name, amount_str, row.get('memo', '')]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                if c == 4 and row['absent_crew']:
                    item.setForeground(QColor('#ef4444'))
                if c == 6 and row['disposal_amount'] > 0:
                    item.setForeground(QColor('#10b981'))
                self.tbl_search_logs.setItem(r, c, item)

    def _delete_search_log(self):
        sel = sorted(set(i.row() for i in self.tbl_search_logs.selectedItems()))
        if not sel:
            QMessageBox.information(self, "알림", "삭제할 일지 기록을 선택해주세요.")
            return
        if QMessageBox.question(self, "삭제 확인", f"{len(sel)}건의 일지 기록을 삭제하시겠습니까?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        for r in sorted(sel, reverse=True):
            self.logic.delete_log(self._search_log_ids[r])
        self._load_search_logs()
        self._load_reg_logs()
        self._load_summary()

    # ── 3. 차량 및 반입처 등록 관리 탭 (내부 탭 분리) ─────────
    def _management_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(12)

        m_tabs = QTabWidget()

        # [3-1] 차량 등록 관리
        veh_tab = QWidget()
        veh_v = QVBoxLayout(veh_tab)
        veh_v.setContentsMargins(12, 12, 12, 12)
        veh_v.setSpacing(10)

        th = QHBoxLayout(); th.setSpacing(8)
        lbl_v = QLabel("🚍  등록된 차량 목록")
        lbl_v.setStyleSheet("color:#818cf8; font-size:12pt; font-weight:bold;")
        th.addWidget(lbl_v); th.addStretch()

        btn_add_veh = QPushButton("차량 등록")
        btn_add_veh.setObjectName("btn_success")
        btn_add_veh.clicked.connect(lambda: self._open_vehicle_dialog(None))
        th.addWidget(btn_add_veh)

        btn_edit_veh = QPushButton("수정")
        btn_edit_veh.setObjectName("btn_ghost")
        btn_edit_veh.clicked.connect(self._edit_vehicle)
        th.addWidget(btn_edit_veh)

        btn_del_veh = QPushButton("비활성화/상태변경")
        btn_del_veh.setObjectName("btn_danger")
        btn_del_veh.clicked.connect(self._deactivate_vehicle)
        th.addWidget(btn_del_veh)
        veh_v.addLayout(th)

        self.tbl_vehicles = self._tbl(
            ['ID', '차량번호', '차종', '탑승인원 수', '탑승인원 명단', '기본 작업시간', '상태']
        )
        hh = self.tbl_vehicles.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.Stretch)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        veh_v.addWidget(self.tbl_vehicles)
        m_tabs.addTab(veh_tab, "🚍  차량 등록 관리")

        # [3-2] 반입처 등록 관리
        site_tab = QWidget()
        site_v = QVBoxLayout(site_tab)
        site_v.setContentsMargins(12, 12, 12, 12)
        site_v.setSpacing(10)

        bh = QHBoxLayout(); bh.setSpacing(8)
        lbl_s = QLabel("🏢  등록된 폐기물 반입처 (거래처) 목록")
        lbl_s.setStyleSheet("color:#10b981; font-size:12pt; font-weight:bold;")
        bh.addWidget(lbl_s); bh.addStretch()

        btn_add_site = QPushButton("반입처 등록")
        btn_add_site.setObjectName("btn_success")
        btn_add_site.clicked.connect(lambda: self._open_site_dialog(None))
        bh.addWidget(btn_add_site)

        btn_edit_site = QPushButton("수정")
        btn_edit_site.setObjectName("btn_ghost")
        btn_edit_site.clicked.connect(self._edit_site)
        bh.addWidget(btn_edit_site)

        btn_del_site = QPushButton("비활성화/상태변경")
        btn_del_site.setObjectName("btn_danger")
        btn_del_site.clicked.connect(self._deactivate_site)
        bh.addWidget(btn_del_site)
        site_v.addLayout(bh)

        self.tbl_sites = self._tbl(['ID', '반입처명', '주소', '메모', '상태'])
        hh_s = self.tbl_sites.horizontalHeader()
        hh_s.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh_s.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh_s.setSectionResizeMode(2, QHeaderView.Stretch)
        hh_s.setSectionResizeMode(3, QHeaderView.Stretch)
        hh_s.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        site_v.addWidget(self.tbl_sites)
        m_tabs.addTab(site_tab, "🏢  폐기물 반입처 (거래처) 관리")

        v.addWidget(m_tabs)
        return w

    def _load_management_tables(self):
        vehs = self.logic.get_all_vehicles(include_inactive=True)
        self.tbl_vehicles.setRowCount(len(vehs))
        for r, row in enumerate(vehs):
            status = "운영중" if row['is_active'] else "비활성"
            color = "#10b981" if row['is_active'] else "#94a3b8"
            time_str = f"{row['default_start_time']} ~ {row['end_time']}" if 'end_time' in row else f"{row['default_start_time']} ~ {row['default_end_time']}"
            vals = [row['id'], row['vehicle_number'], row['vehicle_type'],
                    f"{row['crew_count']}명", row.get('crew_names', ''),
                    time_str, status]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                if c == 6:
                    item.setForeground(QColor(color))
                self.tbl_vehicles.setItem(r, c, item)

        sites = self.logic.get_all_disposal_sites(include_inactive=True)
        self.tbl_sites.setRowCount(len(sites))
        for r, row in enumerate(sites):
            status = "사용중" if row['is_active'] else "비활성"
            color = "#10b981" if row['is_active'] else "#94a3b8"
            vals = [row['id'], row['name'], row.get('address', ''), row.get('memo', ''), status]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                if c == 4:
                    item.setForeground(QColor(color))
                self.tbl_sites.setItem(r, c, item)

    def _open_vehicle_dialog(self, vid=None):
        dlg = VehicleDialog(self, vehicle_id=vid)
        if dlg.exec_():
            self._load_all()

    def _edit_vehicle(self):
        sel = self.tbl_vehicles.selectedItems()
        if not sel:
            QMessageBox.information(self, "알림", "수정할 차량을 선택해주세요.")
            return
        vid = int(self.tbl_vehicles.item(self.tbl_vehicles.currentRow(), 0).text())
        self._open_vehicle_dialog(vid)

    def _deactivate_vehicle(self):
        sel = self.tbl_vehicles.selectedItems()
        if not sel:
            QMessageBox.information(self, "알림", "상태를 변경할 차량을 선택해주세요.")
            return
        row_idx = self.tbl_vehicles.currentRow()
        vid = int(self.tbl_vehicles.item(row_idx, 0).text())
        status = self.tbl_vehicles.item(row_idx, 6).text()
        if status == "운영중":
            self.logic.deactivate_vehicle(vid)
        else:
            self.logic.activate_vehicle(vid)
        self._load_all()

    def _open_site_dialog(self, sid=None):
        dlg = DisposalSiteDialog(self, site_id=sid)
        if dlg.exec_():
            self._load_all()

    def _edit_site(self):
        sel = self.tbl_sites.selectedItems()
        if not sel:
            QMessageBox.information(self, "알림", "수정할 반입처를 선택해주세요.")
            return
        sid = int(self.tbl_sites.item(self.tbl_sites.currentRow(), 0).text())
        self._open_site_dialog(sid)

    def _deactivate_site(self):
        sel = self.tbl_sites.selectedItems()
        if not sel:
            QMessageBox.information(self, "알림", "상태를 변경할 반입처를 선택해주세요.")
            return
        row_idx = self.tbl_sites.currentRow()
        sid = int(self.tbl_sites.item(row_idx, 0).text())
        status = self.tbl_sites.item(row_idx, 4).text()
        if status == "사용중":
            self.logic.deactivate_disposal_site(sid)
        else:
            self.logic.activate_disposal_site(sid)
        self._load_all()

    # ── 공통 로딩 및 요약 ────────────────────────────────────
    def _load_combos(self):
        vehs = self.logic.get_all_vehicles(include_inactive=False)
        self._vehicle_ids = [v['id'] for v in vehs]
        
        self.combo_reg_veh.clear()
        self.combo_search_veh.clear()
        self.combo_search_veh.addItem("전체 차량", None)
        for v in vehs:
            label = f"{v['vehicle_number']} [{v['vehicle_type']} | 탑승 {v['crew_count']}명]"
            self.combo_reg_veh.addItem(label, v['id'])
            self.combo_search_veh.addItem(label, v['id'])

        sites = self.logic.get_all_disposal_sites(include_inactive=False)
        self._site_ids = [s['id'] for s in sites]
        
        self.combo_reg_site.clear()
        self.combo_reg_site.addItem("(선택 안함 / 반입 없음)", None)
        self.combo_search_site.clear()
        self.combo_search_site.addItem("전체 반입처", None)
        for s in sites:
            self.combo_reg_site.addItem(s['name'], s['id'])
            self.combo_search_site.addItem(s['name'], s['id'])

    def _load_summary(self):
        cur = dt.today()
        s_date = f"{cur.year:04d}-{cur.month:02d}-01"
        rows = self.logic.get_logs(start_date=s_date)
        
        work_entries = set((r['record_date'], r['vehicle_id']) for r in rows if r['start_time'] and r['end_time'])
        total_logs = len(work_entries)
        
        total_amount = sum(r['disposal_amount'] for r in rows)
        vehs = self.logic.get_all_vehicles(include_inactive=False)

        self.sc_total_logs.set_value(f"{total_logs} 일")
        self.sc_total_amount.set_value(f"{fmt_number(total_amount)} kg/톤")
        self.sc_active_veh.set_value(f"{len(vehs)} 대")

    def _load_all(self):
        self._load_combos()
        self._load_management_tables()
        self._load_reg_logs()
        self._load_search_logs()
        self._load_summary()

    def _tbl(self, headers) -> QTableWidget:
        tbl = QTableWidget(0, len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.setSelectionBehavior(QTableWidget.SelectRows)
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        return tbl

    def refresh(self):
        self._load_all()
