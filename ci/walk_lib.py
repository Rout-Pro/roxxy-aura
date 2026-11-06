"""Onboarding walker logic. Device access is injected so it can be unit-tested on saved UI dumps.
Rules: select by dump semantics (text / checkable / clickable ancestor), never by fixed coordinates;
test elements with `is None` (an XML element with no children is falsy); every failure stops the run."""
import re
import xml.etree.ElementTree as ET

PKG = "com.roxxy.aura"
KEY_MARKERS = ("Verify Key", "Bring your own Gemini key")

def box(nd):
    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", nd.get("bounds", ""))
    return tuple(map(int, m.groups())) if m else None

def texts(r):
    return [n.get("text") for n in r.iter("node") if n.get("text")]

def find_text(r, *labels):
    """First node whose text equals one of labels, tried in order. Returns None if absent."""
    for t in labels:
        for n in r.iter("node"):
            if n.get("text") == t:
                return n
    return None

def clickable_for(r, t):
    """Smallest clickable ancestor (or the node itself) of the node with text t, or None."""
    def walk(n, anc):
        for ch in n:
            na = anc + [ch]
            if ch.get("text") == t:
                for a in reversed(na):
                    if a.get("clickable") == "true":
                        return a
                return ch
            res = walk(ch, na)
            if res is not None:
                return res
        return None
    return walk(r, [r])

def checkables(r):
    return [n for n in r.iter("node") if n.get("checkable") == "true"]

def contains(outer, inner):
    o, i = box(outer), box(inner)
    return o is not None and i is not None and o[0] <= i[0] and o[1] <= i[1] and o[2] >= i[2] and o[3] >= i[3]

def in_app(r):
    return any(n.get("package") == PKG for n in r.iter("node"))

def fully_visible(nd, screen_h):
    b = box(nd)
    return b is not None and b[1] >= 0 and b[3] <= screen_h and b[3] > b[1]

class DumpUnavailable(Exception):
    pass

class _Guard:
    def __init__(self, dev): self._d = dev
    def __getattr__(self, k): return getattr(self._d, k)
    def dump(self, name):
        r = self._d.dump(name)
        if not any(True for _ in r.iter("node")):
            raise DumpUnavailable(name)
        return r

def run(dev, log):
    try:
        return _run(_Guard(dev), log)
    except DumpUnavailable as e:
        return "FAIL", "UI dump unavailable at %s (uiautomator returned nothing)" % e

def _run(dev, log):
    """dev: dump(name)->Element, tap(node), back(), scroll_down(), screen_h. Returns (status, detail)."""
    r = dev.dump("1_landing")
    log("1 landing %s" % texts(r)[:6])
    if not in_app(r):
        return "FAIL", "not in app at start"
    n = clickable_for(r, "Get Started")
    if n is None:
        return "FAIL", "no Get Started"
    dev.tap(n)
    r = dev.dump("2_policy")
    log("2 policy %s" % texts(r)[:4])
    cb = None
    for _ in range(4):
        c = checkables(r)
        if c and fully_visible(c[0], dev.screen_h):
            cb = c[0]
            break
        dev.scroll_down()
        r = dev.dump("2_policy_scrolled")
    if cb is None:
        return "FAIL", "agreement checkbox not found/visible"
    btn = find_text(r, "Accept Terms", "I Understand")
    if btn is None:
        return "FAIL", "policy button label not found"
    bc = clickable_for(r, btn.get("text"))
    log("button before tick: %r enabled=%s" % (btn.get("text"), bc.get("enabled")))
    log("agreement bounds %s checked=%s" % (cb.get("bounds"), cb.get("checked")))
    if cb.get("checked") == "true":
        return "FAIL", "agreement already checked before tap"
    dev.tap(cb)
    r = dev.dump("3_agreement_checked")
    c = checkables(r)
    if not c or c[0].get("checked") != "true":
        return "FAIL", "agreement did not become checked"
    btn = find_text(r, "I Understand", "Accept Terms")
    if btn is None:
        return "FAIL", "policy button missing after tick"
    bc = clickable_for(r, btn.get("text"))
    log("button after tick: %r enabled=%s" % (btn.get("text"), bc.get("enabled")))
    if bc.get("enabled") != "true":
        return "FAIL", "button still disabled after tick"
    dev.tap(bc)
    r = dev.dump("4_after_policy")
    # Stages: tap Next until the first stage without one (the mandatory Accessibility gate).
    for k in range(5, 9):
        t = texts(r)
        log("stage %s" % t[:6])
        if not in_app(r):
            return "FAIL", "left app unexpectedly"
        if any(m in t for m in KEY_MARKERS):
            return "STOP", "reached key step before the permission gate (nothing entered)"
        if find_text(r, "Next") is None:
            break
        dev.tap(clickable_for(r, "Next"))
        r = dev.dump("%d_stage" % k)
    else:
        return "FAIL", "too many stages before the accessibility gate"
    sw = checkables(r)
    if find_text(r, "Skip for now") is not None:
        return "FAIL", "accessibility gate must not be skippable"
    if not sw:
        return "FAIL", "no switch on accessibility gate"
    log("accessibility gate (no Next, no skip); switch=%s" % sw[0].get("bounds"))
    dev.tap(sw[0])
    r = dev.dump("a1_settings_list")
    row = find_text(r, "Roxxy")
    if in_app(r) or row is None:
        return "FAIL", "Settings Accessibility list with Roxxy not shown"
    dev.tap(clickable_for(r, "Roxxy"))
    r = dev.dump("a2_service_page")
    if in_app(r):
        return "FAIL", "service page not shown"
    bars = [n for n in r.iter("node") if n.get("text") == "Use Roxxy"]
    main_row = clickable_for(r, "Use Roxxy") if len(bars) == 1 else None
    if main_row is None or main_row.get("clickable") != "true":
        return "FAIL", "ambiguous: cannot identify the single 'Use Roxxy' main toggle row (%d labels)" % len(bars)
    inside = [c for c in checkables(r) if contains(main_row, c)]
    if len(inside) != 1:
        return "FAIL", "ambiguous: %d switches inside the 'Use Roxxy' row" % len(inside)
    if inside[0].get("checked") == "true":
        log("service already on")
    dev.tap(main_row)
    r = dev.dump("a3_after_toggle")
    ctx = [t for t in texts(r) if "Roxxy" in t]
    allow = find_text(r, "Allow", "OK", "Turn on")
    if allow is not None:
        # An affirmative label alone is not enough: the dialog must be about the Roxxy service.
        if not ctx or in_app(r):
            return "FAIL", "unknown dialog (no Roxxy consent context); not approving"
        log("confirm dialog context=%r button=%r" % (ctx[0], allow.get("text")))
        dev.tap(allow if allow.get("clickable") == "true" else (clickable_for(r, allow.get("text")) or allow))
    elif any(n.get("resource-id") == "android:id/button1" for n in r.iter("node")):
        return "FAIL", "dialog with unrecognized affirmative label; not approving"
    else:
        row3 = clickable_for(r, "Use Roxxy")
        c3 = [c for c in checkables(r) if row3 is not None and contains(row3, c)]
        if in_app(r) or not c3 or c3[0].get("checked") != "true":
            return "FAIL", "toggle neither showed a confirm dialog nor turned on (OS blocked or unknown dialog)"
    # Everything after consent is screenshot-grounded (uiautomator dumps were unreliable once the
    # Roxxy accessibility service was on). See shot_lib.py.
    return dev.after_consent(log)
