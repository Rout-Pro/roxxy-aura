import subprocess, time, sys, os
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(__file__))
import walk_lib as W

def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True).stdout

class Adb:
    def __init__(self):
        out = sh("adb shell wm size")
        self.screen_h = int(out.strip().split(":")[-1].strip().split("x")[1])
    def dump(self, name):
        for _ in range(3):
            sh("adb shell rm -f /sdcard/w.xml; rm -f out/walk_%s.xml; adb shell uiautomator dump /sdcard/w.xml >/dev/null 2>&1; adb pull /sdcard/w.xml out/walk_%s.xml >/dev/null 2>&1" % (name, name, name))
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
    def back(self): sh("adb shell input keyevent KEYCODE_BACK"); time.sleep(2)
    def scroll_down(self):
        h = self.screen_h; sh("adb shell input swipe 160 %d 160 %d 300" % (int(h * .7), int(h * .3))); time.sleep(1)

dev = Adb()
print("size h:", dev.screen_h)
status, detail = W.run(dev, print)
print("RESULT:", status, "-", detail)
print("NOT EXERCISED: remaining mandatory permission steps and the key gate")
