import subprocess, time, sys, os
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(__file__))
import walk_lib as W
import shot_lib

def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True).stdout

def dump_cmd(name):
    """Shell command for one UI dump; removes the stale device and local copies first."""
    out = "out/walk_%s.xml" % name
    return ("adb shell rm -f /sdcard/w.xml; rm -f %s; adb shell uiautomator dump /sdcard/w.xml >/dev/null 2>&1; "
            "adb pull /sdcard/w.xml %s >/dev/null 2>&1" % (out, out))

class Adb:
    def __init__(self):
        out = sh("adb shell wm size")
        self.screen_h = int(out.strip().split(":")[-1].strip().split("x")[1])
    def dump(self, name):
        for _ in range(5):
            sh(dump_cmd(name))
            try:
                r = ET.parse("out/walk_%s.xml" % name).getroot()
                if len(list(r.iter("node"))) > 0:
                    break
            except Exception:
                r = ET.fromstring("<hierarchy/>")
            time.sleep(2)
        sh("adb exec-out screencap -p > out/walk_%s.png" % name)
        return r
    def tap(self, nd):
        a, b, c, d = W.box(nd); sh("adb shell input tap %d %d" % ((a + c) // 2, (b + d) // 2)); time.sleep(3)
    def sleep(self, n): time.sleep(n)
    def focus(self):
        return shot_lib.parse_focus(sh("adb shell dumpsys window | grep mCurrentFocus"))
    def shot(self, name):
        """Fresh capture: local copy removed first; returns the path or None if nothing was written."""
        p = "out/shot_%s.png" % name
        sh("rm -f %s; adb exec-out screencap -p > %s" % (p, p))
        return p if os.path.exists(p) and os.path.getsize(p) > 0 else None
    def shot_to(self, p):
        sh("rm -f %s; adb exec-out screencap -p > %s" % (p, p))
        return p if os.path.exists(p) and os.path.getsize(p) > 0 else None
    def type_secret(self, key):
        # argv only, output discarded: the value is never echoed by a shell or logged
        subprocess.run(["adb", "shell", "input", "text", key], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        time.sleep(1)
    def tap_xy(self, x, y): sh("adb shell input tap %d %d" % (x, y)); time.sleep(3)
    def after_consent(self, log): return shot_lib.run_after_consent(self, log)
    def back(self): sh("adb shell input keyevent KEYCODE_BACK"); time.sleep(2)
    def scroll_down(self):
        h = self.screen_h; sh("adb shell input swipe 160 %d 160 %d 300" % (int(h * .7), int(h * .3))); time.sleep(1)

if __name__ == "__main__":
    dev = Adb()
    print("size h:", dev.screen_h)
    status, detail = W.run(dev, print)
    if status == "GATE":
        import key_phase
        try:
            cls = key_phase.run_key_phase(dev, print)
            status, detail = "PASS", "key verified, step 9 (%s), Home reached" % cls
            try:
                sh("adb shell am force-stop com.roxxy.aura; adb shell monkey -p com.roxxy.aura -c android.intent.category.LAUNCHER 1"); time.sleep(12)
                s2 = shot_lib.Shots(dev, print); rp = s2.capture("k10_restart", "app")
                s2.unique(rp, "talk to roxxy", loose=True); s2.absent(rp, "bring your own gemini key")
                detail += "; after force-stop+relaunch app opens on Home without the key gate (stored-key read not directly observed)"
            except shot_lib.Stop as e:
                status, detail = "FAIL", "restart check stopped: %s" % e
        except shot_lib.Stop as e:
            status, detail = "FAIL", "key phase stopped: %s" % e
        finally:
            key_phase.wipe_private()
        print("RESULT:", status, "-", detail)
        print("NOT EXERCISED: any AI task response, overlay, voice, ARM hardware, user device")
        sys.exit(0 if status == "PASS" else 1)
    print("RESULT:", status, "-", detail)
    print("NOT EXERCISED: anything after the key gate; nothing is entered there")
    sys.exit(0 if status == "STOP" else 1)
