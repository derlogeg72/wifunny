#!/bin/bash
# Скрипт для установки Kali Linux в Termux

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Функция для вывода баннера
print_banner() {
    clear
    echo -e "${BOLD}${GREEN}"
    echo " __        ___ _____                         "
    echo " \ \      / (_)  ___|   _ _ __  _ __  _   _ "
    echo "  \ \ /\ / /| | |_ | | | | '_ \| '_ \| | | |"
    echo "   \ V  V / | |  _|| |_| | | | | | | | |_| |"
    echo "    \_/\_/  |_|_|   \__,_|_| |_|_| |_|\__, |"
    echo "                                       |___/ "
    echo -e "${NC}"
    echo -e "${BOLD}${BLUE}[---] Установщик Kali Linux для Termux [---]${NC}"
    echo -e "${YELLOW}[i] Подготовка среды для WiFunny${NC}"
    echo ""
}

# Функция для проверки Termux
check_termux() {
    echo -e "${BLUE}[*] Проверка среды Termux...${NC}"
    
    if [ -d "/data/data/com.termux/files/usr" ]; then
        echo -e "${GREEN}[✓] Скрипт запущен в Termux${NC}"
        return 0
    else
        echo -e "${RED}[✗] Скрипт должен быть запущен в Termux${NC}"
        echo -e "${YELLOW}[i] Установите Termux из F-Droid и повторите попытку${NC}"
        exit 1
    fi
}

# Проверка наличия необходимых пакетов
check_requirements() {
    echo -e "${BLUE}[*] Проверка наличия необходимых пакетов...${NC}"
    
    packages=("curl" "wget" "proot" "tar" "python")
    missing_packages=()
    
    for package in "${packages[@]}"; do
        if ! command -v "$package" &> /dev/null; then
            echo -e "${RED}[✗] Пакет $package не установлен${NC}"
            missing_packages+=("$package")
        else
            echo -e "${GREEN}[✓] Пакет $package установлен${NC}"
        fi
    done
    
    if [ ${#missing_packages[@]} -gt 0 ]; then
        echo -e "${YELLOW}[i] Установка отсутствующих пакетов...${NC}"
        
        pkg update -y
        
        for package in "${missing_packages[@]}"; do
            echo -e "${BLUE}[*] Установка $package...${NC}"
            pkg install -y "$package"
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}[✓] Пакет $package успешно установлен${NC}"
            else
                echo -e "${RED}[✗] Не удалось установить пакет $package${NC}"
                echo -e "${YELLOW}[i] Попробуйте установить его вручную: pkg install -y $package${NC}"
                exit 1
            fi
        done
    fi
    
    echo -e "${GREEN}[✓] Все необходимые пакеты установлены${NC}"
}

# Установка Kali Linux с помощью Nethunter
install_nethunter() {
    echo -e "${BLUE}[*] Установка Kali Linux с помощью Nethunter...${NC}"
    
    # Проверка, существует ли уже установка Kali
    if [ -d "$HOME/kali-arm64" ]; then
        echo -e "${YELLOW}[i] Kali Linux уже установлен${NC}"
        echo -ne "${YELLOW}[?] Хотите переустановить? (y/n): ${NC}"
        read reinstall
        
        if [ "$reinstall" != "y" ] && [ "$reinstall" != "Y" ]; then
            echo -e "${GREEN}[✓] Используем существующую установку${NC}"
            return 0
        else
            echo -e "${BLUE}[*] Удаление существующей установки...${NC}"
            rm -rf "$HOME/kali-arm64"
            echo -e "${GREEN}[✓] Существующая установка удалена${NC}"
        fi
    fi
    
    echo -e "${BLUE}[*] Загрузка скрипта установки...${NC}"
    wget -O "$HOME/install-nethunter-termux" \
        https://offs.ec/2MceZWr
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}[✗] Не удалось загрузить скрипт установки${NC}"
        echo -e "${YELLOW}[i] Попробуйте выполнить команду вручную:${NC}"
        echo -e "${YELLOW}   wget -O install-nethunter-termux https://offs.ec/2MceZWr${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}[✓] Скрипт установки загружен${NC}"
    
    echo -e "${BLUE}[*] Установка прав на выполнение...${NC}"
    chmod +x "$HOME/install-nethunter-termux"
    
    echo -e "${BLUE}[*] Запуск установки Kali Nethunter...${NC}"
    echo -e "${YELLOW}[i] Это может занять некоторое время...${NC}"
    
    "$HOME/install-nethunter-termux"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}[✗] Установка Kali Nethunter завершилась с ошибкой${NC}"
        echo -e "${YELLOW}[i] Попробуйте запустить скрипт установки вручную:${NC}"
        echo -e "${YELLOW}   ./install-nethunter-termux${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}[✓] Kali Linux успешно установлен${NC}"
}

# Создание скрипта запуска WiFunny из Kali
create_launcher() {
    echo -e "${BLUE}[*] Создание скрипта запуска WiFunny из Kali...${NC}"
    
    launcher="$HOME/launch-wifunny.sh"
    
    cat > "$launcher" << 'EOF'
#!/bin/bash
# Скрипт запуска WiFunny из Kali в Termux

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Запуск WiFunny из Kali Linux..."

# Проверка наличия WiFunny
if [ ! -d "$SCRIPT_DIR/wifunny" ]; then
    echo "Папка wifunny не найдена. Клонирование репозитория..."
    cd "$SCRIPT_DIR"
    git clone https://github.com/yourusername/wifunny
    if [ $? -ne 0 ]; then
        echo "Не удалось клонировать репозиторий. Проверьте подключение к интернету."
        exit 1
    fi
fi

# Запуск Kali и WiFunny
cd "$SCRIPT_DIR"
nethunter kex passwd # Установка пароля для VNC сервера (если нужно)
nethunter kex &      # Запуск VNC сервера в фоновом режиме

# Ждем запуска VNC сервера
sleep 5

# Запуск WiFunny в Kali
nethunter -r "cd /sdcard/Download/wifunny && python setup.py && python wifunny.py"

echo "WiFunny завершил работу."
EOF
    
    chmod +x "$launcher"
    
    echo -e "${GREEN}[✓] Скрипт запуска создан: $launcher${NC}"
    echo -e "${YELLOW}[i] Для запуска WiFunny используйте команду:${NC}"
    echo -e "${YELLOW}   ./launch-wifunny.sh${NC}"
}

# Основная функция
main() {
    print_banner
    
    check_termux
    check_requirements
    install_nethunter
    create_launcher
    
    echo -e "\n${GREEN}[✓] Установка Kali Linux завершена!${NC}"
    echo -e "${YELLOW}[i] Теперь вы можете использовать WiFunny следующим образом:${NC}"
    echo -e "${BOLD}"
    echo "    1. Запустите Kali Linux: nethunter"
    echo "    2. Внутри Kali выполните: cd /sdcard/Download/wifunny"
    echo "    3. Установите зависимости: python setup.py"
    echo "    4. Запустите WiFunny: python wifunny.py"
    echo -e "${NC}"
    echo -e "${YELLOW}[i] Или используйте скрипт автоматического запуска:${NC}"
    echo -e "${BOLD}"
    echo "    ./launch-wifunny.sh"
    echo -e "${NC}"
}

# Запуск основной функции
main
