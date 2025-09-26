import asyncio
from telethon import events
from telethon.tl.functions.messages import DeleteHistoryRequest

class VoiceModule:
    def __init__(self, client):
        self.client = client
        self.voice_bot_username = "@CyberVoiceBot"

    async def cleanup_bot_chat(self):
        """Очищает чат с ботом"""
        try:
            bot_entity = await self.client.get_entity(self.voice_bot_username)
            await self.client(DeleteHistoryRequest(peer=bot_entity, max_id=0, just_clear=True))
            return True
        except:
            return False

    async def send_to_voice_bot(self, event, text_to_speak):
        """Отправляет текст боту и получает голосовое"""
        try:
            # Удаляем команду пользователя
            await event.delete()
            
            bot_entity = await self.client.get_entity(self.voice_bot_username)
            
            # Параллельные задачи
            await asyncio.gather(
                self.cleanup_bot_chat(),
                self.process_voice_request(event, bot_entity, text_to_speak)
            )

        except:
            pass

    async def process_voice_request(self, event, bot_entity, text_to_speak):
        """Обрабатывает запрос голосового"""
        try:
            # Быстрая инициализация бота
            await self.client.send_message(bot_entity, "/start")
            await self.client.send_message(bot_entity, text_to_speak)

            # Ожидание и поиск голосового
            await asyncio.sleep(3)

            # Ищем голосовое сообщение
            async for message in self.client.iter_messages(bot_entity, limit=5):
                if message.voice:
                    # Отправляем голосовое БЕЗ КАПШЕНА (скрыто)
                    await self.client.send_file(
                        event.chat_id, 
                        message.voice,
                        caption=None  # Убираем текст сверху
                    )
                    break

            # Очищаем чат
            await self.cleanup_bot_chat()

        except:
            pass

    async def handle_message(self, event):
        """Обрабатывает команды"""
        try:
            text = event.raw_text

            if text.startswith('.гф ') and len(text) > 3:
                text_to_speak = text[3:].strip()
                if text_to_speak:
                    asyncio.create_task(self.send_to_voice_bot(event, text_to_speak))

        except:
            pass

    def register(self):
        """Регистрирует обработчики"""
        @self.client.on(events.NewMessage(pattern=r'\.гф'))
        async def handler(event):
            await self.handle_message(event)
