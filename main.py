#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# StudyMate v4.0  —  실행: python main.py
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore    import *
from PyQt5.QtGui     import *
from datetime        import datetime

import core.data as D
from core.theme  import T, apply_theme, icon_color_on, current_name
from core.assets import setup_font, app_icon, svg_icon, svg_pixmap
from ui.base_widgets       import lbl, hdiv, ToggleSwitch
from ui.tabs               import AssignmentTab, ExamTab, TrashTab
from ui.mini_widget        import MiniWidget
from ui.dialogs.settings_dialog import SettingsDialog


class ActivityFilter(QObject):
    activity=pyqtSignal()
    def eventFilter(self,obj,event):
        if event.type() in (QEvent.MouseMove,QEvent.KeyPress,QEvent.MouseButtonPress,QEvent.Wheel):
            self.activity.emit()
        return False


class TrayIcon(QSystemTrayIcon):
    def __init__(self,main_win,mini_win,app):
        super().__init__(app_icon(),app)
        self._main=main_win; self._mini=mini_win
        menu=QMenu()
        menu.setStyleSheet(f"QMenu{{background:{T('CARD')};border:1px solid {T('BDR')};border-radius:8px;padding:4px;}}QMenu::item{{padding:8px 20px;font-size:10pt;color:{T('TXT')};border-radius:4px;}}QMenu::item:selected{{background:{T('PRI_L')};color:{T('PRI')};}}")
        # choose icon colors based on menu background
        menu_bg = T('CARD')
        a1=menu.addAction("메인 창 열기"); a1.setIcon(svg_icon("homework",16,icon_color_on(menu_bg)))
        a2=menu.addAction("미니 위젯 토글"); a2.setIcon(svg_icon("widgetsetting",16,icon_color_on(menu_bg)))
        menu.addSeparator()
        a3=menu.addAction("종료"); a3.setIcon(svg_icon("delete",16,icon_color_on(menu_bg)))
        a1.triggered.connect(self._show_main)
        a2.triggered.connect(self._toggle_mini)
        a3.triggered.connect(QApplication.quit)
        self.setContextMenu(menu); self.activated.connect(self._activated)
        self.setToolTip("StudyMate"); self.show()

    def _show_main(self): self._main.show(); self._main.raise_()
    def _toggle_mini(self):
        if self._mini.isVisible(): self._mini.hide()
        else: self._mini.show(); self._mini.raise_()
    def _activated(self,reason):
        if reason==QSystemTrayIcon.DoubleClick: self._show_main()


