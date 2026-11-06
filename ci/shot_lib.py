"""Screenshot-grounded walker for the stages after Accessibility is enabled (uiautomator dumps were
unreliable there). Rules: every tap point is derived by OCR from a FRESH screenshot of the current
screen; the foreground package/activity is verified from dumpsys right before the capture and
again right before the tap; every phrase must match exactly once with enough confidence; anything
else stops the run. Never a coordinate from a previous run or an assumed layout.

dev interface: focus() -> (pkg, activity) or None; shot(name) -> png path or None (fresh capture, old
copy deleted first); tap_xy(x, y); back(); sleep(s). find(png, phrase) -> [(x, y, conf)] is injectable."""
import hashlib, os, re
import ocr

APP = "com.roxxy.aura"
PERM_PKGS = ("com.google.android.permissioncontroller", "com.android.permissioncontroller")
MIN_CONF = 70  # per-word OCR confidence floor (real screenshots scored 92-97)

def _read(p):
    with open(p, "rb") as f:
        return f.read()

class Stop(Exception):
    pass

def parse_focus(text):
    """Parse `dumpsys window` output. Exactly one mCurrentFocus window naming pkg/activity, else None."""
    lines = [l for l in text.splitlines() if "mCurrentFocus" in l]
    if len(lines) != 1:
        return None
    m = re.search(r"\s([A-Za-z0-9_.]+)/([A-Za-z0-9_.$]+)\}", lines[0])
    return (m.group(1), m.group(2)) if m else None

def activity_ok(pkg, act, kind):
    if kind == "app":
        return pkg == APP and act.endswith("MainActivity")
    if kind == "perm":
        return pkg in PERM_PKGS and "GrantPermissionsActivity" in act
    return False

class Shots:
    def __init__(self, dev, log, find=None):
        self.d, self.log = dev, log
        self.find = find or (lambda png, ph, loose=False: ocr.find_phrase(png, ph, min_conf=MIN_CONF, exact_line=not loose))
        self.prev_hash = None

    def foreground(self, kind, tries=5):
        seen = None
        for _ in range(tries):
            seen = self.d.focus()
            if seen and activity_ok(seen[0], seen[1], kind):
                return seen
            self.d.sleep(1)
        raise Stop("foreground is %s, expected %s" % ("%s/%s" % seen if seen else "unknown", kind))

    def capture(self, name, kind):
        """Verify foreground, take a fresh screenshot, verify it is a real image."""
        self.foreground(kind)
        png = self.d.shot(name)
        if not png or not os.path.exists(png) or os.path.getsize(png) == 0:
            raise Stop("screenshot capture failed at %s" % name)
        try:
            from PIL import Image
            Image.open(png).verify()
        except Exception:
            raise Stop("screenshot at %s is not a valid image" % name)
        return png

    def unique(self, png, phrase, loose=False):
        hits = self.find(png, phrase, loose)
        if len(hits) != 1:
            raise Stop("%r matched %d times on %s (need exactly 1 with conf>=%d)" % (phrase, len(hits), os.path.basename(png), MIN_CONF))
        return hits[0]

    def absent(self, png, phrase):
        if self.find(png, phrase, True):
            raise Stop("%r unexpectedly present on %s" % (phrase, os.path.basename(png)))

    def step7_identity(self, png):
        """Step 7 has two real variants (source: OnboardingScreen Step 7, AnimatedContent on notifGranted):
        API 33+ shows "1/2: Push Notifications"; API <33 has no POST_NOTIFICATIONS runtime permission, so
        notifGranted is true and it shows "2/2: Live Alerts & Listener" (the title wraps over two lines).
        Exactly ONE variant must be present; the other variant's heading must be absent."""
        push = self.find(png, "push notifications", False)
        live = self.find(png, "live alerts", False)
        listener = self.find(png, "listener", True)
        if len(push) == 1 and not live and not listener:
            self.log("step 7 variant: 1/2 Push Notifications (API 33+)"); return "push"
        if len(live) == 1 and len(listener) == 1 and not push:
            self.log("step 7 variant: 2/2 Live Alerts & Listener (API <33: no runtime notification permission)"); return "live"
        raise Stop("step 7 identity ambiguous on %s (push=%d live=%d listener=%d)" % (os.path.basename(png), len(push), len(live), len(listener)))

    def screen(self, name, kind, must, absent=(), loose=()):
        png = self.capture(name, kind)
        for p in must:
            self.unique(png, p)
        for p in loose:
            self.unique(png, p, loose=True)
        for p in absent:
            self.absent(png, p)
        h = hashlib.sha256(_read(png)).hexdigest()
        self.prev_hash = h
        return png

    def tap_phrase(self, png, phrase, kind):
        x, y, conf = self.unique(png, phrase)
        self.foreground(kind)  # still the same foreground right before the tap
        self.log("tap %r at (%d,%d) conf=%s from %s" % (phrase, x, y, conf, os.path.basename(png)))
        before = hashlib.sha256(_read(png)).hexdigest()
        self.d.tap_xy(x, y)
        return before

    def changed(self, before, name, kind):
        """After a tap the next fresh capture must differ from the pre-tap one (stale-capture guard)."""
        png = self.capture(name, kind)
        if hashlib.sha256(_read(png)).hexdigest() == before:
            raise Stop("screen unchanged after tap at %s (stale capture or ineffective tap)" % name)
        return png

