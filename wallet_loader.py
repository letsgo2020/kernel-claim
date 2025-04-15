#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from typing import List, Dict, Optional
from eth_account import Account
from dotenv import load_dotenv
from web3 import Web3

# Загружаем переменные окружения
load_dotenv()

def load_wallets(file_path: str = "wallets.txt") -> List[Dict[str, str]]:
    """
    Загружает приватные ключи из файла и возвращает список кошельков
    
    Args:
        file_path (str): Путь к файлу с приватными ключами
        
    Returns:
        List[Dict[str, str]]: Список словарей с данными кошельков 
                             (приватный ключ и соответствующий адрес)
    """
    logger = logging.getLogger("wallet_loader")
    
    wallets = []
    try:
        if not os.path.exists(file_path):
            logger.error(f"Файл с приватными ключами не найден: {file_path}")
            return []
            
        with open(file_path, "r") as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            try:
                # Разделяем строку на приватный ключ и адрес биржи
                parts = line.split(",")
                private_key = parts[0].strip()
                
                # Удаляем префикс 0x, если он есть
                if private_key.startswith("0x"):
                    private_key = private_key[2:]
                
                # Создаем аккаунт из приватного ключа, чтобы получить адрес
                account = Account.from_key(private_key)
                address = account.address
                
                # Проверяем наличие адреса биржи во второй части
                exchange_address = None
                if len(parts) > 1 and parts[1].strip() and parts[1].strip().lower() != "нету":
                    exchange_address = parts[1].strip()
                    # Проверяем формат адреса биржи
                    if exchange_address.startswith("0x") and Web3.is_address(exchange_address):
                        exchange_address = Web3.to_checksum_address(exchange_address)
                    else:
                        logger.warning(f"Некорректный адрес биржи в строке {i+1}: {exchange_address}")
                
                # Добавляем кошелек в список
                wallet = {
                    "private_key": private_key,
                    "address": address,
                    "exchange_address": exchange_address
                }
                wallets.append(wallet)
                
            except Exception as e:
                logger.error(f"Ошибка при обработке строки {i+1}: {str(e)}")
                
        logger.info(f"Успешно загружено {len(wallets)} кошельков")
        return wallets
    
    except Exception as e:
        logger.error(f"Ошибка при загрузке кошельков: {str(e)}")
        return []

def create_sample_wallets_file(file_path: str = "wallets.txt") -> bool:
    """
    Создает шаблон файла с примерами приватных ключей и адресов бирж
    
    Args:
        file_path (str): Путь к создаваемому файлу
        
    Returns:
        bool: True, если файл создан успешно, False, если файл уже существует
    """
    if os.path.exists(file_path):
        return False
        
    with open(file_path, "w") as f:
        f.write("# Формат файла: ПРИВАТНЫЙ_КЛЮЧ,АДРЕС_БИРЖИ\n")
        f.write("# Приватные ключи могут быть с префиксом 0x или без него\n")
        f.write("# Пример:\n")
        f.write("# 0x123abc456def789abc123def456abc789def123abc456def789abc123def456a,0x742d35Cc6634C0532925a3b844Bc454e4438f44e\n")
        f.write("# Заполните этот файл вашими приватными ключами и адресами бирж\n\n")
    
    return True

if __name__ == "__main__":
    # Настраиваем базовое логирование для тестирования
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Если запускается напрямую, создаем шаблон файла
    if create_sample_wallets_file():
        print(f"Создан шаблон файла wallets.txt")
    else:
        print(f"Файл wallets.txt уже существует")
    
    # Загружаем кошельки
    wallets = load_wallets()
    for i, wallet in enumerate(wallets):
        print(f"Wallet {i+1}: {wallet['address']}" + 
              (f" -> Exchange: {wallet['exchange_address']}" if wallet.get('exchange_address') else " (без адреса биржи)")) 