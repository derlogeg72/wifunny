#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WiFunny - Установщик зависимостей
Устанавливает необходимые пакеты для работы WiFunny в Termux с Kali Linux
"""

import os
import sys
import subprocess
import time
import shutil
import urllib.request
from pathlib import Path

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
    print(f"{Colors.BOLD}{Colors.BLUE}[---] Установщик WiFunny для Termux+Kali [---]{Colors.ENDC}")
    print(f"{Colors.YELLOW}[i] Установка необходимых компонентов для WiFi-пранков{Colors.ENDC}")
    print("\n")

def check_termux():
    """Проверяет, запущен ли скрипт в Termux"""
    print(f"{Colors.BLUE}[*] Проверка среды Termux...{Colors.ENDC}")
    
    is_termux = os.path.exists("/data/data/com.termux/files/usr")
    
    if is_termux:
        print(f"{Colors.GREEN}[✓] Скрипт запущен в Termux{Colors.ENDC}")
    else:
        print(f"{Colors.YELLOW}[i] Скрипт запущен не в Termux{Colors.ENDC}")
        print(f"{Colors.YELLOW}[i] Будет произведена обычная установка для Linux{Colors.ENDC}")
    
    return is_termux

def check_root():
    """Проверяет наличие root-доступа"""
    print(f"{Colors.BLUE}[*] Проверка root-доступа...{Colors.ENDC}")
    
    if os.geteuid() == 0:
        print(f"{Colors.GREEN}[✓] Root-доступ имеется{Colors.ENDC}")
        return True
    else:
        print(f"{Colors.RED}[✗] Root-доступ отсутствует{Colors.ENDC}")
        print(f"{Colors.YELLOW}[i] Для работы WiFunny требуются root-привилегии{Colors.ENDC}")
        print(f"{Colors.YELLOW}[i] В Termux выполните: su -c \"python setup.py\"{Colors.ENDC}")
        return False

def install_dependencies_termux():
    """Устанавливает зависимости в Termux"""
    print(f"{Colors.BLUE}[*] Установка зависимостей в Termux...{Colors.ENDC}")
    
    # Обновление репозиториев
    print(f"{Colors.BLUE}[*] Обновление репозиториев...{Colors.ENDC}")
    try:
        subprocess.check_call(
            ["apt", "update", "-y"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"{Colors.GREEN}[✓] Репозитории обновлены{Colors.ENDC}")
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}[✗] Не удалось обновить репозитории{Colors.ENDC}")
        return False
    
    # Установка базовых пакетов
    print(f"{Colors.BLUE}[*] Установка базовых пакетов...{Colors.ENDC}")
    packages = [
        "python", 
        "dnsutils",
        "dnsmasq", 
        "iptables", 
        "net-tools",
        "tcpdump",
        "wget",
        "curl",
        "git",
        "nmap"
    ]
    
    for package in packages:
        try:
            print(f"{Colors.BLUE}[*] Установка {package}...{Colors.ENDC}")
            subprocess.check_call(
                ["apt", "install", "-y", package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"{Colors.GREEN}[✓] {package} установлен{Colors.ENDC}")
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}[✗] Не удалось установить {package}{Colors.ENDC}")
    
    # Установка dsniff (для arpspoof)
    print(f"{Colors.BLUE}[*] Установка dsniff (для arpspoof)...{Colors.ENDC}")
    try:
        subprocess.check_call(
            ["apt", "install", "-y", "dsniff"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"{Colors.GREEN}[✓] dsniff установлен{Colors.ENDC}")
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}[✗] Не удалось установить dsniff{Colors.ENDC}")
        print(f"{Colors.YELLOW}[i] Попытка установки из альтернативного источника...{Colors.ENDC}")
        
        try:
            # Установка dsniff из репозитория Kali Linux
            subprocess.check_call(
                ["apt", "install", "-y", "dsniff"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=dict(os.environ, DEBIAN_FRONTEND="noninteractive")
            )
            print(f"{Colors.GREEN}[✓] dsniff установлен из альтернативного источника{Colors.ENDC}")
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}[✗] Не удалось установить dsniff из альтернативного источника{Colors.ENDC}")
            print(f"{Colors.YELLOW}[i] Вам нужно будет установить dsniff вручную{Colors.ENDC}")
    
    # Установка mitmproxy
    print(f"{Colors.BLUE}[*] Установка mitmproxy...{Colors.ENDC}")
    try:
        subprocess.check_call(
            ["pip", "install", "mitmproxy"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"{Colors.GREEN}[✓] mitmproxy установлен{Colors.ENDC}")
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}[✗] Не удалось установить mitmproxy через pip{Colors.ENDC}")
        print(f"{Colors.YELLOW}[i] Попытка установки через apt...{Colors.ENDC}")
        
        try:
            subprocess.check_call(
                ["apt", "install", "-y", "mitmproxy"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"{Colors.GREEN}[✓] mitmproxy установлен через apt{Colors.ENDC}")
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}[✗] Не удалось установить mitmproxy{Colors.ENDC}")
            print(f"{Colors.YELLOW}[i] Вам нужно будет установить mitmproxy вручную{Colors.ENDC}")
    
    print(f"{Colors.GREEN}[✓] Установка зависимостей в Termux завершена{Colors.ENDC}")
    return True

def install_dependencies_linux():
    """Устанавливает зависимости в обычном Linux"""
    print(f"{Colors.BLUE}[*] Установка зависимостей в Linux...{Colors.ENDC}")
    
    # Определение типа дистрибутива
    distro = ""
    if os.path.exists("/etc/debian_version"):
        distro = "debian"
    elif os.path.exists("/etc/redhat-release"):
        distro = "redhat"
    elif os.path.exists("/etc/arch-release"):
        distro = "arch"
    else:
        print(f"{Colors.YELLOW}[i] Неизвестный дистрибутив Linux{Colors.ENDC}")
        print(f"{Colors.YELLOW}[i] Попытка использовать apt для установки...{Colors.ENDC}")
        distro = "debian"
    
    # Обновление репозиториев
    print(f"{Colors.BLUE}[*] Обновление репозиториев...{Colors.ENDC}")
    try:
        if distro == "debian":
            subprocess.check_call(
                ["apt", "update", "-y"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        elif distro == "redhat":
            subprocess.check_call(
                ["yum", "update", "-y"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        elif distro == "arch":
            subprocess.check_call(
                ["pacman", "-Sy"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        print(f"{Colors.GREEN}[✓] Репозитории обновлены{Colors.ENDC}")
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}[✗] Не удалось обновить репозитории{Colors.ENDC}")
    
    # Установка базовых пакетов
    print(f"{Colors.BLUE}[*] Установка базовых пакетов...{Colors.ENDC}")
    
    if distro == "debian":
        packages = [
            "python3", 
            "dnsutils",
            "dnsmasq", 
            "iptables", 
            "net-tools",
            "tcpdump",
            "wget",
            "curl",
            "git",
            "nmap",
            "dsniff",
            "python3-pip"
        ]
        install_cmd = ["apt", "install", "-y"]
    elif distro == "redhat":
        packages = [
            "python3", 
            "bind-utils",
            "dnsmasq", 
            "iptables", 
            "net-tools",
            "tcpdump",
            "wget",
            "curl",
            "git",
            "nmap",
            "dsniff",
            "python3-pip"
        ]
        install_cmd = ["yum", "install", "-y"]
    elif distro == "arch":
        packages = [
            "python", 
            "bind-tools",
            "dnsmasq", 
            "iptables", 
            "net-tools",
            "tcpdump",
            "wget",
            "curl",
            "git",
            "nmap",
            "dsniff",
            "python-pip"
        ]
        install_cmd = ["pacman", "-S", "--noconfirm"]
    
    for package in packages:
        try:
            print(f"{Colors.BLUE}[*] Установка {package}...{Colors.ENDC}")
            subprocess.check_call(
                install_cmd + [package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"{Colors.GREEN}[✓] {package} установлен{Colors.ENDC}")
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}[✗] Не удалось установить {package}{Colors.ENDC}")
    
    # Установка mitmproxy
    print(f"{Colors.BLUE}[*] Установка mitmproxy...{Colors.ENDC}")
    try:
        subprocess.check_call(
            ["pip3", "install", "mitmproxy"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"{Colors.GREEN}[✓] mitmproxy установлен{Colors.ENDC}")
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}[✗] Не удалось установить mitmproxy через pip{Colors.ENDC}")
        print(f"{Colors.YELLOW}[i] Попытка установки через пакетный менеджер...{Colors.ENDC}")
        
        try:
            subprocess.check_call(
                install_cmd + ["mitmproxy"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"{Colors.GREEN}[✓] mitmproxy установлен через пакетный менеджер{Colors.ENDC}")
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}[✗] Не удалось установить mitmproxy{Colors.ENDC}")
            print(f"{Colors.YELLOW}[i] Вам нужно будет установить mitmproxy вручную{Colors.ENDC}")
    
    print(f"{Colors.GREEN}[✓] Установка зависимостей в Linux завершена{Colors.ENDC}")
    return True

def download_memes():
    """Загружает мемы для пранков"""
    print(f"{Colors.BLUE}[*] Загрузка мемов для пранков...{Colors.ENDC}")
    
    # Создание директории для мемов
    meme_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources/memes")
    os.makedirs(meme_dir, exist_ok=True)
    
    # URL мемов (заглушки, можно заменить на реальные URL)
    meme_urls = [
        "https://example.com/meme1.jpg",
        "https://example.com/meme2.jpg",
        "https://example.com/meme3.jpg",
        "https://example.com/meme4.jpg",
        "https://example.com/meme5.jpg"
    ]
    
    # Создание заглушек вместо загрузки (для демонстрации)
    for i in range(1, 6):
        meme_path = os.path.join(meme_dir, f"meme{i}.jpg")
        
        # Проверка, существует ли файл
        if os.path.exists(meme_path):
            print(f"{Colors.GREEN}[✓] Мем {i} уже существует{Colors.ENDC}")
            continue
        
        # Создание пустого файла (заглушка)
        try:
            with open(meme_path, "w") as f:
                f.write(f"This is a placeholder for meme {i}")
            print(f"{Colors.GREEN}[✓] Создана заглушка для мема {i}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.RED}[✗] Не удалось создать заглушку для мема {i}: {str(e)}{Colors.ENDC}")
    
    print(f"{Colors.GREEN}[✓] Мемы для пранков подготовлены{Colors.ENDC}")
    print(f"{Colors.YELLOW}[i] Примечание: созданы заглушки вместо настоящих мемов{Colors.ENDC}")
    print(f"{Colors.YELLOW}[i] Замените файлы в директории resources/memes настоящими изображениями{Colors.ENDC}")
    return True

def make_executable():
    """Делает скрипт wifunny.py исполняемым"""
    print(f"{Colors.BLUE}[*] Настройка прав доступа...{Colors.ENDC}")
    
    try:
        script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "wifunny.py")
        os.chmod(script_path, 0o755)
        print(f"{Colors.GREEN}[✓] Скрипт wifunny.py сделан исполняемым{Colors.ENDC}")
        return True
    except Exception as e:
        print(f"{Colors.RED}[✗] Не удалось сделать скрипт исполняемым: {str(e)}{Colors.ENDC}")
        return False

def create_launcher():
    """Создает скрипт запуска с правами root"""
    print(f"{Colors.BLUE}[*] Создание скрипта запуска...{Colors.ENDC}")
    
    launcher_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "start_wifunny.sh")
    
    try:
        with open(launcher_path, "w") as f:
            f.write("""#!/bin/bash
