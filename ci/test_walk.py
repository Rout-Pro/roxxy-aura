import os, unittest, xml.etree.ElementTree as ET
import walk_lib as W
D = os.path.join(os.path.dirname(__file__), "fixtures")
def load(n): return ET.parse(os.path.join(D, n + ".xml")).getroot()
def node(text="", clickable="false", checkable="false", checked="false", enabled="true", bounds="[0,0][10,10]", pkg=W.PKG, children=()):
    e = ET.Element("node", text=text, clickable=clickable, checkable=checkable, checked=checked, enabled=enabled, bounds=bounds, package=pkg)
    for c in children: e.append(c)
    return e
def screen(*kids, pkg=W.PKG):
    r = ET.Element("hierarchy"); root = node(pkg=pkg, children=kids); r.append(root); return r
def next_screen(): return screen(node(text="Restricted settings"), node(clickable="true", bounds="[70,574][250,626]", children=[node(text="Next", bounds="[111,591][209,610]")]))
def perm_screen(): return screen(node(text="Accessibility Service"), node(checkable="true", clickable="true", bounds="[20,300][300,360]"))
def key_screen(): return screen(node(text="Bring your own Gemini key"), node(text="Verify Key"))
SYSTEM = lambda: screen(node(text="Accessibility", pkg="com.android.settings"), pkg="com.android.settings")


def row(text, bounds="[0,254][320,333]"): return node(clickable="true", bounds=bounds, children=[node(text=text)])
def settings_list(): return screen(node(text="Downloaded apps", pkg="com.android.settings"), node(clickable="true", pkg="com.android.settings", children=[node(text="Roxxy", pkg="com.android.settings")]), pkg="com.android.settings")
def service_page(checked="false"): return screen(node(clickable="true", pkg="com.android.settings", bounds="[0,203][320,311]", children=[node(text="Use Roxxy", pkg="com.android.settings", bounds="[44,243][204,271]"), node(checkable="true", checked=checked, pkg="com.android.settings", bounds="[228,233][284,281]")]), node(checkable="true", clickable="true", pkg="com.android.settings", bounds="[232,362][304,441]"), pkg="com.android.settings")
def dialog(): return screen(node(text="Allow Roxxy full control?", pkg="com.android.settings"), node(clickable="true", pkg="com.android.settings", children=[node(text="Allow", pkg="com.android.settings")]), pkg="com.android.settings")
def other_dialog(): return screen(node(text="Allow something else?", pkg="com.android.settings"), node(clickable="true", pkg="com.android.settings", children=[node(text="Allow", pkg="com.android.settings")]), pkg="com.android.settings")
def odd_dialog():
    b = node(text="Proceed", clickable="true", pkg="com.android.settings"); b.set("resource-id", "android:id/button1")
    return screen(node(text="Roxxy wants control", pkg="com.android.settings"), b, pkg="com.android.settings")
def blocked_page(): return service_page("false")
def two_toggles(): return screen(node(checkable="true", clickable="true", pkg="com.android.settings", bounds="[1,1][2,2]"), node(checkable="true", clickable="true", pkg="com.android.settings", bounds="[3,3][4,4]"), pkg="com.android.settings")
def skip_screen(txt="Voice and the floating overlay stay off until you enable them."): return screen(node(text="Microphone Access"), node(checkable="true", clickable="true", bounds="[20,80][300,130]"), node(text=txt), node(clickable="true", children=[node(text="Skip for now")]))
def mic_dialog(): return screen(node(text="Allow Roxxy to record audio?", pkg="com.android.permissioncontroller"), node(clickable="true", pkg="com.android.permissioncontroller", children=[node(text="Don\u2019t allow", pkg="com.android.permissioncontroller")]), pkg="com.android.permissioncontroller")
def plain_stage(): return screen(node(text="Roxxy Virtual Keyboard"), node(clickable="true", children=[node(text="Skip for now")]))

class Dev:
    """Scripted device: dumps come from a queue keyed by action sequence."""
    def __init__(self, seq, screen_h=640): self.seq = list(seq); self.screen_h = screen_h; self.handed_off = False; self.taps = []; self.backs = 0; self.scrolls = 0; self.names = []
    def dump(self, name): self.names.append(name); return self.seq.pop(0)
    def tap(self, nd): self.taps.append(nd.get("bounds"))
    def back(self): self.backs += 1
    def scroll_down(self): self.scrolls += 1
    def sleep(self, n): pass
    def after_consent(self, log): self.handed_off = True; return ("STOP", "handed to screenshot driver")

def go(seq, **kw):
    d = Dev(seq, **kw); logs = []
    res = W.run(d, logs.append); return res, d, logs

