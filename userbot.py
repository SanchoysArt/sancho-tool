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
        logging.StreamHandler(sys.stdout),  # Вывод в консоль
        logging.FileHandler('sancho_errors.log')  # Запись в файл
    ]
)

CONFIG_FILE = "config.json"
MODULES_DIR = "modules"
start_time = time.time()

# Глобальная переменная для отслеживания ошибок загрузки
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

def load_modules(client):
    global modules_load_errors
    try:
        if not os.path.exists(MODULES_DIR):
            os.makedirs(MODULES_DIR)
        
        # Очищаем кэш модулей перед загрузкой
        for module_name in list(sys.modules.keys()):
            if module_name.startswith(MODULES_DIR + '.'):
                del sys.modules[module_name]
        
        for filename in os.listdir(MODULES_DIR):
            if filename.endswith(".py"):
                try:
                    module_name = f"{MODULES_DIR}.{filename[:-3]}"
                    
                    # Если модуль уже загружен, перезагружаем его
                    if module_name in sys.modules:
                        module = importlib.reload(sys.modules[module_name])
                    else:
                        module = importlib.import_module(module_name)
                    
                    if hasattr(module, "register"):
                        module.register(client)
                        print(f"Загружен модуль: {filename}")
                except Exception as e:
                    modules_load_errors = True
                    logging.error(f"Error loading module {filename}: {str(e)}")
                    print(f"Ошибка загрузки модуля {filename}: {e}")
                    
    except Exception as e:
        modules_load_errors = True
        logging.error(f"Error in load_modules: {str(e)}")
        print(f"Ошибка в load_modules: {e}")

@client.on(events.NewMessage(pattern=r"\.update", outgoing=True))
async def update(event):
    try:
        await event.edit("🔄 Обновление Sancho-Tool из репозитория SanchoysArt/sancho-tool...")
        
        # Добавляем remote репозитория если его нет
        remote_check = subprocess.run(["git", "remote", "get-url", "sanchoysart"], 
                                    capture_output=True, text=True)
        
        if remote_check.returncode != 0:
            # Добавляем remote репозитория SanchoysArt
            add_remote = subprocess.run(["git", "remote", "add", "sanchoysart", 
                                       "https://github.com/SanchoysArt/sancho-tool.git"],
                                      capture_output=True, text=True)
            if add_remote.returncode != 0:
                await event.edit("❌ Ошибка добавления remote репозитория")
                return
        
        # Получаем последние изменения из репозитория SanchoysArt
        fetch_process = subprocess.run(["git", "fetch", "sanchoysart", "main"],
                                     capture_output=True, text=True, timeout=60)
        
        if fetch_process.returncode != 0:
            error_msg = fetch_process.stderr if fetch_process.stderr else "Unknown error"
            await event.edit(f"❌ Ошибка при получении обновлений:\n`{error_msg}`")
            return
        
        # Проверяем, есть ли обновления
        check_updates = subprocess.run(["git", "log", "HEAD..sanchoysart/main", "--oneline"],
                                     capture_output=True, text=True)
        
        if not check_updates.stdout.strip():
            await event.edit("✅ Sancho-Tool уже актуален (последняя версия от SanchoysArt)")
            return
        
        # Сохраняем текущие изменения (если есть)
        stash_process = subprocess.run(["git", "stash"],
                                     capture_output=True, text=True, timeout=30)
        
        # Сливаем изменения из репозитория SanchoysArt
        merge_process = subprocess.run(["git", "merge", "sanchoysart/main"],
                                     capture_output=True, text=True, timeout=120)
        
        if merge_process.returncode != 0:
            # Если есть конфликты, делаем reset и принудительно перезаписываем
            reset_process = subprocess.run(["git", "reset", "--hard", "sanchoysart/main"],
                                        capture_output=True, text=True, timeout=30)
            
            if reset_process.returncode != 0:
                error_msg = merge_process.stderr if merge_process.stderr else "Unknown error"
                await event.edit(f"❌ Ошибка при обновлении:\n`{error_msg}`")
                return
        
        # Получаем информацию о коммитах
        commit_info = subprocess.run(["git", "log", "-1", "--pretty=format:%s"],
                                   capture_output=True, text=True)
        
        commit_message = commit_info.stdout if commit_info.returncode == 0 else "Обновление завершено"
        
        # Перезагружаем модули после обновления
        global modules_load_errors
        modules_load_errors = False
        load_modules(client)
        
        await event.edit(f"✅ Обновление от SanchoysArt завершено!\n\n"
                       f"**Последние изменения:**\n`{commit_message}`\n\n"
                       f"**Статус модулей:** {'✅ Успешно' if not modules_load_errors else '❌ С ошибками'}\n\n"
                       f"Перезапуск через 3 секунды для полного применения изменений...")
        
        # Даем время для отправки сообщения перед перезапуском
        await asyncio.sleep(3)
        os.execl(sys.executable, sys.executable, *sys.argv)
            
    except subprocess.TimeoutExpired:
        await event.edit("❌ Таймаут при обновлении")
    except Exception as e:
        logging.error(f"Error in update: {str(e)}")
        await event.edit(f"❌ Ошибка при обновлении: `{str(e)}`")

