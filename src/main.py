import flet as ft

# MyLibrary
import voiceCtrl as vc


def main(page: ft.Page):
    page.title = "Flet_voiceControl"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.bgcolor = ft.Colors.WHITE

    page.add(vc.voiceControlApp())


ft.run(main)
