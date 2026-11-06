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

class Dev:
    """Scripted device: dumps come from a queue keyed by action sequence."""
    def __init__(self, seq, screen_h=640): self.seq = list(seq); self.screen_h = screen_h; self.taps = []; self.backs = 0; self.scrolls = 0; self.names = []
    def dump(self, name): self.names.append(name); return self.seq.pop(0)
    def tap(self, nd): self.taps.append(nd.get("bounds"))
    def back(self): self.backs += 1
    def scroll_down(self): self.scrolls += 1

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
    def test_full_path_to_first_permission_system_ui(self):
        res, d, _ = go(self.happy_prefix() + [next_screen(), next_screen(), perm_screen(), SYSTEM(), perm_screen()])
        self.assertEqual(res[0], "STOP"); self.assertIn("BACK returned", res[1]); self.assertEqual(d.backs, 1)
        self.assertEqual(len(d.taps), 6)
    def test_stays_in_app_after_permission_tap(self):
        res, d, _ = go(self.happy_prefix() + [next_screen(), perm_screen(), perm_screen()])
        self.assertEqual(res, ("STOP", "first permission row tapped; stayed in app")); self.assertEqual(d.backs, 0)
    def test_reaches_key_step(self):
        res, _, _ = go(self.happy_prefix() + [key_screen()]); self.assertEqual(res[0], "STOP"); self.assertIn("key step", res[1])
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
    def test_fail_left_app_and_back_fails(self):
        res, _, _ = go(self.happy_prefix() + [SYSTEM(), SYSTEM()]); self.assertEqual(res[0], "FAIL")
    def test_fail_too_many_stages(self):
        res, _, _ = go(self.happy_prefix() + [next_screen()] * 7); self.assertEqual(res, ("FAIL", "too many stages"))
    def test_fail_stage_without_next_or_switch(self):
        res, _, _ = go(self.happy_prefix() + [screen(node(text="???"))]); self.assertEqual(res[0], "FAIL")
if __name__ == "__main__": unittest.main()
