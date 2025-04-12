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
        return {"folder_path": None,"current_music": None, "theme": "dark", "sort_by": "Name"}
    except Exception as e:
        logger.exception("An error occurred while loading config: %s", e)
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
                "theme": "dark",
                "sort_by": "Name"
            }
            with open("config.json", "w") as json_file:
                json.dump(config, json_file)

    file_picker = ft.FilePicker(on_result=on_result)
    # file_picker.allowed_extensions=["mp3", "opus"]
    # file_picker.file_type = ft.FilePickerFileType.CUSTOM
    file_picker.file_type = ft.FilePickerFileType.AUDIO
    self.page.overlay.append(file_picker)
    self.page.update()
    file_picker.get_directory_path()

def load_music(self, folder_path):
    music_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith((".mp3",".opus",".wav"))]  # add ".m4a" support
    if not music_files:
        self.file_list.controls.append(
            ft.Row(
                [
                    ft.Text("No Music Files Found (supported: OPUS, MP3, WAV)")
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )
        )
        self.page.update()
        return
    self.current_song.value="Loading. Please Wait..."
    self.current_song.update()
    self.music_files = []
    self.file_list.controls.clear()

    for index, file in enumerate(music_files):
        
        file_path = os.path.join(folder_path, file)

        audio_file = File(file_path)
        if audio_file is not None:
            song_duration = audio_file.info.length
        else:
            song_duration = 0
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
        else:
            file_metadata["album_cover"] = None

        self.music_files.append(file_metadata)


        if file_metadata["album_cover"]:
            # album_cover_widget.src_base64=file_metadata["album_cover"]
            album_cover_widget = ft.Image(src_base64=file_metadata["album_cover"],height=40, width=100)
        else:
            album_cover_widget = ft.Image(src_base64="""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""",height=40, width=100)


        self.file_list.controls.append(
            ft.TextButton(
                content=ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Text(index+1),
                                album_cover_widget,
                                ft.Text(file_metadata['name'])
                            ],
                            spacing=0
                        ),
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
        logger.exception("An error occurred while extracting mp3 cover: %s", e)
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
        logger.exception("An error occurred while extracting OPUS cover: %s", e)
    return None

def sort_playlist(self, e):
    """ Sorting  using stored metadata """
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

    self.music_files.sort(key=sort_method, reverse=True if sort_label=="Recently Added" else False)

    if sort_label=="Name":
        self.sort_button.icon=ft.Icons.SORT_BY_ALPHA_ROUNDED
    elif sort_label=="Recently Added":
        self.sort_button.icon=ft.Icons.ADD_ROUNDED
    elif sort_label=="Size (Ascending)":
        self.sort_button.icon=ft.Icons.FORMAT_SIZE_ROUNDED
    elif sort_label=="Type":
        self.sort_button.icon=ft.Icons.SORT_ROUNDED

    self.sort_button.tooltip = f"Sort by {sort_label}"
    self.sort_button.update()
    display_files(self) 
    config = load_config()
    config["sort_by"] = sort_label
    with open("config.json", "w") as json_file:
        json.dump(config, json_file)

def search_files(self, e):
    """Filters the music files based on the search text."""
    query = self.search_field.value.lower()
    
    if query == "": 
        self.search_field.bar_trailing=None
        self.search_field.update()
        display_files(self, [(index, file) for index, file in enumerate(self.music_files)])
    else:
        filtered_files = [
            (index, file) for index, file in enumerate(self.music_files) if query in file["name"].lower()
        ]
        self.search_field.bar_trailing=[ft.IconButton(ft.Icons.CLOSE_ROUNDED, on_click=self.close_search)]
        self.search_field.update()
        display_files(self, filtered_files)

def display_files(self, files=None):
    """Update the file list UI based on the provided filtered list."""
    
    progress_ring = ft.ProgressRing(width=36, height=36, stroke_width=4)
    progress_container = ft.Row(
        [
            ft.Column(
                [
                    progress_ring,
                    ft.Text(),
                    ft.Text(),
                    ft.Text(),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True
            )
        ]
    )
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
                        ft.Row(
                            [
                                ft.Text(index + 1),
                                album_cover_widget,
                                ft.Text(file_metadata['name'])
                            ],
                            spacing=0
                        ),
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
