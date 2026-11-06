"""Find a phrase on a screenshot with tesseract. Used when uiautomator dumps are unavailable.
Returns every match as (cx, cy, mean_conf) in ORIGINAL screenshot pixels. Callers must require
exactly one match before tapping."""
import re, subprocess, tempfile, os
from PIL import Image

def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())

_CACHE = {}
def words(png, scale=3):
    st = os.stat(png); key = (os.path.abspath(png), st.st_size, st.st_mtime_ns, scale)
    if key not in _CACHE: _CACHE[key] = _words(png, scale)
    return _CACHE[key]

def _words(png, scale=3):
    im = Image.open(png).convert("L"); w, h = im.size
    im = im.resize((w * scale, h * scale), Image.LANCZOS)
    fd, tmp = tempfile.mkstemp(suffix=".png"); os.close(fd)
    try:
        im.save(tmp)
        out = subprocess.run(["tesseract", tmp, "-", "--psm", "11", "tsv"], capture_output=True, text=True, timeout=60).stdout
    finally:
        os.remove(tmp)
    res = []
    for line in out.splitlines()[1:]:
        c = line.split("\t")
        if len(c) < 12 or not c[11].strip(): continue
        try: conf = float(c[10])
        except ValueError: continue
        t = norm(c[11])
        if not t or conf < 0: continue
        l, tp, ww, hh = (int(c[6]), int(c[7]), int(c[8]), int(c[9]))
        res.append({"line": (c[2], c[3], c[4]), "t": t, "conf": conf, "l": l / scale, "t0": tp / scale, "w": ww / scale, "h": hh / scale})
    return res

def find_phrase(png, phrase, min_conf=50, scale=3, exact_line=True):
    """exact_line: the phrase must be the whole OCR line (optionally after a step number like '1/2:'),
    so a sentence that merely contains the words does not count."""
    toks = [norm(x) for x in phrase.split() if norm(x)]
    ws = words(png, scale); hits = []
    for i in range(len(ws) - len(toks) + 1):
        seq = ws[i:i + len(toks)]
        if [s["t"] for s in seq] != toks: continue
        if min(s["conf"] for s in seq) < min_conf: continue
        if exact_line:
            if len({s["line"] for s in seq}) != 1: continue
            others = [w for w in ws if w["line"] == seq[0]["line"] and w not in seq]
            if any(not (re.fullmatch(r"\d{1,2}", w["t"]) and w["l"] < seq[0]["l"]) for w in others): continue
        cy0 = seq[0]["t0"] + seq[0]["h"] / 2
        if any(abs((s["t0"] + s["h"] / 2) - cy0) > max(8, seq[0]["h"]) for s in seq): continue
        x1 = min(s["l"] for s in seq); x2 = max(s["l"] + s["w"] for s in seq)
        y1 = min(s["t0"] for s in seq); y2 = max(s["t0"] + s["h"] for s in seq)
        hits.append((round((x1 + x2) / 2), round((y1 + y2) / 2), round(sum(s["conf"] for s in seq) / len(seq))))
    return hits
