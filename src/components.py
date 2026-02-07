import flet as ft
from dataclasses import field

# 各種ボタンなどのコンポーネント
@ft.control
class VoiceRecogButton(ft.Button):
    expand: bool = field(default=True)
    bgcolor: ft.Colors = ft.Colors.GREY_900