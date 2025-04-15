#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import time
from typing import List, Dict, Any, Optional
from web3 import Web3
from web3.exceptions import ContractLogicError
from eth_account import Account
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Константы
DROP_CONTRACT_ADDRESS = "0x68b55c20a2634b25a50a219b632f22854d810bf5"
DEFAULT_GAS_LIMIT = 200000
DEFAULT_GAS_PRICE_GWEI = 30

# ABI контракта - обновленная версия на основе имплементации
DROP_CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType":"uint256","name":"index","type":"uint256"},
            {"internalType":"address","name":"account","type":"address"},
            {"internalType":"uint256","name":"cumulativeAmount","type":"uint256"},
            {"internalType":"bytes32[]","name":"merkleProof","type":"bytes32[]"}
        ],
        "name": "claim",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType":"uint256","name":"index","type":"uint256"},
            {"internalType":"address","name":"account","type":"address"}
        ],
        "name": "isClaimed",
        "outputs": [{"internalType":"bool","name":"","type":"bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType":"address","name":"user","type":"address"}
        ],
        "name": "userClaims",
        "outputs": [
            {"internalType":"uint256","name":"lastClaimedIndex","type":"uint256"},
            {"internalType":"uint256","name":"cumulativeAmount","type":"uint256"}
        ],
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

def is_already_claimed(address: str, index: int = 8) -> bool:
    """
    Проверяет, был ли уже выполнен клейм для указанного адреса
    
    Args:
        address (str): Адрес для проверки
        index (int): Индекс в merkle tree (всегда 8 для KernelDAO)
        
    Returns:
        bool: True если адрес уже клеймил дроп, иначе False
    """
    logger = logging.getLogger("claimer")
    
    try:
        web3 = get_web3_provider()
        
        # Создаем объект контракта
        contract = web3.eth.contract(
            address=web3.to_checksum_address(DROP_CONTRACT_ADDRESS),
            abi=DROP_CONTRACT_ABI
        )
        
        # Проверяем статус клейма
        is_claimed = contract.functions.isClaimed(
            index,
            web3.to_checksum_address(address)
        ).call()
        
        return is_claimed
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса клейма для {address}: {str(e)}")
        return False

def claim_tokens(
    private_key: str,
    index: int = 8,
    account: str = None,
    amount: str = None,
    proof: List[str] = None,
    use_direct_api: bool = False  # Оставлен для совместимости
) -> Optional[str]:
    """
    Вызывает функцию claim() в контракте дропа
    
    Args:
        private_key (str): Приватный ключ для подписи транзакции
        index (int): Индекс в merkle tree (всегда 8 для KernelDAO)
        account (str): Адрес получателя
        amount (str): Сумма в wei (строка)
        proof (List[str]): Merkle proof в виде списка bytes32
        use_direct_api (bool): Параметр оставлен для совместимости
        
    Returns:
        Optional[str]: Хеш транзакции или None в случае ошибки
    """
    logger = logging.getLogger("claimer")
    
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
        
        # Всегда используем index=8 для KernelDAO
        index = 8
        logger.info(f"Используем фиксированный index={index} для KernelDAO")
        
        # Преобразуем amount из строки в int, если это необходимо
        amount_int = int(amount) if isinstance(amount, str) else amount
        
        # Проверяем, был ли уже выполнен клейм для этого адреса
        logger.info(f"Проверка, был ли уже выполнен клейм для {address}...")
        if is_already_claimed(address, index):
            logger.info(f"Адрес {address} уже клеймил дроп (index={index}), пропуск")
            return None
            
        # Создаем объект контракта
        logger.info("Создание объекта контракта...")
        contract = web3.eth.contract(
            address=web3.to_checksum_address(DROP_CONTRACT_ADDRESS),
            abi=DROP_CONTRACT_ABI
        )
        
        # Получаем nonce
        logger.info(f"Получение nonce для {address}...")
        nonce = web3.eth.get_transaction_count(address)
        logger.info(f"Получен nonce: {nonce}")
        
        # EIP-1559: Получаем базовый fee из последнего блока
        logger.info("Получение цены газа из последнего блока...")
        try:
            latest_block = web3.eth.get_block('latest')
            base_fee = latest_block['baseFeePerGas']
            logger.info(f"Базовая цена газа: {web3.from_wei(base_fee, 'gwei'):.2f} Gwei")
        except Exception as e:
            logger.error(f"Ошибка при получении цены газа: {str(e)}")
            # Устанавливаем значение по умолчанию
            base_fee = web3.to_wei(25, 'gwei')
            logger.info(f"Используем цену газа по умолчанию: 25 Gwei")
        
        # Устанавливаем минимальную приоритетную комиссию
        priority_fee = web3.to_wei(0.1, 'gwei')
        
        # Используем базовую цену газа как максимальную с небольшим запасом
        max_fee = int(base_fee * 1.2)
        
        # Пытаемся оценить gasLimit для транзакции
        gas_limit = DEFAULT_GAS_LIMIT  # Значение по умолчанию
        logger.info("Оценка gasLimit для транзакции...")
        try:
            # Установим таймаут для estimate_gas, чтобы избежать зависания
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Timeout in estimate_gas")
            
            # Устанавливаем таймаут в 15 секунд
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(15)
            
            gas_limit = contract.functions.claim(
                index,
                web3.to_checksum_address(account),
                amount_int,
                proof
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
        claim_tx = contract.functions.claim(
            index,
            web3.to_checksum_address(account),
            amount_int,
            proof
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
        signed_tx = web3.eth.account.sign_transaction(claim_tx, private_key)
        
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
        logger.error(f"Ошибка при клейме токенов: {str(e)}")
        return None

if __name__ == "__main__":
    # Настраиваем логирование
    logging.basicConfig(level=logging.INFO,
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("Этот скрипт нельзя запустить напрямую. Пожалуйста, используйте main.py") 