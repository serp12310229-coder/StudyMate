# ui/tabs.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore    import *
from PyQt5.QtGui     import *
from datetime        import datetime
from core.theme      import T, subj_color
from core.assets     import svg_icon, svg_pixmap
from ui.base_widgets import lbl, mk_btn, hdiv, ConfirmDialog
from ui.cards        import AssignmentCard, ExamCard
from ui.dialogs.add_assignment import AddAssignmentDialog
from ui.dialogs.add_exam       import AddExamDialog


def _sa(w):
    sc=QScrollArea(); sc.setWidgetResizable(True)
    sc.setStyleSheet(f"QScrollArea{{background:{T('BG')};border:none;}}"); sc.setWidget(w); return sc

def _empty(emoji,title,sub):
    w=QWidget(); w.setStyleSheet(f"background:{T('BG')};")
    vl=QVBoxLayout(w); vl.setAlignment(Qt.AlignCenter)
    for tx,sz,b,c in [(emoji,48,False,T("TXT")),(title,14,True,T("SUB")),(sub,10,False,T("SUB"))]:
        lb=lbl(tx,sz,b,c); lb.setAlignment(Qt.AlignCenter); vl.addWidget(lb)
    return w


class AssignmentTab(QWidget):
    refreshed=pyqtSignal()
    def __init__(self,data,on_save,parent=None):
        super().__init__(parent); self.data=data; self.on_save=on_save; self._cmap={}
        self.setStyleSheet(f"background:{T('BG')};")
        self._vl=QVBoxLayout(self); self._vl.setContentsMargins(0,0,0,0); self._vl.setSpacing(0)
        self._build()

    def _col(self,item):
        if item.get("color"): self._cmap[item["subject"]]=item["color"]; return item["color"]
        return subj_color(item["subject"],self._cmap)

    def _build(self):
        items=self.data.get("assignments",[])
        pending=sum(1 for a in items if a.get("tasks") and any(not t["done"] for t in a["tasks"]))
        tb=QWidget(); tb.setStyleSheet(f"background:{T('BG')};")
        tl=QHBoxLayout(tb); tl.setContentsMargins(24,18,24,12)
        tl.addWidget(lbl("과제 목록",16,True))
        tl.addWidget(lbl(f"  전체 {len(items)}  ·  진행 중 {pending}",10,False,T("SUB")))
        tl.addStretch()
        ab=mk_btn("  새 과제",T("PRI"),icon_name="plus",icon_color="white")
        ab.clicked.connect(self._add); tl.addWidget(ab); self._vl.addWidget(tb)
        if not items:
            self._vl.addWidget(_empty("📋","아직 과제가 없어요","위 버튼으로 과제를 추가해보세요"),1); return
        con=QWidget(); con.setStyleSheet(f"background:{T('BG')};")
        cl=QVBoxLayout(con); cl.setContentsMargins(20,8,20,20); cl.setSpacing(12)
        for a in items:
            card=AssignmentCard(a,self._col(a),self.on_save)
            card.deleted.connect(self._delete); card.changed.connect(self._changed); cl.addWidget(card)
        cl.addStretch(); self._vl.addWidget(_sa(con))

    def _rebuild(self):
        while self._vl.count():
            i=self._vl.takeAt(0)
            if i.widget(): i.widget().deleteLater()
        self._build()

    def _changed(self): self.on_save(); self.refreshed.emit()

    def _add(self):
        dlg=AddAssignmentDialog(self.window())
        if dlg.exec_()==QDialog.Accepted and dlg.result_data:
            self.data.setdefault("assignments",[]).append(dlg.result_data)
            self.on_save(); self._rebuild(); self.refreshed.emit()

    def _delete(self,aid):
        items=self.data.get("assignments",[])
        removed=next((a for a in items if a["id"]==aid),None)
        if removed:
            self.data["assignments"]=[a for a in items if a["id"]!=aid]
            self.data.setdefault("deleted",[]).append({**removed,"_deleted_at":datetime.now().strftime("%Y-%m-%d %H:%M")})
        self.on_save(); self._rebuild(); self.refreshed.emit()


