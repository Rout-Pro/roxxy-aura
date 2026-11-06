import subprocess,time,re
import xml.etree.ElementTree as ET
def sh(c): return subprocess.run(c,shell=True,capture_output=True,text=True).stdout
def dump(n):
    sh("adb shell uiautomator dump /sdcard/w.xml >/dev/null 2>&1; adb pull /sdcard/w.xml out/walk_%s.xml >/dev/null 2>&1"%n)
    sh("adb exec-out screencap -p > out/walk_%s.png"%n)
    try: return ET.parse("out/walk_%s.xml"%n).getroot()
    except Exception: return ET.fromstring("<hierarchy/>")
def box(nd):
    m=re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",nd.get("bounds","")); return tuple(map(int,m.groups())) if m else None
def tap(nd):
    a,b,c,d=box(nd); sh("adb shell input tap %d %d"%((a+c)//2,(b+d)//2)); time.sleep(3)
def texts(r): return [n.get("text") for n in r.iter("node") if n.get("text")]
def find_text(r,t):
    for n in r.iter("node"):
        if n.get("text")==t: return n
def clickable_for(r,t):
    best=[None]
    def walk(n,anc):
        for ch in n:
            na=anc+[ch]
            if ch.get("text")==t:
                for a in reversed(na):
                    if a.get("clickable")=="true": best[0]=a;return True
                best[0]=ch;return True
            if walk(ch,na): return True
        return False
    walk(r,[r]); return best[0]
def in_app(r): return any(n.get("package")=="com.roxxy.aura" for n in r.iter("node"))
print("size:",sh("adb shell wm size").strip())
r=dump("1"); print("1 landing",texts(r)[:6])
n=clickable_for(r,"Get Started")
if n is None: print("STOP: no Get Started"); raise SystemExit
tap(n)
r=dump("2"); print("2 policy",texts(r)[:10])
cbs=[n for n in r.iter("node") if n.get("checkable")=="true"]
print("checkable nodes:",[(n.get("class"),n.get("checked"),n.get("bounds")) for n in cbs])
btn=clickable_for(r,"Accept Terms")
if btn is not None: print("button label before tick:",btn.get("text") or [t for t in texts(r) if t in ("Accept Terms","I Understand")],"| enabled:",btn.get("enabled"),"bounds",btn.get("bounds"))
if not cbs: print("STOP: agreement checkbox not found in dump"); raise SystemExit
print("agreement bounds",cbs[0].get("bounds")); tap(cbs[0])
r=dump("3_agreement_checked")
cbs=[n for n in r.iter("node") if n.get("checkable")=="true"]
print("after tap checked:",[n.get("checked") for n in cbs])
if not cbs or cbs[0].get("checked")!="true": print("STOP: agreement did not become checked"); raise SystemExit
b=find_text(r,"I Understand"); b=b if b is not None else find_text(r,"Accept Terms"); print("button label after tick:",b.get("text") if b is not None else None)
if b is None: print("STOP: no policy button"); raise SystemExit
tap(clickable_for(r,b.get("text")))
r=dump("4_after_policy"); print("4 after policy",texts(r)[:12])
# Stages after policy: tap the dump's own "Next" until the first stage without one (a permission step).
r=dump("5_stage")
for k in range(6,10):
    t=texts(r); print("stage",t[:10])
    if any(x in t for x in ("Verify Key","Bring your own Gemini key")):
        print("REACHED key step; stopping (no key entered)"); raise SystemExit
    if find_text(r,"Next") is None: break
    tap(clickable_for(r,"Next")); r=dump("%d_stage"%k)
print("FIRST MANDATORY PERMISSION STEP (no Next button):",texts(r)[:10])
sw=[n for n in r.iter("node") if n.get("checkable")=="true"]
print("switches:",[(n.get("checked"),n.get("bounds")) for n in sw])
if sw:
    tap(sw[0]); r=dump("perm_row_tapped")
    print("after tapping first row once; in_app:",in_app(r),texts(r)[:8])
    if not in_app(r):
        sh("adb shell input keyevent KEYCODE_BACK"); time.sleep(2); r=dump("perm_back")
        print("after BACK; in_app:",in_app(r),texts(r)[:8])
print("STOP: remaining mandatory permission steps and key gate not exercised")
