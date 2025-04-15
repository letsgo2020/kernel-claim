#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from typing import Optional
from web3 import Web3
from web3.exceptions import ContractLogicError
from eth_account import Account
from dotenv import load_dotenv
import signal
import time
from prettytable import PrettyTable

# Загружаем переменные окружения
load_dotenv()

# Константы
TOKEN_ADDRESS = "0x3f80b1c54ae920be41a77f8b902259d48cf24ccf"
DEFAULT_GAS_LIMIT = 100000
DEFAULT_GAS_PRICE_GWEI = 30

# ABI для функции transfer из ERC20 контракта
TOKEN_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

def get_web3_provider() -> Web3:
    """
    Получает объект Web3 на основе RPC URL из .env файла или использует дефолтный
    
    Returns:
        Web3: Объект Web3 с подключенным провайдером
    """
    # Получаем RPC URL из переменных окружения или используем дефолтный
    rpc_url = os.getenv("ETH_RPC_URL", "https://eth.llamarpc.com")
    
    # Создаем Web3 объект с таймаутом
    web3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 30}))
    
    # Проверяем подключение
    if not web3.is_connected():
        raise ConnectionError(f"Не удалось подключиться к RPC провайдеру: {rpc_url}")
        
    return web3

def send_tokens_to_exchange(
    private_key: str,
    exchange_address: str,
    token_address: str = TOKEN_ADDRESS,
    amount: float = None
) -> Optional[str]:
    """
    Отправляет токены на биржевой адрес
    
    Args:
        private_key (str): Приватный ключ отправителя
        exchange_address (str): Адрес биржи для отправки
        token_address (str): Адрес токена для отправки
        amount (float): Количество токенов для отправки, None для отправки всего баланса
        
    Returns:
        Optional[str]: Хеш транзакции или None в случае ошибки
    """
    logger = logging.getLogger("sender")
    
    try:
        # Проверяем формат приватного ключа
        if private_key.startswith("0x"):
            private_key = private_key[2:]
        
        logger.info("Инициализация Web3-провайдера...")    
        web3 = get_web3_provider()
        
        # Создаем аккаунт из приватного ключа
        logger.info("Создание объекта аккаунта...")
        account_obj = Account.from_key(private_key)
        address = account_obj.address
        
        # Выводим информацию об отправке в виде таблицы
        table = PrettyTable()
        table.field_names = ["Отправитель", "Адрес биржи"]
        # Сокращаем адреса для лучшей читаемости
        sender_display = f"{address[:8]}...{address[-6:]}"
        exchange_display = f"{exchange_address[:8]}...{exchange_address[-6:]}"
        table.add_row([sender_display, exchange_display])
        print("\nИнформация об отправке токенов:")
        print(table)
        print()
        
        # Создаем объект контракта
        logger.info(f"Создание объекта контракта {token_address}...")
        token_contract = web3.eth.contract(
            address=web3.to_checksum_address(token_address),
            abi=TOKEN_ABI
        )
        
        # Получаем количество десятичных знаков токена
        logger.info("Получение decimals токена...")
        try:
            # Используем таймаут для вызова decimals()
            def timeout_handler(signum, frame):
                raise TimeoutError("Timeout in decimals call")
                
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(15)
            
            decimals = token_contract.functions.decimals().call()
            
            # Отключаем таймаут
            signal.alarm(0)
            
            logger.info(f"Decimals: {decimals}")
        except TimeoutError:
            logger.warning("Таймаут при получении decimals. Используем значение по умолчанию.")
            decimals = 18
        except Exception as e:
            logger.error(f"Ошибка при получении decimals: {str(e)}")
            decimals = 18  # Стандартное значение для большинства ERC20 токенов
            logger.info(f"Используем стандартное значение decimals: {decimals}")
        
        # Проверяем баланс токена
        logger.info(f"Проверка баланса токенов для {address}...")
        try:
            # Используем таймаут для вызова balanceOf()
            def timeout_handler(signum, frame):
                raise TimeoutError("Timeout in balanceOf call")
                
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(20)  # Даём больше времени на проверку баланса
            
            logger.info("Выполняется запрос balanceOf...")
            balance_raw = token_contract.functions.balanceOf(address).call()
            
            # Отключаем таймаут
            signal.alarm(0)
            
            balance = balance_raw / (10 ** decimals)
            logger.info(f"Баланс токенов: {balance}")
        except TimeoutError:
            logger.error("Таймаут при проверке баланса токенов!")
            return None
        except Exception as e:
            logger.error(f"Ошибка при проверке баланса: {str(e)}")
            return None
        
        if balance <= 0:
            logger.warning(f"Нет токенов для отправки с {address}")
            return None
            
        # Если сумма не указана, отправляем весь баланс
        if amount is None:
            amount = balance
            
        # Если пытаемся отправить больше чем есть, ограничиваем суммой баланса
        if amount > balance:
            logger.warning(f"Сумма для отправки больше баланса, отправляем весь баланс")
            amount = balance
            
        # Конвертируем сумму в wei
        amount_wei = int(amount * (10 ** decimals))
        logger.info(f"Сумма для отправки: {amount} токенов ({amount_wei} wei)")
        
        # Получаем nonce
        logger.info(f"Получение nonce для {address}...")
        nonce = web3.eth.get_transaction_count(address)
        logger.info(f"Nonce: {nonce}")
        
        # EIP-1559: Получаем базовый fee из последнего блока
        logger.info("Получение цены газа...")
        try:
            latest_block = web3.eth.get_block('latest')
            base_fee = latest_block['baseFeePerGas']
            logger.info(f"Базовая цена газа: {web3.from_wei(base_fee, 'gwei'):.2f} Gwei")
        except Exception as e:
            logger.error(f"Ошибка при получении цены газа: {str(e)}")
            # Устанавливаем значение по умолчанию
            base_fee = web3.to_wei(30, 'gwei')
            logger.info(f"Используем цену газа по умолчанию: 30 Gwei")
        
        # Устанавливаем минимальную приоритетную комиссию (почти нулевую)
        priority_fee = web3.to_wei(0.1, 'gwei')
        
        # Используем базовую цену газа как максимальную с запасом
        max_fee = int(base_fee * 1.5)
        
        # Пытаемся оценить gasLimit для транзакции
        gas_limit = DEFAULT_GAS_LIMIT
        logger.info("Оценка gasLimit для транзакции...")
        try:
            # Установим таймаут для estimate_gas, чтобы избежать зависания
            def timeout_handler(signum, frame):
                raise TimeoutError("Timeout in estimate_gas")
            
            # Устанавливаем таймаут в 15 секунд
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(15)
            
            gas_limit = token_contract.functions.transfer(
                web3.to_checksum_address(exchange_address),
                amount_wei
            ).estimate_gas({
                'from': address
            })
            
            # Отключаем таймаут
            signal.alarm(0)
            
            # Добавляем небольшой запас для надежности
            gas_limit = int(gas_limit * 1.2)
            logger.info(f"Рассчитанный gasLimit: {gas_limit}")
        except TimeoutError:
            logger.warning("Таймаут при оценке gasLimit. Используем значение по умолчанию.")
        except Exception as e:
            logger.warning(f"Не удалось оценить gasLimit: {str(e)}. Используем дефолтное значение.")
        
        # Подготавливаем транзакцию с EIP-1559 параметрами
        logger.info("Подготовка транзакции...")
        transfer_tx = token_contract.functions.transfer(
            web3.to_checksum_address(exchange_address),
            amount_wei
        ).build_transaction({
            'from': address,
            'gas': gas_limit,
            'maxFeePerGas': max_fee,
            'maxPriorityFeePerGas': priority_fee,
            'nonce': nonce,
            'chainId': web3.eth.chain_id
        })
        
        # Подписываем транзакцию
        logger.info("Подписание транзакции...")
        signed_tx = web3.eth.account.sign_transaction(transfer_tx, private_key)
        
        # Отправляем транзакцию
        logger.info("Отправка транзакции в сеть...")
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hash_hex = web3.to_hex(tx_hash)
        
        logger.info(f"Транзакция отправлена: {tx_hash_hex}")
        logger.info(f"Параметры газа: gasLimit={gas_limit}, " +
                   f"baseFee={web3.from_wei(base_fee, 'gwei'):.2f} gwei, " +
                   f"priorityFee={web3.from_wei(priority_fee, 'gwei'):.2f} gwei, " +
                   f"maxFee={web3.from_wei(max_fee, 'gwei'):.2f} gwei")
        
        # Ждем подтверждения
        logger.info(f"Ожидание подтверждения транзакции...")
        try:
            # Ждем не более 60 секунд
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if receipt['status'] == 1:
                logger.info(f"Транзакция успешно подтверждена: {tx_hash_hex}")
                return tx_hash_hex
            else:
                logger.error(f"Транзакция не удалась: {tx_hash_hex}")
                return None
        except Exception as e:
            logger.warning(f"Не удалось дождаться подтверждения транзакции: {str(e)}")
            logger.info("Возвращаем хеш транзакции, но её статус неизвестен")
            return tx_hash_hex
            
    except ContractLogicError as e:
        logger.error(f"Ошибка в контракте: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при отправке токенов: {str(e)}")
        return None

if __name__ == "__main__":
    # Настраиваем логирование
    logging.basicConfig(level=logging.INFO,
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("Этот скрипт нельзя запустить напрямую. Пожалуйста, используйте main.py") 