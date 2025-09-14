# plugins/troll.py
import asyncio
import json
import os
import gc
from telethon import events, TelegramClient
from telethon.errors import FloodWaitError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FNAME = os.path.join(BASE_DIR, "troll_phrases.json")

# default data
_data = {"phrases": [], "delay": 1.5}

# load / create file
if os.path.exists(FNAME):
    try:
        with open(FNAME, "r", encoding="utf-8") as f:
            _data = json.load(f)
    except Exception:
        _data = {"phrases": [], "delay": 1.5}
else:
    try:
        with open(FNAME, "w", encoding="utf-8") as f:
            json.dump(_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

phrases = list(_data.get("phrases", []))
delay = float(_data.get("delay", 1.5))

# tasks per chat_id
spam_tasks = {}


def _save():
    try:
        with open(FNAME, "w", encoding="utf-8") as f:
            json.dump({"phrases": phrases, "delay": delay}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


async def _send_safe(client, chat_id, text):
    try:
        await client.send_message(chat_id, text)
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds)
        try:
            await client.send_message(chat_id, text)
        except Exception:
            pass
    except Exception:
        pass


async def _spam_cycle(client, chat_id):
    global delay
    try:
        idx = 0
        while True:
            # Проверяем, что задача всё ещё активна
            task = spam_tasks.get(chat_id)
            if task is None or task.done():
                return
            
            if not phrases:
                return
            
            await _send_safe(client, chat_id, phrases[idx])
            idx = (idx + 1) % len(phrases)
            
            # Проверяем задачу снова перед задержкой
            task = spam_tasks.get(chat_id)
            if task is None or task.done():
                return
            
            await asyncio.sleep(delay)
    except asyncio.CancelledError:
        return
    finally:
        spam_tasks.pop(chat_id, None)


async def _spam_words(client, chat_id, words):
    global delay
    try:
        for w in words:
            # Проверяем, что задача всё ещё активна
            task = spam_tasks.get(chat_id)
            if task is None or task.done():
                return
            
            await _send_safe(client, chat_id, w)
            
            # Проверяем задачу снова перед задержкой
            task = spam_tasks.get(chat_id)
            if task is None or task.done():
                return
            
            await asyncio.sleep(delay)
    except asyncio.CancelledError:
        return
    finally:
        spam_tasks.pop(chat_id, None)


def register(client: TelegramClient):
    """
    Регистрирует обработчики в переданном client.
    Вызов: troll.register(client)
    """

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.troll\s+help$'))
    async def _help(event):
        # удаляем команду (если возможно)
        try:
            await event.delete()
        except Exception:
            pass

        help_text = (
            "⚡ Справка по Troll-командам:\n"
            ".troll help — показать справку\n"
            ".troll spam <фразы> — одноразовый спам словами\n"
            ".troll on — запустить спам сохранёнными фразами\n"
            ".troll off — остановить спам\n"
            ".st <фраза> — добавить фразу\n"
            ".st list — список фраз\n"
            ".st del <номер> — удалить фразу\n"
            ".st clear — очистить все фразы\n"
            ".troll time set <сек> — установить задержку (можно дробное)\n"
        )
        await event.respond(help_text)

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.troll\s+spam\s+(.+)$'))
    async def _spam_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass
        chat_id = event.chat_id
        raw = event.pattern_match.group(1).strip()
        # preserve multi-word phrases separated by |
        if '|' in raw:
            phrases_list = [p.strip() for p in raw.split('|') if p.strip()]
        else:
            phrases_list = raw.split()
        # cancel existing task in this chat (so one-shot doesn't overlap)
        t = spam_tasks.get(chat_id)
        if t and not t.done():
            t.cancel()
        task = asyncio.create_task(_spam_words(client, chat_id, phrases_list))
        spam_tasks[chat_id] = task

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.troll\s+on$'))
    async def _on(event):
        try:
            await event.delete()
        except Exception:
            pass
        chat_id = event.chat_id
        if not phrases:
            return
        t = spam_tasks.get(chat_id)
        if t and not t.done():
            return
        task = asyncio.create_task(_spam_cycle(client, chat_id))
        spam_tasks[chat_id] = task

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.troll\s+off$'))
    async def _off(event):
        try:
            await event.delete()
        except Exception:
            pass
        chat_id = event.chat_id
        t = spam_tasks.get(chat_id)
        if t and not t.done():
            t.cancel()

    # .st list
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.st\s+list$'))
    async def _list(event):
        try:
            await event.delete()
        except Exception:
            pass
        if not phrases:
            return
        text = "\n".join(f"{i+1}. {p}" for i, p in enumerate(phrases))
        await event.respond("📜 Список фраз:\n" + text)

    # .st del N
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.st\s+del\s+(\d+)$'))
    async def _del(event):
        try:
            await event.delete()
        except Exception:
            pass
        idx = int(event.pattern_match.group(1)) - 1
        if 0 <= idx < len(phrases):
            phrases.pop(idx)
            _save()

    # .st clear
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.st\s+clear$'))
    async def _clear(event):
        try:
            await event.delete()
        except Exception:
            pass
        phrases.clear()
        _save()

    # .st add (any other .st <text>)
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.st\s+(.+)$'))
    async def _st_add(event):
        try:
            await event.delete()
        except Exception:
            pass
        raw = event.pattern_match.group(1).strip()
        if raw.lower().startswith(("list", "del ", "clear")):
            return
        phrases.append(raw)
        _save()

    # .troll time set X
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.troll\s+time\s+set\s+([0-9]*\.?[0-9]+)$'))
    async def _time_set(event):
        try:
            await event.delete()
        except Exception:
            pass
        global delay
        try:
            v = float(event.pattern_match.group(1))
            if v > 0:
                delay = v
                _save()
        except Exception:
            pass

    # return client for convenience
    return client


# УДАЛЕНО: авто-регистрация, чтобы избежать дублирования
# def _auto_register():
#     try:
#         for obj in gc.get_objects():
#             if isinstance(obj, TelegramClient):
#                 try:
#                     register(obj)
#                     print("[troll] auto-registered to TelegramClient")
#                     return True
#                 except Exception:
#                     continue
#     except Exception:
#         pass
#     return False
# 
# _auto_register()
