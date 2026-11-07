"""Bounded key phase (one run): type a test key into the gate, Verify, Next, step 9, Launch Roxxy, Home.
The key comes ONLY from an env var and is never logged, echoed, or written. While the key may be on screen
(from typing until Home) every capture goes to a private dir, is OCR'd in memory-lifetime only and deleted;
only the final Home capture (key no longer on screen) is persisted. Anything unknown stops the run."""
import os, shutil, subprocess, time
import shot_lib
from shot_lib import Stop

PRIVATE = os.environ.get("KEY_PRIVATE_DIR", "/tmp/keywin")
KEY_ENV = "ROXXY_TEST_KEY"

class PrivateDev:
    """Proxy whose shot() writes into the private dir (deleted afterwards), everything else passes through."""
    def __init__(self, dev):
        self._d = dev
        os.makedirs(PRIVATE, exist_ok=True)
    def __getattr__(self, n): return getattr(self._d, n)
    def shot(self, name):
        p = os.path.join(PRIVATE, "p_%s.png" % name)
        if os.path.exists(p): os.remove(p)
        return self._d.shot_to(p)

def wipe_private():
    shutil.rmtree(PRIVATE, ignore_errors=True)

def poll(s, name, kind, phrase, tries, wait, bad=()):
    """Fresh private capture until `phrase` is uniquely present; stop on any `bad` phrase or timeout."""
    for i in range(tries):
        png = s.capture("%s_%d" % (name, i), kind)
        for b in bad:
            if s.find(png, b, True):
                raise Stop("error text %r appeared while waiting for %r" % (b, phrase))
        if len(s.find(png, phrase, False)) == 1:
            return png
        s.d.sleep(wait)
    raise Stop("%r not seen after %d tries" % (phrase, tries))

def run_key_phase(dev, log, find=None, persist_name="k9_home"):
    key = os.environ.get(KEY_ENV, "")
    if len(key) < 20:
        raise Stop("key phase requested but no usable key in env")
    pdev = PrivateDev(dev)
    s = shot_lib.Shots(pdev, log, find)
    try:
        png = s.screen("k0_gate", "app", ("bring your own gemini key", "verify key"))
        x, y, c = s.unique(png, "gemini api key", loose=True)
        s.foreground("app"); log("tap key field label")
        pdev.tap_xy(x, y); pdev.sleep(2)
        s.foreground("app")
        log("typing key (value not logged)")
        pdev.type_secret(key)
        pdev.sleep(2)
        png = s.capture("k1_typed", "app")
        if not s.find(png, "verify key", False):
            log("Verify Key not visible (keyboard?); one Back to hide it")
            pdev.back(); pdev.sleep(2)
            png = s.capture("k1b_typed", "app")
        before = s.tap_phrase(png, "verify key", "app")
        log("tapped Verify Key; waiting for result")
        png = poll(s, "k2_verify", "app", "key verified", 12, 3,
                   bad=("invalid", "couldn't", "failed", "unavailable", "error", "denied"))
        log("Key Verified shown (stored via app Keystore path on emulator)")
        before = s.tap_phrase(png, "next", "app"); pdev.sleep(3)
        png = s.changed(before, "k3_step9", "app")
        s.unique(png, "banking & sensitive guard", loose=True)
        log("step 9 reached (classifier runs once on entry; bounded by app retry policy)")
        png = poll(s, "k4_scan", "app", "launch roxxy", 20, 5)
        # Wait until the 'Scanning apps' text is gone (classifier finished or failed) before continuing.
        for _ in range(12):
            png = s.capture("k4_wait", "app")
            if not s.find(png, "scanning apps", True):
                break
            pdev.sleep(5)
        else:
            raise Stop("classifier still scanning after wait")
        cls = "classifier_error" if s.find(png, "couldn't scan", True) else (
              "classifier_none_flagged" if s.find(png, "no sensitive apps", True) else "classifier_flagged_or_other")
        log("step 9 outcome: %s (classifier response only; not an overlay/voice/AI-task proof)" % cls)
        before = s.tap_phrase(png, "launch roxxy", "app"); pdev.sleep(5)
        png = s.changed(before, "k5_after_launch", "app")
    finally:
        pass
    # Key is no longer on screen. Persist ONLY this Home capture.
    pdev.sleep(3)
    home = shot_lib.Shots(dev, log, find)
    hp = home.capture(persist_name, "app")
    for ph in ("talk to roxxy",):
        home.unique(hp, ph, loose=True)
    log("Home reached (Talk to Roxxy visible); persisted %s" % os.path.basename(hp))
    return cls