class ExamTab(QWidget):
    refreshed=pyqtSignal()
    def __init__(self,data,on_save,parent=None):
        super().__init__(parent); self.data=data; self.on_save=on_save; self._cmap={}
        self.setStyleSheet(f"background:{T('BG')};")
        self._vl=QVBoxLayout(self); self._vl.setContentsMargins(0,0,0,0); self._vl.setSpacing(0)
        self._build()

    def _col(self,item):
        if item.get("color"): self._cmap[item["subject"]]=item["color"]; return item["color"]
        return subj_color(item["subject"],self._cmap)

    def _build(self):
        items=self.data.get("exams",[])
        tb=QWidget(); tb.setStyleSheet(f"background:{T('BG')};")
        tl=QHBoxLayout(tb); tl.setContentsMargins(24,18,24,12)
        tl.addWidget(lbl("시험공부 관리",16,True))
        tl.addWidget(lbl(f"  전체 {len(items)}",10,False,T("SUB")))
        tl.addStretch()
        ab=mk_btn("  새 시험",T("RED"),icon_name="plus",icon_color="white")
        ab.clicked.connect(self._add); tl.addWidget(ab); self._vl.addWidget(tb)
        if not items:
            self._vl.addWidget(_empty("📚","아직 시험 일정이 없어요","위 버튼으로 시험을 추가해보세요"),1); return
        con=QWidget(); con.setStyleSheet(f"background:{T('BG')};")
        cl=QVBoxLayout(con); cl.setContentsMargins(20,8,20,20); cl.setSpacing(12)
        for e in items:
            card=ExamCard(e,self._col(e),self.on_save)
            card.deleted.connect(self._delete); card.changed.connect(self._changed); cl.addWidget(card)
        cl.addStretch(); self._vl.addWidget(_sa(con))

    def _rebuild(self):
        while self._vl.count():
            i=self._vl.takeAt(0)
            if i.widget(): i.widget().deleteLater()
        self._build()

    def _changed(self): self.on_save(); self.refreshed.emit()

    def _add(self):
        dlg=AddExamDialog(self.window())
        if dlg.exec_()==QDialog.Accepted and dlg.result_data:
            self.data.setdefault("exams",[]).append(dlg.result_data)
            self.on_save(); self._rebuild(); self.refreshed.emit()

    def _delete(self,eid):
        items=self.data.get("exams",[])
        removed=next((e for e in items if e["id"]==eid),None)
        if removed:
            self.data["exams"]=[e for e in items if e["id"]!=eid]
            self.data.setdefault("deleted",[]).append({**removed,"_deleted_at":datetime.now().strftime("%Y-%m-%d %H:%M")})
        self.on_save(); self._rebuild(); self.refreshed.emit()


class TrashTab(QWidget):
    refreshed=pyqtSignal()
    def __init__(self,data,on_save,parent=None):
        super().__init__(parent); self.data=data; self.on_save=on_save
        self.setStyleSheet(f"background:{T('BG')};")
        self._vl=QVBoxLayout(self); self._vl.setContentsMargins(0,0,0,0); self._vl.setSpacing(0)
        self._build()

    def _build(self):
        items=self.data.get("deleted",[])
        tb=QWidget(); tb.setStyleSheet(f"background:{T('BG')};")
        tl=QHBoxLayout(tb); tl.setContentsMargins(24,18,24,12)
        ic=QLabel(); ic.setPixmap(svg_pixmap("delete",20,T("RED"))); tl.addWidget(ic)
        tl.addWidget(lbl("휴지통",16,True))
        tl.addWidget(lbl(f"  {len(items)}개",10,False,T("SUB")))
        tl.addStretch()
        if items:
            clr=mk_btn("  전체 삭제",T("RED"),icon_name="delete",icon_color="white")
            clr.clicked.connect(self._clear_all); tl.addWidget(clr)
        self._vl.addWidget(tb)
        if not items:
            self._vl.addWidget(_empty("🗑","휴지통이 비어있어요","삭제된 과제/시험이 여기에 표시됩니다"),1); return
        con=QWidget(); con.setStyleSheet(f"background:{T('BG')};")
        cl=QVBoxLayout(con); cl.setContentsMargins(20,8,20,20); cl.setSpacing(10)
        for item in items:
            row=QFrame()
            row.setStyleSheet(f"QFrame{{background:{T('CARD')};border-radius:12px;border:1.5px solid {T('BDR')};}}")
            rl=QHBoxLayout(row); rl.setContentsMargins(16,12,16,12); rl.setSpacing(10)
            name=item.get("name") or item.get("subject","")
            rl.addWidget(lbl(name,11,True))
            rl.addWidget(lbl(item.get("subject",""),10,False,T("SUB")))
            rl.addStretch()
            rl.addWidget(lbl(item.get("_deleted_at",""),9,False,T("SUB")))
            xb=QPushButton(); xb.setFixedSize(26,26); xb.setCursor(Qt.PointingHandCursor)
            xb.setIcon(svg_icon("delete",14,T("RED"))); xb.setIconSize(QSize(14,14))
            xb.setStyleSheet(f"QPushButton{{background:transparent;border:none;border-radius:13px;}}QPushButton:hover{{background:#FEE2E2;}}")
            xb.clicked.connect(lambda _,iid=item.get("id",""): self._del_one(iid))
            rl.addWidget(xb); cl.addWidget(row)
        cl.addStretch(); self._vl.addWidget(_sa(con))

    def _rebuild(self):
        while self._vl.count():
            i=self._vl.takeAt(0)
            if i.widget(): i.widget().deleteLater()
        self._build()

    def _del_one(self,iid):
        self.data["deleted"]=[d for d in self.data.get("deleted",[]) if d.get("id")!=iid]
        self.on_save(); self._rebuild(); self.refreshed.emit()

    def _clear_all(self):
        dlg=ConfirmDialog("전체 삭제","휴지통의 모든 항목을 영구 삭제할까요?\n이 작업은 되돌릴 수 없습니다.",
            ok_text="전체 삭제",ok_color=T("RED"),icon_name="delete",parent=self.window())
        if dlg.exec_()==QDialog.Accepted:
            self.data["deleted"]=[]; self.on_save(); self._rebuild(); self.refreshed.emit()
