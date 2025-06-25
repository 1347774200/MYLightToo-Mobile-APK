#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文旅多媒体演出控制 - 移动端平板控制应用
专为演出操作人员设计的Android平板控制界面
"""

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.switch import Switch
from kivy.uix.slider import Slider
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.core.window import Window

import requests
import json
import threading
import time
from datetime import datetime
import websocket
import ssl

class ConnectionManager:
    """网络连接管理器"""
    
    def __init__(self):
        self.server_ip = "192.168.1.100"  # 主控制系统IP
        self.server_port = 8080
        self.websocket_port = 8081
        
        self.connected = False
        self.websocket = None
        self.last_heartbeat = 0
        
        # 状态回调
        self.status_callbacks = []
        
    def set_server_address(self, ip, port=8080):
        """设置服务器地址"""
        self.server_ip = ip
        self.server_port = port
        
    def add_status_callback(self, callback):
        """添加状态变化回调"""
        self.status_callbacks.append(callback)
        
    def notify_status_change(self, status):
        """通知状态变化"""
        for callback in self.status_callbacks:
            try:
                callback(status)
            except Exception as e:
                print(f"状态回调错误: {e}")
    
    def test_connection(self):
        """测试连接"""
        try:
            url = f"http://{self.server_ip}:{self.server_port}/api/status"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                self.connected = True
                self.notify_status_change("connected")
                return True
        except Exception as e:
            print(f"连接测试失败: {e}")
        
        self.connected = False
        self.notify_status_change("disconnected")
        return False
    
    def send_command(self, command, data=None):
        """发送控制命令"""
        try:
            url = f"http://{self.server_ip}:{self.server_port}/api/command"
            payload = {"command": command, "data": data or {}}
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"命令发送失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"发送命令错误: {e}")
            return None
    
    def get_scenes(self):
        """获取场景列表"""
        try:
            url = f"http://{self.server_ip}:{self.server_port}/api/scenes"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"获取场景列表失败: {e}")
        return []
    
    def get_status(self):
        """获取系统状态"""
        try:
            url = f"http://{self.server_ip}:{self.server_port}/api/status"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"获取状态失败: {e}")
        return {}


class LoginScreen(Screen):
    """登录界面"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'login'
        
        # 主布局
        main_layout = BoxLayout(orientation='vertical', padding=dp(50), spacing=dp(20))
        
        # 标题
        title = Label(
            text='文旅多媒体演出控制\n移动端控制台',
            font_size=dp(24),
            size_hint_y=0.3,
            halign='center'
        )
        title.bind(size=title.setter('text_size'))
        
        # 登录表单
        form_layout = GridLayout(cols=2, spacing=dp(10), size_hint_y=0.4)
        
        form_layout.add_widget(Label(text='服务器IP:', size_hint_x=0.3))
        self.ip_input = TextInput(
            text='192.168.1.100',
            multiline=False,
            size_hint_x=0.7
        )
        form_layout.add_widget(self.ip_input)
        
        form_layout.add_widget(Label(text='用户名:', size_hint_x=0.3))
        self.username_input = TextInput(
            text='operator',
            multiline=False,
            size_hint_x=0.7
        )
        form_layout.add_widget(self.username_input)
        
        form_layout.add_widget(Label(text='密码:', size_hint_x=0.3))
        self.password_input = TextInput(
            password=True,
            multiline=False,
            size_hint_x=0.7
        )
        form_layout.add_widget(self.password_input)
        
        # 按钮布局
        button_layout = BoxLayout(orientation='horizontal', spacing=dp(20), size_hint_y=0.2)
        
        self.connect_btn = Button(
            text='连接',
            size_hint_x=0.5,
            background_color=(0.2, 0.6, 1, 1)
        )
        self.connect_btn.bind(on_press=self.connect_to_server)
        
        self.test_btn = Button(
            text='测试连接',
            size_hint_x=0.5,
            background_color=(0.8, 0.8, 0.8, 1)
        )
        self.test_btn.bind(on_press=self.test_connection)
        
        button_layout.add_widget(self.test_btn)
        button_layout.add_widget(self.connect_btn)
        
        # 状态显示
        self.status_label = Label(
            text='请输入服务器信息并连接',
            size_hint_y=0.1,
            color=(0.7, 0.7, 0.7, 1)
        )
        
        # 组装界面
        main_layout.add_widget(title)
        main_layout.add_widget(form_layout)
        main_layout.add_widget(button_layout)
        main_layout.add_widget(self.status_label)
        
        self.add_widget(main_layout)
    
    def test_connection(self, instance):
        """测试连接"""
        self.status_label.text = '正在测试连接...'
        self.status_label.color = (1, 1, 0, 1)
        
        # 在后台线程中测试连接
        def test_thread():
            app = App.get_running_app()
            app.connection_manager.set_server_address(self.ip_input.text)
            
            if app.connection_manager.test_connection():
                Clock.schedule_once(lambda dt: self.update_status('连接成功！', (0, 1, 0, 1)), 0)
            else:
                Clock.schedule_once(lambda dt: self.update_status('连接失败，请检查IP地址和网络', (1, 0, 0, 1)), 0)
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def connect_to_server(self, instance):
        """连接到服务器"""
        if not self.username_input.text or not self.password_input.text:
            self.update_status('请输入用户名和密码', (1, 0, 0, 1))
            return
        
        self.status_label.text = '正在连接...'
        self.status_label.color = (1, 1, 0, 1)
        
        def connect_thread():
            app = App.get_running_app()
            app.connection_manager.set_server_address(self.ip_input.text)
            
            # 模拟登录验证
            if app.connection_manager.test_connection():
                # 保存用户信息
                app.current_user = self.username_input.text
                app.server_ip = self.ip_input.text
                
                Clock.schedule_once(lambda dt: self.login_success(), 0)
            else:
                Clock.schedule_once(lambda dt: self.update_status('连接失败', (1, 0, 0, 1)), 0)
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def update_status(self, text, color):
        """更新状态显示"""
        self.status_label.text = text
        self.status_label.color = color
    
    def login_success(self):
        """登录成功"""
        self.update_status('登录成功！正在进入控制界面...', (0, 1, 0, 1))
        
        # 切换到主控制界面
        app = App.get_running_app()
        app.root.current = 'main_control'


