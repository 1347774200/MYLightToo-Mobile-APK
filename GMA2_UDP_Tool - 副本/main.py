#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文旅多媒体演出控制 - 移动端应用入口（简化测试版本）
"""

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

class SimpleTestApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # 标题
        title = Label(
            text='文旅多媒体演出控制\n移动端测试版',
            font_size='20sp',
            size_hint_y=0.3
        )

        # 测试按钮
        test_btn = Button(
            text='测试按钮',
            size_hint_y=0.2
        )
        test_btn.bind(on_press=self.on_test_press)

        # 状态标签
        self.status_label = Label(
            text='应用已启动，点击测试按钮',
            size_hint_y=0.5
        )

        layout.add_widget(title)
        layout.add_widget(test_btn)
        layout.add_widget(self.status_label)

        return layout

    def on_test_press(self, instance):
        self.status_label.text = '测试按钮已点击！\nAPK构建成功！'

if __name__ == '__main__':
    SimpleTestApp().run()
