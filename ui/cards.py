# ui/cards.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore    import *
from PyQt5.QtGui     import *
from datetime        import datetime
from core.theme      import T, dk, dday_color
from core.data       import calc_progress, new_task
from core.assets     import svg_icon, svg_pixmap
from ui.base_widgets import (lbl, hdiv, sbadge, dbadge, mk_btn,
                              ghost_btn, icon_btn, prog_bar, ConfirmDialog, InputDialog)
from ui.dialogs.add_assignment import AddAssignmentDialog
from ui.dialogs.add_exam       import AddExamDialog


def _diff(dl, fmt="%Y-%m-%d %H:%M"):
    try:
        dt=datetime.strptime(dl,fmt)
        return int((dt-datetime.now()).total_seconds()//86400)
    except Exception: return None

def _dc(d):
    return dday_color(d)

def _dt(d):
    if d is None: return ""
    if d<0: return "기간 지남"
    if d==0: return "D-Day!"
    return f"D-{d}"


def _clear_layout(layout):
    # 재귀적으로 레이아웃 내부의 위젯/레이아웃을 제거
    while layout.count():
        item = layout.takeAt(0)
        if item is None:
            continue
        w = item.widget()
        if w:
            w.deleteLater()
        else:
            sub = item.layout()
            if sub:
                _clear_layout(sub)
            # spacerItem는 무시


class AssignmentCard(QFrame):
    deleted=pyqtSignal(str)
    changed=pyqtSignal()
    def __init__(self,data,color,on_save,parent=None):
        super().__init__(parent); self.data=data; self.color=color; self.on_save=on_save
        self.setObjectName("ac")
        self.setStyleSheet(f"QFrame#ac{{background:{T('CARD')};border-radius:14px;border:1.5px solid {T('BDR')};}}")
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Minimum)
        outer=QHBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        self._bar=QFrame(); self._bar.setFixedWidth(6)
        self._bar.setStyleSheet(f"background:{color};border-radius:6px 0 0 6px;"); outer.addWidget(self._bar)
        inner=QWidget(); inner.setStyleSheet(f"background:{T('CARD')};border-radius:0 14px 14px 0;")
        self._cl=QVBoxLayout(inner); self._cl.setContentsMargins(16,14,16,14); self._cl.setSpacing(8)
        outer.addWidget(inner,1); self._populate()

    def _populate(self):
        # clear existing layout children (레이아웃/위젯 모두 제거)
        _clear_layout(self._cl)
        cl=self._cl
        hdr=QHBoxLayout(); hdr.setSpacing(8)
        cd=QPushButton(); cd.setFixedSize(16,16); cd.setCursor(Qt.PointingHandCursor)
        cd.setToolTip("색상 변경")
        cd.setStyleSheet(f"background:{self.color};border-radius:8px;border:2px solid white;")
        cd.clicked.connect(self._pick_color); hdr.addWidget(cd)
        hdr.addWidget(sbadge(self.data["subject"],self.color))
        hdr.addWidget(lbl(self.data["name"],12,True)); hdr.addStretch()
        xb=icon_btn(None,"x",26); xb.clicked.connect(self._delete); hdr.addWidget(xb)
        cl.addLayout(hdr)
        diff=_diff(self.data.get("deadline",""))
        dr=QHBoxLayout(); dr.setSpacing(8)
        ic=QLabel(); ic.setPixmap(svg_pixmap("deadline",14,T("SUB"))); dr.addWidget(ic)
        try:
            dt=datetime.strptime(self.data.get("deadline",""),"%Y-%m-%d %H:%M")
            dl_str=dt.strftime("%Y.%m.%d  %H:%M")
        except Exception: dl_str=self.data.get("deadline","")
        dr.addWidget(lbl(dl_str,10,False,T("SUB")))
        if diff is not None: dr.addWidget(dbadge(_dt(diff),_dc(diff)))
        dr.addStretch(); cl.addLayout(dr)
        prog=calc_progress(self.data.get("tasks",[])); cp=T("GRN") if prog==100 else self.color
        pr=QHBoxLayout()
        pr.addWidget(lbl("진행도",9,False,T("SUB"))); pr.addStretch()
        self._pct=lbl(f"{prog}%",9,True,cp); pr.addWidget(self._pct)
        cl.addLayout(pr)
        self._pbar=prog_bar(prog,cp); cl.addWidget(self._pbar)
        cl.addWidget(hdiv()); cl.addWidget(lbl("할일 목록",9,True,T("SUB")))
        self._tw=QWidget(); self._tw.setStyleSheet("background:transparent;")
        self._tl=QVBoxLayout(self._tw); self._tl.setContentsMargins(0,0,0,0); self._tl.setSpacing(3)
        cl.addWidget(self._tw); self._build_tasks()
        abr=QHBoxLayout()
        ab=mk_btn("  할일 추가",T("PRI_L"),T("PRI"),9,6,"5px 12px","plus",T("PRI"))
        ab.clicked.connect(self._add_task); abr.addWidget(ab); abr.addStretch(); cl.addLayout(abr)
        self._sw=QWidget(); self._sw.setStyleSheet("background:transparent;")
        self._sl=QHBoxLayout(self._sw); self._sl.setContentsMargins(0,0,0,0)
        cl.addWidget(self._sw)
        if prog==100: self._show_submit()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("수정", lambda: self._edit())
        menu.addAction("삭제", lambda: self._delete())
        menu.exec_(event.globalPos())

    def _edit(self):
        dlg=AddAssignmentDialog(self.window(), initial=self.data)
        if dlg.exec_()==QDialog.Accepted and dlg.result_data:
            # preserve id
            newd = dlg.result_data
            self.data.update(newd)
            self._populate(); self.on_save(); self.changed.emit()

    def _build_tasks(self):
        while self._tl.count():
            i=self._tl.takeAt(0)
            if i.widget(): i.widget().deleteLater()
        for task in self.data.get("tasks",[]):
            row=QWidget(); row.setStyleSheet("background:transparent;")
            rl=QHBoxLayout(row); rl.setContentsMargins(2,0,2,0); rl.setSpacing(8)
            cb=QCheckBox(); cb.setChecked(task["done"])
            cb.setStyleSheet(f"QCheckBox::indicator{{width:16px;height:16px;border-radius:4px;border:2px solid {T('BDR')};background:{T('CARD')};}}QCheckBox::indicator:checked{{background:{self.color};border:2px solid {self.color};}}")
            cb.stateChanged.connect(lambda s,tid=task["id"]: self._toggle(tid,s)); rl.addWidget(cb)
            sx="text-decoration:line-through;" if task["done"] else ""
            tl2=lbl(task["text"],10,False,T("SUB") if task["done"] else T("TXT"))
            tl2.setStyleSheet(tl2.styleSheet()+sx); rl.addWidget(tl2,1)
            xb=QPushButton("x"); xb.setFixedSize(20,20); xb.setCursor(Qt.PointingHandCursor)
            xb.setStyleSheet(f"QPushButton{{background:transparent;color:{T('SUB')};border:none;font-size:13pt;border-radius:10px;}}QPushButton:hover{{background:{T('RED')};color:white;}}")
            xb.clicked.connect(lambda _,tid=task["id"]: self._del_task(tid))
            rl.addWidget(xb); self._tl.addWidget(row)

    def _toggle(self,tid,state):
        for t in self.data.get("tasks",[]):
            if t["id"]==tid: t["done"]=(state==Qt.Checked); break
        self._refresh(); self.on_save(); self.changed.emit()

    def _refresh(self):
        prog=calc_progress(self.data.get("tasks",[])); cp=T("GRN") if prog==100 else self.color
        self._pct.setText(f"{prog}%")
        self._pct.setStyleSheet(f"color:{cp};font-size:9pt;font-weight:bold;background:transparent;")
        self._pbar.setValue(prog)
        self._pbar.setStyleSheet(f"QProgressBar{{background:{T('BDR')};border-radius:4px;border:none;}}QProgressBar::chunk{{background:{cp};border-radius:4px;}}")
        self._build_tasks()
        while self._sl.count():
            i=self._sl.takeAt(0)
            if i.widget(): i.widget().deleteLater()
        if prog==100: self._show_submit()

    def _show_submit(self):
        b=mk_btn("  제출 완료  —  목록에서 삭제",T("GRN"),"white",10,8,"9px 18px","check","white")
        b.clicked.connect(self._submit_done); self._sl.addWidget(b); self._sl.addStretch()

    def _submit_done(self):
        dlg=ConfirmDialog("제출 완료",
            f"'{self.data['name']}' 과제를 제출 완료로 처리하고 삭제할까요?",
            ok_text="제출 완료",ok_color=T("GRN"),icon_name="check",parent=self.window())
        if dlg.exec_()==QDialog.Accepted:
            self.on_save()
            self.deleted.emit(self.data["id"])

    def _add_task(self):
        dlg=InputDialog("할일 추가","새 할일을 입력하세요:",self.window())
        if dlg.exec_()==QDialog.Accepted and dlg.value:
            self.data.setdefault("tasks",[]).append(new_task(dlg.value))
            self._build_tasks(); self._refresh(); self.on_save(); self.changed.emit()

    def _del_task(self,tid):
        self.data["tasks"]=[t for t in self.data.get("tasks",[]) if t["id"]!=tid]
        self._build_tasks(); self._refresh(); self.on_save(); self.changed.emit()

    def _pick_color(self):
        c=QColorDialog.getColor(QColor(self.color),self.window(),"색상 선택")
        if c.isValid():
            self.color=c.name(); self.data["color"]=self.color
            self._bar.setStyleSheet(f"background:{self.color};border-radius:6px 0 0 6px;")
            self.on_save(); self.changed.emit()

    def _delete(self):
        dlg=ConfirmDialog("과제 삭제",
            f"'{self.data['name']}' 과제를 삭제할까요?\n삭제된 과제는 휴지통에서 확인할 수 있습니다.",
            ok_text="삭제",ok_color=T("RED"),parent=self.window())
        if dlg.exec_()==QDialog.Accepted:
            self.on_save()
            self.deleted.emit(self.data["id"])