class T(unittest.TestCase):
    def test_element_truthiness_regression(self):
        e = ET.Element("node", text="x"); self.assertFalse(bool(e))  # the bug class
        r = load("policy_checked"); self.assertIsNotNone(W.find_text(r, "I Understand"))
        self.assertIsNone(W.find_text(r, "Accept Terms"))
    def test_dynamic_labels(self):
        self.assertEqual(W.find_text(load("policy_unchecked"), "Accept Terms", "I Understand").get("text"), "Accept Terms")
        self.assertEqual(W.find_text(load("policy_checked"), "I Understand", "Accept Terms").get("text"), "I Understand")
    def test_clickable_ancestor_and_enabled_state(self):
        self.assertEqual(W.clickable_for(load("policy_unchecked"), "Accept Terms").get("enabled"), "false")
        self.assertEqual(W.clickable_for(load("policy_checked"), "I Understand").get("enabled"), "true")
    def test_checkbox_semantics(self):
        c = W.checkables(load("policy_unchecked")); self.assertEqual(len(c), 1); self.assertEqual(c[0].get("checked"), "false")
        self.assertEqual(W.checkables(load("policy_checked"))[0].get("checked"), "true")
    def test_visibility_on_320x640(self):
        self.assertTrue(W.fully_visible(W.checkables(load("policy_unchecked"))[0], 640))
    def happy_prefix(self): return [load("landing"), load("policy_unchecked"), load("policy_checked")]
    def test_fail_no_get_started(self):
        self.assertEqual(go([screen(node(text="Loading"))])[0][0], "FAIL")
    def test_fail_not_in_app(self):
        self.assertEqual(go([SYSTEM()])[0], ("FAIL", "not in app at start"))
    def test_fail_empty_hierarchy(self):
        self.assertEqual(go([ET.fromstring("<hierarchy/>")])[0][0], "FAIL")
    def test_scrolls_when_checkbox_offscreen(self):
        off = screen(node(text="Accept Terms"), node(checkable="true", clickable="true", bounds="[20,700][300,780]"))
        res, d, _ = go([load("landing"), off, load("policy_unchecked"), load("policy_checked"), key_screen()])
        self.assertEqual(res[0], "STOP"); self.assertEqual(d.scrolls, 1)
    def test_fail_checkbox_never_found(self):
        bare = screen(node(text="Accept Terms"))
        res, d, _ = go([load("landing"), bare] + [bare] * 4); self.assertEqual(res, ("FAIL", "agreement checkbox not found/visible")); self.assertEqual(d.scrolls, 4)
    def test_fail_checkbox_does_not_toggle(self):
        res, _, _ = go([load("landing"), load("policy_unchecked"), load("policy_unchecked")]); self.assertEqual(res, ("FAIL", "agreement did not become checked"))
    def test_fail_button_stays_disabled(self):
        r = load("policy_checked")
        for n in r.iter("node"):
            if n.get("clickable") == "true" and n.get("bounds") == "[70,574][250,626]": n.set("enabled", "false")
        self.assertEqual(go([load("landing"), load("policy_unchecked"), r])[0], ("FAIL", "button still disabled after tick"))
    def full(self, **over):
        seq = self.happy_prefix() + [next_screen(), next_screen(), perm_screen(), settings_list(), service_page(), dialog()]
        return seq
    def test_full_revised_path(self):
        res, d, logs = go(self.full())
        self.assertEqual(res, ("STOP", "handed to screenshot driver")); self.assertTrue(d.handed_off); self.assertEqual(d.backs, 0)
        self.assertEqual(d.names[-1], "a3_after_toggle")  # no dump is taken after the consent tap
    def test_accessibility_gate_must_not_be_skippable(self):
        res, _, _ = go(self.happy_prefix() + [next_screen(), next_screen(), skip_screen()])
        self.assertEqual(res, ("FAIL", "accessibility gate must not be skippable"))
    def test_fail_settings_list_without_roxxy(self):
        res, _, _ = go(self.happy_prefix() + [next_screen(), next_screen(), perm_screen(), SYSTEM()]); self.assertEqual(res[0], "FAIL")
    def test_real_service_page_dump_selects_use_roxxy_row(self):
        r = load("service_page_real")
        self.assertEqual(len(W.checkables(r)), 2)  # the ambiguity that stopped the 20:37 run
        row = W.clickable_for(r, "Use Roxxy")
        self.assertEqual(row.get("resource-id"), "com.android.settings:id/main_switch_bar")
        inside = [c for c in W.checkables(r) if W.contains(row, c)]
        self.assertEqual(len(inside), 1); self.assertEqual(inside[0].get("resource-id"), "android:id/switch_widget")
        self.assertEqual(inside[0].get("checked"), "false")
    def test_real_settings_list_has_single_roxxy_row(self):
        r = load("settings_list_real"); self.assertEqual(len([n for n in r.iter("node") if n.get("text") == "Roxxy"]), 1)
        self.assertEqual(W.clickable_for(r, "Roxxy").get("clickable"), "true")
    def test_fail_ambiguous_toggles(self):
        res, _, _ = go(self.happy_prefix() + [next_screen(), next_screen(), perm_screen(), settings_list(), two_toggles()])
        self.assertEqual(res[0], "FAIL"); self.assertIn("ambiguous", res[1])
    def test_fail_os_blocks_enable(self):
        res, _, _ = go(self.happy_prefix() + [next_screen(), next_screen(), perm_screen(), settings_list(), service_page(), blocked_page()])
        self.assertEqual(res[0], "FAIL"); self.assertIn("OS blocked", res[1])
    def test_no_absolute_free_claim_and_free_tier_data_use_disclosed(self):
        root = os.path.join(os.path.dirname(__file__), "..", "aura-android/app/src/main/java/com/aura/aura_ui/presentation/screens")
        files = ["onboarding/OnboardingScreen.kt", "ProviderSettingsScreen.kt", "CompanionScreen.kt", "legal/LegalCopy.kt"]
        for f in files:
            with open(os.path.join(root, f)) as fh: src = fh.read()
            self.assertNotIn("at no cost", src, f); self.assertNotIn("free-tier eligible", src, f)
        for f in files[:3]:
            with open(os.path.join(root, f)) as fh: src = fh.read()
            self.assertIn("improve its products", src, f)
        with open(os.path.join(root, files[3])) as fh: self.assertIn("improve their products", fh.read())
    def test_skip_and_missing_permission_copy_present_in_source(self):
        src = open(os.path.join(os.path.dirname(__file__), "..", "aura-android/app/src/main/java/com/aura/aura_ui/presentation/screens/onboarding/OnboardingScreen.kt")).read()
        for needle in ("Skip for now", "stay off until you enable them", "will fail until you enable its keyboard"): self.assertIn(needle, src)
    def test_fail_dialog_without_roxxy_context(self):
        res, _, _ = go(self.happy_prefix() + [next_screen(), next_screen(), perm_screen(), settings_list(), service_page(), other_dialog()])
        self.assertEqual(res[0], "FAIL"); self.assertIn("unknown dialog", res[1])
    def test_fail_button1_with_unknown_label(self):
        res, d, _ = go(self.happy_prefix() + [next_screen(), next_screen(), perm_screen(), settings_list(), service_page(), odd_dialog()])
        self.assertEqual(res[0], "FAIL"); self.assertIn("unrecognized", res[1]); self.assertEqual(len(d.taps), 8)
