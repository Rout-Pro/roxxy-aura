#!/usr/bin/env bash
# Installs the debug APK on the emulator, launches it, and records screenshots, UI text and logcat.
set -u
APK=$(ls aura-android/app/build/outputs/apk/release/*.apk | head -1)
PKG=com.roxxy.aura
mkdir -p out
adb install -r -g "$APK" > out/install.txt 2>&1; cat out/install.txt
adb logcat -c
adb shell monkey -p $PKG -c android.intent.category.LAUNCHER 1 > out/launch.txt 2>&1
for t in 10 25; do
  sleep $t
  adb exec-out screencap -p > out/shot_$t.png
  adb shell uiautomator dump /sdcard/ui_$t.xml >/dev/null 2>&1; adb pull /sdcard/ui_$t.xml out/ >/dev/null 2>&1
done
adb shell pidof $PKG > out/pid.txt 2>&1; echo "pid: $(cat out/pid.txt)"
adb logcat -d > out/logcat.txt
grep -E "FATAL EXCEPTION|AndroidRuntime|FirebaseApp|IllegalStateException" out/logcat.txt | head -30 > out/errors.txt
echo "--- errors:"; cat out/errors.txt
echo "--- ui text:"; grep -o 'text="[^"]\+"' out/ui_25.xml | head -30

# ---- walk onboarding (bounded) ----
cat > /tmp/walk.py <<'PY'
import subprocess,re,sys,time
def sh(c): return subprocess.run(c,shell=True,capture_output=True,text=True).stdout
want=["Get Started","Accept Terms","I Understand","Next","Skip","Continue"]
prev=None
done_cb=False
for i in range(1,13):
    sh("adb shell uiautomator dump /sdcard/w.xml >/dev/null 2>&1; adb pull /sdcard/w.xml out/walk_%d.xml >/dev/null 2>&1"%i)
    x=open("out/walk_%d.xml"%i).read() if __import__('os').path.exists("out/walk_%d.xml"%i) else ""
    sh("adb exec-out screencap -p > out/walk_%d.png"%i)
    texts=re.findall(r'text="([^"]+)"',x); print(i,texts[:8])
    tgt=None
    for w in want:
        m=re.search(r'text="%s"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'%re.escape(w),x)
        if m: tgt=m;break
    if i>1 and prev==texts[:8] and not done_cb:
        # stuck: tap the policy checkbox (narrow clickable in the lower half), else the first clickable
        cands=[tuple(map(int,mm.groups())) for mm in re.finditer(r'clickable="true"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',x)]
        cands=[c for c in cands if c[2]-c[0]<120 and c[1]>300]
        if cands:
            a,b,c,d=cands[0]; sh("adb shell input tap %d %d"%((a+c)//2,(b+d)//2)); time.sleep(3); prev=texts[:8]; done_cb=True; continue
    prev=texts[:8]
    if not tgt: break
    a,b,c,d=map(int,tgt.groups()); sh("adb shell input tap %d %d"%((a+c)//2,(b+d)//2)); time.sleep(4)
PY
python3 /tmp/walk.py | tee out/walk_log.txt
adb logcat -d | grep -E "FATAL EXCEPTION|ANR in" | head -10 > out/errors_after_walk.txt; echo "--- fatal/anr after walk:"; cat out/errors_after_walk.txt
adb shell pidof $PKG > out/pid_after.txt 2>&1; echo "pid after: $(cat out/pid_after.txt)"
