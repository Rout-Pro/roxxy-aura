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

def in_app(r):
    return any(n.get("package") == PKG for n in r.iter("node"))

def fully_visible(nd, screen_h):
    b = box(nd)
    return b is not None and b[1] >= 0 and b[3] <= screen_h and b[3] > b[1]

def run(dev, log):
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
    for k in range(5, 10):
        t = texts(r)
        log("stage %s" % t[:6])
        if not in_app(r):
            dev.back()
            r = dev.dump("%d_back" % k)
            if not in_app(r):
                return "FAIL", "left app and BACK did not return"
            return "STOP", "left app at stage; pressed BACK once and returned"
        if any(m in t for m in KEY_MARKERS):
            return "STOP", "reached key step (nothing entered)"
        nxt = find_text(r, "Next")
        if nxt is None:
            sw = checkables(r)
            log("first mandatory permission step (no Next); switches=%s" % [(s.get("checked"), s.get("bounds")) for s in sw])
            if not sw:
                return "FAIL", "no Next and no switch on stage"
            dev.tap(sw[0])
            r = dev.dump("perm_row_tapped")
            if not in_app(r):
                dev.back()
                r = dev.dump("perm_back")
                if not in_app(r):
                    return "FAIL", "left app for permission and BACK did not return"
                return "STOP", "first permission row opened system UI; BACK returned to app"
            return "STOP", "first permission row tapped; stayed in app"
        dev.tap(clickable_for(r, "Next"))
        r = dev.dump("%d_stage" % k)
    return "FAIL", "too many stages"
