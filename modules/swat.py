from telethon import events
from telethon.tl.types import Message

class SwatModule:
    def __init__(self, client):
        self.client = client
        self.enabled = False
        self.translate_map = {
            ord("з"): "3", ord("е"): "3", ord("Е"): "3", ord("З"): "3", ord("z"): "3",
            ord("о"): "0", ord("o"): "0", ord("и"): "u", ord("И"): "U", ord("i"): "1",
            ord("А"): "4", ord("а"): "4", ord("a"): "4", ord("A"): "4",
        }
    
    def register(self):
        @self.client.on(events.NewMessage(pattern=r'\.ebal$', outgoing=True))
        async def swat_handler(event):
            """Включить или отключить режим swat"""
            self.enabled = not self.enabled
            
            if self.enabled:
                await event.edit("🤍 **Режим swat включен** 🤍")
            else:
                await event.edit("❌ **Режим swat выключен**")
        
        @self.client.on(events.NewMessage(pattern=r'\.swat ', outgoing=True))
        async def swat_text_handler(event):
            """Эваулировать текст (ответ на сообщение)"""
            reply = await event.get_reply_message()
            if not reply or not reply.text:
                await event.edit("❌ **Ответь на сообщение с текстом**")
                return
            
            translated_text = reply.text.translate(self.translate_map)
            await event.edit(f"**Эваулированный текст:**\n\n{translated_text}")
        
        @self.client.on(events.NewMessage(outgoing=True))
        async def message_watcher(event):
            """Автоматически эваулировать исходящие сообщения"""
            if self.enabled and event.text and not event.text.startswith('.'):
                translated_text = event.text.translate(self.translate_map)
                if event.text != translated_text:
                    await event.edit(translated_text)

def register(client):
    swat_module = SwatModule(client)
    swat_module.register()
