import asyncio
from telethon import TelegramClient, events
import os
import importlib
import json
import time
import subprocess
import sys
import random
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.ERROR,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('sancho_errors.log')
    ]
)

CONFIG_FILE = "config.json"
MODULES_DIR = "modules"
start_time = time.time()
modules_load_errors = False

def get_api_credentials():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as file:
                return json.load(file)
        print("=== Sancho-Tool Configuration ===")
        api_id = input("Введите API_ID: ")
        api_hash = input("Введите API_HASH: ")
        credentials = {"API_ID": int(api_id), "API_HASH": api_hash}
        with open(CONFIG_FILE, "w") as file:
            json.dump(credentials, file)
        return credentials
    except Exception as e:
        logging.error(f"Error in get_api_credentials: {str(e)}")
        raise

credentials = get_api_credentials()

device_models = [
    "Samsung Galaxy S23 Ultra",
    "iPhone 14 Pro Max",
    "Google Pixel 7 Pro",
    "Xiaomi 13 Pro",
    "OnePlus 11",
    "Huawei P60 Pro",
    "Realme GT 3",
    "Nothing Phone 2",
    "Sony Xperia 1 V",
    "Motorola Edge 40 Pro"
]
device_model = random.choice(device_models)

client = TelegramClient(
    "sancho_tool_session",
    credentials["API_ID"],
    credentials["API_HASH"],
    device_model=device_model,
    system_version="Android 13",
    app_version="10.2.1",
    lang_code="ru",
    system_lang_code="ru-RU"
)

# ========================== Нормальный loader ==========================

import importlib.util

def load_modules(client):
    global modules_load_errors
    modules_loaded = 0
    print("🔄 Загрузка модулей...")
    try:
        if not os.path.exists(MODULES_DIR):
            os.makedirs(MODULES_DIR)
            print(f"📁 Создана папка {MODULES_DIR}")
            return modules_loaded

        if MODULES_DIR not in sys.path:
            sys.path.insert(0, MODULES_DIR)

        for filename in os.listdir(MODULES_DIR):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                try:
                    spec = importlib.util.spec_from_file_location(module_name, os.path.join(MODULES_DIR, filename))
                    if spec is None:
                        print(f"❌ Не удалось загрузить {filename}")
                        continue
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and 'Module' in attr_name and hasattr(attr, 'register'):
                            module_class = attr
                            module_instance = module_class(client)
                            module_instance.register()
                            modules_loaded += 1
                            print(f"✅ Модуль загружен: {filename} (класс: {attr_name})")
                            break
                    else:
                        print(f"⚠️ В модуле {filename} не найден подходящий класс")
                except Exception as e:
                    modules_load_errors = True
                    logging.error(f"Error loading {filename}: {str(e)}")
                    print(f"❌ Ошибка модуля {filename}: {e}")
    except Exception as e:
        modules_load_errors = True
        logging.error(f"Error in load_modules: {str(e)}")
        print(f"❌ Ошибка в load_modules: {e}")

    print(f"📦 Всего загружено модулей: {modules_loaded}")
    return modules_loaded

# ========================== Команды ==========================

@client.on(events.NewMessage(pattern=r"\.update", outgoing=True))
async def update(event):
    await event.delete()
    try:
        repo_dir = os.path.expanduser("~/sancho-tool")
        os.chdir(repo_dir)
        subprocess.run(["git", "fetch", "--all"], check=True)
        diff = subprocess.run(
            ["git", "diff", "--name-status", "origin/main"],
            capture_output=True, text=True
        ).stdout
        subprocess.run(["git", "reset", "--hard", "origin/main"], check=True)
        changes = f"Изменения:\n{diff}" if diff.strip() else "✅ Все файлы синхронизированы"
        await client.send_message(event.chat_id, f"🔄 Обновление завершено!\n\n{changes}\n\nПерезапуск...")
        await asyncio.sleep(2)
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        await client.send_message(event.chat_id, f"❌ Ошибка при обновлении: {str(e)}")

@client.on(events.NewMessage(pattern=r"\.repo", outgoing=True))
async def repo_info(event):
    await event.delete()
    try:
        process = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True, timeout=10)
        repo_info_text = "**Информация о репозитории:**\n"
        repo_info_text += f"```{process.stdout.strip()}```\n" if process.returncode == 0 else "Не удалось получить информацию\n"
        repo_info_text += "**Ссылка:** https://github.com/SancboysArt/sancho-tool"
        await client.send_message(event.chat_id, repo_info_text)
    except Exception as e:
        await client.send_message(event.chat_id, f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern=r"\.ping", outgoing=True))
