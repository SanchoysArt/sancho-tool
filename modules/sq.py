from telethon import events
import asyncio

class AutoSendModule:
    def __init__(self, client):
        self.client = client
    
    def register(self):
        @self.client.on(events.NewMessage(pattern=r'\.sq (\d+) (.+)', outgoing=True))
        async def auto_send_handler(event):
            """Автоотправка сообщения через указанное время"""
            try:
                # Получаем время и текст из команды
                seconds = int(event.pattern_match.group(1))
                text = event.pattern_match.group(2)
                
                # Подтверждаем запуск
                await event.edit(f"⏰ **Сообщение будет отправлено через {seconds} секунд**")
                
                # Ждем указанное время
                await asyncio.sleep(seconds)
                
                # Отправляем сообщение
                await event.respond(text)
                
                # Удаляем служебное сообщение
                await event.delete()
                
            except ValueError:
                await event.edit("❌ **Неверный формат времени! Используй: .sq <секунды> <текст>**")
            except Exception as e:
                await event.edit(f"❌ **Ошибка: {str(e)}**")

def register(client):
    auto_send_module = AutoSendModule(client)
    auto_send_module.register()
