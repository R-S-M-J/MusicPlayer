import json
import flet as ft
import pygame
import threading
from backend.all_func_volume import VolumeControl
from backend.all_func_file_handling import choose_folder, load_config, load_current_music, load_theme, sort_playlist, search_files, display_files, load_music, load_folder_path
from backend.all_func_playback_controls import PlaybackControls
from math import pi


class MusicPlayer(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.music_files = []

        pygame.mixer.init()
        self.volume_control = VolumeControl()
        self.playback_controls = PlaybackControls(self)

        self.page_theme=ft.IconButton(
            ft.Icons.DARK_MODE_ROUNDED,
            icon_size=30,
            on_click=self.toggle_theme,
            tooltip="Dark Mode",
            rotate=ft.transform.Rotate(0, alignment=ft.alignment.center),
            animate_rotation=ft.animation.Animation(300, ft.AnimationCurve.FAST_OUT_SLOWIN),
        )
        
        self.file_list = ft.Column()
        self.current_song = ft.Text("Select a folder")
        self.progress = ft.Slider(min=0, max=100, value=0, on_change=lambda e:self.playback_controls.seek(e), disabled=True, expand=1)
        
        self.search_field=ft.SearchBar(
            on_change=lambda e: search_files(self,e),
            bar_hint_text="Search By Song Name...",
            bar_leading=ft.IconButton(ft.Icons.SEARCH_ROUNDED, disabled=True),
            visible=False,
            expand=1,
        )
        self.search_button=ft.IconButton(
            ft.Icons.SEARCH_ROUNDED,
            icon_size=30,
            on_click=self.toggle_search,
            disabled=True
        )
        self.play_button = ft.IconButton(
            ft.Icons.PLAY_CIRCLE_OUTLINE_ROUNDED, 
            icon_size=50,
            on_click=lambda e:self.playback_controls.play_pause(e), 
            disabled=True,
        )
        self.next_button = ft.IconButton(
            ft.Icons.SKIP_NEXT_ROUNDED, 
            icon_size=50,
            on_click=lambda e:self.playback_controls.next_song(e), 
            disabled=True,
            tooltip="Next Song"
        )
        self.back_button = ft.IconButton(
            ft.Icons.SKIP_PREVIOUS_ROUNDED, 
            icon_size=50,
            on_click=lambda e:self.playback_controls.prev_song(e), 
            disabled=True,
            tooltip="Previous Song"
        )
        self.sort_button = ft.IconButton(
            ft.Icons.SORT_BY_ALPHA_ROUNDED, 
            icon_size=30,
            on_click=lambda e: sort_playlist(self, e),
            disabled=True,
            tooltip="Sort by Name"
        )
        self.current_sort = 0  # 0 = Name, 1 = Date Modified, 2 = Size, 3 = Type
        self.folder_button = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN_OUTLINED, 
            icon_size=30,
            on_click=lambda e: choose_folder(self, e)
        )
        
        self.loop_button = ft.IconButton(
            ft.Icons.LOOP_ROUNDED, 
            icon_size=30,
            icon_color=ft.Colors.GREY_600,
            on_click=lambda e:self.playback_controls.toggle_loop(e),
            disabled=True,
            tooltip="No Loop"
        )

        self.equalizer_button = ft.IconButton(
            ft.Icons.EQUALIZER_ROUNDED,
            icon_size=30,
            on_click=lambda e: self.show_equalizer(e),
            tooltip="Equalizer",
            disabled=False
        )

        self.seek_forward_button = ft.IconButton(
            ft.Icons.FAST_FORWARD_ROUNDED, 
            icon_size=30,
            on_click=lambda e:self.playback_controls.seek_forward(e),
            disabled=True,
            tooltip="+5 sec"
        )

        self.seek_backward_button = ft.IconButton(
            ft.Icons.FAST_REWIND_ROUNDED, 
            icon_size=30,
            on_click=lambda e:self.playback_controls.seek_backward(e),
            disabled=True,
            tooltip="-5 sec"
        )
        
        self.volume_slider = ft.Slider(min=0, max=100, 
            value=self.volume_control.get_current_volume(), 
            divisions=100,
            label="{value}",
            on_change=self.set_volume,
        )
        self.mute_button=ft.IconButton(
            ft.Icons.VOLUME_UP_ROUNDED if self.volume_slider.value>50 else ft.Icons.VOLUME_MUTE_ROUNDED if self.volume_slider.value==0 else ft.Icons.VOLUME_DOWN_ROUNDED,
            on_click=self.mute_unmute
        )
        self.song_progress=ft.Text()
        self.song_duration=ft.Text("00:00")
        
        self.update_progress_thread = threading.Thread(target=self.playback_controls.update_progress, daemon=True)
        self.update_progress_thread.start()

        self.play_list_container = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        ft.Column(
                            [
                                self.file_list
                            ],
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        expand=1
                    )
                ]
            ),
            height=self.page.height-200
        )
        self.first_time=True

        # ===== equalizer doesnt work for now
        # self.bass_level = 50 
        # self.mid_level = 50
        # self.treble_level = 50
        # self.equalizer_sheet = ft.BottomSheet(
        #     content=ft.Container(
        #         content=ft.Column(
        #             [
        #                 ft.Text("Equalizer", style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD)),
        #                 ft.Slider(min=0, max=100, divisions=100, value=self.bass_level, label="Bass", on_change=self.adjust_bass),
        #                 ft.Slider(min=0, max=100, divisions=100, value=self.mid_level, label="Mid", on_change=self.adjust_mid),
        #                 ft.Slider(min=0, max=100, divisions=100, value=self.treble_level, label="Treble", on_change=self.adjust_treble),
        #             ],
        #             alignment=ft.MainAxisAlignment.CENTER,
        #             horizontal_alignment=ft.CrossAxisAlignment.CENTER
        #         ),
        #         padding=ft.padding.all(10)
        #     ),
        # )
        # self.page.overlay.append(self.equalizer_sheet)

    # def show_equalizer(self, e):
    #     """Toggle Equalizer sheet visibility."""
    #     self.equalizer_sheet.open=True
    #     self.page.update()

    # def adjust_bass(self, e):
    #     """Adjust bass level."""
    #     self.bass_level = e.control.value
    #     self.volume_control.set_equalizer(bass=self.bass_level)
    #     print(f"Adjusting Bass to: {self.bass_level}")

    # def adjust_mid(self, e):
    #     """Adjust mid level."""
    #     self.mid_level = e.control.value
    #     self.volume_control.set_equalizer(mid=self.mid_level)
    #     print(f"Adjusting Mid to: {self.mid_level}")

    # def adjust_treble(self, e):
    #     """Adjust treble level."""
    #     self.treble_level = e.control.value
    #     self.volume_control.set_equalizer(treble=self.treble_level)
    #     print(f"Adjusting Treble to: {self.treble_level}")


    def close_search(self, e):
        self.search_field.value=""
        self.search_field.update()
        search_files(self, "")

    def toggle_theme(self, e):
        if self.page.theme_mode=="dark":
            self.page_theme.icon=ft.Icons.LIGHT_MODE_ROUNDED
            self.page.theme_mode="light"
            self.page_theme.tooltip="Light mode"
            self.page_theme.rotate.angle += pi
        else:
            self.page_theme.icon=ft.Icons.DARK_MODE_ROUNDED
            self.page.theme_mode="dark"
            self.page_theme.tooltip="Dark mode"
            self.page_theme.rotate.angle += pi
        self.page.update()
        config = load_config() 
        config["theme"] = self.page.theme_mode
        with open("config.json", "w") as json_file:
            json.dump(config, json_file)

    def set_volume(self, e):
        """Set the volume based on the slider value."""
        self.volume_control.set_volume(self.volume_slider.value)
        if int(self.volume_slider.value) == 0:
            self.mute_button.icon = ft.Icons.VOLUME_MUTE_ROUNDED  
        elif int(self.volume_slider.value) < 50:
            self.mute_button.icon = ft.Icons.VOLUME_DOWN_ROUNDED  
        else:
            self.mute_button.icon = ft.Icons.VOLUME_UP_ROUNDED
        self.mute_button.update()
    
    def mute_unmute(self, e):
        """Toggle mute/unmute."""
        action, tooltip = self.volume_control.mute_unmute()
        if action=="unmute" and self.first_time:
            self.page.open(ft.SnackBar(ft.Text(f"Please make sure to turn off mute from system volume first.")))
            self.first_time=False
        self.mute_button.icon = ft.Icons.VOLUME_OFF_ROUNDED if action == "mute" else ft.Icons.VOLUME_UP_ROUNDED if self.volume_slider.value > 50 else ft.Icons.VOLUME_MUTE_ROUNDED if self.volume_slider.value == 0 else ft.Icons.VOLUME_DOWN_ROUNDED
        self.mute_button.tooltip = tooltip
        self.mute_button.update()

    def toggle_search(self, e):
        """show or hide search bar"""
        self.search_field.visible= not self.search_field.visible
        if self.search_field.visible==True:
            self.search_field.value=""
            self.search_field.focus()
            self.play_list_container.height=self.page.height-265
        else:
            self.play_list_container.height=self.page.height-200
            display_files(self, [(index, file) for index, file in enumerate(self.music_files)])
        self.page.update()

    def handle_key_down(self, e):
        """Handle key press events."""
        if e.key == ' ':
            self.playback_controls.play_pause(None)
        elif e.key == 'ArrowRight':
            self.playback_controls.seek_forward(None) 
        elif e.key == 'ArrowLeft':
            self.playback_controls.seek_backward(None) 
        elif e.key == 'ArrowDown': 
            self.playback_controls.next_song(None) 
        elif e.key == 'ArrowUp': 
            self.playback_controls.prev_song(None) 

    def did_mount(self):
        theme=load_theme()
        if theme:
            if theme=="light":
                self.page_theme.rotate.angle += pi
                self.page_theme.icon=ft.Icons.LIGHT_MODE_ROUNDED
                self.page_theme.tooltip="Light mode"
            self.page.theme_mode=theme
        folder_path = load_folder_path()
        if folder_path:
            load_music(self, folder_path)
            current_music, looping = load_current_music()
            
            config = load_config()
            saved_sort_by = config.get("sort_by", "Name")
            sort_labels = ["Name", "Recently Added", "Size (Ascending)", "Type"]
            
            if saved_sort_by in sort_labels:
                self.current_sort = sort_labels.index(saved_sort_by) - 1
                sort_playlist(self, None)

            if current_music is not None:
                self.playback_controls.current_index = current_music
                self.current_song.value = f"[{current_music + 1}/{len(self.music_files)}] {self.music_files[current_music]['name']}"
                self.current_song.update()

            if looping is not None:
                if looping=="No Loop":
                    pass
                elif looping=="Loop Song":
                    self.playback_controls.toggle_loop(None)
                elif looping=="Next Song":
                    self.playback_controls.toggle_loop(None)
                    self.playback_controls.toggle_loop(None)
                elif looping=="Random Song":
                    self.playback_controls.toggle_loop(None)
                    self.playback_controls.toggle_loop(None)
                    self.playback_controls.toggle_loop(None)

        return super().did_mount()


    def resize(self, e):
        if self.search_field.visible:
            self.play_list_container.height = self.page.height - 265
        else:
            self.play_list_container.height = self.page.height - 200
        self.update()

    def build(self):
        self.page.on_resized = self.resize
        self.page.on_keyboard_event = self.handle_key_down
        self.padding=ft.padding.all(0)
        self.content = ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            self.search_field,
                            self.play_list_container
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    padding=ft.Padding(left=10, right=10, top=10, bottom=0)
                ),
                
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row([self.progress]),
                            ft.Row(
                                [
                                    self.current_song,
                                    ft.Row(
                                        [
                                            self.song_progress,
                                            self.song_duration
                                        ],
                                        spacing=0
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Row(
                                [
                                    ft.Container(
                                        content=ft.Row(
                                            [
                                                self.mute_button,
                                                self.volume_slider
                                            ],
                                            spacing=0
                                        ),
                                    ),
                                    ft.Row(
                                        [
                                            self.folder_button,
                                            self.search_button,
                                            self.sort_button,
                                            self.seek_backward_button,
                                            self.back_button,
                                            self.play_button,
                                            self.next_button,
                                            self.seek_forward_button,
                                            self.loop_button,
                                            self.page_theme,
                                            # self.equalizer_button
                                            ft.IconButton(
                                                ft.Icons.CODE_ROUNDED,
                                                on_click=lambda e:self.page.launch_url("https://github.com/R-S-M-J/MusicPlayer")
                                            )
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            )
                        ],
                        expand=1
                    ),
                    padding=ft.Padding(left=10, right=10, top=0, bottom=0),
                    border_radius=20,
                    blur=ft.Blur(10, 50, ft.BlurTileMode.MIRROR),
                ),
            ],
            spacing=0
        )
        return super().build()
