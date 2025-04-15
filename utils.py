#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import datetime
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

def setup_logging(log_dir: str = "logs") -> None:
    """
    Настраивает логирование с сохранением в файлы по категориям
    
    Args:
        log_dir (str): Директория для сохранения логов
    """
    # Создаем директорию для логов, если её нет
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # Текущая дата для формирования имен файлов
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Список категорий логов и соответствующих файлов
    log_categories = [
        ("main", f"{log_dir}/main_{current_date}.log"),
        ("wallet_loader", f"{log_dir}/wallet_loader_{current_date}.log"),
        ("signer", f"{log_dir}/signer_{current_date}.log"),
        ("api_checker", f"{log_dir}/api_checker_{current_date}.log"),
        ("eligibility", f"{log_dir}/eligibility_{current_date}.log"),
        ("balance_checker", f"{log_dir}/balance_checker_{current_date}.log"),
        ("gas_balance", f"{log_dir}/gas_balance_{current_date}.log"),
        ("token_balance", f"{log_dir}/token_balance_{current_date}.log"),
        ("claimer", f"{log_dir}/claimer_{current_date}.log"),
        ("claim", f"{log_dir}/claim_{current_date}.log"),
        ("sender", f"{log_dir}/sender_{current_date}.log"),
        ("send_tokens", f"{log_dir}/send_tokens_{current_date}.log"),
        ("tx_replacer", f"{log_dir}/tx_replacer_{current_date}.log"),
    ]
    
    # Базовый формат логов
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Настраиваем основной логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Добавляем консольный обработчик для всех логов уровня INFO и выше
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Добавляем файловые обработчики для каждой категории
    for category, log_file in log_categories:
        # Создаем файловый обработчик
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Создаем фильтр для категории
        class CategoryFilter(logging.Filter):
            def filter(self, record):
                return record.name == category
                
        file_handler.addFilter(CategoryFilter())
        
        # Добавляем обработчик к корневому логгеру
        root_logger.addHandler(file_handler)
        
    # Также добавляем общий файл лога для всех сообщений
    all_file_handler = logging.FileHandler(f"{log_dir}/all_{current_date}.log")
    all_file_handler.setLevel(logging.DEBUG)
    all_file_handler.setFormatter(formatter)
    root_logger.addHandler(all_file_handler)
    
    logging.info("Логирование настроено")

def parallel_process(tasks: List[Dict[str, Any]], worker_function, max_workers: int = 10) -> List[Dict[str, Any]]:
    """
    Выполняет задачи параллельно с использованием ThreadPoolExecutor
    
    Args:
        tasks (List[Dict[str, Any]]): Список задач для выполнения
        worker_function: Функция, которая будет выполнять задачи
        max_workers (int): Максимальное количество потоков
        
    Returns:
        List[Dict[str, Any]]: Список результатов выполнения задач
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Создаем словарь {future: task_index}
        future_to_index = {executor.submit(worker_function, task): i for i, task in enumerate(tasks)}
        
        # Обрабатываем результаты по мере их завершения
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                result = future.result()
                results.append({
                    "task": tasks[index],
                    "result": result,
                    "success": True,
                    "error": None
                })
            except Exception as e:
                results.append({
                    "task": tasks[index],
                    "result": None,
                    "success": False,
                    "error": str(e)
                })
                
    # Сортируем результаты в том же порядке, что и исходные задачи
    results.sort(key=lambda x: tasks.index(x["task"]))
    
    return results

def create_env_file() -> bool:
    """
    Создает файл .env если его не существует
    
    Returns:
        bool: True если файл был создан, False если уже существует
    """
    if os.path.exists(".env"):
        return False
        
    try:
        with open(".env", 'w') as file:
            file.write("# Ethereum RPC URL\n")
            file.write("ETH_RPC_URL=https://eth.llamarpc.com\n")
            file.write("\n# Не изменять эти настройки, если не знаете что делаете\n")
            file.write("CLAIM_GAS_LIMIT=200000\n")
            file.write("TRANSFER_GAS_LIMIT=100000\n")
        return True
    except Exception:
        return False

if __name__ == "__main__":
    # Если запускается напрямую, создаем файл .env
    if create_env_file():
        print(f"Создан файл .env")
    else:
        print(f"Файл .env уже существует") 