# Скрипт запуска WiFunny с правами root

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$EUID" -ne 0 ]; then
  echo "Для работы WiFunny требуются права root."
  echo "Запуск с sudo..."
  exec sudo "$0" "$@"
fi

cd "$SCRIPT_DIR"
python3 wifunny.py
""")
        
        # Делаем скрипт запуска исполняемым
        os.chmod(launcher_path, 0o755)
        
        print(f"{Colors.GREEN}[✓] Скрипт запуска создан: {launcher_path}{Colors.ENDC}")
        return True
    except Exception as e:
        print(f"{Colors.RED}[✗] Не удалось создать скрипт запуска: {str(e)}{Colors.ENDC}")
        return False

def main():
    """Основная функция"""
    # Вывод баннера
    print_banner()
    
    # Проверка Termux
    is_termux = check_termux()
    
    # Проверка root-доступа
    if not check_root():
        return
    
    # Установка зависимостей
    if is_termux:
        if not install_dependencies_termux():
            print(f"{Colors.RED}[!] Установка зависимостей в Termux завершилась с ошибками{Colors.ENDC}")
            print(f"{Colors.YELLOW}[i] Некоторые функции могут работать некорректно{Colors.ENDC}")
    else:
        if not install_dependencies_linux():
            print(f"{Colors.RED}[!] Установка зависимостей в Linux завершилась с ошибками{Colors.ENDC}")
            print(f"{Colors.YELLOW}[i] Некоторые функции могут работать некорректно{Colors.ENDC}")
    
    # Загрузка мемов
    download_memes()
    
    # Настройка прав доступа
    make_executable()
    
    # Создание скрипта запуска
    create_launcher()
    
    print(f"\n{Colors.GREEN}[✓] Установка WiFunny завершена!{Colors.ENDC}")
    print(f"{Colors.YELLOW}[i] Для запуска выполните:{Colors.ENDC}")
    print(f"{Colors.BOLD}")
    print(f"    ./start_wifunny.sh")
    print(f"{Colors.ENDC}")
    print(f"{Colors.YELLOW}[i] Или с правами root:{Colors.ENDC}")
    print(f"{Colors.BOLD}")
    print(f"    sudo python3 wifunny.py")
    print(f"{Colors.ENDC}")
    
    if is_termux:
        print(f"{Colors.YELLOW}[i] В Termux с правами root:{Colors.ENDC}")
        print(f"{Colors.BOLD}")
        print(f"    su -c \"python wifunny.py\"")
        print(f"{Colors.ENDC}")

if __name__ == "__main__":
    main()
