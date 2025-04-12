import flet as ft
from frontend.music_player import MusicPlayer

def main(page: ft.Page):
    page.title = "Music Player"
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode=ft.ThemeMode.SYSTEM
    page.padding=ft.padding.all(0)
    player=MusicPlayer(page)
    page.add(player)

ft.app(target=main)
