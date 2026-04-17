"""
后台服务脚本 - 保持通知栏常驻
"""

import time
import os
import sys

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """服务主循环"""
    print("Timer service started")
    
    # 导入 Android 类
    try:
        from jnius import autoclass
        
        PythonService = autoclass('org.kivy.android.PythonService')
        NotificationBuilder = autoclass('android.app.Notification$Builder')
        Context = autoclass('android.content.Context')
        Intent = autoclass('android.content.Intent')
        PendingIntent = autoclass('android.app.PendingIntent')
        ComponentName = autoclass('android.content.ComponentName')
        
        service = PythonService.mService
        context = service.getApplicationContext()
        
        # 创建打开主应用的 Intent
        intent = Intent(context, PythonService)
        intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP)
        pending_intent = PendingIntent.getActivity(
            context, 0, intent, 
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        )
        
        # 构建通知
        builder = NotificationBuilder(context)
        builder.setContentTitle("双倒计时器运行中")
        builder.setContentText("点击返回应用")
        builder.setSmallIcon(context.getApplicationInfo().icon)
        builder.setOngoing(True)  # 常驻通知
        builder.setContentIntent(pending_intent)
        
        # Android O+ 需要通知渠道
        try:
            NotificationChannel = autoclass('android.app.NotificationChannel')
            NotificationManager = autoclass('android.app.NotificationManager')
            
            channel_id = "timer_channel"
            channel = NotificationChannel(
                channel_id, "Timer Service", 
                NotificationManager.IMPORTANCE_LOW
            )
            manager = context.getSystemService(Context.NOTIFICATION_SERVICE)
            manager.createNotificationChannel(channel)
            builder.setChannelId(channel_id)
        except:
            pass
        
        notification = builder.build()
        service.startForeground(1, notification)
        
        # 保持服务运行
        while True:
            time.sleep(1)
            
    except Exception as e:
        print(f"Service error: {e}")
        # 非 Android 环境测试
        while True:
            time.sleep(10)


if __name__ == '__main__':
    main()