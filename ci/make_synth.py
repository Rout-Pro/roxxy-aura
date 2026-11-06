"""Renders SYNTHETIC 320x640 screens (not real device captures) for the screenshot-driver tests.
Real captures are only step5_real.png and accessibility_dialog_real.png. Run: python3 make_synth.py"""
import os
from PIL import Image, ImageDraw, ImageFont
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def draw(name, items, bg="white", blur=0):
    im = Image.new("RGB", (320, 640), bg); d = ImageDraw.Draw(im)
    for text, cx, cy, size in items:
        f = ImageFont.truetype(FONT, size); w = d.textlength(text, font=f)
        d.text((cx - w / 2, cy - size / 2 - 2), text, fill="black", font=f)
    if blur:
        from PIL import ImageFilter; im = im.filter(ImageFilter.GaussianBlur(blur))
    im.save(os.path.join(OUT, name))
SKIP = ("Skip for now", 160, 617, 14)
S = {
 "synth_mic_dialog.png": [("Allow Roxxy to record", 160, 300, 16), ("audio?", 160, 325, 16), ("While using the app", 160, 380, 15), ("Only this time", 160, 420, 15), ("Don't allow", 160, 460, 15)],
 "synth_mic_dialog_deny.png": [("Allow Roxxy to record", 160, 300, 16), ("audio?", 160, 325, 16), ("While using the app", 160, 380, 15), ("Only this time", 160, 420, 15), ("Deny", 160, 460, 15)],
 "synth_mic_both_labels.png": [("Allow Roxxy to record", 160, 300, 16), ("audio?", 160, 325, 16), ("Only this time", 160, 420, 15), ("Don't allow", 160, 460, 15), ("Deny", 160, 500, 15)],
 "synth_mic_no_refusal.png": [("Allow Roxxy to record", 160, 300, 16), ("audio?", 160, 325, 16), ("While using the app", 160, 380, 15), ("Only this time", 160, 420, 15)],
 "synth_other_perm_deny.png": [("Allow Camera to take", 160, 300, 16), ("pictures?", 160, 325, 16), ("Deny", 160, 460, 15)],
 "synth_step7_live_dup.png": [("2/2: Live Alerts &", 160, 108, 14), ("Listener", 160, 128, 14), ("2/2: Live Alerts &", 160, 300, 14), SKIP],
 "synth_step7_listener_only.png": [("Listener", 160, 128, 14), ("Notes", 160, 300, 14), SKIP],
 "synth_step7_both.png": [("1/2: Push Notifications", 160, 108, 14), ("2/2: Live Alerts &", 160, 170, 14), ("Listener", 160, 190, 14), SKIP],
 "synth_step7_live_wrapped.png": [("2/2: Live Alerts &", 160, 108, 14), ("Listener", 160, 128, 14), SKIP],
 "synth_step6.png": [("Roxxy Virtual Keyboard", 160, 108, 14), ("Automated Typing", 160, 300, 14), SKIP],
 "synth_step7.png": [("1/2: Push Notifications", 160, 108, 14), ("Notification Center", 160, 300, 14), SKIP],
 "synth_key.png": [("Bring your own Gemini key", 160, 108, 14), ("Verify Key", 160, 590, 15)],
 # negatives: words match a target but the screen is something else
 "synth_other_perm_dialog.png": [("Allow Camera to take", 160, 300, 16), ("pictures?", 160, 325, 16), ("Don't allow", 160, 460, 15)],
 "synth_dup_skip.png": [("1/2: Microphone Access", 160, 108, 14), ("Skip for now", 160, 560, 14), SKIP],
 "synth_notes_app.png": [("Notes about Microphone Access", 160, 108, 14), ("Skip for now", 160, 617, 14)],
}
for n, it in S.items(): draw(n, it)
draw("synth_step6_blur.png", S["synth_step6.png"], blur=2.2)
print("ok")
