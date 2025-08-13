import os
import sys
import re
import platform
import psutil
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class Device:
    path: str
    name: str
    size: Optional[int]
    protected: bool = False

IS_WIN = os.name == "nt"
IS_MAC = sys.platform == "darwin"
IS_LIN = sys.platform.startswith("linux")

def _linux_base(dev):
    if not dev or not dev.startswith("/dev/"):
        return None
    b = os.path.basename(dev)
    if b.startswith(("nvme","mmcblk")):
        return re.sub(r"p\d+$", "", b)
    return re.sub(r"\d+$", "", b)

def _linux_size_bytes(base):
    try:
        with open(f"/sys/block/{base}/size","r") as f:
            sectors = int(f.read().strip() or "0")
        ssz = 512
        p2 = f"/sys/block/{base}/queue/logical_block_size"
        if os.path.exists(p2):
            with open(p2,"r") as f:
                ssz = int(f.read().strip() or "512")
        return sectors * ssz
    except Exception:
        return None

def _mac_base(dev):
    if not dev or not dev.startswith("/dev/disk"):
        return None
    m = re.match(r"^/dev/disk(\d+)s\d+$", dev)
    return f"disk{m.group(1)}" if m else None

def _win_letter_to_phys(letter):
    vol = f"\\\\.\\{letter.strip(':')}:"
    GENERIC_READ = 0x80000000
    FILE_SHARE_READ  = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    OPEN_EXISTING = 3
    CreateFileW = ctypes.windll.kernel32.CreateFileW
    CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                            wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    CreateFileW.restype  = wintypes.HANDLE
    CloseHandle = ctypes.windll.kernel32.CloseHandle
    h = CreateFileW(vol, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, None, OPEN_EXISTING, 0, None)
    if int(h) == -1 or h is None:
        return None
    try:
        IOCTL_STORAGE_GET_DEVICE_NUMBER = 0x002D1080
        class STORAGE_DEVICE_NUMBER(ctypes.Structure):
            _fields_ = [("DeviceType", wintypes.DWORD),
                        ("DeviceNumber", wintypes.DWORD),
                        ("PartitionNumber", wintypes.DWORD)]
        buf = STORAGE_DEVICE_NUMBER()
        bytes_ret = wintypes.DWORD(0)
        ok = ctypes.windll.kernel32.DeviceIoControl(
            h, IOCTL_STORAGE_GET_DEVICE_NUMBER,
            None, 0, ctypes.byref(buf), ctypes.sizeof(buf),
            ctypes.byref(bytes_ret), None)
        if not ok:
            return None
        return r"\\.\PhysicalDrive{}".format(buf.DeviceNumber)
    finally:
        CloseHandle(h)

def _win_disk_size_bytes(phys_path):
    IOCTL_DISK_GET_LENGTH_INFO = 0x0007405C
    GENERIC_READ = 0x80000000
    FILE_SHARE_READ  = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    OPEN_EXISTING = 3
    class LARGE_INTEGER(ctypes.Structure):
        _fields_ = [("QuadPart", ctypes.c_longlong)]
    h = ctypes.windll.kernel32.CreateFileW(phys_path, GENERIC_READ,
                                           FILE_SHARE_READ | FILE_SHARE_WRITE,
                                           None, OPEN_EXISTING, 0, None)
    if int(h) == -1 or h is None:
        return None
    try:
        li = LARGE_INTEGER()
        ret = wintypes.DWORD(0)
        ok = ctypes.windll.kernel32.DeviceIoControl(h, IOCTL_DISK_GET_LENGTH_INFO,
                                                    None, 0, ctypes.byref(li),
                                                    ctypes.sizeof(li),
                                                    ctypes.byref(ret), None)
        if not ok:
            return None
        return int(li.QuadPart)
    finally:
        ctypes.windll.kernel32.CloseHandle(h)

def system_disk_path():
    if IS_LIN:
        root_dev = next((p.device for p in psutil.disk_partitions(all=True) if p.mountpoint=="/"), None)
        if not root_dev:
            return None
        base = _linux_base(root_dev)
        return f"/dev/{base}" if base else None
    if IS_MAC:
        root_dev = next((p.device for p in psutil.disk_partitions(all=True) if p.mountpoint=="/"), None)
        if not root_dev:
            return None
        base = _mac_base(root_dev)
        return f"/dev/{base}" if base else None
    if IS_WIN:
        sys_drive = os.environ.get("SystemDrive", "C:")
        return _win_letter_to_phys(sys_drive)
    return None

def list_devices() -> List[Device]:
    devs: Dict[str, Device] = {}
    if IS_LIN:
        for p in psutil.disk_partitions(all=True):
            base = _linux_base(p.device or "")
            if not base:
                continue
            path = f"/dev/{base}"
            devs.setdefault(path, Device(path, base, _linux_size_bytes(base)))
        try:
            for b in os.listdir("/sys/block"):
                if b.startswith(("loop","ram","fd")):
                    continue
                path = f"/dev/{b}"
                devs.setdefault(path, Device(path, b, _linux_size_bytes(b)))
        except Exception:
            pass
    elif IS_MAC:
        for p in psutil.disk_partitions(all=True):
            base = _mac_base(p.device or "")
            if not base:
                continue
            path = f"/dev/{base}"
            devs.setdefault(path, Device(path, base, None))
        for i in range(0, 32):
            path = f"/dev/disk{i}"
            if os.path.exists(path):
                devs.setdefault(path, Device(path, f"disk{i}", None))
    else:
        seen = {}
        for p in psutil.disk_partitions(all=True):
            letter = (p.device or "").strip("\\/").split(":")[0]
            if not letter or not letter[0].isalpha():
                continue
            phys = _win_letter_to_phys(letter + ":")
            if not phys:
                continue
            seen.setdefault(phys, set()).add(letter.upper()+":")
        for phys, letters in seen.items():
            devs.setdefault(phys, Device(phys, f"{phys} ({', '.join(sorted(letters))})", _win_disk_size_bytes(phys)))
    sysdisk = system_disk_path()
    for d in devs.values():
        if sysdisk and d.path.lower() == sysdisk.lower():
            d.protected = True
    lst = list(devs.values())
    lst.sort(key=lambda x: (x.protected, x.name))
    return lst
