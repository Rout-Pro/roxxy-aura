#!/usr/bin/env bash
# Installs the debug APK on the emulator, launches it, and records screenshots, UI text and logcat.
set -u
APK=$(ls aura-android/app/build/outputs/apk/release/*.apk | head -1)
PKG=com.roxxy.aura
mkdir -p out
adb install -r "$APK" > out/install.txt 2>&1; cat out/install.txt
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

# ---- walk onboarding (semantic selectors from the UI dump; one bounded pass) ----
python3 ci/walk.py 2>&1 | tee out/walk_log.txt
adb logcat -d | grep -E "FATAL EXCEPTION|ANR in" | head -10 > out/errors_after_walk.txt; echo "--- fatal/anr after walk:"; cat out/errors_after_walk.txt
adb shell pidof $PKG > out/pid_after.txt 2>&1; echo "pid after: $(cat out/pid_after.txt)"
