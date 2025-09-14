import asyncio
from telethon import events
from datetime import datetime

class TimeModule:
    def __init__(self, client):
        self.client = client
        print("Модуль time загружен")
        
    async def register_handlers(self):
        """Регистрация обработчиков команды .time"""
        
        @self.client.on(events.NewMessage(pattern=r'\.time$'))
        async def time_handler(event):
            """Обработчик команды .time"""
            try:
                # Московское время (UTC+3)
                moscow_time = datetime.utcnow().timestamp() + 3 * 3600
                time_str = datetime.fromtimestamp(moscow_time).strftime("%H:%M:%S")
                
                response = f"time - {time_str}"
                await event.reply(response)
                
            except Exception as e:
                print(f"Ошибка в time: {e}")

def setup(client):
    """Функция установки модуля"""
    return TimeModule(client)
