# KernelDAO Claimer Bot

Бот для автоматического клейма токенов KernelDAO и отправки их на биржу.

## Содержание
- [Требования](#требования)
- [Установка Python](#установка-python)
  - [Windows](#windows)
  - [macOS](#macos)
- [Установка бота](#установка-бота)
  - [Windows](#windows-1)
  - [macOS](#macos-1)
- [Настройка конфигурации](#настройка-конфигурации)
- [Запуск бота](#запуск-бота)
- [Функции бота](#функции-бота)
- [Безопасность](#безопасность)

## Требования
- Python 3.8 или выше
- Доступ к интернету
- Ethereum кошельки с приватными ключами
- Достаточно ETH для газа

## Установка Python

### Windows
1. Скачайте Python с официального сайта: https://www.python.org/downloads/
2. При установке обязательно отметьте галочку "Add Python to PATH"
3. Нажмите "Install Now"
4. Проверьте установку, открыв командную строку (cmd) и выполнив:
   ```bash
   python --version
   ```

### macOS
1. Установите Homebrew (если еще не установлен):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Установите Python через Homebrew:
   ```bash
   brew install python
   ```
3. Проверьте установку:
   ```bash
   python3 --version
   ```

## Установка бота

### Windows
1. Скачайте репозиторий:
   ```bash
   git clone https://github.com/letsgo2020/kernel-claim.git
   cd kernel-claim
   ```
2. Создайте виртуальное окружение:
   ```bash
   python -m venv venv
   ```
3. Активируйте виртуальное окружение:
   ```bash
   venv\Scripts\activate
   ```
4. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

### macOS
1. Скачайте репозиторий:
   ```bash
   git clone https://github.com/letsgo2020/kernel-claim.git
   cd kernel-claim
   ```
2. Создайте виртуальное окружение:
   ```bash
   python3 -m venv venv
   ```
3. Активируйте виртуальное окружение:
   ```bash
   source venv/bin/activate
   ```
4. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

## Настройка конфигурации

1. Создайте файл `.env` в корневой директории проекта:
   ```bash
   # Windows
   copy .env.example .env
   
   # macOS
   cp .env.example .env
   ```

2. Отредактируйте файл `.env`, указав следующие параметры:
   ```
   # RPC URL (выберите один из вариантов)
   ETH_RPC_URL=https://eth.llamarpc.com
   # или
   # ETH_RPC_URL=https://rpc.ankr.com/eth
   # или с API ключом
   # ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY
   
   # Адрес биржи для отправки токенов
   EXCHANGE_ADDRESS=your_exchange_address_here
   
   # Адрес токена KernelDAO
   TOKEN_ADDRESS=0x3f80b1c54ae920be41a77f8b902259d48cf24ccf
   
   # Адрес контракта дропа
   DROP_CONTRACT=0x68b55c20a2634b25a50a219b632f22854d810bf5
   
   # Лимиты газа
   CLAIM_GAS_LIMIT=200000
   TRANSFER_GAS_LIMIT=100000
   ```

3. Создайте файл `wallets.txt` в корневой директории:
   ```
   приватный_ключ1,адрес_биржи1
   приватный_ключ2,адрес_биржи2
   ```
   Каждая строка должна содержать приватный ключ кошелька и адрес биржи, куда будут отправлены токены, разделенные запятой.

## Запуск бота

1. Убедитесь, что виртуальное окружение активировано:
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS
   source venv/bin/activate
   ```

2. Запустите бота:
   ```bash
   python main.py
   ```

## Функции бота

1. **Проверка eligibility** - проверяет, может ли кошелек получить токены
2. **Проверка газа** - проверяет баланс ETH для клейма и отправки токенов
3. **Клейм токенов** - получает токены для eligible кошельков
4. **Проверка полученных токенов** - показывает баланс полученных токенов
5. **Отправка на биржу** - отправляет токены на указанный адрес биржи

## Безопасность

- Никогда не публикуйте файлы `.env` и `wallets.txt` в публичных репозиториях
- Храните приватные ключи в безопасном месте
- Регулярно проверяйте баланс ETH на кошельках
- Используйте надежные RPC провайдеры
- При использовании API ключей (Alchemy, Infura) храните их в безопасности

## Логирование

Логи сохраняются в директории `logs/`:
- `all_YYYY-MM-DD.log` - Общий лог со всеми событиями
- Отдельные логи для каждого модуля (eligibility, claim, sender и т.д.)

## Зависимости

См. файл `requirements.txt` 