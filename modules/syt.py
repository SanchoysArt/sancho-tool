from telethon import events
import requests
import os
import re

class VideoDownloadModule:
    def __init__(self, client):
        self.client = client
    
    def register(self):
        @self.client.on(events.NewMessage(pattern=r'\.sk (https?://\S+)', outgoing=True))
        async def video_download_handler(event):
            """Скачать видео с TikTok через API"""
            try:
                url = event.pattern_match.group(1)
                
                if 'tiktok.com' not in url:
                    await event.edit("❌ **Поддерживаются только TikTok ссылки**")
                    return
                
                await event.edit("📥 **Скачиваю через API...**")
                
                # Используем бесплатный API
                api_url = f"https://tikwm.com/api/?url={url}"
                response = requests.get(api_url, timeout=30)
                data = response.json()
                
                if data['code'] == 0:
                    video_url = data['data']['play']
                    title = data['data']['title']
                    
                    # Скачиваем видео
                    video_data = requests.get(video_url, timeout=60).content
                    
                    # Сохраняем временный файл
                    with open('tiktok_video.mp4', 'wb') as f:
                        f.write(video_data)
                    
                    # Отправляем видео
                    await event.edit("📤 **Отправляю видео...**")
                    await event.client.send_file(
                        event.chat_id,
                        'tiktok_video.mp4',
                        caption=f"🎬 **{title}**\n\n📹 Скачано через Sancho-Tool",
                        supports_streaming=True
                    )
                    
                    # Удаляем временный файл
                    if os.path.exists('tiktok_video.mp4'):
                        os.remove('tiktok_video.mp4')
                    await event.delete()
                    
                else:
                    await event.edit("❌ **Не удалось скачать видео**")
                    
            except Exception as e:
                await event.edit(f"❌ **Ошибка:** {str(e)}")

def register(client):
    video_download_module = VideoDownloadModule(client)
    video_download_module.register()
