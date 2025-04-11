# this method stores images to the folder, instead of base_64 format. did not improve performance considerably
# if implementing, fix this: search did not work. check others.

import json
import os
import flet as ft
from mutagen import File
import base64
from mutagen.oggopus import OggOpus
from mutagen.flac import Picture, error as FLACError
from mutagen.id3 import ID3, ID3NoHeaderError
from backend.logger import setup_logger

logger = setup_logger()

def load_config():
    try:
        with open("config.json", "r") as json_file:
            config = json.load(json_file)
            return config
    except FileNotFoundError:
        return {"folder_path": None, "current_music": None, "theme": "dark", "sort_by": "Name"}
    except Exception as e:
        logger.exception("An error occurred: %s", e)
        return {}

def load_current_music():
    config = load_config()
    return config.get("current_music", None), config.get("loop", None)

def load_folder_path():
    config = load_config()
    return config.get("folder_path", None)

def load_theme():
    config = load_config()
    return config.get("theme", None)

def choose_folder(self, e):
    def on_result(result: ft.FilePickerResultEvent):
        if result.path:
            load_music(self, result.path)
            config = {
                "folder_path": result.path,
                "current_music": None,
                "song_progress": 0,
                "sort_by": "Name"
            }
            with open("config.json", "w") as json_file:
                json.dump(config, json_file)

    file_picker = ft.FilePicker(on_result=on_result)
    file_picker.file_type = ft.FilePickerFileType.AUDIO
    self.page.overlay.append(file_picker)
    self.page.update()
    file_picker.get_directory_path()

