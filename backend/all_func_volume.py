from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import comtypes
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

class VolumeControl:
    def __init__(self):
        self.is_muted = False
        self.previous_volume = self.get_current_volume
        comtypes.CoInitialize()
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))
        self.bass_level = 50
        self.mid_level = 50
        self.treble_level = 50


    def get_current_volume(self):
        """Get the current volume level as a percentage (0 to 100)."""
        return round(self.volume.GetMasterVolumeLevelScalar() * 100)

    def set_volume(self, volume_percent):
        """Set the system volume to the specified percentage (0 to 100)."""
        volume_scalar = volume_percent / 100
        self.volume.SetMasterVolumeLevelScalar(volume_scalar, None)

    def mute_unmute(self):
        """Toggle mute/unmute."""
        if self.is_muted:
            self.is_muted = False
            self.set_volume(self.previous_volume)
            return "unmute", "Mute"
        else:
            self.is_muted = True
            self.previous_volume = self.get_current_volume() 
            self.set_volume(0)
            return "mute", "Unmute"