class AdbAdapter(unittest.TestCase):
    def test_dump_cmd_formats_and_removes_stale_files(self):
        import walk
        c = walk.dump_cmd("perm_back")
        self.assertIn("adb shell rm -f /sdcard/w.xml", c); self.assertIn("rm -f out/walk_perm_back.xml", c)
        self.assertIn("adb pull /sdcard/w.xml out/walk_perm_back.xml", c); self.assertNotIn("%", c)
    def test_adapter_dump_end_to_end_with_fake_shell(self):
        import walk, tempfile, shutil
        d = tempfile.mkdtemp(); cwd = os.getcwd(); os.chdir(d); os.makedirs("out")
        calls = []
        def fake_sh(cmd):
            calls.append(cmd)
            if cmd.startswith("adb shell wm size"): return "Physical size: 320x640"
            if "uiautomator dump" in cmd: shutil.copy(os.path.join(D, "landing.xml"), "out/walk_x.xml")
            return ""
        walk.sh = fake_sh
        a = walk.Adb(); self.assertEqual(a.screen_h, 640)
        r = a.dump("x"); self.assertIsNotNone(W.find_text(r, "Get Started"))
        os.chdir(cwd); shutil.rmtree(d)
class AdbInputs(unittest.TestCase):
    def test_tap_back_scroll_commands(self):
        import walk
        calls = []
        walk.sh = lambda c: (calls.append(c), "Physical size: 320x640")[1]
        walk.time.sleep = lambda n: None
        a = walk.Adb(); a.tap(node(bounds="[20,485][300,564]")); a.back(); a.scroll_down()
        self.assertIn("adb shell input tap 160 524", calls); self.assertIn("adb shell input keyevent KEYCODE_BACK", calls)
        self.assertTrue(any(c.startswith("adb shell input swipe 160 ") for c in calls))
if __name__ == "__main__": unittest.main()
