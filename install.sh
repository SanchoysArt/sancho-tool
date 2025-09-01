#!/bin/bash

echo "Установка Sancho-Tool..."
pkg update -y && pkg upgrade -y
pkg install python git -y
pip install telethon
git clone https://github.com/SanchoysArt/sancho-tool.git
cd sancho-tool
echo "Установка завершена! Запуск: python userbot.py"
