# ui/dialogs/calendar_dialog.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore    import *
from PyQt5.QtGui     import *
from core.theme      import T
from ui.base_widgets import lbl, mk_btn, ghost_btn

class CalendarDialog(QDialog):
    def __init__(self, include_time=True, parent=None):
        super().__init__(parent)
        self.result_dt = ''
        self._inc = include_time
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        frame = QFrame()
        frame.setObjectName('cf')
        frame.setStyleSheet(
            'QFrame#cf{background:' + T('CARD') + ';border-radius:20px;border:1px solid ' + T('BDR') + ';}'
        )
        sh = QGraphicsDropShadowEffect(frame)
        sh.setBlurRadius(32); sh.setOffset(0, 8); sh.setColor(QColor(0, 0, 0, 50))
        frame.setGraphicsEffect(sh)
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(0, 0, 0, 16); vl.setSpacing(0)

        hdr = QWidget()
        hdr.setStyleSheet('background:' + T('PRI') + ';border-radius:19px 19px 0 0;')
        hdr.setFixedHeight(52)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(20, 0, 14, 0)
        hl.addWidget(lbl('날짜 선택', 12, True, 'white'))
        hl.addStretch()
        xb = QPushButton('x'); xb.setFixedSize(26, 26); xb.setCursor(Qt.PointingHandCursor)
        xb.setStyleSheet('QPushButton{background:rgba(255,255,255,0.2);color:white;border:none;border-radius:13px;font-size:10pt;}QPushButton:hover{background:rgba(255,255,255,0.38);}')
        xb.clicked.connect(self.reject); hl.addWidget(xb); vl.addWidget(hdr)

        self._cal = QCalendarWidget()
        self._cal.setSelectedDate(QDate.currentDate())
        self._cal.setGridVisible(False)
        self._cal.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        card=T('CARD'); txt=T('TXT'); pri=T('PRI'); pri_l=T('PRI_L')
        gl=T('GL'); bdr=T('BDR'); sub=T('SUB')
        css = (
            'QCalendarWidget{background:' + card + ';border:none;}'
            'QCalendarWidget QAbstractItemView{background:' + card + ';color:' + txt + ';'
            'selection-background-color:' + pri + ';selection-color:white;border:none;font-size:10pt;outline:none;}'
            'QCalendarWidget QWidget#qt_calendar_navigationbar{background:' + gl + ';border-bottom:1px solid ' + bdr + ';padding:4px 8px;}'
            'QCalendarWidget QToolButton{background:transparent;color:' + txt + ';font-size:11pt;font-weight:bold;border:none;padding:6px 10px;border-radius:8px;}'
            'QCalendarWidget QToolButton:hover{background:' + pri_l + ';color:' + pri + ';}'
            'QCalendarWidget QToolButton#qt_calendar_prevmonth,QCalendarWidget QToolButton#qt_calendar_nextmonth{font-size:14pt;color:' + pri + ';}'
            'QCalendarWidget QSpinBox{background:' + gl + ';color:' + txt + ';border:1px solid ' + bdr + ';border-radius:6px;padding:3px 8px;font-size:11pt;font-weight:bold;}'
        )
        self._cal.setStyleSheet(css)
        vl.addWidget(self._cal)

        if self._inc:
            tw = QWidget()
            tw.setStyleSheet('background:' + T('GL') + ';border-radius:12px;border:1px solid ' + T('BDR') + ';')
            tl = QHBoxLayout(tw); tl.setContentsMargins(16, 10, 16, 10); tl.setSpacing(8)
            tl.addWidget(lbl('시간', 10, False, T('SUB'))); tl.addStretch()
            sp_s = ('QSpinBox{background:' + T('CARD') + ';border:1.5px solid ' + T('BDR') + ';'
                    'border-radius:8px;padding:5px 10px;font-size:11pt;color:' + T('TXT') + ';min-width:52px;}'
                    'QSpinBox:focus{border-color:' + T('PRI') + ';}'
                    'QSpinBox::up-button,QSpinBox::down-button{width:0;}')
            self._h = QSpinBox(); self._h.setRange(0,23); self._h.setValue(23)
            self._m = QSpinBox(); self._m.setRange(0,59); self._m.setValue(59)
            for sp in [self._h, self._m]: sp.setStyleSheet(sp_s); sp.setAlignment(Qt.AlignCenter)
            tl.addWidget(self._h); tl.addWidget(lbl(':', 14, True, T('PRI'))); tl.addWidget(self._m)
            pw = QWidget(); pw.setStyleSheet('background:' + T('CARD') + ';')
            pl = QVBoxLayout(pw); pl.setContentsMargins(16, 8, 16, 0); pl.addWidget(tw)
            vl.addWidget(pw)
        else:
            self._h = self._m = None

        bw = QWidget(); bw.setStyleSheet('background:' + T('CARD') + ';')
        bl = QHBoxLayout(bw); bl.setContentsMargins(16, 10, 16, 0); bl.setSpacing(8); bl.addStretch()
        cancel = ghost_btn('취소'); cancel.clicked.connect(self.reject)
        ok = mk_btn('선택', T('PRI'), pad='9px 24px'); ok.clicked.connect(self._ok)
        bl.addWidget(cancel); bl.addWidget(ok); vl.addWidget(bw)
        outer.addWidget(frame)

    def _ok(self):
        d = self._cal.selectedDate()
        ds = f'{d.year():04d}-{d.month():02d}-{d.day():02d}'
        if self._h:
            self.result_dt = f'{ds} {self._h.value():02d}:{self._m.value():02d}'
        else:
            self.result_dt = ds
        self.accept()