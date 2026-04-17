"""
双倒计时器 Android 应用
功能：两个可配置倒计时，交替运行，锁屏显示，通知栏常驻
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.utils import platform
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window

import time
import json
import os

# Android 特定导入
if platform == 'android':
    from jnius import autoclass, cast
    from android import AndroidService
    from android.permissions import request_permissions, Permission
    from android.runnable import run_on_ui_thread
    import android.activity

# 颜色主题
COLORS = {
    'primary': [0.2, 0.6, 1, 1],      # 蓝色
    'secondary': [1, 0.4, 0.4, 1],    # 红色
    'background': [0.1, 0.1, 0.15, 1], # 深蓝黑
    'text': [1, 1, 1, 1],
    'accent': [0.3, 0.8, 0.6, 1]      # 绿色
}


class TimerDisplay(Label):
    """自定义倒计时显示组件"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = '64sp'
        self.bold = True
        self.color = COLORS['text']
        self.size_hint_y = 0.4


class TimerCard(BoxLayout):
    """单个计时器卡片"""
    
    timer_name = StringProperty("计时器")
    duration = NumericProperty(20)  # 默认分钟
    is_running = BooleanProperty(False)
    time_left = NumericProperty(0)  # 秒
    
    def __init__(self, name, default_minutes, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.timer_name = name
        self.duration = default_minutes
        self.time_left = default_minutes * 60
        self.padding = 20
        self.spacing = 10
        
        # 背景
        with self.canvas.before:
            Color(*COLORS['primary'] if '1' in name else COLORS['secondary'])
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # 标题
        self.title_label = Label(
            text=self.timer_name,
            font_size='24sp',
            color=COLORS['text'],
            size_hint_y=0.2
        )
        self.add_widget(self.title_label)
        
        # 时间显示
        self.time_display = TimerDisplay(text=self.format_time(self.time_left))
        self.add_widget(self.time_display)
        
        # 设置区域
        settings_box = BoxLayout(size_hint_y=0.3, spacing=10)
        
        self.minute_input = TextInput(
            text=str(self.duration),
            multiline=False,
            input_filter='int',
            font_size='20sp',
            halign='center',
            size_hint_x=0.4,
            background_color=[0.2, 0.2, 0.3, 1],
            foreground_color=[1, 1, 1, 1]
        )
        settings_box.add_widget(Label(text='分钟:', font_size='18sp', size_hint_x=0.3))
        settings_box.add_widget(self.minute_input)
        
        set_btn = Button(
            text='设置',
            size_hint_x=0.3,
            background_color=COLORS['accent'],
            color=[1, 1, 1, 1]
        )
        set_btn.bind(on_press=self.set_duration)
        settings_box.add_widget(set_btn)
        
        self.add_widget(settings_box)
    
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def format_time(self, seconds):
        """格式化时间为 MM:SS"""
        m, s = divmod(int(seconds), 60)
        return f"{m:02d}:{s:02d}"
    
    def set_duration(self, instance):
        """设置新的时长"""
        try:
            mins = int(self.minute_input.text)
            if mins > 0:
                self.duration = mins
                self.time_left = mins * 60
                self.time_display.text = self.format_time(self.time_left)
        except ValueError:
            pass
    
    def tick(self):
        """倒计时一秒"""
        if self.is_running and self.time_left > 0:
            self.time_left -= 1
            self.time_display.text = self.format_time(self.time_left)
            return self.time_left
        return 0
    
    def reset(self):
        """重置计时器"""
        self.is_running = False
        self.time_left = self.duration * 60
        self.time_display.text = self.format_time(self.time_left)
    
    def start(self):
        self.is_running = True
    
    def stop(self):
        self.is_running = False


class DualTimerApp(App):
    """主应用类"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_timer_index = 0  # 0 = 第一个, 1 = 第二个
        self.timers = []
        self.sound = None
        self.vibrator = None
        self.service = None
        self.is_active = False
        self.cycle_count = 0
        
        # 加载提示音
        self.load_sound()
        
        # 请求权限（Android）
        if platform == 'android':
            self.request_android_permissions()
    
    def request_android_permissions(self):
        """请求必要权限"""
        try:
            request_permissions([
                Permission.WAKE_LOCK,
                Permission.VIBRATE,
                Permission.FOREGROUND_SERVICE,
                Permission.POST_NOTIFICATIONS
            ])
        except Exception as e:
            print(f"Permission error: {e}")
    
    def load_sound(self):
        """加载提示音"""
        try:
            # 尝试加载自定义音效，如果不存在则使用系统音效
            sound_path = os.path.join(os.path.dirname(__file__), 'assets', 'alert.mp3')
            if os.path.exists(sound_path):
                self.sound = SoundLoader.load(sound_path)
            else:
                # 使用系统默认通知音
                if platform == 'android':
                    self.sound = None  # 将在 Android 层处理
        except Exception as e:
            print(f"Sound load error: {e}")
    
    def vibrate_and_sound(self):
        """振动三次并播放提示音"""
        # 播放声音
        if self.sound:
            self.sound.play()
        elif platform == 'android':
            # 使用 Android 系统通知音
            self.play_android_sound()
        
        # 振动三次
        if platform == 'android':
            self.vibrate_android()
        else:
            # 桌面端测试
            print("VIBRATE: 振动三次")
    
    def play_android_sound(self):
        """播放 Android 系统提示音"""
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            RingtoneManager = autoclass('android.media.RingtoneManager')
            Uri = autoclass('android.net.Uri')
            
            context = PythonActivity.mActivity
            notification = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
            r = RingtoneManager.getRingtone(context, notification)
            r.play()
        except Exception as e:
            print(f"Android sound error: {e}")
    
    def vibrate_android(self):
        """Android 振动三次"""
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Vibrator = autoclass('android.os.Vibrator')
            Context = autoclass('android.content.Context')
            
            activity = PythonActivity.mActivity
            vibrator = activity.getSystemService(Context.VIBRATOR_SERVICE)
            
            # 振动模式：振动500ms，暂停200ms，重复3次
            pattern = [0, 500, 200, 500, 200, 500]
            vibrator.vibrate(pattern, -1)
        except Exception as e:
            print(f"Vibrate error: {e}")
    
    def build(self):
        """构建 UI"""
        Window.clearcolor = COLORS['background']
        
        # 根布局
        root = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # 标题
        title = Label(
            text='双倒计时器',
            font_size='32sp',
            bold=True,
            color=COLORS['accent'],
            size_hint_y=0.1
        )
        root.add_widget(title)
        
        # 计时器容器
        timers_box = GridLayout(cols=1, spacing=20, size_hint_y=0.6)
        
        # 创建两个计时器
        self.timer1 = TimerCard("计时器 1 (工作)", 20)
        self.timer2 = TimerCard("计时器 2 (休息)", 10)
        
        self.timers = [self.timer1, self.timer2]
        timers_box.add_widget(self.timer1)
        timers_box.add_widget(self.timer2)
        
        root.add_widget(timers_box)
        
        # 状态显示
        self.status_label = Label(
            text='准备就绪',
            font_size='18sp',
            color=COLORS['accent'],
            size_hint_y=0.1
        )
        root.add_widget(self.status_label)
        
        # 控制按钮区域
        controls = GridLayout(cols=2, spacing=15, size_hint_y=0.2)
        
        self.start_btn = Button(
            text='开始',
            font_size='20sp',
            background_color=COLORS['accent'],
            color=[1, 1, 1, 1]
        )
        self.start_btn.bind(on_press=self.start_timers)
        
        self.stop_btn = Button(
            text='停止',
            font_size='20sp',
            background_color=COLORS['secondary'],
            color=[1, 1, 1, 1]
        )
        self.stop_btn.bind(on_press=self.stop_timers)
        
        self.reset_btn = Button(
            text='重置',
            font_size='20sp',
            background_color=[0.5, 0.5, 0.6, 1],
            color=[1, 1, 1, 1]
        )
        self.reset_btn.bind(on_press=self.reset_timers)
        
        self.cycle_label = Label(
            text='循环: 0',
            font_size='16sp',
            color=COLORS['text']
        )
        
        controls.add_widget(self.start_btn)
        controls.add_widget(self.stop_btn)
        controls.add_widget(self.reset_btn)
        controls.add_widget(self.cycle_label)
        
        root.add_widget(controls)
        
        # 启动后台服务（Android）
        if platform == 'android':
            self.start_service()
        
        # 绑定时钟事件
        Clock.schedule_interval(self.update_timer, 1)
        
        # 保持屏幕常亮（锁屏显示）
        if platform == 'android':
            self.keep_screen_on()
        
        return root
    
    def keep_screen_on(self):
        """保持屏幕常亮，允许锁屏显示"""
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            WindowManager = autoclass('android.view.WindowManager')
            
            activity = PythonActivity.mActivity
            window = activity.getWindow()
            window.addFlags(
                WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON |
                WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED |
                WindowManager.LayoutParams.FLAG_DISMISS_KEYGUARD |
                WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON
            )
        except Exception as e:
            print(f"Screen on error: {e}")
    
    def start_service(self):
        """启动后台服务"""
        try:
            service = AndroidService('双倒计时器', '计时器正在后台运行...')
            service.start('服务已启动')
            self.service = service
        except Exception as e:
            print(f"Service start error: {e}")
    
    def start_timers(self, instance):
        """开始计时"""
        self.is_active = True
        self.current_timer_index = 0
        
        # 重置并启动第一个计时器
        for t in self.timers:
            t.reset()
        
        self.timers[0].start()
        self.status_label.text = f'运行中: {self.timers[0].timer_name}'
        self.update_timer_highlight()
    
    def stop_timers(self, instance):
        """停止计时"""
        self.is_active = False
        for t in self.timers:
            t.stop()
        self.status_label.text = '已暂停'
    
    def reset_timers(self, instance):
        """重置所有计时器"""
        self.is_active = False
        self.current_timer_index = 0
        self.cycle_count = 0
        self.cycle_label.text = '循环: 0'
        
        for t in self.timers:
            t.reset()
        
        self.status_label.text = '准备就绪'
        self.update_timer_highlight()
    
    def update_timer_highlight(self):
        """更新当前活动计时器的视觉高亮"""
        for i, t in enumerate(self.timers):
            if i == self.current_timer_index and self.is_active:
                # 高亮当前计时器
                t.title_label.color = [1, 0.9, 0.3, 1]  # 黄色高亮
            else:
                t.title_label.color = COLORS['text']
    
    def update_timer(self, dt):
        """每秒更新"""
        if not self.is_active:
            return
        
        current_timer = self.timers[self.current_timer_index]
        remaining = current_timer.tick()
        
        # 更新通知（如果服务运行）
        if platform == 'android' and self.service:
            self.update_notification(current_timer)
        
        if remaining <= 0:
            # 当前计时器结束
            self.timer_finished()
    
    def timer_finished(self):
        """计时器结束处理"""
        # 播放提示音和振动
        self.vibrate_and_sound()
        
        # 切换到下一个计时器
        self.current_timer_index = (self.current_timer_index + 1) % 2
        next_timer = self.timers[self.current_timer_index]
        
        # 重置并启动下一个
        next_timer.reset()
        next_timer.start()
        
        # 更新循环计数（每完成两个计时器算一个循环）
        if self.current_timer_index == 0:
            self.cycle_count += 1
            self.cycle_label.text = f'循环: {self.cycle_count}'
        
        self.status_label.text = f'运行中: {next_timer.timer_name}'
        self.update_timer_highlight()
    
    def update_notification(self, timer):
        """更新通知栏信息"""
        # 实际实现需要在 service 中处理
        pass
    
    def on_pause(self):
        """应用进入后台"""
        return True  # 返回 True 保持服务运行
    
    def on_resume(self):
        """应用恢复"""
        pass
    
    def on_stop(self):
        """应用停止"""
        if self.service:
            try:
                self.service.stop()
            except:
                pass


if __name__ == '__main__':
    DualTimerApp().run()