def load_music(self, folder_path):
    music_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith((".mp3", ".opus", ".wav"))]
    if not music_files:
        self.file_list.controls.append(
            ft.Row([ft.Text("No Music Files Found (supported: OPUS, MP3, WAV)")], alignment=ft.MainAxisAlignment.CENTER)
        )
        self.page.update()
        return

    self.current_song.value = "Loading. Please Wait..."
    self.current_song.update()

    # Clear previous album covers and music file list
    if not os.path.exists("images"):
        os.makedirs("images")  # Create image folder if not exists
    else:
        for img_file in os.listdir("images"):
            img_path = os.path.join("images", img_file)
            try:
                os.remove(img_path)  # Clear out old images
            except Exception as e:
                logger.exception(f"Error clearing old images: {e}")

    self.music_files = []
    self.file_list.controls.clear()

    for index, file in enumerate(music_files):
        file_path = os.path.join(folder_path, file)
        audio_file = File(file_path)
        song_duration = audio_file.info.length if audio_file else 0
        minutes = int(song_duration // 60)
        seconds = int(song_duration % 60)
        formatted_duration = f"{minutes:02}:{seconds:02}"

        file_metadata = {
            "name": os.path.splitext(os.path.basename(file))[0],
            "path": file_path,
            "date_modified": os.path.getmtime(file_path),
            "size": os.path.getsize(file_path),
            "type": os.path.splitext(file)[1].lower(),
            "duration": formatted_duration,
            "duration_seconds": song_duration,
        }

        album_cover = None
        if file_metadata["type"] == ".mp3":
            album_cover = extract_mp3_cover(file_path)
        elif file_metadata["type"] == ".opus":
            album_cover = extract_opus_cover(file_path)

        if album_cover:
            album_cover_base64 = base64.b64encode(album_cover).decode("utf-8")
            file_metadata["album_cover"] = f"{album_cover_base64}"
            save_album_cover(file_metadata["name"], album_cover)  # Save the album cover to disk
        else:
            file_metadata["album_cover"] = None

        self.music_files.append(file_metadata)

        if file_metadata["album_cover"]:
            album_cover_widget = ft.Image(src_base64=file_metadata["album_cover"], height=40, width=100)
        else:
            album_cover_widget = ft.Image(src="/images/default1.png", height=40, width=100)

        self.file_list.controls.append(
            ft.TextButton(
                content=ft.Row(
                    [
                        ft.Row([ft.Text(index + 1), album_cover_widget, ft.Text(file_metadata['name'])], spacing=0),
                        ft.Text(file_metadata['duration']),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                on_click=lambda e, i=index: self.playback_controls.play_music(i),
                key=index,
            )
        )

        progress_value = int(((index + 1) / len(music_files)) * 100)
        self.progress.value = progress_value
        self.progress.update()

    self.current_song.value = f"[1/{len(self.music_files)}] - {self.music_files[0]['name']}"
    self.progress.disabled = False
    self.search_button.disabled = False
    self.sort_button.disabled = False
    self.play_button.disabled = False
    self.next_button.disabled = False
    self.loop_button.disabled = False
    self.seek_forward_button.disabled = False
    self.seek_backward_button.disabled = False
    self.page.update()

def extract_mp3_cover(file_path):
    """Extract album cover for MP3 files."""
    try:
        try:
            tags = ID3(file_path)
        except ID3NoHeaderError:
            tags = ID3()
        apic_tags = []
        for tag in tags.values():
            if tag.FrameID.startswith('APIC'):
                apic_tags.append(tag)
        if apic_tags:
            return apic_tags[0].data
    except Exception as e:
        print(f"Error extracting MP3 cover: {e}")
    return None

def extract_opus_cover(file_path):
    """Extract album cover for OPUS files."""
    try:
        file_ = OggOpus(file_path)
        for b64_data in file_.get("METADATA_BLOCK_PICTURE", []):
            try:
                data = base64.b64decode(b64_data)
                picture = Picture(data)
                return picture.data
            except (TypeError, ValueError, FLACError):
                continue
    except Exception as e:
        print(f"Error extracting OPUS cover: {e}")
    return None

def save_album_cover(file_name, album_cover_data):
    """Save the album cover image to disk."""
    cover_path = os.path.join("images", f"{file_name}_cover.jpg")
    with open(cover_path, "wb") as f:
        f.write(album_cover_data)

def sort_playlist(self, e):
    """Sorting using stored metadata"""
    def sort_by_name(file_metadata):
        return file_metadata["name"].lower()

    def sort_by_date_modified(file_metadata):
        return file_metadata["date_modified"]

    def sort_by_size(file_metadata):
        return file_metadata["size"]

    def sort_by_type(file_metadata):
        return file_metadata["type"]

    sort_methods = [sort_by_name, sort_by_date_modified, sort_by_size, sort_by_type]
    sort_labels = ["Name", "Recently Added", "Size (Ascending)", "Type"]

    self.current_sort = (self.current_sort + 1) % len(sort_methods)
    sort_method = sort_methods[self.current_sort]
    sort_label = sort_labels[self.current_sort]

    self.music_files.sort(key=sort_method, reverse=True if sort_label == "Recently Added" else False)

    if sort_label == "Name":
        self.sort_button.icon = ft.Icons.SORT_BY_ALPHA_ROUNDED
    elif sort_label == "Recently Added":
        self.sort_button.icon = ft.Icons.ADD_ROUNDED
    elif sort_label == "Size (Ascending)":
        self.sort_button.icon = ft.Icons.FORMAT_SIZE_ROUNDED
    elif sort_label == "Type":
        self.sort_button.icon = ft.Icons.SORT_ROUNDED

    self.sort_button.tooltip = f"Sort by {sort_label}"
    self.sort_button.update()
    display_files(self)

    # Save the sort method to config
    config = load_config()
    config["sort_by"] = sort_label
    with open("config.json", "w") as json_file:
        json.dump(config, json_file)

def search_files(self, e):
    """Filters the music files based on the search text."""
    query = self.search_field.value.lower()
    
    if query == "": 
        display_files(self, [(index, file) for index, file in enumerate(self.music_files)])
    else:
        filtered_files = [
            (index, file) for index, file in enumerate(self.music_files) if query in file["name"].lower()
        ]
        display_files(self, filtered_files)

def display_files(self, files=None):
    """Update the file list UI based on the provided filtered list."""
    progress_ring = ft.ProgressRing(width=36, height=36, stroke_width=4)
    progress_container = ft.Row([ft.Column([progress_ring, ft.Text(), ft.Text(), ft.Text()], alignment=ft.MainAxisAlignment.CENTER)], expand=True)
    self.page.overlay.append(progress_container)
    self.page.update()

    if not files:
        files = [(index, file) for index, file in enumerate(self.music_files)]
    
    self.file_list.controls.clear()

    for index, file_metadata in files:
        if file_metadata["album_cover"]:
            album_cover_widget = ft.Image(src_base64=file_metadata["album_cover"], height=40, width=100)
        else:
            album_cover_widget = ft.Image(src="/images/default1.png", height=40, width=100)

        self.file_list.controls.append(
            ft.TextButton(
                content=ft.Row(
                    [
                        ft.Row([ft.Text(index + 1), album_cover_widget, ft.Text(file_metadata['name'])], spacing=0),
                        ft.Text(file_metadata['duration']),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                on_click=lambda e, i=index: self.playback_controls.play_music(i),
                key=index,
            )
        )

    self.page.overlay.remove(progress_container)
    self.page.update()
