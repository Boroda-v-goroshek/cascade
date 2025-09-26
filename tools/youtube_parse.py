import os
from typing import Set
import time

from src.cascade.youtube.youtube_download import download_youtube_video
from src.cascade.youtube.parse_procces import search_youtube_videos
from src.cascade.youtube.parse_procces import filter_videos_by_keywords
from src.cascade.config.parser import get_parser
from src.cascade.config.config_loader import load_config


def download_youtube_videos_by_keywords(
    search_queries: list[str],
    keywords: list[str], 
    output_path: str, 
    max_videos: int = 10,
    quality: str = 'best[height<=720]'
):
    """Main function: download videos from yotube for keywords.
    
    Parameters
    ----------
    search_quaries: list[str]
        List of queries for youtube
    keywords: list[str]
        List of target words
    output_path: str
        Path to output directory
    max_videos: int
        Count videos for each keywords
    quality: str
        Video quality
    """
    print("🚀 Запуск скачивания видео с YouTube")
    print("=" * 60)
    
    os.makedirs(output_path, exist_ok=True)
    
    downloaded_urls: Set[str] = set()
    total_downloaded = 0
    print(f"🎯 Ключевые слова: {', '.join(keywords)}")
    print(f"📁 Выходная директория: {output_path}")
    
    for search_query in search_queries:
        print(f"🔍 Поисковый запрос: '{search_query}'")
        print()
        
        all_videos = search_youtube_videos(search_query, max_videos)
        
        if not all_videos:
            print("❌ Не найдено видео по заданным ключевым словам")
            return
        
        filtered_videos = filter_videos_by_keywords(all_videos, keywords)
        
        if not filtered_videos:
            print("❌ После фильтрации по ключевым словам не осталось видео")
            return
        
        print(f"\n Начинаем скачивание {len(filtered_videos)} видео...")
        print("-" * 50)
        
        for i, video in enumerate(filtered_videos, 1):
            url = video.get('url', '')
            title = video.get('title', '')
            
            if not url:
                continue

            if url in downloaded_urls:
                print(f"⏭️  [{i}] Пропускаем дубликат: {title}")
                continue
            
            print(f"\n📹 [{i}/{len(filtered_videos)}] {title}")
            print(f"    🔗 {url}")
            
            if download_youtube_video(url, output_path, quality):
                downloaded_urls.add(url)
                total_downloaded += 1
            
            time.sleep(2)
    
    print("\n" + "=" * 60)
    print(f"🎉 Скачивание завершено!")
    print(f"📊 Всего успешно скачано: {total_downloaded} видео")
    print(f"💾 Сохранено в: {output_path}")


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    opts = load_config(args.config_path)
    download_youtube_videos_by_keywords(opts.search_queries, opts.keywords, opts.output_path, opts.max_videos, opts.quality)