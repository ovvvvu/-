[app]
# 应用标题
title = 双倒计时器
# 包名
package.name = dualtimer
# 包域名 
package.domain = org.example
# 源码目录
source.dir = .
# 主文件
source.include_exts = py,png,jpg,kv,atlas,mp3,wav
# 版本
version = 1.0.0
# 要求
requirements = python3,kivy,plyer,pyjnius,android
# 图标（可选）
# icon.filename = %(source.dir)s/assets/icon.png
# 方向
orientation = portrait
# 全屏
fullscreen = 0
# Android API
android.api = 33
# Android NDK
android.ndk = 23b
# 最小 SDK
android.minapi = 21
# 目标 SDK
android.sdk = 33
# 架构
android.archs = arm64-v8a, armeabi-v7a
# 权限
android.permissions = WAKE_LOCK,VIBRATE,FOREGROUND_SERVICE,POST_NOTIFICATIONS,FOREGROUND_SERVICE_SPECIAL_USE
# 服务
android.services = TimerService:timer_service.py:foreground:sticky
# 启动模式
android.launch_mode = singleTop
# 屏幕常亮
android.wakelock = True
# 日志
android.logcat_filters = *:S python:D
# 构建模式（debug/release）
android.build_mode = release

[buildozer]
log_level = 2
warn_on_root = 1
