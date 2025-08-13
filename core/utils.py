import os
import zipfile
import tempfile

SIZE_UNITS = ["B","KB","MB","GB","TB","PB"]

def human_size(n):
    if n is None:
        return "—"
    d = float(n)
    i = 0
    while d >= 1024 and i < len(SIZE_UNITS) - 1:
        d /= 1024.0
        i += 1
    return f"{d:.1f} {SIZE_UNITS[i]}" if i else f"{int(d)} {SIZE_UNITS[i]}"

def unzip_first(zip_path):
    try:
        with zipfile.ZipFile(zip_path) as zf:
            member = next((m for m in zf.infolist() if not m.is_dir()), None)
            if not member:
                return None, None, None
            fd, tmp = tempfile.mkstemp(prefix="bitburner_", suffix="_img.bin")
            os.close(fd)
            size_written = 0
            with zf.open(member, "r") as src, open(tmp, "wb") as out:
                while True:
                    b = src.read(4 * 1024 * 1024)
                    if not b:
                        break
                    out.write(b)
                    size_written += len(b)
            return tmp, size_written, member.filename
    except Exception:
        return None, None, None
