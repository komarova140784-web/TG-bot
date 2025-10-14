# watcher.py
import time
import os
import psutil
import telepot
import signal
import sys
import logging

# Настройка логирования
logging.basicConfig(
    filename='watcher.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Ваши данные
TOKEN = '7576092582:AAFYsY_iXq__70QuFrEbaAqU82wY4pUwyzk'
CHAT_ID = '1678221039'
PID_FILE = 'monitor.pid'
CHECK_INTERVAL = 60  # Интервал проверки в секундах

def send_message(message):
    try:
        bot = telepot.Bot(TOKEN)
        bot.sendMessage(CHAT_ID, message)
    except Exception as e:
        logging.error(f"Ошибка отправки сообщения: {e}")

def is_script_running():
    if not os.path.exists(PID_FILE):
        return False
    
    with open(PID_FILE, 'r') as f:
        pid = int(f.read().strip())
    
    try:
        proc = psutil.Process(pid)
        return proc.status() == psutil.STATUS_RUNNING
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def handle_exit(signum, frame):
    logging.info("Наблюдатель завершает работу...")
    sys.exit(0)

def main():
    # Регистрируем обработчик завершения
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    # Запускаем основной скрипт в фоновом режиме
    os.system(f'start /B python monitor.py')
    logging.info("Запущен monitor.py")
    
    time.sleep(5)  # Даём время на запуск
    
    while True:
        if not is_script_running():
            send_message("🚫 Компьютер выключен (скрипт остановлен)")
            logging.warning("Монитор остановлен, отправлено уведомление")
            break
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Произошла ошибка в watcher: {e}")
        send_message("⚠️ Произошла ошибка в работе наблюдателя")