async def ping(event):
    await event.delete()
    try:
        start_time_ping = time.time()
        ping_time = round((time.time() - start_time_ping) * 1000, 2)
        await client.send_message(event.chat_id, f"Ping: {ping_time}ms")
    except Exception as e:
        await client.send_message(event.chat_id, f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern=r"\.uptime", outgoing=True))
async def uptime(event):
    await event.delete()
    try:
        uptime_seconds = int(time.time() - start_time)
        h, r = divmod(uptime_seconds, 3600)
        m, s = divmod(r, 60)
        await client.send_message(event.chat_id, f"Время работы: {h}ч {m}м {s}с")
    except Exception as e:
        await client.send_message(event.chat_id, f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern=r"\.save", outgoing=True))
async def save_self_destructing_media(event):
    await event.delete()
    try:
        reply = await event.get_reply_message()
        if reply and reply.media and reply.media.ttl_seconds:
            await client.send_message("me", "Сохранено медиа:", file=reply.media)
            await client.send_message(event.chat_id, "Медиа сохранено в избранное")
        else:
            await client.send_message(event.chat_id, "Ответьте на самоудаляющееся медиа")
    except Exception as e:
        await client.send_message(event.chat_id, f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern=r"\.phones", outgoing=True))
async def scan_numbers(event):
    await event.delete()
    try:
        chat = await event.get_chat()
        users = await client.get_participants(chat)
        phones = {u.first_name or "Без имени": u.phone for u in users if u.phone}
        if phones:
            result = "Найденные номера:\n" + "\n".join(f"{n}: {p}" for n, p in phones.items())
            await client.send_message("me", result)
            await client.send_message(event.chat_id, "Номера отправлены в избранное")
        else:
            await client.send_message(event.chat_id, "В чате нет номеров")
    except Exception as e:
        await client.send_message(event.chat_id, f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern=r"\.start", outgoing=True))
async def start_command(event):
    await event.delete()
    await client.send_message(event.chat_id, "Sancho-Tool запущен\nИспользуйте .help для команд")

@client.on(events.NewMessage(pattern=r"\.restart", outgoing=True))
async def restart_command(event):
    await event.delete()
    await client.send_message(event.chat_id, "Перезапуск Sancho-Tool...")
    await asyncio.sleep(2)
    os.execl(sys.executable, sys.executable, *sys.argv)

@client.on(events.NewMessage(pattern=r"\.me", outgoing=True))
async def me_command(event):
    await event.delete()
    try:
        me = await client.get_me()
        text = (f"Имя: {me.first_name}\nФамилия: {me.last_name or 'Нет'}\n"
                f"Username: @{me.username or 'Нет'}\nID: {me.id}\nНомер: {'Скрыт'}")
        await client.send_message(event.chat_id, text)
    except Exception as e:
        await client.send_message(event.chat_id, f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern=r"\.help", outgoing=True))
async def help_command(event):
    await event.delete()
    try:
        help_text = (
            "**Sancho-Tool | Команды**\n"
            ".start, .help, .ping, .uptime, .me, .restart, .update, .repo, .sancho\n"
            ".save, .phones, и модули (.call, .respond, .sq, .swat, .who, .gpt)"
        )
        image_path = "help.jpg"
        if os.path.exists(image_path):
            await client.send_file(event.chat_id, image_path, caption=help_text)
        else:
            await client.send_message(event.chat_id, help_text)
    except Exception as e:
        await client.send_message(event.chat_id, f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern=r"\.sancho", outgoing=True))
async def sancho_info(event):
    await event.delete()
    try:
        ping_time = round((time.time() - start_time) * 1000, 2)
        status = "Active" if not modules_load_errors else "Errors"
        info_text = (
            "**Sancho-Tool | System**\n"
            f"Version: 1.0\nPlatform: Telethon\nPing: {ping_time}ms\n"
            f"Status: {status}\nDeveloper: @xranutel"
        )
        image_path = "sancho.jpg"
        if os.path.exists(image_path):
            await client.send_file(event.chat_id, image_path, caption=info_text)
        else:
            await client.send_message(event.chat_id, info_text)
    except Exception as e:
        await client.send_message(event.chat_id, f"Ошибка: {str(e)}")

# ========================== Запуск ==========================

modules_count = load_modules(client)

print("🚀 Запуск Sancho-Tool...")
print("📱 Device:", device_model)
print("⏰ Время запуска:", time.strftime("%Y-%m-%d %H:%M:%S"))

client.start()
print("✅ Sancho-Tool успешно запущен")
print("💡 Используйте .help для списка команд")

client.run_until_disconnected()
