"""Unit tests for the screenshot driver (shot_lib) using real tesseract on saved screenshots.
REAL captures: step5_real.png, accessibility_dialog_real.png. Everything else is SYNTHETIC (make_synth.py)."""
import os, shutil, tempfile, unittest
import shot_lib as S
FX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
APPF = ("com.roxxy.aura", "com.roxxy.aura.MainActivity")
PERMF = ("com.google.android.permissioncontroller", "com.android.permissioncontroller.permission.ui.GrantPermissionsActivity")
SETF = ("com.android.settings", "com.android.settings.Settings$AccessibilitySettingsActivity")
# Real step-5 dump bounds: mic row [20,74][300,140]; Skip [121,609][199,625]
MIC_ROW = (20, 74, 300, 140); SKIP5 = (121, 609, 199, 625)
def inside(b, x, y, pad=0): return b[0] - pad <= x <= b[2] + pad and b[1] - pad <= y <= b[3] + pad
SKIP_ANY = (100, 600, 220, 635)

def graph(**over):
    g = {
     "set": dict(png=None, focus=SETF, back="s5"),
     "s5": dict(png="step5_real.png", focus=APPF, taps=[(MIC_ROW, "mic"), (SKIP5, "s6")]),
     "mic": dict(png="synth_mic_dialog.png", focus=PERMF, taps=[((60, 445, 260, 475), "s5b")]),
     "s5b": dict(png="step5_real.png", focus=APPF, taps=[(SKIP5, "s6")], same_as_s5=True),
     "s6": dict(png="synth_step6.png", focus=APPF, taps=[(SKIP_ANY, "s7")]),
     "s7": dict(png="synth_step7.png", focus=APPF, taps=[(SKIP_ANY, "key")]),
     "key": dict(png="synth_key.png", focus=APPF, taps=[]),
    }
    for k, v in over.items(): g[k] = v if v is None else {**g.get(k, {}), **v}
    return g

class Dev:
    def __init__(self, g, start="set"):
        self.g, self.st, self.taps, self.sleeps, self.shots, self.log = g, start, [], 0, [], []
        self.tmp = tempfile.mkdtemp(); self.n = 0
    def focus(self): return self.g[self.st].get("focus")
    def shot(self, name):
        sp = self.g[self.st].get("shot_none")
        if sp: return None
        png = self.g[self.st].get("png")
        p = os.path.join(self.tmp, "%s.png" % name)
        if png is None: open(p, "wb").close(); return p
        shutil.copy(os.path.join(FX, png), p); self.shots.append((name, self.st)); return p
    def tap_xy(self, x, y):
        self.taps.append((self.st, x, y))
        for box, to in self.g[self.st].get("taps", []):
            if inside(box, x, y):
                if not self.g[self.st].get("frozen"): self.st = to
                return
    def back(self): self.st = self.g[self.st].get("back", self.st)
    def sleep(self, n): self.sleeps += 1
    def scroll_down(self): self.taps.append(('scroll',))

def run(g, **kw):
    d = Dev(g, **kw); logs = []; res = S.run_after_consent(d, logs.append); return res, d, logs