class MainWindow(QMainWindow):
    def __init__(self,data,mini_win):
        super().__init__(); self.data=data; self.mini_win=mini_win
        self.setWindowTitle("StudyMate  —  대학생 과제/공부 관리")
        self.setWindowIcon(app_icon()); self.setMinimumSize(900,620); self.resize(1120,760)
        scr=QApplication.primaryScreen().geometry()
        self.move((scr.width()-1120)//2,(scr.height()-760)//2)
        self._build()

    def _build(self):
        cw=QWidget(); cw.setStyleSheet(f"background:{T('BG')};"); self.setCentralWidget(cw)
        ml=QVBoxLayout(cw); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)
        hdr=QWidget(); hdr.setFixedHeight(68)
        hdr.setStyleSheet(f"background:{T('PRI')};")
        hl=QHBoxLayout(hdr); hl.setContentsMargins(28,0,28,0); hl.setSpacing(12)
        ic=QLabel()
        # header icon color: 자동 결정
        try:
            icon_col = icon_color_on(T('PRI'))
        except Exception:
            icon_col = "white"
        ic.setPixmap(svg_pixmap("homework",24,icon_col)); hl.addWidget(ic)
        hl.addWidget(lbl("StudyMate",18,True,"white")); hl.addStretch()
        hl.addWidget(lbl(datetime.now().strftime("%Y년 %m월 %d일"),10,False,"rgba(255,255,255,0.7)"))
        hl.addSpacing(16)
        sb=QPushButton(); sb.setCursor(Qt.PointingHandCursor)
        # settings icon sits on PRI bar -> choose color accordingly
        sb.setIcon(svg_icon("setting",18,icon_color_on(T("PRI")))); sb.setIconSize(QSize(18,18)); sb.setToolTip("설정")
        sb.setStyleSheet("QPushButton{background:rgba(255,255,255,0.18);border:none;border-radius:8px;padding:7px 10px;}QPushButton:hover{background:rgba(255,255,255,0.28);}")
        sb.clicked.connect(self._open_settings); hl.addWidget(sb); hl.addSpacing(10)
        tog_w=QWidget(); tog_w.setStyleSheet("background:transparent;")
        tog_l=QHBoxLayout(tog_w); tog_l.setContentsMargins(0,0,0,0); tog_l.setSpacing(6)
        tog_l.addWidget(lbl("최상단 고정",9,False,"rgba(255,255,255,0.8)"))
        self._top_tg=ToggleSwitch(self.data.get("always_on_top",False))
        self._top_tg.toggled.connect(self._toggle_top)
        tog_l.addWidget(self._top_tg); hl.addWidget(tog_w); ml.addWidget(hdr)
        tabbar=QWidget(); tabbar.setStyleSheet(f"background:{T('CARD')};"); tabbar.setFixedHeight(50)
        tbl=QHBoxLayout(tabbar); tbl.setContentsMargins(20,0,0,0); tbl.setSpacing(0)
        self._tab_btns={}
        TAB_DEFS=[("assignment","homework","과제 관리"),("exam","exam","시험공부 관리"),("trash","delete","휴지통")]
        for key,icon_n,label_text in TAB_DEFS:
            btn=QPushButton(); 
            # icon color should be chosen according to the button background when active/inactive
            btn_icon_col = icon_color_on(T('PRI')) if key=="assignment" else icon_color_on(T('CARD'))
            btn.setIcon(svg_icon(icon_n,16,icon_color_on(T('CARD')))); btn.setIconSize(QSize(16,16))
            btn.setText("  "+label_text); btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True); btn.setFixedHeight(50)
            btn.clicked.connect(lambda _,k=key: self._switch(k))
            self._tab_btns[key]=btn; tbl.addWidget(btn)
        tbl.addStretch(); self._upd_tabs("assignment"); ml.addWidget(tabbar); ml.addWidget(hdiv())
        self._stack=QStackedWidget(); self._stack.setStyleSheet(f"background:{T('BG')};")
        self._atab=AssignmentTab(self.data,self._save)
        self._etab=ExamTab(self.data,self._save)
        self._ttab=TrashTab(self.data,self._save)
        for tab in [self._atab,self._etab,self._ttab]:
            tab.refreshed.connect(self._on_data_changed)
        self._stack.addWidget(self._atab); self._stack.addWidget(self._etab); self._stack.addWidget(self._ttab)
        self._stack.setCurrentIndex(0); ml.addWidget(self._stack,1)
        if self.data.get("always_on_top",False): self._apply_top(True)

    def _upd_tabs(self,active):
        TAB_ICONS={"assignment":"homework","exam":"exam","trash":"delete"}
        for key,btn in self._tab_btns.items():
            active_bg = T('PRI') if key==active else T('CARD')
            ic_col = icon_color_on(active_bg) if key==active else icon_color_on(T('CARD'))
            btn.setIcon(svg_icon(TAB_ICONS[key],16,ic_col)); btn.setIconSize(QSize(16,16))
            btn.setChecked(key==active)
            if key==active:
                btn.setStyleSheet(f"QPushButton{{background:{T('CARD')};color:{T('PRI')};border:none;border-bottom:3px solid {T('PRI')};font-size:10pt;font-weight:bold;padding:0 22px;}}")
            else:
                btn.setStyleSheet(f"QPushButton{{background:{T('CARD')};color:{T('SUB')};border:none;border-bottom:3px solid transparent;font-size:10pt;padding:0 22px;}}QPushButton:hover{{color:{T('TXT')};}}")

    def _switch(self,key):
        self._upd_tabs(key); idx={"assignment":0,"exam":1,"trash":2}[key]; self._stack.setCurrentIndex(idx)

    def _toggle_top(self,checked):
        self.data["always_on_top"]=checked; self._apply_top(checked)
        self.mini_win.set_always_on_top(checked)
        if checked: self.mini_win.show(); self.mini_win.raise_()
        else: self.mini_win.hide()
        D.save(self.data)

    def _apply_top(self,on):
        flags=self.windowFlags()
        if on: flags|=Qt.WindowStaysOnTopHint
        else: flags&=~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags); self.show()

    def _open_settings(self):
        dlg=SettingsDialog(self.data,self)
        dlg.theme_changed.connect(self._on_theme_changed); dlg.exec_()

    def _on_theme_changed(self):
        # rebuild main UI and rebuild each tab + mini widget so theme changes apply immediately
        self._build()
        try:
            self._atab._rebuild(); self._etab._rebuild(); self._ttab._rebuild()
        except Exception:
            pass
        self.mini_win._build(); self.mini_win._refresh_list()

    def _on_data_changed(self):
        # when data changes (including deletions), rebuild tabs and refresh mini widget immediately
        try:
            self._atab._rebuild(); self._etab._rebuild(); self._ttab._rebuild()
        except Exception:
            pass
        self.mini_win._refresh_list()

    def _save(self): D.save(self.data); self.mini_win._refresh_list()
    def closeEvent(self,e): e.ignore(); self.hide()


def main():
    app=QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)
    data=D.load(); fam=setup_font()
    app.setFont(QFont(fam,10)); app.setWindowIcon(app_icon())
    app.setStyleSheet(
        f"QScrollBar:vertical{{background:{T('BG')};width:7px;margin:0;border:none;}}"
        f"QScrollBar::handle:vertical{{background:{T('BDR')};border-radius:3px;min-height:24px;}}"
        f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;border:none;}}"
        f"QScrollBar:horizontal{{background:{T('BG')};height:7px;margin:0;border:none;}}"
        f"QScrollBar::handle:horizontal{{background:{T('BDR')};border-radius:3px;min-width:24px;}}"
        f"QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal{{width:0;border:none;}}"
        f"QToolTip{{background:{T('CARD')};color:{T('TXT')};border:1px solid {T('BDR')};padding:4px 8px;border-radius:6px;}}"
    )
    mini=MiniWidget(data,lambda: D.save(data))
    main_win=MainWindow(data,mini)
    mini.open_main.connect(lambda: (main_win.show(),main_win.raise_()))
    mini.data_changed.connect(main_win._on_data_changed)
    act=ActivityFilter(); act.activity.connect(mini.reset_inactivity); app.installEventFilter(act)
    if QSystemTrayIcon.isSystemTrayAvailable():
        TrayIcon(main_win,mini,app)
    if data.get("always_on_top",False): mini.show()
    main_win.show()
    sys.exit(app.exec_())


if __name__=="__main__":
    main()