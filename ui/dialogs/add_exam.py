# ui/dialogs/add_exam.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore    import *
from PyQt5.QtGui     import *
from core.theme      import T
from core.data       import new_id
from core.assets     import svg_icon
from ui.base_widgets import lbl, mk_btn, ghost_btn, inp_style, foot_row, ChecklistEditor
from ui.dialogs.calendar_dialog import CalendarDialog


class _DateButton(QFrame):
    """클릭 또는 포커스 후 Enter 키로 캘린더를 열도록 설계된 커스텀 위젯."""
    clicked = pyqtSignal()

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.TabFocus)
        self.setCursor(Qt.PointingHandCursor)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 9, 12, 9)
        self._layout.setSpacing(8)
        self._icon_lbl = QLabel()
        self._icon_lbl.setStyleSheet("background:transparent;")
        self._text_lbl = QLabel(text)
        self._text_lbl.setStyleSheet(
            f"background:transparent;font-size:10pt;color:{T('TXT')};"
        )
        self._layout.addWidget(self._icon_lbl)
        self._layout.addWidget(self._text_lbl, 1)
        self._apply_style(focused=False)

    def set_icon(self, icon, size):
        self._icon_lbl.setPixmap(icon.pixmap(size, size))

    def setText(self, text):
        self._text_lbl.setText(text)
        self._text_lbl.setStyleSheet(
            f"background:transparent;font-size:10pt;color:{T('TXT')};"
        )

    def _apply_style(self, focused: bool):
        border_color = T("RED") if focused else T("BDR")
        self.setStyleSheet(
            f"QFrame{{background:{T('GL')};border:1.5px solid {border_color};"
            f"border-radius:8px;}}"
        )

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()

    def keyPressEvent(self, e):
        # 포커스가 이 위젯에 있을 때 Enter → 캘린더 열기
        if e.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.clicked.emit()
        else:
            super().keyPressEvent(e)

    def focusInEvent(self, e):
        self._apply_style(focused=True)
        super().focusInEvent(e)

    def focusOutEvent(self, e):
        self._apply_style(focused=False)
        super().focusOutEvent(e)


class AddExamDialog(QDialog):
    def __init__(self, parent=None, initial=None):
        super().__init__(parent)
        self.result_data = None
        self._date = ""
        self._initial = initial
        self.setWindowTitle("새 시험 추가")
        self.setMinimumWidth(500)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setStyleSheet(f"background:{T('CARD')};")
        self._build()

    def _frow(self, label_text, widget):
        w = QWidget()
        w.setStyleSheet(f"background:{T('CARD')};")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(4)
        vl.addWidget(lbl(label_text, 10, True))
        vl.addWidget(widget)
        return w

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        hdr = QWidget()
        hdr.setFixedHeight(60)
        hdr.setStyleSheet(f"background:{T('RED')};")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(24, 0, 24, 0)
        hl.addWidget(lbl("새 시험 추가", 14, True, "white"))
        root.addWidget(hdr)

        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setStyleSheet("QScrollArea{border:none;}")
        sc.setMinimumHeight(420)

        body = QWidget()
        body.setStyleSheet(f"background:{T('CARD')};")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 16, 24, 16)
        bl.setSpacing(14)

        is_ = f"QLineEdit{{background:{T('GL')};border:1.5px solid {T('BDR')};border-radius:8px;padding:9px 12px;font-size:10pt;color:{T('TXT')};}}QLineEdit:focus{{border:2px solid {T('RED')};background:{T('CARD')};}}"

        # ① 과목명 -> Enter -> 날짜 버튼으로 포커스만 이동
        self.f_subj = QLineEdit()
        self.f_subj.setPlaceholderText("예) 운영체제")
        self.f_subj.setStyleSheet(is_)
        self.f_subj.returnPressed.connect(lambda: QTimer.singleShot(0, lambda: self._date_btn.setFocus()))

        # 날짜 버튼 (커스텀 위젯: Enter/click 분리)
        self._date_btn = _DateButton("  날짜를 선택하세요")
        ic = svg_icon("deadline", 15, T("SUB"))
        if ic:
            self._date_btn.set_icon(ic, 15)
        self._date_btn.clicked.connect(self._pick_date)

        # ③ 시험 장소
        self.f_place = QLineEdit()
        self.f_place.setPlaceholderText("예) 공학관 101호")
        self.f_place.setStyleSheet(is_)
        self.f_place.returnPressed.connect(lambda: QTimer.singleShot(0, lambda: self.f_range.setFocus()))

        # ④ 시험 범위
        self.f_range = QLineEdit()
        self.f_range.setPlaceholderText("예) 1강~6강, 교재 p.1~150")
        self.f_range.setStyleSheet(is_)
        self.f_range.returnPressed.connect(lambda: QTimer.singleShot(0, self._focus_extra_editor))

        initial_items = None
        if self._initial:
            self.f_subj.setText(self._initial.get("subject", ""))
            self.f_place.setText(self._initial.get("place", ""))
            self.f_range.setText(self._initial.get("range", ""))
            self._date = self._initial.get("date", "")
            if self._date:
                self._date_btn.setText("  " + self._date)
            initial_items = self._initial.get("extra_tasks", [])

        self._extra_ed = ChecklistEditor(items=initial_items, placeholder="추가 항목  예) 문제 풀이 완료")
        ex_sc = QScrollArea()
        ex_sc.setWidgetResizable(True)
        ex_sc.setFixedHeight(180)
        ex_sc.setStyleSheet(
            f"QScrollArea{{border:1.5px solid {T('BDR')};border-radius:8px;background:{T('CARD')};}}"
        )
        ex_sc.setWidget(self._extra_ed)

        bl.addWidget(self._frow("과목명  *", self.f_subj))
        bl.addWidget(self._frow("시험 일자  *", self._date_btn))
        bl.addWidget(self._frow("시험 장소", self.f_place))
        bl.addWidget(self._frow("시험 범위", self.f_range))
        bl.addWidget(self._frow("추가 체크리스트", ex_sc))

        sc.setWidget(body)
        root.addWidget(sc, 1)
        root.addWidget(foot_row(self, self._submit, "추가하기", T("RED")))

    def _focus_extra_editor(self):
        try:
            if hasattr(self._extra_ed, "_rows") and self._extra_ed._rows:
                self._extra_ed._rows[0][1].setFocus()
            else:
                inp = self._extra_ed._add_row()
                inp.setFocus()
        except Exception:
            self._date_btn.setFocus()

    def _pick_date(self):
        dlg = CalendarDialog(include_time=False, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._date = dlg.result_dt
            self._date_btn.setText("  " + self._date)
        # 날짜 선택 후 시험 장소로 포커스
        QTimer.singleShot(0, lambda: self.f_place.setFocus())

    def _submit(self):
        subj = self.f_subj.text().strip()
        if not subj:
            QMessageBox.warning(self, "오류", "과목명을 입력해주세요.")
            return
        if not self._date:
            QMessageBox.warning(self, "오류", "시험 일자를 선택해주세요.")
            return
        extra = self._extra_ed.get_items()
        eid = self._initial.get("id", new_id()) if self._initial else new_id()
        self.result_data = {
            "id": eid,
            "subject": subj,
            "date": self._date,
            "place": self.f_place.text().strip(),
            "range": self.f_range.text().strip(),
            "color": self._initial.get("color") if self._initial else None,
            "read1": False, "read2": False, "read_extra": False,
            "extra_tasks": extra,
        }
        self.accept()