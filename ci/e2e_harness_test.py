"""End-to-end local test of the EXACT ci/startup_check.sh -> ci/walk.py -> adb adapter entrypoint,
using ci/fake_adb.py (scripted adb). Landing/policy dumps are saved real dumps; every later screen
is explicitly SYNTHETIC (permission/Settings stages have not been seen on a device)."""
import json, os, shutil, subprocess, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); FIX = os.path.join(HERE, "fixtures")
APP, SET, PC = "com.roxxy.aura", "com.android.settings", "com.google.android.permissioncontroller"

def screen(pkg, items):
    rows = []
    for text, kind, b in items:
        if kind == "txt": rows.append('<node text="%s" package="%s" clickable="false" checkable="false" checked="false" enabled="true" bounds="%s"/>' % (text, pkg, b))
        elif kind == "chk": rows.append('<node text="" package="%s" clickable="true" checkable="true" checked="false" enabled="true" bounds="%s"/>' % (pkg, b))
        else: rows.append('<node text="" package="%s" clickable="true" checkable="false" checked="false" enabled="true" bounds="%s"><node text="%s" package="%s" clickable="false" checkable="false" checked="false" enabled="true" bounds="%s"/></node>' % (pkg, b, text, pkg, b))
    return '<?xml version="1.0"?><hierarchy rotation="0"><node package="%s" bounds="[0,0][320,640]" clickable="false" checkable="false" checked="false" enabled="true" text="">%s</node></hierarchy>' % (pkg, "".join(rows))

NEXT = ("Next", "btn", "[70,574][250,626]"); SKIP = ("Skip for now", "btn", "[90,560][230,600]")
SYN = {
 "name": screen(APP, [("Personalize your Roxxy", "txt", "[20,80][300,110]"), NEXT]),
 "info": screen(APP, [("One Android security step", "txt", "[20,80][300,110]"), NEXT]),
 "acc": screen(APP, [("Accessibility Service", "txt", "[20,20][200,60]"), ("", "chk", "[234,83][286,131]")]),
 "list": screen(SET, [("Downloaded apps", "txt", "[24,227][304,246]"), ("Roxxy", "btn", "[0,254][320,333]")]),
 "service": screen(SET, [("Use Roxxy", "txt", "[20,100][200,140]"), ("", "chk", "[250,100][310,140]")]),
 "dialog": screen(SET, [("Allow Roxxy full control of your device?", "txt", "[20,100][300,200]"), ("Allow", "btn", "[200,300][300,340]"), ("Deny", "btn", "[20,300][120,340]")]),
 "dialog_other": screen(SET, [("Allow something else?", "txt", "[20,100][300,200]"), ("Allow", "btn", "[200,300][300,340]")]),
 "service_on": screen(SET, [("Use Roxxy", "txt", "[20,100][200,140]")]),
 "s5": screen(APP, [("Microphone Access", "txt", "[20,20][200,60]"), ("", "chk", "[234,83][286,131]"), ("Voice and the floating overlay stay off until you enable them.", "txt", "[20,500][300,540]"), SKIP]),
 "mic": screen(PC, [("Allow Roxxy to record audio?", "txt", "[20,100][300,200]"), ("Don\u2019t allow", "btn", "[20,300][300,340]")]),
 "s6": screen(APP, [("Roxxy Virtual Keyboard", "txt", "[20,20][200,60]"), ("", "chk", "[234,83][286,131]"), SKIP]),
 "s7": screen(APP, [("Notifications", "txt", "[20,20][200,60]"), ("", "chk", "[234,83][286,131]"), SKIP]),
 "key": screen(APP, [("Bring your own Gemini key", "txt", "[20,20][300,60]"), ("Verify Key", "btn", "[70,574][250,626]")]),
}
def graph(**over):
    st = {
     "landing": {"xml": "landing.xml", "trans": {"Get Started": "pol"}},
     "pol": {"xml": "policy_unchecked.xml", "trans": {"CHECK": "polc"}},
     "polc": {"xml": "policy_checked.xml", "trans": {"I Understand": "name"}},
     "name": {"xml": "name.xml", "trans": {"Next": "info"}},
     "info": {"xml": "info.xml", "trans": {"Next": "acc"}},
     "acc": {"xml": "acc.xml", "trans": {"CHECK": "list"}},
     "list": {"xml": "list.xml", "trans": {"Roxxy": "service"}},
     "service": {"xml": "service.xml", "trans": {"CHECK": "dialog"}},
     "dialog": {"xml": "dialog.xml", "trans": {"Allow": "service_on"}},
     "service_on": {"xml": "service_on.xml", "trans": {"BACK": "s5"}},
     "s5": {"xml": "s5.xml", "trans": {"CHECK": "mic", "Skip for now": "s6"}},
     "mic": {"xml": "mic.xml", "trans": {"Don\u2019t allow": "s5b"}},
     "s5b": {"xml": "s5.xml", "trans": {"Skip for now": "s6"}},
     "s6": {"xml": "s6.xml", "trans": {"Skip for now": "s7"}},
     "s7": {"xml": "s7.xml", "trans": {"Skip for now": "key"}},
     "key": {"xml": "key.xml", "trans": {}},
    }
    g = {"start": "landing", "states": st}; g.update(over); return g

