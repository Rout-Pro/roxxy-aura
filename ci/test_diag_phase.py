import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import diag_phase, shot_lib
class Dev:
    def __init__(self, pids, fg):
        self.pids, self.fg, self.shots, self.n = list(pids), fg, {}, 0
    tapped = False
    def focus(self): return self.fg if self.tapped else APP
    def sleep(self, s): pass
    def tap_xy(self, x, y): self.tapped = True
    def shot(self, name):
        self.n += 1; p = os.path.join(self.tmp, name + ".png"); Image.new("RGB", (4 + self.n, 4)).save(p); return p
    def run(self, c):
        if "pidof" in c: return self.pids.pop(0)
        if "exit-info" in c: return "ApplicationExitInfo:\n  pid=1 reason=4 (CRASH)\n  description=SECRETLOOKING sk-abc\n  something else\n"
        if "logcat" in c: return "am_proc_died: [0,6697,com.roxxy.aura,0,0]\nother line with data\n"
APP = (shot_lib.APP, "com.roxxy.aura.MainActivity")
find = lambda png, ph, loose=False: [(5, 5, 95)]
class T(unittest.TestCase):
    def go(self, dev):
        dev.tmp = tempfile.mkdtemp(); logs = []
        r = diag_phase.run_diag(dev, logs.append, find, out=dev.tmp); return r, dev.tmp
    def test_survived(self):
        r, d = self.go(Dev(["100\n", "100\n"], APP)); self.assertEqual(r[0], "SURVIVED")
    def test_changed_pid(self):
        r, d = self.go(Dev(["100\n", "200\n"], APP)); self.assertEqual(r[0], "CHANGED")
    def test_changed_foreground(self):
        r, d = self.go(Dev(["100\n", "100\n"], ("com.google.android.apps.nexuslauncher", "x.NexusLauncherActivity"))); self.assertEqual(r[0], "CHANGED")
    def test_scrub_drops_unlisted(self):
        r, d = self.go(Dev(["100\n", "100\n"], APP))
        t = open(os.path.join(d, "diag_exit_info.txt")).read()
        self.assertIn("reason=4", t); self.assertNotIn("something else", t)
        ev = open(os.path.join(d, "diag_events.txt")).read()
        self.assertIn("am_proc_died", ev); self.assertNotIn("other line", ev)
if __name__ == "__main__": unittest.main()
