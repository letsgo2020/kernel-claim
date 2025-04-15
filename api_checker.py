#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
import json
from typing import Dict, Any, Optional, List
import time

# API URL для получения доказательства
API_URL = "https://common.kerneldao.com/merkle/proofs/kernel_eth"

def check_eligibility(address: str, signature: str) -> Optional[Dict[str, Any]]:
    """
    Проверяет eligibility адреса для получения дропа, делая запрос к API KernelDAO
    
    Args:
        address (str): Адрес, для которого проверяется eligibility
        signature (str): Подпись сообщения "Sign message to view your Season 1 points"
        
    Returns:
        Optional[Dict[str, Any]]: Словарь с данными eligibility (balance, proof)
                                 или None если адрес не eligible или произошла ошибка
    """
    logger = logging.getLogger("api_checker")
    
    try:
        # Формируем URL с параметрами
        url = f"{API_URL}?address={address}&signature={signature}"
        
        # Устанавливаем заголовки
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 KernelDAO-Bot/1.0"
        }
        
        # Делаем запрос к API
        logger.info(f"Отправка запроса к API для адреса {address}")
        response = requests.get(url, headers=headers, timeout=30)
        
        # Проверяем ответ
        if response.status_code == 200:
            response_data = response.json()
            
            # Проверяем наличие data в ответе
            if "data" not in response_data:
                logger.warning(f"API вернул ответ без поля 'data' для {address}: {response_data}")
                return None
                
            data = response_data["data"]
            
            # Получаем proof и balance
            proof = data.get("proof", [])
            balance = data.get("balance", "0")
            balance_tokens = int(balance) / 1e18
            
            # Проверяем критерии eligibility: непустой proof и положительный balance
            if proof and int(balance) > 0:
                logger.info(f"✅ Адрес {address} eligible для получения {balance_tokens:.4f} KERNEL")
                return data
            else:
                logger.info(f"❌ Адрес {address} не eligible. Balance: {balance_tokens:.4f} KERNEL, Proof: {'Есть' if proof else 'Отсутствует'}")
                return None
                
        elif response.status_code == 404:
            # 404 обычно означает что адрес не eligible
            logger.info(f"❌ Адрес {address} не eligible для получения дропа (404)")
            return None
            
        else:
            # Другие ошибки
            logger.error(f"Ошибка API: {response.status_code} - {response.text}")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Ошибка сети при запросе к API: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования ответа API: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при проверке eligibility: {str(e)}")
        return None

def retry_check_eligibility(address: str, signature: str, max_retries: int = 3, delay: int = 2) -> Optional[Dict[str, Any]]:
    """
    Проверяет eligibility с повторными попытками в случае ошибки сети
    
    Args:
        address (str): Адрес кошелька
        signature (str): Подпись сообщения
        max_retries (int): Максимальное количество попыток
        delay (int): Задержка между попытками в секундах
        
    Returns:
        Optional[Dict[str, Any]]: Данные eligibility (balance, proof) или None
    """
    logger = logging.getLogger("api_checker")
    
    for attempt in range(max_retries):
        try:
            result = check_eligibility(address, signature)
            if result is not None:
                return result
                
            # Если получили None из-за 404 (не eligible), не повторяем
            elif attempt == 0:
                return None
                
        except Exception as e:
            logger.warning(f"Попытка {attempt+1}/{max_retries} не удалась: {str(e)}")
            
        # Ждем перед следующей попыткой
        if attempt < max_retries - 1:
            time.sleep(delay)
            
    return None

if __name__ == "__main__":
    # Настраиваем базовое логирование для тестирования
    logging.basicConfig(level=logging.INFO,
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Пример использования (нужно заменить на реальный адрес и подпись)
    test_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    test_signature = "0x..."  # Подставьте реальную подпись
    
    result = check_eligibility(test_address, test_signature)
    if result:
        print(f"✅ Адрес {test_address} eligible!")
        print(f"Balance: {int(result.get('balance', '0'))/10**18:.4f} KERNEL")
        print(f"Proof: {result.get('proof', [])}")
    else:
        print(f"❌ Адрес {test_address} не eligible или произошла ошибка") 