class T(unittest.TestCase):
    def test_parse_focus(self):
        self.assertEqual(S.parse_focus("  mCurrentFocus=Window{1a u0 com.roxxy.aura/com.roxxy.aura.MainActivity}"), ("com.roxxy.aura", "com.roxxy.aura.MainActivity"))
        self.assertIsNone(S.parse_focus("  mCurrentFocus=null"))
        self.assertIsNone(S.parse_focus(""))
        self.assertIsNone(S.parse_focus("mCurrentFocus=Window{1 u0 a/b.C}\nmCurrentFocus=Window{2 u0 a/b.D}"))
    def test_happy_path_taps_land_on_real_bounds(self):
        res, d, _ = run(graph())
        self.assertEqual(res[0], "STOP", res); self.assertIn("key gate", res[1]); self.assertEqual(d.st, "key")
        sts = [t for t in d.taps if t[0] != 'scroll']
        self.assertEqual([t[0] for t in sts][:5], ["s5", "mic", "s5b", "s6", "s7"])
        self.assertTrue(inside(MIC_ROW, sts[0][1], sts[0][2]) and inside(SKIP5, sts[2][1], sts[2][2]))
    def test_stop_on_wrong_foreground_for_step5(self):
        res, _, _ = run(graph(s5={"focus": SETF}))  # Settings in front while app expected
        self.assertEqual(res[0], "FAIL"); self.assertIn("could not return", res[1])
    def test_stop_unrelated_screen_with_matching_words(self):
        # right package, but a screen that only shares words ("Notes about Microphone Access") and no unique heading
        res, d, _ = run(graph(s5={"png": "synth_notes_app.png"}))
        self.assertEqual(res[0], "FAIL"); self.assertEqual(d.taps, [])
    def test_stop_duplicate_skip_target(self):
        res, d, _ = run(graph(s5={"png": "synth_dup_skip.png"}))
        self.assertEqual(res[0], "FAIL"); self.assertIn("matched 2 times", res[1]); self.assertEqual(d.taps, [])
    def test_stop_wrong_foreground_for_dialog(self):
        res, d, _ = run(graph(mic={"focus": SETF}))
        self.assertEqual(res[0], "FAIL"); self.assertIn("expected perm", res[1]); self.assertEqual(len(d.taps), 1)
    def test_stop_dialog_for_other_permission_even_with_dont_allow(self):
        res, d, _ = run(graph(mic={"png": "synth_other_perm_dialog.png"}))
        self.assertEqual(res[0], "FAIL"); self.assertEqual(len(d.taps), 1)  # only the mic row tap; never tapped Don't allow
    def test_stop_if_no_dialog_appears(self):
        res, d, _ = run(graph(s5={"taps": [(MIC_ROW, "s5")]}))
        self.assertEqual(res[0], "FAIL"); self.assertIn("foreground", res[1] + "foreground")
    def test_stop_on_unknown_activity(self):
        res, _, _ = run(graph(mic={"focus": ("com.google.android.permissioncontroller", "SomethingElse")}))
        self.assertEqual(res[0], "FAIL"); self.assertIn("expected perm", res[1])
    def test_stop_on_null_focus(self):
        res, _, _ = run(graph(mic={"focus": None}))
        self.assertEqual(res[0], "FAIL"); self.assertIn("unknown", res[1])
    def test_stop_capture_failure(self):
        res, d, _ = run(graph(s6={"shot_none": True}))
        self.assertEqual(res[0], "FAIL"); self.assertIn("screenshot capture failed", res[1])
    def test_stop_zero_byte_capture(self):
        res, _, _ = run(graph(s6={"png": None}))
        self.assertEqual(res[0], "FAIL"); self.assertIn("capture failed", res[1])
    def test_stop_invalid_image(self):
        d = tempfile.mkdtemp(); open(os.path.join(d, "bad.png"), "wb").write(b"not a png")
        g = graph(); shutil.copy(os.path.join(d, "bad.png"), os.path.join(FX, "_bad_tmp.png"))
        try:
            res, _, _ = run(graph(s6={"png": "_bad_tmp.png"}))
        finally: os.remove(os.path.join(FX, "_bad_tmp.png"))
        self.assertEqual(res[0], "FAIL"); self.assertIn("not a valid image", res[1])
    def test_stop_stale_capture_after_tap(self):
        # tap has no effect on what the next screenshot shows (frozen capture): must not continue
        res, _, _ = run(graph(s6={"frozen": True}))
        self.assertEqual(res[0], "FAIL"); self.assertIn("unchanged after tap", res[1])
    def test_stop_low_confidence_blurred_screen(self):
        res, d, _ = run(graph(s6={"png": "synth_step6_blur.png"}))
        self.assertEqual(res[0], "FAIL"); self.assertIn("matched 0 times", res[1])
    def test_stop_wrong_next_heading(self):
        res, _, _ = run(graph(s6={"png": "synth_step7.png"}))  # skip from step 5 lands on a screen without the keyboard heading
        self.assertEqual(res[0], "FAIL")
    def test_stop_key_gate_not_reached(self):
        res, _, _ = run(graph(key={"png": "synth_step6.png"}))
        self.assertEqual(res[0], "FAIL")
    def test_real_dialog_png_is_not_step5(self):
        # the real Accessibility consent dialog has none of step 5's targets
        import ocr
        self.assertEqual(ocr.find_phrase(os.path.join(FX, "accessibility_dialog_real.png"), "skip for now", min_conf=70), [])
    def test_ocr_targets_inside_real_dump_bounds(self):
        import ocr
        p = os.path.join(FX, "step5_real.png")
        x, y, _ = ocr.find_phrase(p, "microphone access", min_conf=70)[0]; self.assertTrue(inside(MIC_ROW, x, y))
        x, y, _ = ocr.find_phrase(p, "skip for now", min_conf=70)[0]; self.assertTrue(inside(SKIP5, x, y))

if __name__ == "__main__": unittest.main()
