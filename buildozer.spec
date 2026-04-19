[app]
title = 双倒计时器
package.name = dualtimer
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,mp3,wav
version = 1.0.0
requirements = python3,kivy==2.2.1,plyer,pyjnius,android
orientation = portrait
fullscreen = 0
android.api = 33
android.ndk = 25b
android.minapi = 21
android.sdk = 33
android.archs = arm64-v8a, armeabi-v7a
android.permissions = WAKE_LOCK,VIBRATE,FOREGROUND_SERVICE,POST_NOTIFICATIONS
# android.services = TimerService:timer_service.py:foreground:sticky
android.launch_mode = singleTop
android.wakelock = True
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1
