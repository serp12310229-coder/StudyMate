# core/data.py
import json, os, uuid
from core.theme import apply_theme, apply_custom

DATA_PATH = os.path.join(os.path.expanduser("~"), ".studymate.json")

def new_id():   return str(uuid.uuid4())
def new_task(text, done=False): return {"id":new_id(),"text":text,"done":done}
def calc_progress(tasks):
    if not tasks: return 0
    return int(sum(1 for t in tasks if t["done"]) / len(tasks) * 100)

def _default():
    return {
        "assignments":[], "exams":[], "deleted":[],
        "theme_name":"mono", "theme_custom":{},
        "widget_config":{"show_timer":True,"show_dday":True,"show_progress":True,"show_subject":True},
        "widget_pos":None, "always_on_top":False,
    }

def load():
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH,"r",encoding="utf-8") as f: d=json.load(f)
            apply_theme(d.get("theme_name","mono"))
            if d.get("theme_custom"): apply_custom(d["theme_custom"])
            for k,v in _default().items(): d.setdefault(k,v)
            return d
        except Exception: pass
    return _default()

def save(data):
    with open(DATA_PATH,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
