import os
import re
import subprocess


def check_volume(path):
    path_to_file = os.path.join(os.getcwd(), path)
    process = subprocess.Popen(
        f'ffmpeg\\bin\\ffmpeg.exe -hide_banner -i {path_to_file} -filter:a volumedetect -f null NUL',
        stderr=subprocess.PIPE)
    _, stderr = process.communicate()

    if process.returncode == 0:
        for l in stderr.decode('utf-8').split('\n'):
            if 'volume:' in l:
                return re.findall(r'-?\d+\.?\d*', l)[-1]
