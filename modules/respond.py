from telethon import events
import json
import os

class AutoResponderModule:
    def __init__(self, client, owner_id=None):
        self.client = client
        self.owner_id = owner_id  # user_id хозяина (если None — подставим позже)
        self.enabled = False
        self.response_text = ""
        self.config_file = "autoresponder_config.json"
        self.message_counters = {}
        self.answered_users = set()
        self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding="utf-8") as f:
                    data = json.load(f)
                    self.enabled = data.get('enabled', False)
                    self.response_text = data.get('response_text', "")
            except Exception as e:
                print(f"[AutoResponder] Ошибка загрузки конфига: {e}")
                self.enabled = False
                self.response_text = ""
    
    def save_config(self):
        data = {
            'enabled': self.enabled,
            'response_text': self.response_text
        }
        with open(self.config_file, 'w', encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def register(self):
        @self.client.on(events.NewMessage(pattern=r'\.respond$', outgoing=True))
        async def respond_toggle(event):
            self.enabled = not self.enabled
            self.save_config()
            if self.enabled:
                await event.edit("✅ **Автоответчик включен**\n📩 **Только в ЛС**")
            else:
                await event.edit("❌ **Автоответчик выключен**")

        @self.client.on(events.NewMessage(pattern=r'\.respond set (.+)', outgoing=True))
        async def respond_set(event):
            self.response_text = event.pattern_match.group(1)
            self.save_config()
            await event.edit(f"✅ **Текст ответа установлен:**\n`{self.response_text}`")

        @self.client.on(events.NewMessage(pattern=r'\.respond status', outgoing=True))
        async def respond_status(event):
            status = "✅ **ВКЛЮЧЕН**" if self.enabled else "❌ **ВЫКЛЮЧЕН**"
            await event.edit(
                f"🤖 **Автоответчик:** {status}\n"
                f"📩 **Режим:** Только личные сообщения\n\n"
                f"💬 **Текст ответа:** {self.response_text or 'Не установлен'}"
            )

        @self.client.on(events.NewMessage(pattern=r'\.respond reset', outgoing=True))
        async def respond_reset(event):
            self.message_counters.clear()
            self.answered_users.clear()
            await event.edit("♻️ **История автоответчика сброшена**")

        @self.client.on(events.NewMessage(pattern=r'\.respond help', outgoing=True))
        async def respond_help(event):
            help_text = (
                "🤖 **Автоответчик - Помощь**\n\n"
                "⚡ **Команды:**\n"
                "• `.respond` - вкл/выкл автоответчик\n"
                "• `.respond set <текст>` - установить текст ответа\n"
                "• `.respond status` - показать статус\n"
                "• `.respond reset` - сбросить историю\n"
                "• `.respond help` - эта справка\n\n"
                "⚙️ **Особенности:**\n"
                "• отвечает только раз на 3 входящих сообщения\n"
                "• не отвечает, если хозяин онлайн\n"
                "• не отвечает, если ты уже писал человеку"
            )
            await event.edit(help_text)

        @self.client.on(events.NewMessage(outgoing=True))
        async def outgoing_watcher(event):
            if event.is_private:
                self.answered_users.add(event.chat_id)

        @self.client.on(events.NewMessage(incoming=True))
        async def message_watcher(event):
            try:
                if not self.enabled or not event.is_private or event.out:
                    return

                sender = await event.get_sender()
                if sender.bot:
                    return

                # Подхват owner_id, если не задан
                if not self.owner_id:
                    me = await self.client.get_me()
                    self.owner_id = me.id

                # Проверка: если хозяин онлайн
                me = await self.client.get_entity(self.owner_id)
                if str(me.status).lower() == "userstatusonline":
                    return

                # Если ты уже отвечал этому юзеру
                if event.chat_id in self.answered_users:
                    return

                # Счётчик сообщений
                self.message_counters[event.chat_id] = self.message_counters.get(event.chat_id, 0) + 1
                count = self.message_counters[event.chat_id]

                if count % 3 == 0 and self.response_text:
                    await event.reply(self.response_text)
                    print(f"[AutoResponder] Ответ отправлен {sender.id}")
            except Exception as e:
                print(f"[AutoResponder] Ошибка: {e}")


def register(client, owner_id=None):
    responder_module = AutoResponderModule(client, owner_id)
    responder_module.register()
