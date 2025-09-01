import asyncio
import os
from telethon import events, types
from yt_dlp import YoutubeDL

def register(client):
    
    @client.on(events.NewMessage(pattern=r"\.media help", outgoing=True))
    async def media_help(event):
        """Помощь по медиа командам"""
        help_text = (
            "📁 **Media Commands Help:**\n\n"
            "**.download** - Скачать медиа в галерею (ответом)\n"
            "**.m <название>** - Найти и отправить музыку\n"
            "**.voice** - Распознать голосовое/видеокружок (ответом)\n"
            "**.voice auto on** - Автораспознавание голосовых\n"
            "**.voice auto off** - Выключить автораспознавание\n\n"
            "💡 **Примеры:**\n"
            "`.download` (ответом на фото/видео)\n"
            "`.m Alan Walker Faded` - Найти музыку\n"
            "`.m русская попса` - Русская музыка\n"
            "`.voice` (ответом на голосовое)"
        )
        await event.edit(help_text)

    @client.on(events.NewMessage(pattern=r"\.download", outgoing=True))
    async def download_media(event):
        """Скачивание медиа в галерею"""
        if not event.reply_to_msg_id:
            await event.edit("❌ Ответьте на сообщение с медиа")
            return
        
        reply_msg = await event.get_reply_message()
        
        if not (reply_msg.photo or reply_msg.video or reply_msg.document):
            await event.edit("❌ В сообщении нет медиа файла")
            return
        
        try:
            await event.edit("📥 Скачиваю медиа...")
            file_path = await reply_msg.download_media()
            
            downloads_dir = "/sdcard/Download/"
            if os.path.exists(downloads_dir):
                import shutil
                filename = os.path.basename(file_path)
                new_path = os.path.join(downloads_dir, filename)
                shutil.move(file_path, new_path)
                await event.edit(f"✅ Медиа сохранено в:\n`{new_path}`")
            else:
                await event.edit(f"✅ Медиа скачано:\n`{file_path}`")
                
        except Exception as e:
            await event.edit(f"❌ Ошибка скачивания: {str(e)}")

    @client.on(events.NewMessage(pattern=r"\.m (.+)", outgoing=True))
    async def search_music(event):
        """Поиск и отправка музыки в MP3"""
        search_query = event.pattern_match.group(1)
        
        try:
            await event.edit(f"🎵 Ищу: `{search_query}`...")
            
            # Настройки для скачивания MP3
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'music_%(id)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'default_search': 'ytsearch1',
                'noplaylist': True,
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                # Ищем трек
                info = ydl.extract_info(f"ytsearch:{search_query}", download=True)
                
                if not info or 'entries' not in info or not info['entries']:
                    await event.edit("❌ Музыка не найдена")
                    return
                
                # Берем первый результат
                video = info['entries'][0]
                title = video.get('title', 'Неизвестный трек')
                duration = video.get('duration', 0)
                
                # Форматируем длительность
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes}:{seconds:02d}"
                
                # Находим скачанный MP3 файл
                mp3_filename = ydl.prepare_filename(video).replace('.webm', '.mp3').replace('.m4a', '.mp3')
                
                if not os.path.exists(mp3_filename):
                    # Если автоматическое переименование не сработало, ищем файл
                    for file in os.listdir('.'):
                        if file.startswith('music_') and file.endswith('.mp3'):
                            mp3_filename = file
                            break
                    else:
                        await event.edit("❌ Ошибка конвертации в MP3")
                        return
                
                # Отправляем MP3 файл
                await event.edit("📤 Отправляю MP3...")
                await client.send_file(
                    event.chat_id,
                    mp3_filename,
                    caption=f"🎵 **{title}**\n⏱ **{duration_str}**\n🔍 **Запрос:** `{search_query}`",
                    attributes=[types.DocumentAttributeAudio(
                        duration=duration,
                        title=title,
                        performer="YouTube"
                    )]
                )
                
                # Удаляем временный файл
                try:
                    os.remove(mp3_filename)
                except:
                    pass
                
                await event.delete()
                
        except Exception as e:
            await event.edit(f"❌ Ошибка: {str(e)}")

    # Голосовые функции
    voice_settings = {}
    processing = False

    @client.on(events.NewMessage(pattern=r"^\.voice$", outgoing=True))
    async def voice_command(event):
        """Распознавание голосовых сообщений"""
        nonlocal processing
        
        if not event.reply_to_msg_id:
            await event.edit("❌ Ответьте на голосовое сообщение или видеокружок")
            return
        
        reply_msg = await event.get_reply_message()
        
        if not (reply_msg.voice or reply_msg.video_note):
            await event.edit("❌ Ответьте на голосовое сообщение или видеокружок")
            return
        
        if processing:
            await event.edit("⏳ Уже идет обработка предыдущего сообщения...")
            return
        
        processing = True
        try:
            status_msg = await event.edit("🎤 Распознавание речи...")
            await client.send_message("@smartspeech_sber_bot", reply_msg)
            
            for _ in range(30):
                await asyncio.sleep(1)
                messages = await client.get_messages("@smartspeech_sber_bot", limit=5)
                
                for msg in messages:
                    if msg.text and msg.text != "Аудиосообщение принято!":
                        await status_msg.edit(f"📝 **Результат:**\n\n{msg.text}")
                        processing = False
                        return
            
            await status_msg.edit("❌ Таймаут: бот не ответил")
            
        except Exception as e:
            await event.edit(f"❌ Ошибка: {str(e)}")
        finally:
            processing = False

    @client.on(events.NewMessage(pattern=r"\.voice auto on", outgoing=True))
    async def voice_auto_on(event):
        """Включение автораспознавания"""
        voice_settings[event.sender_id] = True
        await event.edit("✅ Автораспознавание голосовых включено")

    @client.on(events.NewMessage(pattern=r"\.voice auto off", outgoing=True))
    async def voice_auto_off(event):
        """Выключение автораспознавания"""
        voice_settings[event.sender_id] = False
        await event.edit("🔴 Автораспознавание голосовых выключено")

    print("✅ Модуль медиа загружен")