class MainControlScreen(Screen):
    """主控制界面"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'main_control'
        
        # 主布局
        main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # 顶部状态栏
        self.create_status_bar(main_layout)
        
        # 中间控制区域
        control_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=0.8)
        
        # 左侧场景控制
        self.create_scene_control(control_layout)
        
        # 右侧快速控制
        self.create_quick_control(control_layout)
        
        main_layout.add_widget(control_layout)
        
        # 底部操作按钮
        self.create_bottom_controls(main_layout)
        
        self.add_widget(main_layout)
        
        # 定时更新状态
        Clock.schedule_interval(self.update_status, 2.0)
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=dp(10))
        
        # 连接状态
        self.connection_status = Label(
            text='🔴 未连接',
            size_hint_x=0.3,
            color=(1, 0, 0, 1)
        )
        
        # 当前时间
        self.time_label = Label(
            text=datetime.now().strftime('%H:%M:%S'),
            size_hint_x=0.3,
            halign='center'
        )
        
        # 用户信息
        self.user_label = Label(
            text='用户: 未登录',
            size_hint_x=0.4,
            halign='right'
        )
        
        status_layout.add_widget(self.connection_status)
        status_layout.add_widget(self.time_label)
        status_layout.add_widget(self.user_label)
        
        parent.add_widget(status_layout)
    
    def create_scene_control(self, parent):
        """创建场景控制区域"""
        scene_layout = BoxLayout(orientation='vertical', size_hint_x=0.6)
        
        # 场景控制标题
        scene_title = Label(
            text='🎭 场景控制',
            size_hint_y=0.1,
            font_size=dp(18),
            bold=True
        )
        scene_layout.add_widget(scene_title)
        
        # 场景列表（滚动区域）
        from kivy.uix.scrollview import ScrollView
        
        scroll = ScrollView(size_hint_y=0.7)
        self.scene_grid = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        self.scene_grid.bind(minimum_height=self.scene_grid.setter('height'))
        
        # 添加示例场景按钮
        self.create_scene_buttons()
        
        scroll.add_widget(self.scene_grid)
        scene_layout.add_widget(scroll)
        
        # 场景控制按钮
        scene_control_layout = GridLayout(cols=3, spacing=dp(5), size_hint_y=0.2)
        
        self.play_btn = Button(
            text='▶️ 播放',
            background_color=(0, 0.8, 0, 1)
        )
        self.play_btn.bind(on_press=self.play_scene)
        
        self.pause_btn = Button(
            text='⏸️ 暂停',
            background_color=(1, 0.6, 0, 1)
        )
        self.pause_btn.bind(on_press=self.pause_scene)
        
        self.stop_btn = Button(
            text='⏹️ 停止',
            background_color=(0.8, 0, 0, 1)
        )
        self.stop_btn.bind(on_press=self.stop_scene)
        
        scene_control_layout.add_widget(self.play_btn)
        scene_control_layout.add_widget(self.pause_btn)
        scene_control_layout.add_widget(self.stop_btn)
        
        scene_layout.add_widget(scene_control_layout)
        parent.add_widget(scene_layout)
    
    def create_scene_buttons(self):
        """创建场景按钮"""
        # 示例场景
        scenes = [
            {'name': '开场音乐', 'description': '演出开场背景音乐'},
            {'name': '主持人介绍', 'description': '主持人上台介绍环节'},
            {'name': '节目表演1', 'description': '第一个节目表演'},
            {'name': '互动环节', 'description': '观众互动时间'},
            {'name': '节目表演2', 'description': '第二个节目表演'},
            {'name': '结束致谢', 'description': '演出结束感谢观众'},
        ]
        
        self.selected_scene = None
        
        for scene in scenes:
            btn = Button(
                text=f"{scene['name']}\n{scene['description']}",
                size_hint_y=None,
                height=dp(80),
                halign='center',
                valign='middle'
            )
            btn.bind(size=btn.setter('text_size'))
            btn.bind(on_press=lambda x, s=scene: self.select_scene(s))
            
            self.scene_grid.add_widget(btn)
    
    def create_quick_control(self, parent):
        """创建快速控制区域"""
        quick_layout = BoxLayout(orientation='vertical', size_hint_x=0.4)
        
        # 快速控制标题
        quick_title = Label(
            text='⚡ 快速控制',
            size_hint_y=0.1,
            font_size=dp(18),
            bold=True
        )
        quick_layout.add_widget(quick_title)
        
        # 音量控制
        volume_layout = BoxLayout(orientation='horizontal', size_hint_y=0.15)
        volume_layout.add_widget(Label(text='🔊 音量:', size_hint_x=0.3))
        
        self.volume_slider = Slider(
            min=0, max=100, value=50,
            size_hint_x=0.7
        )
        self.volume_slider.bind(value=self.on_volume_change)
        volume_layout.add_widget(self.volume_slider)
        
        quick_layout.add_widget(volume_layout)
        
        # 灯光控制
        light_layout = GridLayout(cols=2, spacing=dp(5), size_hint_y=0.3)
        
        light_buttons = [
            ('💡 全亮', (1, 1, 1, 1), self.lights_full),
            ('🌙 调暗', (0.3, 0.3, 0.8, 1), self.lights_dim),
            ('🔴 红色', (1, 0, 0, 1), self.lights_red),
            ('🟢 绿色', (0, 1, 0, 1), self.lights_green),
            ('🔵 蓝色', (0, 0, 1, 1), self.lights_blue),
            ('⚫ 全暗', (0.2, 0.2, 0.2, 1), self.lights_off),
        ]
        
        for text, color, callback in light_buttons:
            btn = Button(
                text=text,
                background_color=color,
                size_hint_y=None,
                height=dp(50)
            )
            btn.bind(on_press=callback)
            light_layout.add_widget(btn)
        
        quick_layout.add_widget(light_layout)
        
        # 紧急控制
        emergency_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=0.25)
        
        self.emergency_btn = Button(
            text='🚨 紧急停止',
            background_color=(1, 0, 0, 1),
            size_hint_y=0.6,
            font_size=dp(20),
            bold=True
        )
        self.emergency_btn.bind(on_press=self.emergency_stop)
        
        self.reset_btn = Button(
            text='🔄 系统重置',
            background_color=(0.8, 0.8, 0.8, 1),
            size_hint_y=0.4
        )
        self.reset_btn.bind(on_press=self.system_reset)
        
        emergency_layout.add_widget(self.emergency_btn)
        emergency_layout.add_widget(self.reset_btn)
        
        quick_layout.add_widget(emergency_layout)
        
        # 状态显示
        self.status_display = Label(
            text='系统状态: 待机',
            size_hint_y=0.2,
            color=(0.7, 0.7, 0.7, 1)
        )
        quick_layout.add_widget(self.status_display)
        
        parent.add_widget(quick_layout)
    
    def create_bottom_controls(self, parent):
        """创建底部控制按钮"""
        bottom_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=0.1)
        
        self.settings_btn = Button(
            text='⚙️ 设置',
            size_hint_x=0.25
        )
        self.settings_btn.bind(on_press=self.show_settings)
        
        self.monitor_btn = Button(
            text='📊 监控',
            size_hint_x=0.25
        )
        self.monitor_btn.bind(on_press=self.show_monitor)
        
        self.refresh_btn = Button(
            text='🔄 刷新',
            size_hint_x=0.25
        )
        self.refresh_btn.bind(on_press=self.refresh_data)
        
        self.logout_btn = Button(
            text='🚪 退出',
            size_hint_x=0.25,
            background_color=(0.8, 0.4, 0.4, 1)
        )
        self.logout_btn.bind(on_press=self.logout)
        
        bottom_layout.add_widget(self.settings_btn)
        bottom_layout.add_widget(self.monitor_btn)
        bottom_layout.add_widget(self.refresh_btn)
        bottom_layout.add_widget(self.logout_btn)
        
        parent.add_widget(bottom_layout)
    
    def select_scene(self, scene):
        """选择场景"""
        self.selected_scene = scene
        self.status_display.text = f"已选择: {scene['name']}"
        self.status_display.color = (0, 1, 0, 1)
    
    def play_scene(self, instance):
        """播放场景"""
        if self.selected_scene:
            app = App.get_running_app()
            result = app.connection_manager.send_command('play_scene', {
                'scene_name': self.selected_scene['name']
            })
            
            if result:
                self.status_display.text = f"正在播放: {self.selected_scene['name']}"
                self.status_display.color = (0, 1, 0, 1)
            else:
                self.status_display.text = "播放失败"
                self.status_display.color = (1, 0, 0, 1)
        else:
            self.status_display.text = "请先选择场景"
            self.status_display.color = (1, 1, 0, 1)
    
    def pause_scene(self, instance):
        """暂停场景"""
        app = App.get_running_app()
        app.connection_manager.send_command('pause_scene')
        self.status_display.text = "已暂停"
        self.status_display.color = (1, 0.6, 0, 1)
    
    def stop_scene(self, instance):
        """停止场景"""
        app = App.get_running_app()
        app.connection_manager.send_command('stop_scene')
        self.status_display.text = "已停止"
        self.status_display.color = (0.8, 0.8, 0.8, 1)
    
    def on_volume_change(self, instance, value):
        """音量变化"""
        app = App.get_running_app()
        app.connection_manager.send_command('set_volume', {'volume': int(value)})
    
    def lights_full(self, instance):
        """灯光全亮"""
        app = App.get_running_app()
        app.connection_manager.send_command('lights_control', {'action': 'full'})
    
    def lights_dim(self, instance):
        """灯光调暗"""
        app = App.get_running_app()
        app.connection_manager.send_command('lights_control', {'action': 'dim'})
    
    def lights_red(self, instance):
        """红色灯光"""
        app = App.get_running_app()
        app.connection_manager.send_command('lights_control', {'action': 'red'})
    
    def lights_green(self, instance):
        """绿色灯光"""
        app = App.get_running_app()
        app.connection_manager.send_command('lights_control', {'action': 'green'})
    
    def lights_blue(self, instance):
        """蓝色灯光"""
        app = App.get_running_app()
        app.connection_manager.send_command('lights_control', {'action': 'blue'})
    
    def lights_off(self, instance):
        """灯光全暗"""
        app = App.get_running_app()
        app.connection_manager.send_command('lights_control', {'action': 'off'})
    
    def emergency_stop(self, instance):
        """紧急停止"""
        app = App.get_running_app()
        app.connection_manager.send_command('emergency_stop')
        
        # 显示确认对话框
        popup = Popup(
            title='紧急停止',
            content=Label(text='已执行紧急停止！\n所有设备已停止运行。'),
            size_hint=(0.8, 0.4)
        )
        popup.open()
    
    def system_reset(self, instance):
        """系统重置"""
        app = App.get_running_app()
        app.connection_manager.send_command('system_reset')
        self.status_display.text = "系统已重置"
        self.status_display.color = (0, 1, 0, 1)
    
    def show_settings(self, instance):
        """显示设置"""
        # TODO: 实现设置界面
        pass
    
    def show_monitor(self, instance):
        """显示监控"""
        # TODO: 实现监控界面
        pass
    
    def refresh_data(self, instance):
        """刷新数据"""
        app = App.get_running_app()
        if app.connection_manager.test_connection():
            self.status_display.text = "数据已刷新"
            self.status_display.color = (0, 1, 0, 1)
        else:
            self.status_display.text = "刷新失败"
            self.status_display.color = (1, 0, 0, 1)
    
    def logout(self, instance):
        """退出登录"""
        app = App.get_running_app()
        app.root.current = 'login'
    
    def update_status(self, dt):
        """更新状态显示"""
        # 更新时间
        self.time_label.text = datetime.now().strftime('%H:%M:%S')
        
        # 更新连接状态
        app = App.get_running_app()
        if hasattr(app, 'connection_manager') and app.connection_manager.connected:
            self.connection_status.text = '🟢 已连接'
            self.connection_status.color = (0, 1, 0, 1)
        else:
            self.connection_status.text = '🔴 未连接'
            self.connection_status.color = (1, 0, 0, 1)
        
        # 更新用户信息
        if hasattr(app, 'current_user'):
            self.user_label.text = f'用户: {app.current_user}'


class MobileControllerApp(App):
    """移动控制器应用主类"""
    
    def build(self):
        """构建应用界面"""
        # 设置窗口标题
        self.title = '文旅多媒体演出控制 - 移动端'
        
        # 初始化连接管理器
        self.connection_manager = ConnectionManager()
        
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 添加登录界面
        login_screen = LoginScreen()
        sm.add_widget(login_screen)
        
        # 添加主控制界面
        main_screen = MainControlScreen()
        sm.add_widget(main_screen)
        
        # 设置默认界面
        sm.current = 'login'
        
        return sm
    
    def on_start(self):
        """应用启动时调用"""
        print("移动控制器应用已启动")
        
        # 设置窗口大小（开发时使用）
        if hasattr(Window, 'size'):
            Window.size = (800, 600)
    
    def on_stop(self):
        """应用停止时调用"""
        print("移动控制器应用已停止")
        
        # 清理连接
        if hasattr(self, 'connection_manager'):
            self.connection_manager.connected = False


if __name__ == '__main__':
    # 运行应用
    MobileControllerApp().run()
