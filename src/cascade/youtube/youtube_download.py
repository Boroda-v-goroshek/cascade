import yt_dlp
import os
from typing import cast
from typing import Any

def download_youtube_video(url: str, output_path: str, quality: str='best'):
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'format': quality,
        'quiet': False,
        'no_warnings': False,
        'progress_hooks': [progress_hook],
    }
    
    with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
        info = ydl.extract_info(url, download=True)
        return info

def progress_hook(d):
    if d['status'] == 'downloading':
        print(f"Скачивание: {d['_percent_str']} | Скорость: {d['_speed_str']}")
    elif d['status'] == 'finished':
        print("✓ Скачивание завершено")

