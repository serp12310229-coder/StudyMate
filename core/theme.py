# core/theme.py
THEMES = {
    "mono": {
        "name":"모노크롬","BG":"#F2F2F2","CARD":"#FFFFFF",
        "PRI":"#5C5C5C","PRI_L":"#EBEBEB","GRN":"#6A9E7F","RED":"#C0605A",
        "ORG":"#B8885A","TXT":"#1A1A1A","SUB":"#888888","BDR":"#DEDEDE","GL":"#F8F8F8",
        "SUBJ":["#8A8A8A","#A09898","#7A8A8A","#8A7A8A","#8A8A7A","#9A8A8A","#7A8A7A","#8A9A8A"],
        "DDAY_FROM":"#DEDEDE","DDAY_TO":"#5C5C5C",
    },
    "pastel": {
        "name":"파스텔","BG":"#F2F2F2","CARD":"#FFFFFF",
        "PRI":"#A4DEAB","PRI_L":"#EDE9FF","GRN":"#6BBFA0","RED":"#E8909A",
        "ORG":"#F0B27A","TXT":"#2D2D3A","SUB":"#9090A8","BDR":"#E0D8F0","GL":"#FAF8FF",
        "SUBJ":["#9B8EC4","#E8909A","#6BBFA0","#F0B27A","#7EB8D4","#C4A0C8","#D4BC7A","#88C4C0"],
        "DDAY_FROM":"#F0F0F6","DDAY_TO":"#A4DEAB",
    },
}
_cur = dict(THEMES["mono"])

def T(k):   return _cur.get(k,"#888888")
def apply_theme(name):
    _cur.clear(); _cur.update(THEMES.get(name, THEMES["mono"]))
def apply_custom(ov):
    _cur.update(ov)
def current_snapshot():
    return dict(_cur)
def current_name():
    for k,v in THEMES.items():
        if v["BG"]==_cur.get("BG"): return k
    return "custom"
def subj_color(name, cmap):
    if name not in cmap:
        pal = _cur.get("SUBJ", THEMES["mono"]["SUBJ"])
        cmap[name] = pal[len(cmap) % len(pal)]
    return cmap[name]
def dk(c, a=18):
    h=c.lstrip("#"); r,g,b=int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
    return f"#{max(0,r-a):02x}{max(0,g-a):02x}{max(0,b-a):02x}"

# --- 추가 유틸리티 함수들 ---
def _hex_to_rgb(h):
    hh = h.lstrip("#")
    return int(hh[0:2],16), int(hh[2:4],16), int(hh[4:6],16)

def _rgb_to_hex(r,g,b):
    return f"#{r:02x}{g:02x}{b:02x}"

def _lerp(a, b, t):
    return int(a + (b - a) * t)

def lerp_color(c1, c2, t):
    r1,g1,b1 = _hex_to_rgb(c1); r2,g2,b2 = _hex_to_rgb(c2)
    return _rgb_to_hex(_lerp(r1,r2,t), _lerp(g1,g2,t), _lerp(b1,b2,t))

def is_dark(color, threshold="#B8B8B8"):
    r,g,b = _hex_to_rgb(color)
    thr_r,thr_g,thr_b = _hex_to_rgb(threshold)
    # 단순 평균 밝기 비교
    return (r+g+b)/3 < (thr_r+thr_g+thr_b)/3

def icon_color_on(bg_color):
    # 배경이 어두우면 흰색, 아니면 주요 색상 사용
    if is_dark(bg_color): return "white"
    return T("PRI")

def dday_color(days, max_days=14):
    """
    days: D-day 차이 (정수). None -> 보조 텍스트 색상 반환.
    max_days: 이 범위 이상이면 시작색(옅은 회색)에 가깝게.
    반환: 보간된 hex 색상 (string)
    """
    if days is None:
        return T("SUB")
    # 음수(기간 지남) 또는 0일: 종료색(DDAY_TO)
    try:
        d = int(days)
    except Exception:
        return T("SUB")
    if d <= 0:
        return _cur.get("DDAY_TO", T("PRI"))
    # 비율: 0 -> 0 (DDAY_TO), max_days+ -> 1 (DDAY_FROM)
    t = min(1.0, d / float(max_days))
    # 보간: t==1 -> DDAY_FROM (연한 색), t==0 -> DDAY_TO (주요 색)
    from_col = _cur.get("DDAY_FROM", T("BDR"))
    to_col   = _cur.get("DDAY_TO",   T("PRI"))
    # we want as days increase, color approach from_col, so lerp between to_col and from_col by t
    return lerp_color(to_col, from_col, t)