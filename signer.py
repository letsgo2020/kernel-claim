#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
from typing import Optional

def generate_signature(private_key: str, message: str) -> str:
    """
    Генерирует подпись сообщения с использованием приватного ключа
    
    Args:
        private_key (str): Приватный ключ (с или без префикса 0x)
        message (str): Сообщение для подписи
        
    Returns:
        str: Подпись сообщения в формате hex с префиксом 0x
    """
    logger = logging.getLogger("signer")
    
    try:
        # Убеждаемся, что приватный ключ в правильном формате
        if private_key.startswith("0x"):
            private_key = private_key[2:]
            
        # Создаем объект подписи
        encoded_message = encode_defunct(text=message)
        
        # Подписываем сообщение
        signed_message = Account.sign_message(encoded_message, private_key)
        
        # Получаем подпись в формате hex
        signature = Web3.to_hex(signed_message.signature)
        
        logger.debug(f"Сообщение успешно подписано: {message}")
        return signature
        
    except Exception as e:
        logger.error(f"Ошибка при подписании сообщения: {str(e)}")
        raise

def verify_signature(address: str, message: str, signature: str) -> bool:
    """
    Проверяет подпись сообщения
    
    Args:
        address (str): Адрес кошелька, который подписал сообщение
        message (str): Исходное сообщение
        signature (str): Подпись в формате hex с префиксом 0x
        
    Returns:
        bool: True если подпись верна, иначе False
    """
    try:
        # Создаем объект сообщения
        encoded_message = encode_defunct(text=message)
        
        # Восстанавливаем адрес из подписи
        recovered_address = Account.recover_message(encoded_message, signature=signature)
        
        # Сравниваем адреса (приводим к нижнему регистру для нормализации)
        return recovered_address.lower() == address.lower()
        
    except Exception:
        return False

if __name__ == "__main__":
    # Пример использования
    from eth_account import Account
    import secrets
    
    # Генерируем тестовый приватный ключ
    test_key = secrets.token_hex(32)
    account = Account.from_key(test_key)
    test_address = account.address
    
    # Сообщение для подписи
    test_message = "Sign message to view your Season 1 points"
    
    # Подписываем
    signature = generate_signature(test_key, test_message)
    print(f"Адрес: {test_address}")
    print(f"Сообщение: {test_message}")
    print(f"Подпись: {signature}")
    
    # Проверяем
    is_valid = verify_signature(test_address, test_message, signature)
    print(f"Подпись верна: {is_valid}") 