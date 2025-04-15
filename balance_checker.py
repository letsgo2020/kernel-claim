#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from typing import Optional, Dict, Tuple, Any
from web3 import Web3
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Константы
TOKEN_ADDRESS = "0x3f80b1c54ae920be41a77f8b902259d48cf24ccf"
DROP_CONTRACT_ADDRESS = "0x68b55c20a2634b25a50a219b632f22854d810bf5"
DEFAULT_GAS_LIMIT_CLAIM = 200000
DEFAULT_GAS_LIMIT_TRANSFER = 100000

# ABI только для функции balanceOf из ERC20 контракта
TOKEN_ABI = [
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
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
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
    
    # Создаем Web3 объект
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Проверяем подключение
    if not web3.is_connected():
        raise ConnectionError(f"Не удалось подключиться к RPC провайдеру: {rpc_url}")
        
    return web3

def get_current_gas_prices() -> Dict[str, Any]:
    """
    Получает текущую цену газа и EIP-1559 параметры
    
    Returns:
        Dict[str, Any]: Словарь с ценами газа и необходимыми параметрами
    """
    logger = logging.getLogger("balance_checker")
    
    try:
        web3 = get_web3_provider()
        
        # Получаем последний блок для базовой цены газа
        latest_block = web3.eth.get_block('latest')
        base_fee = latest_block['baseFeePerGas']
        
        # Устанавливаем минимальную приоритетную комиссию (почти нулевую)
        priority_fee = web3.to_wei(0.01, 'gwei')
        
        # Используем базовую цену газа для максимальной цены
        max_fee = base_fee
        
        # Преобразуем все величины в gwei для удобства
        gas_data = {
            'base_fee_gwei': web3.from_wei(base_fee, 'gwei'),
            'priority_fee_gwei': web3.from_wei(priority_fee, 'gwei'),
            'max_fee_gwei': web3.from_wei(max_fee, 'gwei'),
            'base_fee_wei': base_fee,
            'priority_fee_wei': priority_fee,
            'max_fee_wei': max_fee,
        }
        
        logger.debug(f"Текущие цены газа: base_fee={gas_data['base_fee_gwei']:.2f} gwei (используется как maxFee)")
        
        return gas_data
        
    except Exception as e:
        logger.error(f"Ошибка при получении цен газа: {str(e)}")
        # Возвращаем дефолтные значения в случае ошибки
        return {
            'base_fee_gwei': 0.4,
            'priority_fee_gwei': 0.01,
            'max_fee_gwei': 0.4,
            'base_fee_wei': web3.to_wei(0.4, 'gwei'),
            'priority_fee_wei': web3.to_wei(0.01, 'gwei'),
            'max_fee_wei': web3.to_wei(0.4, 'gwei'),
        }

def calculate_tx_cost(gas_limit: int, gas_data: Dict[str, Any]) -> float:
    """
    Рассчитывает примерную стоимость транзакции в ETH
    
    Args:
        gas_limit (int): Предполагаемый лимит газа
        gas_data (Dict[str, Any]): Данные о ценах газа от get_current_gas_prices()
        
    Returns:
        float: Стоимость транзакции в ETH
    """
    max_fee_wei = gas_data['max_fee_wei']
    cost_wei = gas_limit * max_fee_wei
    
    web3 = get_web3_provider()
    cost_eth = web3.from_wei(cost_wei, 'ether')
    
    return float(cost_eth)

def check_gas_balance(address: str) -> float:
    """
    Проверяет баланс газа (ETH) для указанного адреса
    
    Args:
        address (str): Адрес для проверки
        
    Returns:
        float: Баланс в ETH
    """
    logger = logging.getLogger("balance_checker")
    
    try:
        web3 = get_web3_provider()
        
        # Приводим адрес к правильному формату
        address = web3.to_checksum_address(address)
        
        # Получаем баланс ETH в wei
        balance_wei = web3.eth.get_balance(address)
        
        # Конвертируем в ETH
        balance_eth = web3.from_wei(balance_wei, "ether")
        
        logger.debug(f"Баланс газа для {address}: {balance_eth} ETH")
        return float(balance_eth)
        
    except Exception as e:
        logger.error(f"Ошибка при проверке баланса газа для {address}: {str(e)}")
        raise

def check_token_balance(address: str, token_address: str = TOKEN_ADDRESS) -> float:
    """
    Проверяет баланс токена для указанного адреса
    
    Args:
        address (str): Адрес для проверки
        token_address (str): Адрес токена для проверки
        
    Returns:
        float: Баланс токена с учетом десятичных знаков
    """
    logger = logging.getLogger("balance_checker")
    
    try:
        web3 = get_web3_provider()
        
        # Приводим адреса к правильному формату
        address = web3.to_checksum_address(address)
        token_address = web3.to_checksum_address(token_address)
        
        # Создаем объект контракта
        token_contract = web3.eth.contract(address=token_address, abi=TOKEN_ABI)
        
        # Получаем количество десятичных знаков токена
        decimals = token_contract.functions.decimals().call()
        
        # Получаем баланс токена
        balance_raw = token_contract.functions.balanceOf(address).call()
        
        # Конвертируем с учетом десятичных знаков
        balance = balance_raw / (10 ** decimals)
        
        # Получаем символ токена для логирования
        symbol = token_contract.functions.symbol().call()
        
        logger.debug(f"Баланс {symbol} для {address}: {balance}")
        return float(balance)
        
    except Exception as e:
        logger.error(f"Ошибка при проверке баланса токена для {address}: {str(e)}")
        raise

def check_gas_requirements(address: str) -> Dict[str, Any]:
    """
    Проверяет требования к газу и достаточность средств для различных операций
    
    Args:
        address (str): Адрес для проверки
        
    Returns:
        Dict[str, Any]: Словарь с информацией о балансе и требованиях
    """
    gas_balance = check_gas_balance(address)
    gas_data = get_current_gas_prices()
    
    # Рассчитываем стоимость транзакций
    claim_cost = calculate_tx_cost(DEFAULT_GAS_LIMIT_CLAIM, gas_data)
    transfer_cost = calculate_tx_cost(DEFAULT_GAS_LIMIT_TRANSFER, gas_data)
    
    # Определяем, достаточно ли средств
    has_enough_for_claim = gas_balance >= claim_cost
    has_enough_for_transfer = gas_balance >= transfer_cost
    has_enough_for_both = gas_balance >= (claim_cost + transfer_cost)
    
    return {
        'address': address,
        'gas_balance': gas_balance,
        'current_gas_price': gas_data['max_fee_gwei'],
        'claim_cost': claim_cost,
        'transfer_cost': transfer_cost,
        'has_enough_for_claim': has_enough_for_claim,
        'has_enough_for_transfer': has_enough_for_transfer,
        'has_enough_for_both': has_enough_for_both
    }

def has_enough_gas_for_claim(address: str) -> bool:
    """
    Проверяет, достаточно ли газа на адресе для выполнения клейма
    
    Args:
        address (str): Адрес для проверки
        
    Returns:
        bool: True если газа достаточно, иначе False
    """
    try:
        req = check_gas_requirements(address)
        return req['has_enough_for_claim']
    except Exception:
        return False

def has_enough_gas_for_transfer(address: str) -> bool:
    """
    Проверяет, достаточно ли газа на адресе для отправки токенов
    
    Args:
        address (str): Адрес для проверки
        
    Returns:
        bool: True если газа достаточно, иначе False
    """
    try:
        req = check_gas_requirements(address)
        return req['has_enough_for_transfer']
    except Exception:
        return False

if __name__ == "__main__":
    # Настраиваем логирование для тестирования
    logging.basicConfig(level=logging.INFO,
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Пример использования
    test_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    
    try:
        gas_reqs = check_gas_requirements(test_address)
        print(f"Баланс газа для {test_address}: {gas_reqs['gas_balance']:.6f} ETH")
        print(f"Текущая цена газа: {gas_reqs['current_gas_price']:.2f} gwei")
        print(f"Стоимость клейма: ~{gas_reqs['claim_cost']:.6f} ETH")
        print(f"Стоимость перевода: ~{gas_reqs['transfer_cost']:.6f} ETH")
        print(f"Достаточно для клейма: {'✅' if gas_reqs['has_enough_for_claim'] else '❌'}")
        print(f"Достаточно для отправки: {'✅' if gas_reqs['has_enough_for_transfer'] else '❌'}")
        print(f"Достаточно для обеих операций: {'✅' if gas_reqs['has_enough_for_both'] else '❌'}")
        
        token_balance = check_token_balance(test_address)
        print(f"Баланс KERNEL для {test_address}: {token_balance:.4f} KERNEL")
    except Exception as e:
        print(f"Ошибка: {str(e)}") 