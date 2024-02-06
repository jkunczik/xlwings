import winreg
from contextlib import suppress
import itertools
import os
from pathlib import Path

def fullname_url_to_local_path_with_registry(url) -> str:
    key = RegKey(r"Software\SyncEngines\Providers\OneDrive", winreg.HKEY_CURRENT_USER)
    for subkey in key.enumerate_subkeys():
        values = subkey.get_values() 
        if values["UrlNamespace"] in url:
            # the mount point path of shared folders is often shorter that the path in the url. If for example the
            # folder "Documents/MySharedFolder" is synced by another person, the moint point can directly point to this 
            # path. Hence, we need to skip these non existing directories:
            sub_path_parts = url.replace(values["UrlNamespace"], "").split("/")
            path = Path(values["MountPoint"])
            while not (path / sub_path_parts[0]).exists():
                sub_path_parts.pop(0)
                if len(sub_path_parts) == 0:
                    raise FileNotFoundError("Mount point was found, but not the path within it.")
            
            return (path / "\\".join(sub_path_parts)).as_posix()
    raise FileNotFoundError("The URL is not present in the OneDrive registry")


class RegKey:
    """Represents a registry key
    """
    def __init__(self, path: str, hkey=winreg.HKEY_LOCAL_MACHINE, flags=0):
        """initializes a new registry key instance

        :param path: path of the registry key (without HKEY)
        :type path: str
        :param hkey: HKEY the path resides in, defaults to winreg.HKEY_LOCAL_MACHINE
        :type hkey: int, optional
        :param flags: flags, defaults to 0
        :type flags: int, optional
        """
        self.path = path
        self.hkey = hkey
        self.flags = flags
        self.key = winreg.OpenKey(hkey, path, 0, winreg.KEY_READ|flags)

    def enumerate_subkeys(self):
        with suppress(WindowsError), self.key as k:
            for i in itertools.count():
                key_path = winreg.EnumKey(k, i)
                yield RegKey(os.path.join(self.path, key_path), self.hkey, self.flags)

    def enumerate_key_values(self):
        with suppress(WindowsError), self.key as k:
            for i in itertools.count():
                yield winreg.EnumValue(k, i)

    def get_values(self):
        values = {}
        for value in self.enumerate_key_values():
            values[value[0]] = value[1]
        return values