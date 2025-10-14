import asyncio
import telepot
import os
import sys
import re
import pytz
import signal
import psutil
import datetime
import logging
from PIL import ImageGrab
from pynput import mouse, keyboard
from pynput.mouse import Button
import platform
import time
import subprocess

TOKEN = '7576092582:AAFYsY_iXq__70QuFrEbaAqU82wY4pUwyzk'
CHAT_ID = '1678221039'
CHECK_INTERVAL = 3600
PID_FILE = 'monitor.pid'
CURRENT_USER = os.getlogin()
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
steam_path = None

logging.basicConfig(filename='monitor.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_msg(m):
    try:
        telepot.Bot(TOKEN).sendMessage(CHAT_ID, m)
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")

def write_pid():
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

def remove_pid():
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

async def check_status():
    while True:
        try:
            # Получаем время загрузки системы через psutil
            boot_timestamp = psutil.boot_time()
            boot_datetime = datetime.datetime.fromtimestamp(boot_timestamp)
            
            # Форматируем время
            boot_formatted = boot_datetime.strftime('%d.%m.%Y %H:%M:%S')
            current_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            
            # Рассчитываем время работы
            uptime = datetime.datetime.now() - boot_datetime
            days = uptime.days
            seconds = uptime.seconds
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            
            # Форматируем время работы в читаемый вид
            uptime_str = f"{days} дней, {hours} часов, {minutes} минут"
            
            # Формируем сообщение
            msg = (
                f"💻 Система активна\n"
                f"Время запуска: {boot_formatted}\n"
                f"Текущее время: {current_time}\n"
                f"Работает уже: {uptime_str}"
            )
            
            send_msg(msg)
            
        except Exception as e:
            logging.error(f"Ошибка при проверке статуса: {str(e)}")
            send_msg("❌ Произошла ошибка при получении статуса системы")
            
        # Ждем следующий интервал проверки
        await asyncio.sleep(CHECK_INTERVAL)

def handle_exit(*args):
    send_msg("🚫 Остановлен")
    remove_pid()
    sys.exit(0)

def send_screenshot():
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"screenshot_{timestamp}.png"
        img = ImageGrab.grab()
        img.save(screenshot_filename)
        
        if os.path.exists(screenshot_filename):
            with open(screenshot_filename, 'rb') as f:
                telepot.Bot(TOKEN).sendPhoto(CHAT_ID, f)
            send_msg(f"📸 Скриншот отправлен ({timestamp})")
            os.remove(screenshot_filename)
        else:
            send_msg("Ошибка: файл скриншота не создан")
    except Exception as e:
        logging.error(f"Ошибка при отправке скриншота: {e}")
        send_msg(f"Ошибка при отправке скриншота: {str(e)}")

# Функции управления мышью
def move_mouse(x, y):
    try:
        mouse.Controller().position = (int(x), int(y))
        send_msg(f"🖱️ Мышь перемещена в координаты ({x}, {y})")
    except Exception as e:
        logging.error(f"Ошибка перемещения мыши: {e}")
        send_msg(f"Ошибка перемещения мыши: {str(e)}")

def click_mouse(button='left'):
    try:
        if button.lower() == 'левый':
            mouse.Controller().click(Button.left)
            send_msg("🖱️ Нажат левый клик")
        elif button.lower() == 'правый':
            mouse.Controller().click(Button.right)
            send_msg("🖱️ Нажат правый клик")
        elif button.lower() == 'средняя':
            mouse.Controller().click(Button.middle)
            send_msg("🖱️ Нажат средний клик")
        else:
            send_msg("❌ Неверный параметр кнопки")
    except Exception as e:
        logging.error(f"Ошибка клика мыши: {e}")
        send_msg(f"Ошибка клика мыши: {str(e)}")
        
def handle_cmd(msg):
    c_type, _, chat_id = telepot.glance(msg)
    if c_type == 'my_chat_member': 
        return
    
    if c_type == 'text' and str(chat_id) == CHAT_ID:
        cmd = msg['text'].strip().lower()
        
        if cmd in ['скриншот', 'screenshot']:
            send_screenshot()
        
        elif cmd in ('выключить', 'Выключить'):
            os.system('shutdown /s /t 60')
            send_msg("⚠️ Выключение через 60 секунд ⚠️")
        
        elif cmd in ('заблокировать', 'Заблокировать'):
            os.system('rundll32.exe user32.dll,LockWorkStation')
            send_msg("🔒 Система заблокирована")
        
        elif cmd in ('перезагрузить', 'Перезагрузить'):
            os.system('shutdown /r /t 60')
            send_msg("⚠️ Перезагрузка через 60 секунд ⚠️")
        
        elif cmd in ('отменить', 'Отменить'):
            os.system('shutdown /a')
            send_msg("⚠️ Отменено ⚠️")
            
        elif cmd in ['инфа пк', 'Инфа пк']:
            try:
                cpu = psutil.cpu_percent(interval=1, percpu=True)
                cpu_avg = psutil.cpu_percent()
                mem = psutil.virtual_memory()
                
                disks = psutil.disk_partitions()
                disk_info = ""
                for partition in disks:
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        disk_info += (
                            f"Диск {partition.device}: "
                            f"{usage.percent:.2f}% "
                            f"({usage.used/(1024**3):.2f}/{usage.total/(1024**3):.2f} ГБ)\n"
                        )
                        
                    except PermissionError:
                        continue
                
                boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime('%d.%m.%Y %H:%M:%S')
                uptime = str(datetime.timedelta(seconds=int(time.time() - psutil.boot_time())))
                
                message = (
                    f"📊 Системная нагрузка:\n"
                    f"CPU: {cpu_avg:.2f}% ({'; '.join(f'CPU{i+1}: {p:.2f}%' for i, p in enumerate(cpu))})\n"
                    f"Память: {mem.percent:.2f}% ({mem.used/(1024**3):.2f}/{mem.total/(1024**3):.2f} ГБ)\n"
                    f"Диски:\n{disk_info}"
                )
                
                try:
                    if hasattr(psutil, 'sensors_temperatures'):
                        temps = psutil.sensors_temperatures()
                        if temps:
                            sensor = temps.get('coretemp', temps.get('acpitz', temps.get('nvml', temps.values().__next__()))[0])
                            message += f"Температура: {sensor.current:.2f}°C\n"
                        else:
                            message += "Температура: Недоступно\n"
                except Exception as e:
                    message += f"Ошибка температуры: {str(e)}\n"
                
                try:
                    net = psutil.net_io_counters()
                    message += (
                        f"📶 Сеть:\n"
                        f"↑{net.bytes_sent / (1024**2):.2f} МБ/с, "
                        f"↓{net.bytes_recv / (1024**2):.2f} МБ/с\n"
                    )
                except Exception as e:
                    message += f"Ошибка сети: {str(e)}\n"
                
                message += (
                    f"Время загрузки: {boot_time}\n"
                    f"Время работы: {uptime}\n"
                    f"Текущий пользователь: {CURRENT_USER}\n"
                    f"Версия ОС: {platform.platform()}\n"
                    f"Архитектура: {platform.machine()}\n"
                    f"Имя компьютера: {platform.node()}"
                )
                
                send_msg(message)
                
            except Exception as e:
                logging.error(f"Ошибка получения системной информации: {str(e)}")
                send_msg("❌ Произошла ошибка при получении информации о системе")         
        
        elif cmd in ('пк', 'Пк'):
            send_msg("📊 Система активна")

        # Новые команды управления мышью
        elif cmd.startswith('переместить'):
            try:
                _, x, y = cmd.split()
                move_mouse(x, y)
            except:
                send_msg("❌ Неверный формат команды. Используйте: переместить X Y")

        elif cmd.startswith('клик'):
            try:
                _, button = cmd.split()
                click_mouse(button)
            except:
                send_msg("❌ Неверный формат команды. Используйте: клик left/right/middle")

        elif cmd in ('о боте', 'О боте'):
            send_msg(
                "🖥️ **Ваш персональный помощник для управления ПК** 🤖\n\n"
                "Добро пожаловать в мир удобного управления компьютером! 🎯 Я создан, чтобы сделать вашу работу с ПК максимально комфортной и эффективной.\n\n"
            )
        
        elif cmd in ('помощь', 'Помощь'):
            send_msg("🔍 **Список доступных команд:**\n\n"
                    "**Базовые команды:**\n"
                    "• скриншот - сделать скриншот\n"
                    "• выключить - выключение ПК\n"
                    "• перезагрузить - перезагрузка\n"
                    "• заблокировать - блокировка\n"
                    "• отменить - отмена действий\n\n"
                    
                    "**Управление мышью:**\n"
                    "• переместить X Y - перемещение курсора\n"
                    "• клик левый - левый клик\n"
                    "• клик правый - правый клик\n"
                    "• клик средняя - средний клик\n\n"
                    
                    "**Информация:**\n"
                    "• пк - статус системы\n"
                    "• о боте - информация о боте\n"
                    "• помощь - список команд\n\n"
                    
                    "Управление приложениями:**\n"
                    "Открыть стим - происходит открытие стима через приложение если дабавлено в папку ярлык\n"
            )

        elif cmd in ('открыть стим', 'Открыть стим'):
            try:
                # Проверяем существование папки и файла
                if not os.path.exists(os.path.join(script_dir, 'Ярлыки')):
                    raise FileNotFoundError("Папка 'Ярлыки' не найдена")
        
                # Ищем файл с разными расширениями
                steam_path = os.path.join(script_dir, 'Ярлыки', 'Steam.lnk')
                if not os.path.exists(steam_path):
                    steam_path = os.path.join(script_dir, 'Ярлыки', 'Steam')
                    if not os.path.exists(steam_path):
                        raise FileNotFoundError("Ярлык Steam не найден")
        
                # Проверяем права доступа
                if not os.access(steam_path, os.F_OK | os.X_OK):
                    raise PermissionError("Нет прав доступа к ярлыку Steam")
        
                # Запуск через командную строку
                subprocess.Popen(f'cmd /c start "" "{steam_path}"', shell=True)
                send_msg("✅ Steam запущен")
        
            except FileNotFoundError as fnf_error:
                logging.error(f"Ошибка: {fnf_error}")
                send_msg("❌ Не удалось найти папку 'Ярлыки' или ярлык Steam")
        
            except PermissionError as perm_error:
                logging.error(f"Ошибка прав доступа: {perm_error}")
                send_msg("❌ Нет прав доступа к ярлыку Steam")
        
            except Exception as e:
                logging.error(f"Ошибка при запуске Steam: {str(e)}")
                send_msg("❌ Произошла ошибка при запуске Steam")

        elif cmd in ('открыть вк', 'Открыть вк'):
            try:
                subprocess.Popen(f'cmd /c start https://vk.com/im/convo/730734979?entrypoint=list_all', shell=True)
                send_msg("✅ ВКонтакте открыт")
        
            except Exception as e:
                logging.error(f"Ошибка при открытии ВКонтакте: {str(e)}")
                send_msg("❌ Произошла ошибка при открытии ВКонтакте")
            
        elif cmd in ('открыть ютуб', 'Открыть ютуб'):
            try:
                subprocess.Popen(f'cmd /c start https://www.youtube.com/', shell=True)
                send_msg("✅ Ютуб открыт")
        
            except Exception as e:
                logging.error(f"Ошибка при открытии Ютуб: {str(e)}")
                send_msg("❌ Произошла ошибка при открытии Ютуб")

        elif cmd in ('открыть тг', 'Открыть тг'):
            try:
                # Проверяем существование папки и файла
                if not os.path.exists(os.path.join(script_dir, 'Ярлыки')):
                    raise FileNotFoundError("Папка 'Ярлыки' не найдена")
        
                # Ищем файл с разными расширениями
                steam_path = os.path.join(script_dir, 'Ярлыки', 'Telegram.lnk')
                if not os.path.exists(steam_path):
                    steam_path = os.path.join(script_dir, 'Ярлыки', 'Telegram')
                    if not os.path.exists(steam_path):
                        raise FileNotFoundError("Ярлык Telegram не найден")
        
                # Проверяем права доступа
                if not os.access(steam_path, os.F_OK | os.X_OK):
                    raise PermissionError("Нет прав доступа к ярлыку Telegram")
        
                # Запуск через командную строку
                subprocess.Popen(f'cmd /c start "" "{steam_path}"', shell=True)
                send_msg("✅ Telegram запущен")
        
            except FileNotFoundError as fnf_error:
                logging.error(f"Ошибка: {fnf_error}")
                send_msg("❌ Не удалось найти папку 'Ярлыки' или ярлык Telegram")
        
            except PermissionError as perm_error:
                logging.error(f"Ошибка прав доступа: {perm_error}")
                send_msg("❌ Нет прав доступа к ярлыку Telegram")
        
            except Exception as e:
                logging.error(f"Ошибка при запуске Telegram: {str(e)}")
                send_msg("❌ Произошла ошибка при запуске Telegram")
                
        elif cmd in ('открыть дс', 'Открыть дс'):
            try:
                # Проверяем существование папки и файла
                if not os.path.exists(os.path.join(script_dir, 'Ярлыки')):
                    raise FileNotFoundError("Папка 'Ярлыки' не найдена")
        
                # Ищем файл с разными расширениями
                steam_path = os.path.join(script_dir, 'Ярлыки', 'Discord.lnk')
                if not os.path.exists(steam_path):
                    steam_path = os.path.join(script_dir, 'Ярлыки', 'Discord')
                    if not os.path.exists(steam_path):
                        raise FileNotFoundError("Ярлык Discord не найден")
        
                # Проверяем права доступа
                if not os.access(steam_path, os.F_OK | os.X_OK):
                    raise PermissionError("Нет прав доступа к ярлыку Discord")
        
                # Запуск через командную строку
                subprocess.Popen(f'cmd /c start "" "{steam_path}"', shell=True)
                send_msg("✅ Discord запущен")
        
            except FileNotFoundError as fnf_error:
                logging.error(f"Ошибка: {fnf_error}")
                send_msg("❌ Не удалось найти папку 'Ярлыки' или ярлык Discord")
        
            except PermissionError as perm_error:
                logging.error(f"Ошибка прав доступа: {perm_error}")
                send_msg("❌ Нет прав доступа к ярлыку Discord")
        
            except Exception as e:
                logging.error(f"Ошибка при запуске Discord: {str(e)}")
                send_msg("❌ Произошла ошибка при запуске Discord")                

        elif cmd in ('привет', 'Привет'):
            send_msg("Добро пожаловать!\n"
                    "Вы подключены к боту управления ПК.\n"
        "Напишите 'помощь' для списка команд")

async def main():
    signal.signal(signal.SIGINT, handle_exit)
    write_pid()
    bot = telepot.Bot(TOKEN)
    bot.message_loop(handle_cmd)
    send_msg("🔌 Компьютер запущен и готов к работе")
    await check_status()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.critical(f"Критическая ошибка: {e}")
        handle_exit()                    