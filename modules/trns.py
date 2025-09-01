import asyncio
from telethon import events
from googletrans import Translator, LANGUAGES

def register(client):
    translator = Translator()
    active_users = {}

    @client.on(events.NewMessage(pattern=r"\.trns on (\w+)"))
    async def enable_translation(event):
        """Включить автоперевод"""
        lang_code = event.pattern_match.group(1).lower()
        
        if lang_code not in LANGUAGES:
            await event.edit("❌ Неверный код языка!\n"
                           "Используйте `.trns list` для списка кодов")
            return
            
        active_users[event.sender_id] = lang_code
        lang_name = LANGUAGES[lang_code].capitalize()
        
        await event.edit(f"✅ **Переводчик активирован**\n"
                       f"▸ Язык: `{lang_name}`\n"
                       f"▸ Режим: Автоперевод исходящих")

    @client.on(events.NewMessage(pattern=r"\.trns off"))
    async def disable_translation(event):
        """Выключить автоперевод"""
        if event.sender_id in active_users:
            lang_code = active_users[event.sender_id]
            lang_name = LANGUAGES[lang_code].capitalize()
            del active_users[event.sender_id]
            
            await event.edit(f"🔴 **Переводчик деактивирован**\n"
                           f"▸ Был установлен на: `{lang_name}`")
        else:
            await event.edit("ℹ️ Переводчик и так не активен")

    @client.on(events.NewMessage(pattern=r"\.trns list"))
    async def show_languages(event):
        """Показать список языков"""
        languages = []
        for code, name in LANGUAGES.items():
            languages.append(f"`{code}` - {name.capitalize()}")
        
        # Разбиваем на части для избежания ограничения длины
        chunks = [languages[i:i+20] for i in range(0, len(languages), 20)]
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                await event.edit(f"🌍 **Доступные языки:**\n\n" + "\n".join(chunk))
            else:
                await event.reply("\n".join(chunk))

    @client.on(events.NewMessage(pattern=r"\.trns help"))
    async def translation_help(event):
        """Помощь по командам переводчика"""
        help_text = (
            "🌐 **Translation Help:**\n\n"
            "**.trns on <код>** - Включить автоперевод\n"
            "**.trns off** - Выключить автоперевод\n"
            "**.trns list** - Список языков\n"
            "**.trns help** - Эта помощь\n\n"
        )
        await event.edit(help_text)

    @client.on(events.NewMessage(outgoing=True))
    async def auto_translate_outgoing(event):
        """Автоперевод исходящих сообщений"""
        if event.sender_id not in active_users:
            return
            
        if not event.text or event.text.startswith('.'):
            return
            
        try:
            lang_code = active_users[event.sender_id]
            translated = translator.translate(event.text, dest=lang_code)
            
            if translated.src != lang_code:
                await event.edit(translated.text)
                
        except Exception as e:
            print(f"Translation error: {e}")
            await event.reply("⚠️ Ошибка перевода")

    print("🔄 Модуль перевода загружен")
