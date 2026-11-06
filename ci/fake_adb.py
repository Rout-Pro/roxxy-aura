#!/usr/bin/env python3
"""Scripted fake adb for local end-to-end tests of ci/startup_check.sh -> walk.py -> adb adapter.
State lives in $FAKE_DIR; graph in $FAKE_DIR/graph.json. Dumps come from saved real dumps or synthetic XML."""
import json, os, re, shutil, sys
import xml.etree.ElementTree as ET
D = os.environ["FAKE_DIR"]; G = json.load(open(os.path.join(D, "graph.json")))
st_path = os.path.join(D, "state.json")
st = json.load(open(st_path)) if os.path.exists(st_path) else {"state": G["start"], "dumps": 0}
def save(): json.dump(st, open(st_path, "w"))
dev = os.path.join(D, "dev"); os.makedirs(dev, exist_ok=True)
a = sys.argv[1:]
def log(): open(os.path.join(D, "calls.log"), "a").write(" ".join(a) + "\n")
log()
def xml_path(): return os.path.join(D, G["states"][st["state"]]["xml"])
def go(key):
    nxt = G["states"][st["state"]].get("trans", {}).get(key)
    if nxt: st["state"] = nxt
    save()
def key_at(x, y):
    r = ET.parse(xml_path()).getroot(); best = None
    for n in r.iter("node"):
        if n.get("clickable") != "true" and n.get("checkable") != "true": continue
        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", n.get("bounds", ""))
        if not m: continue
        x1, y1, x2, y2 = map(int, m.groups())
        if x1 <= x <= x2 and y1 <= y <= y2:
            area = (x2 - x1) * (y2 - y1)
            if best is None or area < best[0]: best = (area, n)
    if best is None: return None
    n = best[1]
    if n.get("checkable") == "true": return "CHECK"
    if n.get("text"): return n.get("text")
    for d in n.iter("node"):
        if d.get("text"): return d.get("text")
if a[:2] == ["shell", "wm"]: print(G.get("wm_size", "Physical size: 320x640"))
elif a[0] == "install": print(G.get("install_out", "Success"))
elif a[:2] == ["logcat", "-c"]: pass
elif a[:2] == ["logcat", "-d"]: print(G.get("logcat", "I ActivityManager: ok"))
elif a[:2] == ["shell", "monkey"]: print("Events injected: 1"); st["state"] = G["start"]; save()
elif a[:2] == ["shell", "pidof"]:
    if G.get("pid", "4227"): print(G.get("pid", "4227"))
elif a[:3] == ["shell", "rm", "-f"]:
    p = os.path.join(dev, os.path.basename(a[3]))
    if os.path.exists(p): os.remove(p)
elif a[:3] == ["shell", "uiautomator", "dump"]:
    st["dumps"] += 1; save()
    if st["state"] in G.get("dump_fails_in", []): print("ERROR: could not get idle state.")
    else: shutil.copy(xml_path(), os.path.join(dev, os.path.basename(a[3])))
elif a[0] == "pull":
    p = os.path.join(dev, os.path.basename(a[1]))
    if not os.path.exists(p): print("adb: error: remote object does not exist", file=sys.stderr); sys.exit(1)
    shutil.copy(p, a[2])
elif a[:2] == ["exec-out", "screencap"]:
    cur = G["states"][st["state"]]
    if cur.get("shot_empty"): pass
    elif st["state"] in G.get("stale_in", []) and st.get("last_png"):
        sys.stdout.buffer.write(open(st["last_png"], "rb").read())
    elif cur.get("png"):
        p = os.path.join(D, cur["png"]); st["last_png"] = p; save(); sys.stdout.buffer.write(open(p, "rb").read())
    else: sys.stdout.buffer.write(b"\x89PNG-fake-" + st["state"].encode())
elif a[:3] == ["shell", "getprop", "ro.product.cpu.abilist"]: print(G.get("abilist", "x86_64"))
elif a[:3] == ["shell", "getprop", "ro.build.version.sdk"]: print(G.get("sdk", "33"))
elif a[:3] == ["shell", "dumpsys", "package"]: print("    versionCode=559 minSdk=26\n    primaryCpuAbi=" + G.get("primary_abi", "x86_64") + "\n    secondaryCpuAbi=null")
elif a[0] == "shell" and len(a) > 1 and a[1].startswith("grep -c ndk_translation"): print(G.get("translation_maps", "0"))
elif a[:2] == ["shell", "dumpsys"]:
    f = G["states"][st["state"]].get("focus")
    print("  mCurrentFocus=Window{1a2b u0 %s}" % f if f else "  mCurrentFocus=null")
elif a[:3] == ["shell", "input", "tap"]:
    cur = G["states"][st["state"]]
    if "taps" in cur:  # screenshot-driven states: tap boxes instead of dump nodes
        x, y = int(a[3]), int(a[4])
        for x1, y1, x2, y2, to in cur["taps"]:
            if x1 <= x <= x2 and y1 <= y <= y2: st["state"] = to; save(); break
    else:
        k = key_at(int(a[3]), int(a[4])); go(k) if k else None
elif a[:3] == ["shell", "input", "keyevent"]: go("BACK")
elif a[:3] == ["shell", "input", "swipe"]: go("SWIPE")
else: print("fake adb: unhandled " + " ".join(a), file=sys.stderr); sys.exit(2)
