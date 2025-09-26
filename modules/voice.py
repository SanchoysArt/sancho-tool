import asyncio
from telethon import events
from telethon.tl.functions.messages import DeleteHistoryRequest
from telethon.tl.functions.channels import JoinChannelRequest


class VoiceModule:
    def __init__(self, client):
        self.client = client
        self.voice_bot_username = "@silero_voice_bot"
        self.channel_username = "@silero_voice_news"

        self.voices = {
            "азир": "/speaker azir",
            "губка боб": "/speaker spongebob", 
            "сквидвард": "/speaker squidward",
            "шрэк": "/speaker shrek",
            "планктон": "/speaker plankton",
            "доктор ливси": "/speaker livsy", 
            "бандит": "/speaker bandit",
            "pudge": "/speaker pudge"
        }
        self.selected_voice = "азир"
        self.voice_handler = None

    async def cleanup_bot_chat(self):
        """Очищает чат с ботом"""
        try:
            bot_entity = await self.client.get_entity(self.voice_bot_username)
            await self.client(DeleteHistoryRequest(peer=bot_entity, max_id=0, just_clear=True))
        except:
            pass

    async def setup_bot(self, bot_entity):
        """Настраивает бота"""
        try:
            # Подписка на канал
            try:
                await self.client.get_entity(self.channel_username)
            except:
                channel_entity = await self.client.get_entity(self.channel_username)
                await self.client(JoinChannelRequest(channel_entity))

            # Запуск и настройка
            await self.client.send_message(bot_entity, "/start")
            await self.client.send_message(bot_entity, "/videonotes")

            # Ждем и нажимаем кнопку проверки подписки
            async for message in self.client.iter_messages(bot_entity, limit=5):
                if message.reply_markup:
                    for i, row in enumerate(message.reply_markup.rows):
                        for j, button in enumerate(row.buttons):
                            if (hasattr(button, 'data') and b'check_subscription' in button.data):
                                await message.click(i, j)
                                break
            return True
        except Exception as e:
            print(f"❌ Ошибка настройки: {e}")
            return False

    async def wait_for_voice_message(self, bot_entity):
        """Ожидает голосовое сообщение от бота - ПРОСТАЯ ВЕРСИЯ"""
        try:
            # Простой поиск голосового в новых сообщениях
            for _ in range(10):  # 10 попыток в течение ~10 секунд
                async for message in self.client.iter_messages(bot_entity, limit=3):
                    if message.voice:
                        return message.voice
                await asyncio.sleep(1)
            return None
        except:
            return None

    async def process_voice_command(self, event, voice_name, text_to_speak):
        """Обрабатывает команду"""
        try:
            await event.delete()
            bot_entity = await self.client.get_entity(self.voice_bot_username)
            
            # Очищаем чат
            await self.cleanup_bot_chat()
            
            # Настраиваем бота
            success = await self.setup_bot(bot_entity)
            if not success:
                await event.reply("❌ Ошибка настройки бота")
                return

            # Выбор голоса
            if voice_name in self.voices:
                await self.client.send_message(bot_entity, self.voices[voice_name])
                await asyncio.sleep(0.5)  # Минимальная задержка для обработки
            
            # Отправляем текст
            await self.client.send_message(bot_entity, text_to_speak)
            
            # Ждем голосовое сообщение
            voice_message = await self.wait_for_voice_message(bot_entity)
            
            if voice_message:
                await self.client.send_file(event.chat_id, voice_message, caption=None)
                print("✅ Голосовое отправлено в чат")
            else:
                await event.reply("❌ Бот не прислал голосовое")
                print("❌ Голосовое не получено")
            
            # Очищаем чат
            await self.cleanup_bot_chat()

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            await event.reply("❌ Ошибка при генерации голосового")

    async def show_help(self, event):
        """Показывает справку"""
        help_text = """🎤 **Sancho Voice Bot - Помощь**

**Выбор голоса:**
`.голос азир` - выбрать голос Азира
`.голос губка боб` - выбрать голос Губки Боба  
`.голос сквидвард` - выбрать голос Сквидварда
`.голос шрэк` - выбрать голос Шрэка
`.голос планктон` - выбрать голос Планктона
`.голос доктор ливси` - выбрать голос Доктора Ливси
`.голос бандит` - выбрать голос Бандита
`.голос pudge` - выбрать голос Pudge

**Генерация:**
`.гс Текст для озвучки` - с текущим голосом
`.гс хелп` - эта справка"""

        await event.delete()
        await event.reply(help_text)

    async def handle_voice_selection(self, event, voice_name):
        """Обрабатывает выбор голоса"""
        try:
            await event.delete()
            if voice_name in self.voices:
                self.selected_voice = voice_name
                await event.reply(f"✅ Выбран голос: {voice_name}")
            else:
                await event.reply("❌ Голос не найден. Используйте .гс хелп")
        except Exception as e:
            print(f"❌ Ошибка выбора голоса: {e}")

    async def handle_message(self, event):
        """Обрабатывает команды"""
        try:
            text = event.raw_text

            if text.startswith('.голос ') and len(text) > 7:
                voice_name = text[7:].strip().lower()
                await self.handle_voice_selection(event, voice_name)

            elif text.startswith('.гс ') and len(text) > 4:
                text_to_speak = text[4:].strip()
                if text_to_speak.lower() == 'хелп':
                    await self.show_help(event)
                else:
                    asyncio.create_task(self.process_voice_command(event, self.selected_voice, text_to_speak))

            elif text == '.гс хелп':
                await self.show_help(event)

        except Exception as e:
            print(f"❌ Ошибка обработки: {e}")

    def register(self):
        """Регистрирует обработчики"""
        @self.client.on(events.NewMessage(pattern=r'\.(гс|голос) '))
        async def handler(event):
            await self.handle_message(event)
