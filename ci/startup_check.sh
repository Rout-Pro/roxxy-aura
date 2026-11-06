#!/usr/bin/env bash
# Installs the debug APK on the emulator, launches it, and records screenshots, UI text and logcat.
set -u
APK=${APK_PATH:-$(ls aura-android/app/build/outputs/apk/release/*.apk | head -1)}
PKG=com.roxxy.aura
mkdir -p out
adb shell getprop ro.product.cpu.abilist > out/abilist.txt 2>&1; adb shell getprop ro.build.version.sdk > out/sdk.txt 2>&1
echo "abilist: $(cat out/abilist.txt) sdk: $(cat out/sdk.txt)"
if [ -n "${REQUIRE_ABI:-}" ] && ! tr -d '\r' < out/abilist.txt | tr ',' '\n' | grep -qx "$REQUIRE_ABI"; then
  echo "RESULT: FAIL - required ABI $REQUIRE_ABI not in emulator ro.product.cpu.abilist (translation unavailable); nothing installed" | tee out/walk_log.txt; echo "harness exit code: 1"; exit 1
fi
adb install -r "$APK" > out/install.txt 2>&1; cat out/install.txt
if ! grep -q "^Success" out/install.txt; then
  echo "RESULT: FAIL - adb install did not succeed" | tee out/walk_log.txt; echo "harness exit code: 1"; exit 1
fi
adb shell dumpsys package $PKG | grep -E "primaryCpuAbi|secondaryCpuAbi|versionCode|versionName" > out/pkg_abi.txt 2>&1; cat out/pkg_abi.txt
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
python3 ci/walk.py 2>&1 | tee out/walk_log.txt; walk_rc=${PIPESTATUS[0]}
adb logcat -d | grep -E "FATAL EXCEPTION|ANR in" | head -10 > out/errors_after_walk.txt; echo "--- fatal/anr after walk:"; cat out/errors_after_walk.txt
adb shell pidof $PKG > out/pid_after.txt 2>&1; echo "pid after: $(cat out/pid_after.txt)"
P=$(tr -d '\r' < out/pid_after.txt | awk '{print $1}'); if [ -n "$P" ]; then adb shell "grep -c ndk_translation /proc/$P/maps" > out/translation_maps.txt 2>&1; echo "ndk_translation maps in app process: $(cat out/translation_maps.txt)"; fi
rc=$walk_rc
if [ -s out/errors_after_walk.txt ]; then echo "FAIL: FATAL/ANR in logcat"; rc=1; fi
if ! grep -qE "^[0-9]+" out/pid_after.txt; then echo "FAIL: app process not running after walk"; rc=1; fi
echo "harness exit code: $rc"
exit $rc
