"""Keyless diagnostic: focus the EMPTY key field (no typing, no key exists), keep post-tap pixels, record pid before/after,
foreground, and OS exit-info / event-buffer lines (scrubbed to a whitelist and length-capped). Then stop."""
import os, re
import shot_lib
from shot_lib import Stop

PKG = shot_lib.APP
EXIT_OK = re.compile(r"(pid=|reason=|status=|timestamp=|importance=|process(Name)?=|description=|ApplicationExitInfo|packageName=|realUid=|pss=|rss=)", re.I)
EVENT_OK = re.compile(r"(am_proc_died|am_kill|am_low_memory|am_crash|am_anr|am_proc_start)")
MAXLEN = 220

def scrub(text, ok):
    kept, dropped = [], 0
    for l in text.splitlines():
        l = l.rstrip()
        if not l.strip():
            continue
        if ok.search(l):
            kept.append(re.sub(r"[A-Za-z0-9_.\-]{24,}", "[long-token]", l)[:MAXLEN])
        else:
            dropped += 1
    return kept, dropped

def pid(dev):
    return dev.run("adb shell pidof %s" % PKG).strip().split()[:1]

def run_diag(dev, log, find=None, out="out"):
    s = shot_lib.Shots(dev, log, find)
    png = s.screen("d0_gate", "app", ("bring your own gemini key", "verify key"))
    x, y, c = s.unique(png, "gemini api key", loose=True)
    before = pid(dev)
    log("pid before field tap: %s" % before)
    s.foreground("app")
    log("tap key field label at (%d,%d) conf=%s (empty field, nothing typed)" % (x, y, c))
    dev.tap_xy(x, y); dev.sleep(4)
    after = pid(dev)
    fg = dev.focus()
    log("pid after field tap: %s; foreground: %s" % (after, fg))
    shot = dev.shot("d1_after_field_tap")  # persisted: no key exists in this run
    log("post-tap screenshot: %s" % (os.path.basename(shot) if shot else "capture failed"))
    ei, d1 = scrub(dev.run("adb shell dumpsys activity exit-info %s" % PKG), EXIT_OK)
    ev, d2 = scrub(dev.run("adb logcat -b events -d"), EVENT_OK)
    ev = [l for l in ev if PKG in l or str(before[0] if before else "x") in l]
    with open(os.path.join(out, "diag_exit_info.txt"), "w") as f:
        f.write("\n".join(ei) + "\n")
    with open(os.path.join(out, "diag_events.txt"), "w") as f:
        f.write("\n".join(ev) + "\n")
    log("exit-info lines kept=%d dropped=%d; event lines kept=%d (others dropped=%d)" % (len(ei), d1, len(ev), d2))
    survived = bool(before) and before == after and fg and shot_lib.activity_ok(fg[0], fg[1], "app")
    return ("SURVIVED" if survived else "CHANGED"), "pid %s -> %s, foreground %s" % (before, after, fg)


def capture_os(dev, log, out="out"):
    """Scrubbed OS exit-info + event lines for the app, no app output. Safe in key runs (whitelist + token redaction)."""
    ei, d1 = scrub(dev.run("adb shell dumpsys activity exit-info %s" % PKG), EXIT_OK)
    ev, d2 = scrub(dev.run("adb logcat -b events -d"), EVENT_OK)
    ev = [l for l in ev if PKG in l]
    with open(os.path.join(out, "os_exit_info.txt"), "w") as f: f.write("\n".join(ei) + "\n")
    with open(os.path.join(out, "os_events.txt"), "w") as f: f.write("\n".join(ev) + "\n")
    log("os evidence: exit-info kept=%d dropped=%d, event lines kept=%d (dropped=%d)" % (len(ei), d1, len(ev), d2))