@client.on(events.NewMessage(pattern=r"\.repo", outgoing=True))
async def repo_info(event):
    try:
        process = subprocess.run(["git", "remote", "-v"], 
                               capture_output=True, 
                               text=True,
                               timeout=10)
        
        repo_info_text = f"**Информация о репозитории:**\n"
        
        if process.returncode == 0:
            repo_info_text += f"```{process.stdout.strip()}```\n"
        else:
            repo_info_text += "Не удалось получить информацию\n"
        
        repo_info_text += f"**Целевой репозиторий:**\nSancboysArt/sancho-tool\n"
        repo_info_text += f"**Ссылка:** https://github.com/SancboysArt/sancho-tool"
        
        await event.edit(repo_info_text)
        
    except Exception as e:
        logging.error(f"Error in repo_info: {str(e)}")
        await event.edit(f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern=r"\.ping", outgoing=True))
async def ping(event):
    try:
        start_time_ping = time.time()
        msg = await event.edit("Проверка ping...")
        ping_time = round((time.time() - start_time_ping) * 1000, 2)
        await msg.edit(f"Ping: {ping_time}ms")
    except Exception as e:
        logging.error(f"Error in ping: {str(e)}")
        await event.edit(f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern=r"\.uptime", outgoing=True))
async def uptime(event):
    try:
        uptime_seconds = int(time.time() - start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        await event.edit(f"Время работы: {hours}ч {minutes}м {seconds}с")
    except Exception as e:
        logging.error(f"Error in uptime: {str(e)}")
        await event.edit(f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern=r"\.save", outgoing=True))
async def save_self_destructing_media(event):
    try:
        reply = await event.get_reply_message()
        if reply and reply.media and reply.media.ttl_seconds:
            await client.send_message("me", "Сохранено самоудаляющееся медиа:", file=reply.media)
            await event.edit("Медиа сохранено в избранное")
        else:
            await event.edit("Ответьте на самоудаляющееся медиа")
    except Exception as e:
        logging.error(f"Error in save_self_destructing_media: {str(e)}")
        await event.edit(f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern=r"\.phones", outgoing=True))
async def scan_numbers(event):
    try:
        await event.edit("Сканирование номеров...")
        chat = await event.get_chat()
        users = await client.get_participants(chat)
        phone_numbers = {}
        for user in users:
            if user.phone:
                phone_numbers[user.first_name or "Без имени"] = user.phone
        if phone_numbers:
            result = "Найденные номера:\n" + "\n".join(f"{name}: {phone}" for name, phone in phone_numbers.items())
            await client.send_message("me", result)
            await event.edit("Номера отправлены в избранное")
        else:
            await event.edit("В чате нет номеров")
    except Exception as e:
        logging.error(f"Error in scan_numbers: {str(e)}")
        await event.edit(f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern=r"\.start", outgoing=True))
async def start_command(event):
    try:
        await event.edit("Sancho-Tool запущен\nИспользуйте .help для просмотра команд")
    except Exception as e:
        logging.error(f"Error in start_command: {str(e)}")
        await event.edit(f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern=r"\.restart", outgoing=True))
async def restart_command(event):
    try:
        await event.edit("Перезапуск Sancho-Tool...")
        await asyncio.sleep(2)
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        logging.error(f"Error in restart_command: {str(e)}")
        await event.edit(f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern=r"\.me", outgoing=True))