def run_after_consent(dev, log, find=None):
    try:
        return _run(Shots(dev, log, find), dev, log)
    except Stop as e:
        return "FAIL", "screenshot driver stopped: %s" % e

def _run(s, dev, log):
    # Back out of Settings until the app is the verified foreground (no dumps involved).
    for i in range(4):
        fg = dev.focus()
        if fg and activity_ok(fg[0], fg[1], "app"):
            break
        dev.back(); dev.sleep(2)
    else:
        raise Stop("could not return to the app after enabling Accessibility (last focus %s)" % (dev.focus(),))
    dev.sleep(2)
    h5 = ("microphone access", "skip for now")
    png = s.screen("c0_step5", "app", h5)
    log("step 5 reached: Microphone Access + Skip visible (accessibility is on, step 5 only follows it)")
    # The clickable target is the row whose title is "1/2: Microphone Access" (real dump: row [20,74][300,140]).
    before = s.tap_phrase(png, "microphone access", "app")
    dev.sleep(2)
    # The question wraps unpredictably, so each word is matched on its own: the dialog must name
    # Roxxy and the audio permission, and have exactly one "Don't allow".
    png = s.screen("c1_mic_prompt", "perm", (), loose=("roxxy", "record", "audio"))
    # The refusal button is "Don't allow" on API 33 and "Deny" on API 30: accept exactly ONE of the two,
    # matched as a whole line. Zero or both present means an unknown dialog, so stop.
    labels = [l for l in ("dont allow", "deny") if s.find(png, l)]
    if len(labels) != 1:
        raise Stop("refusal button 'dont allow'/'deny' matched %d times on %s (need exactly 1 label)" % (len(labels), os.path.basename(png)))
    before = s.tap_phrase(png, labels[0], "perm")
    dev.sleep(2)
    png = s.screen("c2_mic_refused", "app", h5)
    log("mic refused; back on step 5 with Skip")
    for label, heading, last in (("step 6", "roxxy virtual keyboard", False),
                                 ("step 7", "push notifications", False),
                                 ("step 8 key gate", "bring your own gemini key", True)):
        before = s.tap_phrase(png, "skip for now", "app")
        dev.sleep(2)
        png = s.changed(before, "c3_" + label.replace(" ", "_"), "app")
        if heading == "push notifications":
            s.step7_identity(png)
        else:
            s.unique(png, heading)
        s.absent(png, "microphone access")
        log("reached %s (%s)" % (label, heading))
        if last:
            s.unique(png, "verify key")
            # Evidence only (no taps in fields): scroll once and keep a second screenshot of the gate text.
            dev.scroll_down(); dev.sleep(2)
            p2 = s.capture("c4_gate_scrolled", "app")
            for ph in ("free tier", "improve", "products"):
                log("gate scrolled: %r hits=%d" % (ph, len(s.find(p2, ph, True))))
            return "STOP", "optional steps skipped via screenshot-grounded taps; reached key gate (nothing entered)"
        s.unique(png, "skip for now")
    raise Stop("unreachable")
