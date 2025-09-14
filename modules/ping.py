import asyncio
import time
from telethon import events

class PingModule:
    def __init__(self, client):
        self.client = client
        self.start_time = time.time()
        print("Модуль ping загружен")
        
    async def register_handlers(self):
        """Регистрация обработчиков команды .ping"""
        
        @self.client.on(events.NewMessage(pattern=r'\.ping$'))
        async def ping_handler(event):
            """Обработчик команды .ping"""
            try:
                start = time.time()
                message = await event.reply('...')
                end = time.time()
                ping_time = (end - start) * 1000
                
                response = f"ping - {ping_time:.0f} ms"
                await message.edit(response)
                
            except Exception as e:
                print(f"Ошибка в ping: {e}")

def setup(client):
    """Функция установки модуля"""
    return PingModule(client)
