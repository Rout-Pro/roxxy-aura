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
 "synth_step6.png": [("Roxxy Virtual Keyboard", 160, 108, 14), ("Automated Typing", 160, 300, 14), SKIP],
 "synth_step7.png": [("1/2: Push Notifications", 160, 108, 14), ("2/2: Live Alerts & Listener", 160, 170, 14), SKIP],
 "synth_key.png": [("Bring your own Gemini key", 160, 108, 14), ("Verify Key", 160, 590, 15)],
 # negatives: words match a target but the screen is something else
 "synth_other_perm_dialog.png": [("Allow Camera to take", 160, 300, 16), ("pictures?", 160, 325, 16), ("Don't allow", 160, 460, 15)],
 "synth_dup_skip.png": [("1/2: Microphone Access", 160, 108, 14), ("Skip for now", 160, 560, 14), SKIP],
 "synth_notes_app.png": [("Notes about Microphone Access", 160, 108, 14), ("Skip for now", 160, 617, 14)],
}
for n, it in S.items(): draw(n, it)
draw("synth_step6_blur.png", S["synth_step6.png"], blur=2.2)
print("ok")