class ExamCard(QFrame):
    deleted=pyqtSignal(str)
    changed=pyqtSignal()
    def __init__(self,data,color,on_save,parent=None):
        super().__init__(parent); self.data=data; self.color=color; self.on_save=on_save
        self.setObjectName("ec")
        self.setStyleSheet(f"QFrame#ec{{background:{T('CARD')};border-radius:14px;border:1.5px solid {T('BDR')};}}")
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Minimum)
        outer=QHBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        self._bar=QFrame(); self._bar.setFixedWidth(6)
        self._bar.setStyleSheet(f"background:{color};border-radius:6px 0 0 6px;"); outer.addWidget(self._bar)
        inner=QWidget(); inner.setStyleSheet(f"background:{T('CARD')};border-radius:0 14px 14px 0;")
        self._cl=QVBoxLayout(inner); self._cl.setContentsMargins(16,14,16,14); self._cl.setSpacing(8)
        outer.addWidget(inner,1); self._populate()

    def _populate(self):
        # clear existing layout children (레이아웃/위젯 모두 제거)
        _clear_layout(self._cl)
        cl=self._cl
        hdr=QHBoxLayout(); hdr.setSpacing(8)
        cd=QPushButton(); cd.setFixedSize(16,16); cd.setCursor(Qt.PointingHandCursor)
        cd.setStyleSheet(f"background:{self.color};border-radius:8px;border:2px solid white;")
        cd.clicked.connect(self._pick_color); hdr.addWidget(cd)
        hdr.addWidget(sbadge(self.data["subject"],self.color))
        hdr.addWidget(lbl("시험",12,True)); hdr.addStretch()
        xb=icon_btn(None,"x",26); xb.clicked.connect(self._delete); hdr.addWidget(xb)
        cl.addLayout(hdr)
        diff=_diff(self.data.get("date",""),"%Y-%m-%d")
        ir=QHBoxLayout(); ir.setSpacing(10)
        di=QLabel(); di.setPixmap(svg_pixmap("deadline",14,T("SUB"))); ir.addWidget(di)
        ir.addWidget(lbl(self.data.get("date",""),10,False,T("SUB")))
        if diff is not None: ir.addWidget(dbadge(_dt(diff),_dc(diff)))
        place=self.data.get("place","")
        if place:
            pi=QLabel(); pi.setPixmap(svg_pixmap("loc",14,T("SUB"))); ir.addWidget(pi)
            ir.addWidget(lbl(place,10,False,T("SUB")))
        ir.addStretch(); cl.addLayout(ir)
        rng=self.data.get("range","")
        if rng:
            rb=QFrame(); rb.setStyleSheet(f"background:{T('GL')};border-radius:8px;border:1px solid {T('BDR')};")
            rl=QVBoxLayout(rb); rl.setContentsMargins(12,8,12,8); rl.setSpacing(3)
            rl.addWidget(lbl("시험 범위",9,True,T("SUB")))
            rl.addWidget(lbl(rng,10,False,T("TXT"),wrap=True)); cl.addWidget(rb)
        cl.addWidget(hdiv()); cl.addWidget(lbl("학습 체크리스트",10,True))
        FIXED=[("read1","first","1회독"),("read2","second","2회독"),("read_extra","more","추가 회독")]
        for key,icon_n,lt in FIXED:
            row=QWidget(); row.setStyleSheet("background:transparent;")
            rl=QHBoxLayout(row); rl.setContentsMargins(0,0,0,0); rl.setSpacing(8)
            ic=QLabel(); ic.setPixmap(svg_pixmap(icon_n,16,T("PRI"))); rl.addWidget(ic)
            cb=QCheckBox(lt); cb.setChecked(self.data.get(key,False))
            cb.setStyleSheet(f"QCheckBox{{color:{T('TXT')};font-size:10pt;background:transparent;spacing:8px;}}QCheckBox::indicator{{width:16px;height:16px;border-radius:4px;border:2px solid {T('BDR')};background:{T('CARD')};}}QCheckBox::indicator:checked{{background:{self.color};border:2px solid {self.color};}}")
            cb.stateChanged.connect(lambda s,k=key: self._tog_fixed(k,s))
            rl.addWidget(cb); rl.addStretch(); cl.addWidget(row)
        self._ew=QWidget(); self._ew.setStyleSheet("background:transparent;")
        self._el=QVBoxLayout(self._ew); self._el.setContentsMargins(0,0,0,0); self._el.setSpacing(3)
        cl.addWidget(self._ew); self._build_extra()
        ar=QHBoxLayout()
        ab=mk_btn("  항목 추가","#FEE2E2",T("RED"),9,6,"5px 12px","plus",T("RED"))
        ab.clicked.connect(self._add_extra); ar.addWidget(ab); ar.addStretch(); cl.addLayout(ar)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("수정", lambda: self._edit())
        menu.addAction("삭제", lambda: self._delete())
        menu.exec_(event.globalPos())

    def _edit(self):
        dlg=AddExamDialog(self.window(), initial=self.data)
        if dlg.exec_()==QDialog.Accepted and dlg.result_data:
            self.data.update(dlg.result_data)
            self._populate(); self.on_save(); self.changed.emit()

    def _build_extra(self):
        while self._el.count():
            i=self._el.takeAt(0)
            if i.widget(): i.widget().deleteLater()
        for task in self.data.get("extra_tasks",[]):
            row=QWidget(); row.setStyleSheet("background:transparent;")
            rl=QHBoxLayout(row); rl.setContentsMargins(0,0,0,0); rl.setSpacing(8)
            cb=QCheckBox(); cb.setChecked(task["done"])
            cb.setStyleSheet(f"QCheckBox::indicator{{width:16px;height:16px;border-radius:4px;border:2px solid {T('BDR')};background:{T('CARD')};}}QCheckBox::indicator:checked{{background:{self.color};border:2px solid {self.color};}}")
            cb.stateChanged.connect(lambda s,tid=task["id"]: self._tog_extra(tid,s))
            rl.addWidget(cb)
            sx="text-decoration:line-through;" if task["done"] else ""
            tl2=lbl(task["text"],10,False,T("SUB") if task["done"] else T("TXT"))
            tl2.setStyleSheet(tl2.styleSheet()+sx); rl.addWidget(tl2,1)
            xb=QPushButton("x"); xb.setFixedSize(20,20); xb.setCursor(Qt.PointingHandCursor)
            xb.setStyleSheet(f"QPushButton{{background:transparent;color:{T('SUB')};border:none;font-size:13pt;border-radius:10px;}}QPushButton:hover{{background:{T('RED')};color:white;}}")
            xb.clicked.connect(lambda _,tid=task["id"]: self._del_extra(tid))
            rl.addWidget(xb); self._el.addWidget(row)

    def _tog_fixed(self,key,state): self.data[key]=(state==Qt.Checked); self.on_save(); self.changed.emit()
    def _tog_extra(self,tid,state):
        for t in self.data.get("extra_tasks",[]):
            if t["id"]==tid: t["done"]=(state==Qt.Checked); break
        self.on_save(); self.changed.emit()
    def _add_extra(self):
        dlg=InputDialog("항목 추가","추가할 체크 항목을 입력하세요:",self.window())
        if dlg.exec_()==QDialog.Accepted and dlg.value:
            self.data.setdefault("extra_tasks",[]).append(new_task(dlg.value))
            self._build_extra(); self.on_save(); self.changed.emit()
    def _del_extra(self,tid):
        self.data["extra_tasks"]=[t for t in self.data.get("extra_tasks",[]) if t["id"]!=tid]
        self._build_extra(); self.on_save(); self.changed.emit()
    def _pick_color(self):
        c=QColorDialog.getColor(QColor(self.color),self.window(),"색상 선택")
        if c.isValid():
            self.color=c.name(); self.data["color"]=self.color
            self._bar.setStyleSheet(f"background:{self.color};border-radius:6px 0 0 6px;")
            self.on_save(); self.changed.emit()
    def _delete(self):
        dlg=ConfirmDialog("시험 삭제",f"'{self.data['subject']}' 시험을 삭제할까요?",
            ok_text="삭제",ok_color=T("RED"),parent=self.window())
        if dlg.exec_()==QDialog.Accepted:
            self.on_save()
            self.deleted.emit(self.data["id"])