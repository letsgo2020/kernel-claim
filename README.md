# KernelDAO Claimer Bot

Бот для автоматического клейма токенов KernelDAO и отправки их на биржу.

Bot for automatic claiming of KernelDAO tokens and sending them to an exchange.

## Содержание | Contents
- [Требования | Requirements](#требования--requirements)
- [Установка Python | Python Installation](#установка-python--python-installation)
  - [Windows](#windows)
  - [macOS](#macos)
- [Установка бота | Bot Installation](#установка-бота--bot-installation)
  - [Windows](#windows-1)
  - [macOS](#macos-1)
- [Настройка конфигурации | Configuration](#настройка-конфигурации--configuration)
- [Запуск бота | Running the Bot](#запуск-бота--running-the-bot)
- [Функции бота | Bot Functions](#функции-бота--bot-functions)
- [Безопасность | Security](#безопасность--security)

## Требования | Requirements
- Python 3.8 или выше | Python 3.8 or higher
- Доступ к интернету | Internet access
- Ethereum кошельки с приватными ключами | Ethereum wallets with private keys
- Достаточно ETH для газа | Sufficient ETH for gas

## Установка Python | Python Installation

### Windows
1. Скачайте Python с официального сайта | Download Python from the official website: https://www.python.org/downloads/
2. При установке обязательно отметьте галочку "Add Python to PATH" | During installation, make sure to check "Add Python to PATH"
3. Нажмите "Install Now" | Click "Install Now"
4. Проверьте установку, открыв командную строку (cmd) и выполнив | Verify the installation by opening Command Prompt (cmd) and running:
   ```bash
   python --version
   ```

### macOS
1. Установите Homebrew (если еще не установлен) | Install Homebrew (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Установите Python через Homebrew | Install Python via Homebrew:
   ```bash
   brew install python
   ```
3. Проверьте установку | Verify the installation:
   ```bash
   python3 --version
   ```

## Установка бота | Bot Installation

### Windows
1. Скачайте репозиторий | Clone the repository:
   ```bash
   git clone https://github.com/letsgo2020/kernel-claim.git
   cd kernel-claim
   ```
2. Создайте виртуальное окружение | Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Активируйте виртуальное окружение | Activate the virtual environment:
   ```bash
   venv\Scripts\activate
   ```
4. Установите зависимости | Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### macOS
1. Скачайте репозиторий | Clone the repository:
   ```bash
   git clone https://github.com/letsgo2020/kernel-claim.git
   cd kernel-claim
   ```
2. Создайте виртуальное окружение | Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```
3. Активируйте виртуальное окружение | Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
4. Установите зависимости | Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Настройка конфигурации | Configuration

1. Создайте файл `.env` в корневой директории проекта | Create a `.env` file in the project root directory:
   ```bash
   # Windows
   copy .env.example .env
   
   # macOS
   cp .env.example .env
   ```

2. Отредактируйте файл `.env`, указав следующие параметры | Edit the `.env` file with the following parameters:
   ```
   # RPC URL
   ETH_RPC_URL=https://eth.llamarpc.com
   
   # Адрес токена | Token address
   TOKEN_ADDRESS=0x3f80b1c54ae920be41a77f8b902259d48cf24ccf
   
   # Адрес контракта дропа | Drop contract
   DROP_CONTRACT=0x68b55c20a2634b25a50a219b632f22854d810bf5
   
   # Лимиты газа | Gas limits
   CLAIM_GAS_LIMIT=200000
   TRANSFER_GAS_LIMIT=100000
   ```

3. Создайте файл `wallets.txt` в корневой директории | Create a `wallets.txt` file in the root directory:
   ```
   приватный_ключ1,адрес_биржи1
   приватный_ключ2,адрес_биржи2
   ```
   Каждая строка должна содержать приватный ключ кошелька и адрес биржи, куда будут отправлены токены, разделенные запятой. | Each line should contain a wallet's private key and the exchange address where tokens will be sent, separated by a comma.

## Запуск бота | Running the Bot

1. Убедитесь, что виртуальное окружение активировано | Ensure the virtual environment is activated:
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS
   source venv/bin/activate
   ```

2. Запустите бота | Run the bot:
   ```bash
   python main.py
   ```

## Функции бота | Bot Functions

1. **Проверка eligibility** - проверяет, может ли кошелек получить токены | **Eligibility Check** - checks if a wallet can receive tokens
2. **Проверка газа** - проверяет баланс ETH для клейма и отправки токенов | **Gas Check** - checks ETH balance for claiming and sending tokens
3. **Клейм токенов** - получает токены для eligible кошельков | **Token Claim** - receives tokens for eligible wallets
4. **Проверка полученных токенов** - показывает баланс полученных токенов | **Received Tokens Check** - shows the balance of received tokens
5. **Отправка на биржу** - отправляет токены на указанный адрес биржи | **Send to Exchange** - sends tokens to the specified exchange address

## Безопасность | Security

- Никогда не публикуйте файлы `.env` и `wallets.txt` в публичных репозиториях | Never publish `.env` and `wallets.txt` files in public repositories
- Храните приватные ключи в безопасном месте | Store private keys in a secure location
- Регулярно проверяйте баланс ETH на кошельках | Regularly check ETH balance on wallets
- Используйте надежные RPC провайдеры | Use reliable RPC providers
- При использовании API ключей (Alchemy, Infura) храните их в безопасности | Keep API keys (Alchemy, Infura) secure when used

## Логирование | Logging

Логи сохраняются в директории `logs/` | Logs are saved in the `logs/` directory:
- `all_YYYY-MM-DD.log` - Общий лог со всеми событиями | General log with all events
- Отдельные логи для каждого модуля (eligibility, claim, sender и т.д.) | Separate logs for each module (eligibility, claim, sender, etc.)

## Зависимости | Dependencies

См. файл `requirements.txt` | See `requirements.txt` file 