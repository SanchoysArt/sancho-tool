import os
import subprocess
from telethon import events

MODULE_NAME = "media_download"

def register(client):
    # Команда .sk <ссылка>
    @client.on(events.NewMessage(pattern=r'^\.sk (.+)', outgoing=True))
    async def sk_download(event):
        url = event.pattern_match.group(1)
        await event.edit("⬇️ Скачиваю видео, подождите...")

        try:
            # Временный файл для скачивания
            temp_file = "/data/data/com.termux/files/home/sancho-tool/temp_media.mp4"

            # yt-dlp скачивает видео
            process = subprocess.run(
                ["yt-dlp", "-o", temp_file, url],
                capture_output=True,
                text=True
            )

            if process.returncode != 0:
                await event.edit(f"❌ Ошибка скачивания:\n{process.stderr}")
                return

            # Отправляем видео в чат
            await client.send_file(event.chat_id, temp_file, caption="✅ Видео готово!")
            
            # Удаляем временный файл
            os.remove(temp_file)
            await event.delete()

        except Exception as e:
            await event.edit(f"❌ Ошибка: {e}")
