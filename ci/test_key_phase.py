import os, sys, tempfile, unittest, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import key_phase, shot_lib
from shot_lib import Stop

FAKE_KEY = "AQ.FAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKE0123456789"  # synthetic, not a real credential
SCREENS = {
 "gate": {"bring your own gemini key", "verify key", "gemini api key"},
 "verified": {"key verified", "next"},
 "step9": {"banking & sensitive guard", "launch roxxy", "scanning apps"},
 "step9done": {"banking & sensitive guard", "launch roxxy", "no sensitive apps"},
 "home": {"talk to roxxy"},
 "err": {"invalid api key", "verify key"},
}
class Dev:
    def __init__(self, script, tmp):
        self.script, self.cur, self.typed, self.taps, self.tmp, self.n = script, "gate", [], [], tmp, 0
        self.shots = {}
    def focus(self): return (shot_lib.APP, "com.roxxy.aura.MainActivity")
    def sleep(self, s): pass
    def back(self): pass
    def tap_xy(self, x, y):
        self.taps.append(self.cur); self.cur = self.script.get(self.cur, self.cur)
    def type_secret(self, k): self.typed.append(k)
    def _w(self, p):
        self.n += 1
        Image.new("RGB", (4 + self.n, 4)).save(p); self.shots[os.path.basename(p)] = self.cur; return p
    def shot(self, name):
        return self._w(os.path.join(self.tmp, "out_%s.png" % name))
    def shot_to(self, p): return self._w(p)
def finder(dev):
    def f(png, ph, loose=False):
        return [(10, 10, 95)] if ph in SCREENS[dev.shots[os.path.basename(png)]] else []
    return f

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); key_phase.PRIVATE = os.path.join(self.tmp, "priv"); os.environ[key_phase.KEY_ENV] = FAKE_KEY
        self.logs = []
    def tearDown(self): shutil.rmtree(self.tmp)
    def run_it(self, script, start="gate"):
        d = Dev(script, self.tmp); d.cur = start
        try:
            return d, key_phase.run_key_phase(d, self.logs.append, finder(d))
        finally:
            key_phase.wipe_private()
    def test_happy_path(self):
        d, cls = self.run_it({"gate": "gate", "gate2": "x"}) if False else (None, None)
        script = {"gate": "gate"}
        # tap sequence: field label (stay), Verify -> verified, Next -> step9, Launch -> home
        d = Dev(None, self.tmp); seq = iter(["gate", "verified", "step9done", "home"])
        d.tap_xy = lambda x, y: (d.taps.append(d.cur), setattr(d, "cur", next(seq)))
        d.cur = "gate"
        try:
            cls = key_phase.run_key_phase(d, self.logs.append, finder(d))
        finally:
            key_phase.wipe_private()
        self.assertEqual(cls, "classifier_none_flagged"); self.assertEqual(d.typed, [FAKE_KEY])
        self.assertFalse(any(FAKE_KEY in l for l in self.logs))
        self.assertFalse(os.path.exists(key_phase.PRIVATE))
        persisted = [f for f in os.listdir(self.tmp) if f.endswith(".png")]
        self.assertEqual(persisted, ["out_k9_home.png"])  # only the Home capture is persisted
    def test_verify_error_stops(self):
        d = Dev(None, self.tmp); seq = iter(["gate", "err"]); d.tap_xy = lambda x, y: setattr(d, "cur", next(seq))
        with self.assertRaises(Stop):
            try: key_phase.run_key_phase(d, self.logs.append, finder(d))
            finally: key_phase.wipe_private()
        self.assertEqual([f for f in os.listdir(self.tmp) if f.endswith(".png")], [])
    def test_unknown_ui_stops(self):
        d = Dev({}, self.tmp); d.cur = "home"
        with self.assertRaises(Stop): key_phase.run_key_phase(d, self.logs.append, finder(d))
    def test_no_key_stops(self):
        os.environ[key_phase.KEY_ENV] = ""
        d = Dev({}, self.tmp)
        with self.assertRaises(Stop): key_phase.run_key_phase(d, self.logs.append, finder(d))
if __name__ == "__main__": unittest.main()