async def me_command(event):
    try:
        me = await client.get_me()
        await event.edit(f"Информация о пользователе:\n"
                       f"Имя: {me.first_name}\n"
                       f"Фамилия: {me.last_name or 'Нет'}\n"
                       f"Username: @{me.username or 'Нет'}\n"
                       f"ID: {me.id}\n"
                       f"Номер: {me.phone or 'Скрыт'}")
    except Exception as e:
        logging.error(f"Error in me_command: {str(e)}")
        await event.edit(f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern=r"\.help", outgoing=True))
async def help_command(event):
    try:
        help_text = (
            "**Sancho-Tool | Полный список команд**\n\n"
            "**Основные команды:**\n"
            "• .start - __Запуск системы__\n"
            "• .help - __Полный список команд__\n"
            "• .ping - __Проверка скорости отклика__\n"
            "• .uptime - __Время работы системы__\n"
            "• .me - __Информация о пользователе__\n"
            "• .restart - __Перезагрузка системы__\n"
            "• .update - __Обновление до последней версии__\n\n"
            
            "**Медиа команды:**\n"
            "• .save - __Сохранение самоудаляющегося контента__\n"
            "• .phones - __Сканирование номеров в чате__\n\n"
            
            "**Сервисные команды:**\n"
            "• .sancho - __Информация о системе__\n"
            "• .sk <ссылка> - __Скачать видео с Tiktok/Youtube__\n"
            "• .swat - __Включить/Выключить язык сватера__\n"
            "• .dl help - __Управление автоудалением__\n"
            "• .call <число> - __Призыв участников чата по умолчанию всех__\n"
            "• .respond help - __Помощь с автоответчиком__\n"
            "• .trns help - __Помощь с переводчиком__ \n"
            "• .media help - __Помощь с медиа__\n"
            "• .sq <time> <message> - __Запланировать отправку сообщения__\n"
            "• .who - __Информация о пользователе__\n"
            "• .gpt - __Запрос к AI__\n\n"
            
            "**Техническая информация:**\n"
            "__Версия: 1.0__\n"
            "__Платформа: Telethon__\n"
            "__Разработчик: @CekcyaJlHblu_6po__\n"
            "__Статус: Production Ready__"
        )

        image_path = "help.jpg"
        if os.path.exists(image_path):
            try:
                await client.send_file(event.chat_id, image_path, caption=help_text)
                await event.delete()
            except Exception as e:
                logging.error(f"Ошибка отправки help image: {e}")
                await event.edit(help_text)
        else:
            await event.edit(help_text)
    except Exception as e:
        logging.error(f"Error in help_command: {str(e)}")
        await event.edit(f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern=r"\.sancho", outgoing=True))
async def sancho_info(event):
    try:
        start_time_ping = time.time()
        msg = await event.edit("идет пиздатая загрузка...")
        end_time_ping = time.time()
        ping_time = round((end_time_ping - start_time_ping) * 1000, 2)
        
        me = await client.get_me()
        phone_number = me.phone if me.phone else 'Hidden'
        
        # Проверяем наличие ошибок при загрузке модулей
        status = "Active" if not modules_load_errors else "Errors"
        
        info_text = (
            "**Sancho-Tool | System**\n\n"
            f"**Version:** 1.0\n"
            f"**Platform:** Telethon\n"
            f"**Ping:** __{ping_time}ms__\n"
            f"**Status:** __{status}__\n\n"
            f"**Developer** - @CekcyaJlHblu_6po\n\n"
            "__Multifunctional extension__\n"
            "__for Telegram__"
        )
        
        image_path = "sancho.jpg"
        if os.path.exists(image_path):
            try:
                await client.send_file(event.chat_id, image_path, caption=info_text)
                await event.delete()
            except Exception as e:
                logging.error(f"Error sending image: {e}")
                await event.edit(info_text)
        else:
            await event.edit(info_text)
    except Exception as e:
        logging.error(f"Error in sancho_info: {str(e)}")
        await event.edit(f"Ошибка: {str(e)}")

# Загрузка модулей
load_modules(client)

# Запуск клиента
print("Запуск Sancho-Tool...")
print("Device:", device_model)
print("Время запуска:", time.strftime("%Y-%m-%d %H:%M:%S"))

client.start()
print("Sancho-Tool успешно запущен")
print("Используйте .help для списка команд")

client.run_until_disconnected()