class E2E(unittest.TestCase):
    def run_harness(self, g, extra_env=None, tweak=None):
        d = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, d, True)
        fd = os.path.join(d, "fake"); os.makedirs(fd); work = os.path.join(d, "work"); os.makedirs(work)
        for f in os.listdir(FIX): shutil.copy(os.path.join(FIX, f), os.path.join(fd, f))
        for k, v in SYN.items(): open(os.path.join(fd, k + ".xml"), "w").write(v)
        if tweak: tweak(fd)
        json.dump(g, open(os.path.join(fd, "graph.json"), "w"))
        bindir = os.path.join(d, "bin"); os.makedirs(bindir)
        shutil.copy(os.path.join(HERE, "fake_adb.py"), os.path.join(bindir, "adb")); os.chmod(os.path.join(bindir, "adb"), 0o755)
        open(os.path.join(bindir, "sleep"), "w").write("#!/bin/sh\nexit 0\n"); os.chmod(os.path.join(bindir, "sleep"), 0o755)
        sc = os.path.join(d, "pysc"); os.makedirs(sc); open(os.path.join(sc, "sitecustomize.py"), "w").write("import time; time.sleep = lambda n: None\n")
        os.symlink(HERE, os.path.join(work, "ci")); os.makedirs(os.path.join(work, "aura-android/app/build/outputs/apk/release")); open(os.path.join(work, "aura-android/app/build/outputs/apk/release/app-release.apk"), "w").write("x")
        env = dict(os.environ, PATH=bindir + ":" + os.environ["PATH"], FAKE_DIR=fd, PYTHONPATH=sc); env.update(extra_env or {})
        p = subprocess.run(["bash", os.path.join(HERE, "startup_check.sh")], cwd=work, env=env, capture_output=True, text=True, timeout=60)
        out = os.path.join(work, "out")
        return p, out, open(os.path.join(out, "walk_log.txt")).read() if os.path.exists(os.path.join(out, "walk_log.txt")) else ""

    def test_success_path_exits_zero_with_artifacts(self):
        p, out, log = self.run_harness(graph())
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("RESULT: STOP - optional steps skipped; reached key step", log)
        self.assertIn("button before tick: 'Accept Terms' enabled=false", log); self.assertIn("button after tick: 'I Understand' enabled=true", log)
        self.assertIn("confirm dialog context=", log); self.assertIn("harness exit code: 0", p.stdout)
        for f in ("walk_1_landing.xml", "walk_3_agreement_checked.png", "walk_a1_settings_list.xml", "walk_b2_mic_denied.xml", "walk_b5_after_skip.xml", "pid_after.txt", "errors_after_walk.txt", "logcat.txt", "shot_10.png", "ui_25.xml"):
            self.assertTrue(os.path.exists(os.path.join(out, f)), f)
    def test_unknown_dialog_fails_nonzero_and_keeps_evidence(self):
        g = graph(); g["states"]["service"]["trans"]["CHECK"] = "dialog_other"; g["states"]["dialog_other"] = {"xml": "dialog_other.xml", "trans": {"Allow": "service_on"}}
        p, out, log = self.run_harness(g)
        self.assertNotEqual(p.returncode, 0); self.assertIn("RESULT: FAIL - unknown dialog", log)
        self.assertTrue(os.path.exists(os.path.join(out, "walk_a3_after_toggle.png")))
    def test_stale_dump_is_rejected_and_recovers_via_back(self):
        # the dump fails once in service_on; the previous state's dump must NOT be reused
        p, out, log = self.run_harness(graph(dump_fails_in=["service_on"]))
        x = os.path.join(out, "walk_a4_after_confirm.xml")
        self.assertFalse(os.path.exists(x) and "Allow Roxxy full control" in open(x).read())
        self.assertIn("RESULT: STOP", log)  # BACK returned to the app, whose dump works
        self.assertEqual(p.returncode, 0)
    def test_persistent_dump_failure_fails(self):
        p, out, log = self.run_harness(graph(dump_fails_in=["service_on", "s5"]))
        self.assertNotEqual(p.returncode, 0); self.assertIn("RESULT: FAIL", log)
    def test_walker_exception_stderr_captured_and_nonzero(self):
        p, out, log = self.run_harness(graph(wm_size="garbage"))
        self.assertNotEqual(p.returncode, 0); self.assertIn("Traceback", log)
    def test_fatal_in_logcat_fails_even_if_walk_ok(self):
        p, out, log = self.run_harness(graph(logcat="E AndroidRuntime: FATAL EXCEPTION: main"))
        self.assertNotEqual(p.returncode, 0); self.assertIn("RESULT: STOP", log); self.assertIn("FAIL: FATAL/ANR", p.stdout)
    def test_dead_process_fails(self):
        p, out, log = self.run_harness(graph(pid=""))
        self.assertNotEqual(p.returncode, 0); self.assertIn("app process not running", p.stdout)
    def test_policy_checkbox_not_toggling_fails(self):
        g = graph(); g["states"]["pol"]["trans"] = {}
        p, out, log = self.run_harness(g); self.assertNotEqual(p.returncode, 0); self.assertIn("agreement did not become checked", log)
    def test_no_skip_on_mandatory_accessibility_gate_would_fail(self):
        g = graph(); g["states"]["acc"]["xml"] = "s5.xml"
        p, out, log = self.run_harness(g); self.assertNotEqual(p.returncode, 0); self.assertIn("must not be skippable", log)
if __name__ == "__main__": unittest.main()
