# Team Task Manager Telegram Bot

**Telegram-бот для управління командними завданнями**  
Натхненний реальним досвідом роботи в логістиці (Nova Poshta та Zammler).

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)

## 🎯 Основний функціонал
- ✅ **Покрокове додавання завдань** через зручні кнопки
- ✅ Перегляд **Моїх** і **Всіх** завдань
- ✅ Статистика команди
- ✅ Список прострочених завдань
- ✅ Інлайн-кнопки «✅ Готово»
- ✅ Постійне меню (Reply Keyboard)

## 🛠 Технології
- **Python 3**
- pyTelegramBotAPI
- SQLite3 (зберігання даних)
- ReplyKeyboard + InlineKeyboard
- Git

## 🚀 Як запустити

```bash
# 1. Клонуй репозиторій
git clone https://github.com/burykillia/tgTaskManagerBot.git
cd tgTaskManagerBot

# 2. Встанови залежності
pip install -r requirements.txt

# 3. Встав свій токен від @BotFather у main.py (рядок TOKEN = '...')

# 4. Запусти бота
python main.py