import asyncio
from telethon import events

def register(client):
    auto_delete_settings = {}
    deletion_tasks = {}

    @client.on(events.NewMessage(pattern=r"\.dl (\d+)$", outgoing=True))
    async def auto_delete_on(event):
        """Включение автоудаления"""
        try:
            seconds = int(event.pattern_match.group(1))
            
            if seconds < 5:
                await event.edit("❌ Минимальное время: 5 секунд")
                return
                
            if seconds > 86400:  # 24 часа
                await event.edit("❌ Максимальное время: 86400 секунд (24 часа)")
                return
            
            chat_id = event.chat_id
            auto_delete_settings[chat_id] = seconds
            
            # Форматируем время
            if seconds < 60:
                time_str = f"{seconds} сек"
            elif seconds < 3600:
                time_str = f"{seconds//60} мин {seconds%60} сек"
            else:
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                time_str = f"{hours} час {minutes} мин"
            
            await event.edit(f"✅ Автоудаление включено\n⏰ Сообщения будут удаляться через: {time_str}")
            
        except ValueError:
            await event.edit("❌ Укажите число в секундах\nПример: `.dl 60` - удаление через минуту")

    @client.on(events.NewMessage(pattern=r"\.dl off$", outgoing=True))
    async def auto_delete_off(event):
        """Выключение автоудаления"""
        chat_id = event.chat_id
        
        if chat_id in auto_delete_settings:
            del auto_delete_settings[chat_id]
            
            # Останавливаем задачу если есть
            if chat_id in deletion_tasks:
                deletion_tasks[chat_id].cancel()
                del deletion_tasks[chat_id]
            
            await event.edit("🔴 Автоудаление выключено")
        else:
            await event.edit("ℹ️ Автоудаление и так не активно в этом чате")

    @client.on(events.NewMessage(pattern=r"\.dl status$", outgoing=True))
    async def auto_delete_status(event):
        """Статус автоудаления"""
        chat_id = event.chat_id
        
        if chat_id in auto_delete_settings:
            seconds = auto_delete_settings[chat_id]
            
            if seconds < 60:
                time_str = f"{seconds} секунд"
            elif seconds < 3600:
                time_str = f"{seconds//60} минут {seconds%60} секунд"
            else:
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                time_str = f"{hours} часов {minutes} минут"
            
            await event.edit(f"🟢 Автоудаление активно\n⏰ Время: {time_str}")
        else:
            await event.edit("🔴 Автоудаление не активно")

    @client.on(events.NewMessage(pattern=r"\.dl help$", outgoing=True))
    async def auto_delete_help(event):
        """Помощь по автоудалению"""
        help_text = (
            "🗑️ **Auto Delete Help:**\n\n"
            "**.dl <секунды>** - Включить автоудаление\n"
            "**.dl off** - Выключить автоудаление\n"
            "**.dl status** - Статус автоудаления\n"
            "**.dl help** - Эта помощь\n\n"
            "**Примеры:**\n"
            "`.dl 60` - Удалять через 1 минуту\n"
            "`.dl 300` - Удалять через 5 минут\n"
            "`.dl 3600` - Удалять через 1 час\n\n"
            "⚠️ Работает только для ваших сообщений"
        )
        await event.edit(help_text)

    @client.on(events.NewMessage(outgoing=True))
    async def handle_auto_delete(event):
        """Обработка автоудаления сообщений"""
        chat_id = event.chat_id
        
        if chat_id in auto_delete_settings and not event.text.startswith('.dl'):
            seconds = auto_delete_settings[chat_id]
            message_id = event.id
            
            # Запускаем задачу удаления
            deletion_tasks[message_id] = asyncio.create_task(
                delete_message_after_delay(client, chat_id, message_id, seconds)
            )

    async def delete_message_after_delay(client, chat_id, message_id, delay):
        """Удаление сообщения через задержку"""
        await asyncio.sleep(delay)
        
        try:
            await client.delete_messages(chat_id, message_id)
        except Exception as e:
            print(f"Error deleting message: {e}")
        finally:
            if message_id in deletion_tasks:
                del deletion_tasks[message_id]

    print("✅ Модуль автоудаления загружен")
