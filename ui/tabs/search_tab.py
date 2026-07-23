# ============================================================
# ui/tabs/search_tab.py  —  조회/보고서 탭
# ============================================================

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QDateEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
import os
from datetime import date as dt

from logic.sales_logic import SalesLogic
from logic.customer_logic import CustomerLogic
from logic.report_logic import ReportLogic
from logic.ar_logic import ARLogic
from utils.format_utils import fmt_currency, fmt_number
from utils.export_utils import export_to_excel, EXCEL_AVAILABLE, export_daily_sales_template, print_excel_file
from ui.widgets import StatCard, SectionCard, NoScrollDateEdit



class SearchTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sales_logic    = SalesLogic()
        self.customer_logic = CustomerLogic()
        self.report_logic   = ReportLogic()
        self.ar_logic       = ARLogic()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(0)
        inner = QTabWidget()
        inner.addTab(self._daily_tab(),   "📅  일별 현황")
        inner.addTab(self._period_tab(),  "📆  기간별 현황")
        inner.addTab(self._monthly_tab(), "📊  월별 집계")
        root.addWidget(inner)

    # ── 일별 ─────────────────────────────────────────────────
    def _daily_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(12)

        fh = QHBoxLayout(); fh.setSpacing(8)
        self.date_daily = NoScrollDateEdit(QDate.currentDate())
        self.date_daily.setCalendarPopup(True)
        self.date_daily.setDisplayFormat("yyyy-MM-dd")
        self.date_daily.setFixedWidth(145)
        # 날짜 변경 시 자동 조회
        self.date_daily.dateChanged.connect(self._query_daily)
        fh.addWidget(self.date_daily)

        btn_q = QPushButton("조회")
        btn_q.setObjectName("btn_ghost")
        btn_q.setFixedWidth(80)
        btn_q.clicked.connect(self._query_daily)
        fh.addWidget(btn_q)
        fh.addStretch()

        if EXCEL_AVAILABLE:
            btn_ex = QPushButton("엑셀 내보내기")
            btn_ex.setObjectName("btn_ghost")
            btn_ex.clicked.connect(self._export_daily)
            fh.addWidget(btn_ex)

        btn_tpl = QPushButton("📑 일일판매일지 양식 출력")
        btn_tpl.setObjectName("btn_success")
        btn_tpl.clicked.connect(self._export_daily_template)
        fh.addWidget(btn_tpl)

        btn_print = QPushButton("🖨️ 즉시 인쇄")
        btn_print.setObjectName("btn_primary")
        btn_print.setToolTip("기본 프린터로 가로 60% 자동 설정하여 즉시 인쇄합니다.")
        btn_print.clicked.connect(self._print_daily_template)
        fh.addWidget(btn_print)
        v.addLayout(fh)

        # 요약 카드
        ch = QHBoxLayout(); ch.setSpacing(10)
        self.d_count  = StatCard("📋", "건수",   "—", "#6366f1")
        self.d_qty    = StatCard("📦", "총수량",  "—", "#06b6d4")
        self.d_total  = StatCard("💰", "총금액",  "—", "#10b981")
        self.d_cash   = StatCard("💵", "현금",   "—", "#10b981")
        self.d_credit = StatCard("📝", "미수",   "—", "#ef4444")
        self.d_card   = StatCard("💳", "카드",   "—", "#6366f1")
        for sc in (self.d_count, self.d_qty, self.d_total,
                   self.d_cash, self.d_credit, self.d_card):
            ch.addWidget(sc)
        v.addLayout(ch)

        c1 = SectionCard("거래처별 집계")
        self.tbl_d_cust = self._tbl(['거래처', '수량', '합계금액', '현금', '미수', '카드'])
        c1.add_widget(self.tbl_d_cust)
        v.addWidget(c1)

        c2 = SectionCard("상세 내역 (더블 클릭 시 품목 상세 보기)")
        self.tbl_d_det = self._tbl(
            ['날짜', '거래처', '총 금액', '결제', '메모']
        )
        self.tbl_d_det.cellDoubleClicked.connect(self._show_delivery_details)
        c2.add_widget(self.tbl_d_det)
        v.addWidget(c2)

        # 탭 생성 후 즉시 당일 조회
        self._query_daily()
        return w

    # ── 기간별 ───────────────────────────────────────────────
    def _period_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(12)

        fh = QHBoxLayout(); fh.setSpacing(8)
        def fl(t):
            l = QLabel(t); l.setObjectName("form_label"); return l

        fh.addWidget(fl("시작일"))
        self.date_ps = NoScrollDateEdit(QDate.currentDate().addDays(-30))
        self.date_ps.setCalendarPopup(True)
        self.date_ps.setDisplayFormat("yyyy-MM-dd")
        self.date_ps.setFixedWidth(145)
        fh.addWidget(self.date_ps)

        fh.addWidget(fl("종료일"))
        self.date_pe = NoScrollDateEdit(QDate.currentDate())
        self.date_pe.setCalendarPopup(True)
        self.date_pe.setDisplayFormat("yyyy-MM-dd")
        self.date_pe.setFixedWidth(145)
        fh.addWidget(self.date_pe)

        fh.addWidget(fl("거래처"))
        self.combo_pc = QComboBox()
        self.combo_pc.setMinimumWidth(150)
        fh.addWidget(self.combo_pc)

        btn_q = QPushButton("조회")
        btn_q.setObjectName("btn_ghost")
        btn_q.setFixedWidth(80)
        btn_q.clicked.connect(self._query_period)
        fh.addWidget(btn_q)
        fh.addStretch()

        if EXCEL_AVAILABLE:
            btn_ex = QPushButton("엑셀 내보내기")
            btn_ex.setObjectName("btn_ghost")
            btn_ex.clicked.connect(self._export_period)
            fh.addWidget(btn_ex)
        v.addLayout(fh)

        ph = QHBoxLayout(); ph.setSpacing(10)
        self.p_count  = StatCard("📋", "건수",   "—", "#6366f1")
        self.p_qty    = StatCard("📦", "총수량",  "—", "#06b6d4")
        self.p_total  = StatCard("💰", "총금액",  "—", "#10b981")
        self.p_cash   = StatCard("💵", "현금",   "—", "#10b981")
        self.p_credit = StatCard("📝", "미수",   "—", "#ef4444")
        self.p_card   = StatCard("💳", "카드",   "—", "#6366f1")
        for sc in (self.p_count, self.p_qty, self.p_total,
                   self.p_cash, self.p_credit, self.p_card):
            ph.addWidget(sc)
        v.addLayout(ph)

        c = SectionCard("기간별 판매 상세 (더블 클릭 시 품목 상세 보기)")
        self.tbl_period = self._tbl(
            ['날짜', '거래처', '총 금액', '결제', '메모']
        )
        self.tbl_period.cellDoubleClicked.connect(self._show_delivery_details)
        c.add_widget(self.tbl_period)
        v.addWidget(c)
        return w

    # ── 월별 ─────────────────────────────────────────────────
    def _monthly_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(12)

        fh = QHBoxLayout(); fh.setSpacing(8)
        def fl(t):
            l = QLabel(t); l.setObjectName("form_label"); return l

        fh.addWidget(fl("년도"))
        self.combo_year = QComboBox()
        self.combo_year.setFixedWidth(100)
        cur = dt.today().year
        for y in range(cur - 5, cur + 2):
            self.combo_year.addItem(str(y), y)
        self.combo_year.setCurrentText(str(cur))
        fh.addWidget(self.combo_year)

        fh.addWidget(fl("월"))
        self.combo_month = QComboBox()
        self.combo_month.setFixedWidth(90)
        self.combo_month.addItem("전체", 0)
        for m in range(1, 13):
            self.combo_month.addItem(f"{m}월", m)
        fh.addWidget(self.combo_month)

        btn_q = QPushButton("조회")
        btn_q.setObjectName("btn_ghost")
        btn_q.setFixedWidth(80)
        btn_q.clicked.connect(self._query_monthly)
        fh.addWidget(btn_q)
        fh.addStretch()
        v.addLayout(fh)

        c = SectionCard("월별 판매 집계")
        self.tbl_monthly = self._tbl(['기간', '판매 건수', '총 수량', '총 금액'])
        c.add_widget(self.tbl_monthly)
        v.addWidget(c)
        return w

    # ── 공통 테이블 헬퍼 ─────────────────────────────────────
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

    def _fill(self, tbl: QTableWidget, rows: list, vals_fn):
        PAY = {'현금': '#10b981', '미수': '#ef4444', '카드': '#6366f1'}
        tbl.setRowCount(len(rows))
        for r, row in enumerate(rows):
            try:
                vals = vals_fn(row)
            except Exception:
                continue
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val) if val is not None else '')
                item.setTextAlignment(Qt.AlignCenter)
                if str(val) in PAY:
                    item.setForeground(QColor(PAY[str(val)]))
                tbl.setItem(r, c, item)

    def _fill_deliveries(self, tbl: QTableWidget, rows: list):
        """상세 내역 표시: 납품 단위(날짜+거래처)로 1행씩 요약하고, 더블클릭 용도의 품목 데이터를 저장."""
        PAY = {'현금': '#10b981', '미수': '#ef4444', '카드': '#6366f1'}
        
        # (날짜, 거래처ID, 거래처명, 결제방법, 메모) 단위로 그룹핑
        deliveries = {}
        for row in rows:
            key = (
                row.get('sale_date', ''),
                row.get('customer_id', ''),
                row.get('customer_name', ''),
                row.get('payment_method', ''),
                row.get('memo', '')
            )
            if key not in deliveries:
                deliveries[key] = {'total_amount': 0, 'items': []}
            deliveries[key]['total_amount'] += row.get('total_amount', 0)
            deliveries[key]['items'].append(row)

        tbl.setRowCount(len(deliveries))
        for r, (key, data) in enumerate(deliveries.items()):
            date_val, cid, cust_val, payment_val, memo_val = key
            
            vals = [
                date_val,
                cust_val,
                fmt_currency(data['total_amount']),
                payment_val,
                memo_val
            ]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                if str(val) in PAY:
                    item.setForeground(QColor(PAY[str(val)]))
                # 첫 번째 열에 상세 품목 리스트 저장
                if c == 0:
                    item.setData(Qt.UserRole, data['items'])
                tbl.setItem(r, c, item)

    def _show_delivery_details(self, row, col):
        """테이블 더블클릭 시 품목 상세 팝업 오픈."""
        tbl = self.sender()
        item = tbl.item(row, 0)
        if not item:
            return
        items = item.data(Qt.UserRole)
        if not items:
            return
            
        from ui.dialogs.sale_detail_dialog import SaleDetailDialog
        dlg = SaleDetailDialog(items, self)
        dlg.exec_()
        
        # 삭제된 항목이 있으면 현재 보고 있는 화면을 강제 새로고침
        if hasattr(dlg, 'deleted_any') and dlg.deleted_any:
            if tbl == self.tbl_d_det:
                self._query_daily()
            elif tbl == self.tbl_period:
                self._query_period()

    # ── 쿼리 메서드 ──────────────────────────────────────────
    def refresh(self):
        self._query_daily()
        self._query_period()
        self._query_monthly()

    def _query_daily(self, *args, **kwargs):
        try:
            date = self.date_daily.date().toString("yyyy-MM-dd")

            # 요약 카드
            s = self.sales_logic.get_daily_summary(date) or {}
            self.d_count.set_value(f"{s.get('sale_count', 0)} 건")
            self.d_qty.set_value(f"{fmt_number(s.get('total_qty', 0))} 개")
            self.d_total.set_value(fmt_currency(s.get('total_amount', 0)))
            self.d_cash.set_value(fmt_currency(s.get('cash', 0)))
            self.d_credit.set_value(fmt_currency(s.get('credit', 0)))
            self.d_card.set_value(fmt_currency(s.get('card', 0)))

            # 거래처별 집계
            self._fill(
                self.tbl_d_cust,
                self.report_logic.get_daily_by_customer(date),
                lambda r: [
                    r.get('customer_name', ''),
                    fmt_number(r.get('total_qty', 0)),
                    fmt_currency(r.get('total_amount', 0)),
                    fmt_currency(r.get('cash', 0)),
                    fmt_currency(r.get('credit', 0)),
                    fmt_currency(r.get('card', 0)),
                ]
            )

            # 상세 내역 (납품 1건씩 표시)
            self._fill_deliveries(
                self.tbl_d_det,
                self.sales_logic.get_sales_by_date(date)
            )
        except Exception as e:
            QMessageBox.critical(self, "조회 오류", f"일별 현황 조회 중 오류:\n{e}")

    def _query_period(self, *args, **kwargs):
        try:
            start = self.date_ps.date().toString("yyyy-MM-dd")
            end   = self.date_pe.date().toString("yyyy-MM-dd")
            cid   = self.combo_pc.currentData()

            s = self.report_logic.get_period_summary(start, end) or {}
            self.p_count.set_value(f"{s.get('sale_count', 0)} 건")
            self.p_qty.set_value(f"{fmt_number(s.get('total_qty', 0))} 개")
            self.p_total.set_value(fmt_currency(s.get('total_amount', 0)))
            self.p_cash.set_value(fmt_currency(s.get('cash', 0)))
            self.p_credit.set_value(fmt_currency(s.get('credit', 0)))
            self.p_card.set_value(fmt_currency(s.get('card', 0)))

            # 상세 내역 (납품 1건씩 표시)
            self._fill_deliveries(
                self.tbl_period,
                self.report_logic.get_period_by_customer(start, end, cid or None)
            )
        except Exception as e:
            QMessageBox.critical(self, "조회 오류", f"기간별 현황 조회 중 오류:\n{e}")

    def _query_monthly(self, *args, **kwargs):
        try:
            year  = self.combo_year.currentData()
            month = self.combo_month.currentData()
            if month == 0:
                rows = self.report_logic.get_yearly_monthly_summary(year)
                self._fill(self.tbl_monthly, rows,
                    lambda r: [
                        r.get('ym', ''),
                        f"{fmt_number(r.get('sale_count', 0))} 건",
                        f"{fmt_number(r.get('total_qty', 0))} 개",
                        fmt_currency(r.get('total_amount', 0)),
                    ])
            else:
                rows = self.sales_logic.get_monthly_summary(year, month)
                self._fill(self.tbl_monthly, rows,
                    lambda r: [
                        r.get('sale_date', r.get('ym', '')),
                        f"{fmt_number(r.get('sale_count', 0))} 건",
                        f"{fmt_number(r.get('total_qty', 0))} 개",
                        fmt_currency(r.get('total_amount', 0)),
                    ])
        except Exception as e:
            QMessageBox.critical(self, "조회 오류", f"월별 집계 조회 중 오류:\n{e}")

    # ── 엑셀 ─────────────────────────────────────────────────
    def _export_daily(self):
        try:
            date = self.date_daily.date().toString("yyyy-MM-dd")
            rows = self.sales_logic.get_sales_by_date(date)
            data = [[r.get('sale_date',''), r.get('customer_name',''),
                     r.get('type_name',''), r.get('spec_name',''),
                     r.get('quantity',0), r.get('unit_price',0),
                     r.get('total_amount',0), r.get('payment_method',''),
                     r.get('memo','')] for r in rows]
            path, _ = QFileDialog.getSaveFileName(self, "엑셀 내보내기", f"일별판매_{date}.xlsx", "Excel Files (*.xlsx)")
            if not path:
                return

            path = export_to_excel(
                ['날짜','거래처','종류','규격','수량','단가','금액','결제','메모'],
                data, f"일별판매_{date}", path
            )
            if path:
                QMessageBox.information(self, "완료", f"저장됨:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))

    def _export_daily_template(self):
        try:
            date = self.date_daily.date().toString("yyyy-MM-dd")
            rows = self.sales_logic.get_sales_by_date(date)
            cols = self.ar_logic.get_collections(start_date=date, end_date=date)
            if not rows and not cols:
                if QMessageBox.question(self, "확인", f"[{date}] 일자에 입력된 판매 및 수금 내역이 없습니다.\n빈 양식으로 출력을 진행하시겠습니까?", QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
                    return

            default_dir = r'F:\일일판매일지' if os.path.exists(r'F:\일일판매일지') else os.path.expanduser("~")
            default_name = f"일일판매일지_{date.replace('-','')}.xls"
            path, _ = QFileDialog.getSaveFileName(
                self, "일일판매일지 양식 출력",
                os.path.join(default_dir, default_name),
                "Excel Files (*.xls)"
            )
            if not path:
                return

            out_path = export_daily_sales_template(date, rows, output_path=path, collections_data=cols)
            if out_path and os.path.exists(out_path):
                if QMessageBox.question(self, "출력 완료", f"[{date}] 일일판매일지 양식이 성공적으로 생성되었습니다!\n\n저장 경로:\n{out_path}\n\n지금 바로 파일을 열어보시겠습니까?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                    os.startfile(out_path)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"일일판매일지 양식 출력 중 오류가 발생했습니다:\n{e}")

    def _print_daily_template(self):
        try:
            date = self.date_daily.date().toString("yyyy-MM-dd")
            rows = self.sales_logic.get_sales_by_date(date)
            cols = self.ar_logic.get_collections(start_date=date, end_date=date)
            if not rows and not cols:
                if QMessageBox.question(self, "확인", f"[{date}] 일자에 입력된 판매 및 수금 내역이 없습니다.\n빈 양식으로 인쇄를 진행하시겠습니까?", QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
                    return

            if QMessageBox.question(self, "인쇄 확인", f"[{date}] 일일판매일지를 윈도우 기본 프린터로 즉시 인쇄하시겠습니까?\n\n(쪽설정: 가로 방향 / 확대·축소 60% 한 페이지 자동 적용)", QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
                return

            import tempfile, time
            temp_dir = tempfile.gettempdir()
            temp_name = f"일일판매일지_{date.replace('-','')}_print_{int(time.time() * 1000)}.xls"
            path = os.path.join(temp_dir, temp_name)

            out_path = export_daily_sales_template(date, rows, output_path=path, collections_data=cols)
            if out_path and os.path.exists(out_path):
                print_excel_file(out_path)
                QMessageBox.information(self, "인쇄 요청 완료", f"[{date}] 일일판매일지 인쇄 요청이 윈도우 기본 프린터로 전송되었습니다.\n\n※ 엑셀 백그라운드 출력이 완료될 때까지 잠시 기다려주세요.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"일일판매일지 즉시 인쇄 중 오류가 발생했습니다:\n{e}")

    def _export_period(self):
        try:
            start = self.date_ps.date().toString("yyyy-MM-dd")
            end   = self.date_pe.date().toString("yyyy-MM-dd")
            cid   = self.combo_pc.currentData()
            rows  = self.report_logic.get_period_by_customer(start, end, cid or None)
            data  = [[r.get('sale_date',''), r.get('customer_name',''),
                      r.get('type_name',''), r.get('spec_name',''),
                      r.get('quantity',0), r.get('unit_price',0),
                      r.get('total_amount',0), r.get('payment_method',''),
                      r.get('memo','')] for r in rows]
            path, _ = QFileDialog.getSaveFileName(self, "엑셀 내보내기", f"기간별판매_{start}_{end}.xlsx", "Excel Files (*.xlsx)")
            if not path:
                return

            path = export_to_excel(
                ['날짜','거래처','종류','규격','수량','단가','금액','결제','메모'],
                data, f"기간별판매_{start}_{end}", path
            )
            if path:
                QMessageBox.information(self, "완료", f"저장됨:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))

    # ── refresh ──────────────────────────────────────────────
    def refresh(self):
        # 거래처 필터 콤보 갱신
        self.combo_pc.clear()
        self.combo_pc.addItem("전체", None)
        for c in self.customer_logic.get_all():
            self.combo_pc.addItem(c['name'], c['id'])
        # 당일 현황 자동 갱신
        self._query_daily()
