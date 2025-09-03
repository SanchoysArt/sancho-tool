from telethon import events
from telethon.tl.types import User, Channel, Chat

class WhoModule:
    def __init__(self, client):
        self.client = client
    
    def register(self):
        @self.client.on(events.NewMessage(pattern=r'\.who$', outgoing=True))
        async def who_handler(event):
            """Информация о пользователе (ответом на сообщение)"""
            try:
                reply = await event.get_reply_message()
                if not reply:
                    await event.edit("❌ **Ответь на сообщение пользователя**")
                    return
                
                user = await self.client.get_entity(reply.sender_id)
                info = await self.get_user_info(user)
                
                await event.edit(info)
                
            except Exception as e:
                await event.edit(f"❌ **Ошибка:** {str(e)}")
        
        @self.client.on(events.NewMessage(pattern=r'\.who (@?\w+)$', outgoing=True))
        async def who_username_handler(event):
            """Информация о пользователе по юзернейму"""
            try:
                username = event.pattern_match.group(1).replace('@', '')
                user = await self.client.get_entity(username)
                info = await self.get_user_info(user)
                
                await event.edit(info)
                
            except Exception as e:
                await event.edit(f"❌ **Пользователь @{username} не найден**")
    
    async def get_user_info(self, user):
        """Получить информацию о пользователе"""
        # Базовая информация
        user_id = f"`{user.id}`"
        first_name = user.first_name or "Нет"
        last_name = user.last_name or "Нет"
        username = f"@{user.username}" if user.username else "Нет"
        phone = user.phone or "Скрыт"
        
        # Проверка на бота
        is_bot = "✅ Да" if user.bot else "❌ Нет"
        
        # Проверка верификации
        verified = "✅ Да" if getattr(user, 'verified', False) else "❌ Нет"
        
        # Проверка премиума
        premium = "✅ Да" if getattr(user, 'premium', False) else "❌ Нет"
        
        # Статус пользователя
        status = ""
        if hasattr(user, 'status'):
            if user.status:
                status = f"**Статус:** `{type(user.status).__name__}`\n"
        
        # Информация о чате/канале (если это не пользователь)
        chat_info = ""
        if isinstance(user, (Channel, Chat)):
            chat_type = "Канал" if getattr(user, 'broadcast', False) else "Группа"
            participants = f"{user.participants_count}" if hasattr(user, 'participants_count') else "Неизвестно"
            chat_info = f"**Тип:** {chat_type}\n**Участников:** {participants}\n"
        
        # Формируем сообщение
        info = (
            f"👤 **Информация о пользователе**\n\n"
            f"**ID:** {user_id}\n"
            f"**Имя:** {first_name}\n"
            f"**Фамилия:** {last_name}\n"
            f"**Юзернейм:** {username}\n"
            f"**Телефон:** {phone}\n"
            f"**Бот:** {is_bot}\n"
            f"**Верифицирован:** {verified}\n"
            f"**Премиум:** {premium}\n"
            f"{status}"
            f"{chat_info}"
            f"\n📅 **Аккаунт создан**"
        )
        
        return info

def register(client):
    who_module = WhoModule(client)
    who_module.register()
