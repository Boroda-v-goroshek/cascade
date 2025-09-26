import re
from urllib.parse import quote

import yt_dlp


def search_youtube_videos(search_query: str, max_results: int) -> list[dict]:
    """Search videos from youtube on query.
    
    Parameters
    ---------
    search_query: str
        Quary for yotube search line
    max_results: int
        Max count videos
    
    Returns
    -------
    list[dict]
        List of videos info
    """
    print(f"🔍 Ищем видео по запросу: '{search_query}'")
    
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_url = f"ytsearch{max_results}:{search_query}"
            result = ydl.extract_info(search_url, download=False)
            
            videos = []
            if 'entries' in result:
                for entry in result['entries']:
                    if entry:
                        video_info = {
                            'url': entry.get('url', ''),
                            'title': entry.get('title', ''),
                            'duration': entry.get('duration', 0),
                            'view_count': entry.get('view_count', 0),
                        }
                        videos.append(video_info)
            
            print(f"    📊 Найдено видео: {len(videos)}")
            return videos
            
    except Exception as e:
        print(f"    ❌ Ошибка поиска: {e}")
        return []


def contains_keywords(text: str, keywords: list[str]) -> bool:
    """Check text on include keywords.
    
    Parameters
    ---------
    text: str
        Input text for checking
    keywords: list[str]
        List of keywords
    
    Returns
    -------
    bool
        True, if text include once of keywords
    """
    if not text:
        return False
    
    text_lower = text.lower()
    for keyword in keywords:
        if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', text_lower):
            return True
    return False


def filter_videos_by_keywords(videos: list[dict], keywords: list[str]) -> list[dict]:
    """Filter input videos for keywords in video's names.
    
    Parameters
    ----------
    videos: list[dict]
        Input videos
    keywords: list[str]
        Input list with target keywords
    
    Returns
    -------
    list[dict]
        Filtered list of videos
    """
    filtered_videos = []
    
    for video in videos:
        title = video.get('title', '')
        if contains_keywords(title, keywords):
            filtered_videos.append(video)
    
    print(f"    🎯 После фильтрации осталось: {len(filtered_videos)} видео")
    return filtered_videos
