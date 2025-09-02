from telethon import events
import asyncio
import re

class CallModule:
    def __init__(self, client):
        self.client = client

    def register(self):
        @self.client.on(events.NewMessage(pattern=r'\.call(?: (\d+))?$', outgoing=True))
        async def call_all_handler(event):
            """Призвать участников чата (по количеству)"""
            try:
                # Проверяем, что команда запущена в группе
                if not (event.is_group or event.is_channel):
                    await event.edit("❌ **Эта команда работает только в группах**")
                    return

                # Число из команды (если есть)
                match = re.match(r"\.call(?: (\d+))?", event.raw_text)
                limit = int(match.group(1)) if match and match.group(1) else None

                await event.edit("🔍 **Собираю участников...**")

                # Получаем участников
                participants = []
                async for user in event.client.iter_participants(event.chat_id, limit=None):
                    if not user.bot and user.username:
                        participants.append(user)

                if not participants:
                    await event.edit("❌ **Нет участников с юзернеймами**")
                    return

                # Если указан лимит, берем только первых N
                if limit:
                    participants = participants[:limit]

                await event.edit(f"✅ **Найдено {len(participants)} участников для призыва**")

                # Формируем сообщение
                usernames = [f"@{u.username}" for u in participants]
                call_message = "📢 **Призыв участников!**\n\n" + " ".join(usernames)

                # Разбиваем на части если длинное
                if len(call_message) > 4000:
                    parts = [call_message[i:i+4000] for i in range(0, len(call_message), 4000)]
                    for part in parts:
                        await event.respond(part)
                        await asyncio.sleep(0.5)
                else:
                    await event.respond(call_message)

                await event.delete()

            except Exception as e:
                await event.edit(f"❌ **Ошибка:** {str(e)}")


def register(client):
    call_module = CallModule(client)
    call_module.register()
