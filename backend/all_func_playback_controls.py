import json
import time
import pygame
import random
import flet as ft
import threading
from backend.all_func_file_handling import load_config
from backend.logger import setup_logger
logger = setup_logger()

class PlaybackControls:
    def __init__(self, music_player):
        self.music_player = music_player
        self.seek_target_position = None  # Target seek position
        self.seek_start_time = None       # Timestamp when seek started
        self.seek_lock = threading.Lock() # Thread safety for seek operations
        self.is_playing = False
        self.duration = 0
        self.current_index = -1
        self.first_time=True
        self.loop_mode = 0  # 0: No Loop, 1: Loop Song, 2: Next Song, 3: Random Song

    def play_music(self, index):
        if self.first_time==True:
            self.first_time=False
        try:
            self.music_player.back_button.disabled = index <= 0
            self.music_player.next_button.disabled = index >= len(self.music_player.music_files) - 1
            self.music_player.back_button.update()
            self.music_player.next_button.update()

            if not 0 <= index < len(self.music_player.music_files):
                return

            file_metadata = self.music_player.music_files[index]

            pygame.mixer.music.stop()
            
            try:
                pygame.mixer.music.load(file_metadata["path"])
            except Exception as e:
                logger.exception("An error occurred while loading file: %s", e)
                return
            
            config = load_config() 
            config["current_music"] = index
            with open("config.json", "w") as json_file:
                json.dump(config, json_file)

            self.seek_target_position = None
            self._song_ended = False
            self.music_player.progress.value = 0
            self.music_player.progress.max = file_metadata["duration_seconds"]
            self.music_player.progress.update()
            self.current_index = index
            self.is_playing = True
            self.duration = file_metadata["duration_seconds"]
            self.music_player.current_song.value = f"[{index+1}/{len(self.music_player.music_files)}] - {file_metadata['name']}"
            self.music_player.song_duration.value = file_metadata["duration"]
            self.music_player.play_button.icon = ft.Icons.PAUSE_CIRCLE_OUTLINE_ROUNDED
            
            pygame.mixer.music.play()
            self.music_player.page.update()

        except Exception as e:
            print(f"Error in play_music: {e}")
            self.music_player.open(
                ft.SnackBar(
                    ft.Column(
                        [
                            ft.Text(f"Error in play_music: {e}"),
                            ft.Text(f"Playing next song...")
                        ]
                    )
                )
            )
            time.sleep(3)
            self.play_music(index+1)
            logger.exception("An error occurred: %s", e)

    def play_pause(self, e):
        if self.is_playing:
            pygame.mixer.music.pause()
            self.music_player.play_button.icon = ft.Icons.PLAY_CIRCLE_OUTLINE_ROUNDED
        elif self.current_index == -1 and self.music_player.music_files:
            self.play_music(0)
            return
        elif self.first_time and self.current_index!=0:
                self.play_music(self.current_index)
                return
        else:
            pygame.mixer.music.unpause()
            self.music_player.play_button.icon = ft.Icons.PAUSE_CIRCLE_OUTLINE_ROUNDED
        self.is_playing = not self.is_playing
        self.music_player.page.update()

    def next_song(self, e):
        if self.current_index + 1 < len(self.music_player.music_files):
            self.play_music(self.current_index + 1)

    def prev_song(self, e):
        if self.current_index - 1 >= 0:
            self.play_music(self.current_index - 1)

    def seek(self, e):
        if self.is_playing and self.duration > 0:
            with self.seek_lock:
                seek_pos = self.music_player.progress.value
                seek_pos = max(0, min(seek_pos, self.duration))
                self.seek_target_position = seek_pos
                self.seek_start_time = time.time()

                try:
                    pygame.mixer.music.set_pos(seek_pos)
                except Exception as e:
                    logger.exception("An error occurred while seeking: %s", e)
                    print(f"Seek error: {e}")

                self.music_player.progress.value = seek_pos
                self.music_player.page.update()

    def seek_forward(self, e):
        if self.is_playing and self.duration > 0:
            with self.seek_lock:
                if self.seek_target_position is not None:
                    current_pos = self.seek_target_position + (time.time() - self.seek_start_time)
                else:
                    current_pos = pygame.mixer.music.get_pos() / 1000
                
                new_pos = min(current_pos + 5, self.duration)
                self.seek_target_position = new_pos
                self.seek_start_time = time.time()

                try:
                    pygame.mixer.music.set_pos(new_pos)
                except Exception as e:
                    logger.exception("An error occurred while seeking: %s", e)
                    print(f"Seek error: {e}")

                self.music_player.progress.value = new_pos
                self.music_player.page.update()

    def seek_backward(self, e):
        if self.is_playing and self.duration > 0:
            with self.seek_lock:
                if self.seek_target_position is not None:
                    current_pos = self.seek_target_position + (time.time() - self.seek_start_time)
                else:
                    current_pos = pygame.mixer.music.get_pos() / 1000
                
                new_pos = max(current_pos - 5, 0)
                self.seek_target_position = new_pos
                self.seek_start_time = time.time()

                try:
                    pygame.mixer.music.set_pos(new_pos)
                except Exception as e:
                    logger.exception("An error occurred while seeking: %s", e)

                self.music_player.progress.value = new_pos
                self.music_player.page.update()

    def toggle_loop(self, e):
        self.loop_mode = (self.loop_mode + 1) % 4
        if self.loop_mode == 0:
            self.music_player.loop_button.icon = ft.Icons.LOOP_ROUNDED
            self.music_player.loop_button.icon_color = ft.Colors.GREY_600
        elif self.loop_mode == 1:
            self.music_player.loop_button.icon_color = ft.Colors.BLUE_200
        elif self.loop_mode == 2:
            self.music_player.loop_button.icon = ft.Icons.NEXT_PLAN_ROUNDED
            self.music_player.loop_button.icon_color = ft.Colors.BLUE_200
        elif self.loop_mode == 3:
            self.music_player.loop_button.icon = ft.Icons.SHUFFLE_ON_ROUNDED
        loop_modes = ["No Loop", "Loop Song", "Next Song", "Random Song"]
        self.music_player.loop_button.tooltip = loop_modes[self.loop_mode]
        self.music_player.loop_button.update()
        config = load_config()
        config["loop"] = loop_modes[self.loop_mode]
        with open("config.json", "w") as json_file:
            json.dump(config, json_file)

    def update_progress(self):
        while True:
            if self.is_playing and self.duration > 0:
                with self.seek_lock:
                    if self.seek_target_position is not None:
                        elapsed = time.time() - self.seek_start_time
                        current_pos = min(self.seek_target_position + elapsed, self.duration)
                    else:
                        current_pos = pygame.mixer.music.get_pos() / 1000
                        current_pos = max(0, min(current_pos, self.duration))

                    # Update progress display
                    self.music_player.song_progress.value = f"{int(current_pos // 60):02}:{int(current_pos % 60):02}/"
                    self.music_player.progress.value = current_pos
                    self.music_player.page.update()

                    # Handle song completion
                    if current_pos >= self.duration - 0.5 and not self._song_ended:
                        self._song_ended = True
                        if self.loop_mode == 0:  # No loop
                            self.is_playing = False
                            self.music_player.play_button.icon = ft.Icons.PLAY_CIRCLE_OUTLINE_ROUNDED
                            self.music_player.page.update()
                        elif self.loop_mode == 1:  # Loop current song
                            self.play_music(self.current_index)
                        elif self.loop_mode == 2:  # Next song
                            next_index = (self.current_index + 1) % len(self.music_player.music_files)
                            self.play_music(next_index)
                        elif self.loop_mode == 3:  # Random song
                            self.play_music(random.choice([i for i in range(len(self.music_player.music_files)) if i != self.current_index]))
            time.sleep(0.05)
