#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
from typing import List, Dict, Any, Tuple
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn, SpinnerColumn, TimeElapsedColumn
from web3 import Web3
from rich.panel import Panel
from rich.text import Text
from eth_account import Account
from rich.layout import Layout
from rich.spinner import Spinner
from rich import box

from wallet_loader import load_wallets
from signer import generate_signature
from api_checker import check_eligibility
from balance_checker import check_gas_balance, check_token_balance, check_gas_requirements
from claimer import claim_tokens, is_already_claimed
from sender import send_tokens_to_exchange
from utils import setup_logging

# Константы
TOKEN_ADDRESS = "0x3f80b1c54ae920be41a77f8b902259d48cf24ccf"
DROP_CONTRACT = "0x68b55c20a2634b25a50a219b632f22854d810bf5"
API_URL = "https://common.kerneldao.com/merkle/proofs/kernel_eth"

console = Console()

def display_menu():
    console.print("[bold green]KernelDAO Airdrop Bot[/bold green]")
    console.print("=" * 50)
    console.print("[1] Проверить eligibility")
    console.print("[2] Проверить баланс газа")
    console.print("[3] Клеймить дроп")
    console.print("[4] Проверить полученные токены")
    console.print("[5] Отправить токены на биржу")
    console.print("[0] Выход")
    console.print("=" * 50)
    
    return console.input("[bold yellow]Выберите действие: [/bold yellow]")

def main():
    # Создаем директорию для логов, если её нет
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # Настройка логирования
    setup_logging()
    logger = logging.getLogger("main")
    
    logger.info("KernelDAO Airdrop Bot запущен")
    
    try:
        # Загружаем кошельки
        wallets = load_wallets()
        if not wallets:
            console.print("[bold red]Ошибка: Не удалось загрузить кошельки из wallets.txt[/bold red]")
            return
            
        # Показываем краткую информацию о загруженных кошельках
        wallets_with_exchange = sum(1 for w in wallets if "exchange_address" in w and w["exchange_address"])
        console.print(f"[bold green]✓ Успешно загружено {len(wallets)} кошельков[/bold green]")
        console.print(f"[bold blue]ℹ {wallets_with_exchange} кошельков имеют адрес биржи[/bold blue]")
        
        while True:
            choice = display_menu()
            
            if choice == "0":
                logger.info("Завершение работы")
                console.print("[bold green]Работа завершена[/bold green]")
                break
                
            elif choice == "1":
                check_eligibility_for_all(wallets)
                
            elif choice == "2":
                check_gas_for_all(wallets)
                
            elif choice == "3":
                claim_for_all(wallets)
                
            elif choice == "4":
                check_tokens_for_all(wallets)
                
            elif choice == "5":
                send_tokens_for_all(wallets)
                
            else:
                console.print("[bold red]Неверный выбор. Попробуйте снова.[/bold red]")
                
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
        console.print("\n[bold yellow]Бот остановлен пользователем[/bold yellow]")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}")
        console.print(f"[bold red]Неожиданная ошибка: {str(e)}[/bold red]")

def check_eligibility_for_all(wallets: List[Dict[str, str]]):
    logger = logging.getLogger("eligibility")
    logger.info("Проверка eligibility запущена")
    
    console.print("[bold cyan]Проверка eligibility для всех кошельков...[/bold cyan]")
    
    table = Table(title="Результаты проверки eligibility")
    table.add_column("Адрес", style="cyan")
    table.add_column("Статус", style="green")
    table.add_column("Balance (KERNEL)", style="yellow")
    
    confirmation = console.input("[bold yellow]Продолжить проверку? (y/n): [/bold yellow]")
    if confirmation.lower() != "y":
        return
    
    results = []
    not_eligible_addresses = []
    
    # Создаем прогресс-бар
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[bold]{task.completed}/{task.total}"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("[cyan]Проверка eligibility...", total=len(wallets))
        
        for wallet in wallets:
            address = wallet["address"]
            private_key = wallet["private_key"]
            
            progress.update(task, description=f"[cyan]Проверка адреса {address[:8]}...")
            
            try:
                signature = generate_signature(private_key, "Sign message to view your Season 1 points")
                result = check_eligibility(address, signature)
                
                if result and "balance" in result:
                    balance_in_kernel = int(result["balance"]) / 10**18
                    results.append((address, "✅ Eligible", f"{balance_in_kernel:.4f}"))
                    logger.info(f"Адрес {address} eligible для {balance_in_kernel:.4f} KERNEL")
                else:
                    results.append((address, "❌ Not eligible", "0"))
                    logger.info(f"Адрес {address} не eligible для дропа")
                    not_eligible_addresses.append(wallet)
                    
            except Exception as e:
                results.append((address, f"❌ Ошибка: {str(e)}", "-"))
                logger.error(f"Ошибка при проверке {address}: {str(e)}")
            
            progress.advance(task)
    
    # Заполняем таблицу результатами
    for address, status, balance in results:
        table.add_row(address, status, balance)
    
    console.print(table)
    
    # Если есть неподходящие кошельки, спрашиваем о их удалении
    if not_eligible_addresses:
        console.print(f"\n[bold yellow]Найдено {len(not_eligible_addresses)} кошельков, не имеющих права на клейм.[/bold yellow]")
        remove_confirmation = console.input("[bold red]Удалить эти кошельки из файла wallets.txt? (y/n): [/bold red]")
        
        if remove_confirmation.lower() == "y":
            # Загружаем все кошельки из файла
            wallets_to_keep = []
            not_eligible_addrs = [w["address"].lower() for w in not_eligible_addresses]
            
            with open("wallets.txt", "r") as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split(",")
                if len(parts) >= 1:
                    private_key = parts[0].strip()
                    if private_key.startswith("0x"):
                        private_key = private_key[2:]
                    
                    account = Account.from_key(private_key)
                    address = account.address.lower()
                    
                    if address not in not_eligible_addrs:
                        wallets_to_keep.append(line)
            
            # Сохраняем обновленный список кошельков
            with open("wallets.txt", "w") as f:
                for wallet_line in wallets_to_keep:
                    f.write(f"{wallet_line}\n")
            
            console.print(f"[bold green]Удалено {len(not_eligible_addresses)} неподходящих кошельков. В файле wallets.txt осталось {len(wallets_to_keep)} кошельков.[/bold green]")
            logger.info(f"Удалено {len(not_eligible_addresses)} неподходящих кошельков из файла wallets.txt")

def check_gas_for_all(wallets: List[Dict[str, str]]):
    logger = logging.getLogger("gas_balance")
    logger.info("Проверка баланса газа запущена")
    
    console.print("[bold cyan]Проверка баланса газа для всех кошельков...[/bold cyan]")
    
    # Создаем простую таблицу без ограничения ширины
    table = Table(
        title="Балансы газа и возможности",
        show_lines=True,
        box=box.ROUNDED
    )
    
    # Настраиваем колонки без ограничения ширины для адреса
    table.add_column("Адрес", style="cyan", no_wrap=True)  # Убираем ограничение ширины
    table.add_column("Баланс ETH", style="yellow", justify="right")
    table.add_column("Цена газа", style="magenta", justify="right")
    table.add_column("Стоимость клейма", style="yellow", justify="right")
    table.add_column("Стоимость перевода", style="yellow", justify="right")
    table.add_column("Клейм", style="green", justify="center")
    table.add_column("Перевод", style="green", justify="center")
    table.add_column("Оба", style="green", justify="center")
    
    confirmation = console.input("[bold yellow]Продолжить проверку? (y/n): [/bold yellow]")
    if confirmation.lower() != "y":
        return
    
    results = []
    
    # Создаем прогресс-бар
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[bold]{task.completed}/{task.total}"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("[cyan]Проверка баланса газа...", total=len(wallets))
        
        for wallet in wallets:
            address = wallet["address"]
            
            progress.update(task, description=f"[cyan]Проверка адреса {address}...")
            
            try:
                gas_reqs = check_gas_requirements(address)
                
                results.append((
                    address, 
                    f"{gas_reqs['gas_balance']:.6f}",
                    f"{gas_reqs['current_gas_price']:.2f}",
                    f"{gas_reqs['claim_cost']:.6f}",
                    f"{gas_reqs['transfer_cost']:.6f}",
                    "✅" if gas_reqs['has_enough_for_claim'] else "❌",
                    "✅" if gas_reqs['has_enough_for_transfer'] else "❌",
                    "✅" if gas_reqs['has_enough_for_both'] else "❌"
                ))
                
                logger.info(f"Баланс газа для {address}: {gas_reqs['gas_balance']:.6f} ETH, " +
                           f"достаточно для клейма: {'✅' if gas_reqs['has_enough_for_claim'] else '❌'}, " +
                           f"для перевода: {'✅' if gas_reqs['has_enough_for_transfer'] else '❌'}")
                
            except Exception as e:
                results.append((address, f"Ошибка: {str(e)}", "-", "-", "-", "-", "-", "-"))
                logger.error(f"Ошибка при проверке баланса для {address}: {str(e)}")
            
            progress.advance(task)
    
    # Заполняем таблицу результатами
    for row in results:
        table.add_row(*row)
    
    console.print(table)

def claim_for_all(wallets: List[Dict[str, str]]):
    logger = logging.getLogger("claim")
    logger.info("Клейм токенов запущен")
    
    console.print("[bold cyan]Клейм токенов для всех eligible кошельков...[/bold cyan]")
    
    table = Table(title="Результаты клейма")
    table.add_column("Адрес", style="cyan")
    table.add_column("Статус", style="green")
    table.add_column("Tx Hash", style="yellow")
    table.add_column("Amount (KERNEL)", style="yellow")
    table.add_column("Баланс ETH", style="yellow")
    
    confirmation = console.input("[bold yellow]Продолжить клейм? (y/n): [/bold yellow]")
    if confirmation.lower() != "y":
        return
    
    results = []
    
    # Создаем прогресс-бар
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[bold]{task.completed}/{task.total}"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("[cyan]Выполнение клейма токенов...", total=len(wallets))
        
        for wallet in wallets:
            address = wallet["address"]
            private_key = wallet["private_key"]
            
            progress.update(task, description=f"[cyan]Проверка и клейм для {address[:8]}...")
            
            try:
                # Проверяем баланс ETH
                gas_reqs = check_gas_requirements(address)
                if not gas_reqs['has_enough_for_claim']:
                    results.append((
                        address, 
                        "❌ Недостаточно ETH", 
                        "-", 
                        "-", 
                        f"{gas_reqs['gas_balance']:.6f}"
                    ))
                    logger.warning(f"Недостаточно ETH для клейма на адресе {address}: {gas_reqs['gas_balance']:.6f} ETH (требуется ~{gas_reqs['claim_cost']:.6f} ETH)")
                    progress.advance(task)
                    continue
                    
                # Сначала проверяем eligibility
                progress.update(task, description=f"[cyan]Проверка eligibility для {address[:8]}...")
                signature = generate_signature(private_key, "Sign message to view your Season 1 points")
                eligibility_data = check_eligibility(address, signature)
                
                if not eligibility_data or "balance" not in eligibility_data or int(eligibility_data["balance"]) == 0:
                    results.append((address, "❌ Not eligible", "-", "0", f"{gas_reqs['gas_balance']:.6f}"))
                    logger.info(f"Адрес {address} не eligible для клейма")
                    progress.advance(task)
                    continue
                
                balance = int(eligibility_data["balance"])
                balance_in_kernel = balance / 10**18
                
                # Если already claimed, пропускаем
                progress.update(task, description=f"[cyan]Проверка предыдущих клеймов для {address[:8]}...")
                if is_already_claimed(address, 8):
                    results.append((address, "⚠️ Already claimed", "-", f"{balance_in_kernel:.4f}", f"{gas_reqs['gas_balance']:.6f}"))
                    logger.info(f"Адрес {address} уже выполнил клейм ранее")
                    progress.advance(task)
                    continue
                
                # Если eligible и есть достаточно ETH, делаем клейм
                progress.update(task, description=f"[cyan]Отправка транзакции клейма для {address[:8]}...")
                tx_hash = claim_tokens(
                    private_key,
                    8,  # используем фиксированный index=8 для всех кошельков
                    address,
                    eligibility_data["balance"],
                    eligibility_data["proof"],
                    True  # Используем прямой API для получения точных данных
                )
                
                if tx_hash:
                    progress.update(task, description=f"[cyan]Транзакция отправлена для {address[:8]}, ожидание подтверждения...")
                    results.append((address, "✅ Claimed", tx_hash, f"{balance_in_kernel:.4f}", f"{gas_reqs['gas_balance']:.6f}"))
                    logger.info(f"Успешный клейм для {address}, tx: {tx_hash}, amount: {balance_in_kernel:.4f} KERNEL")
                else:
                    results.append((address, "❌ Failed", "-", f"{balance_in_kernel:.4f}", f"{gas_reqs['gas_balance']:.6f}"))
                    logger.error(f"Не удалось выполнить клейм для {address}")
                    
            except Exception as e:
                results.append((address, f"❌ Ошибка: {str(e)}", "-", "-", "-"))
                logger.error(f"Ошибка при клейме для {address}: {str(e)}")
            
            progress.advance(task)
    
    # Заполняем таблицу результатами
    for row in results:
        table.add_row(*row)
    
    console.print(table)

def check_tokens_for_all(wallets: List[Dict[str, str]]):
    logger = logging.getLogger("token_balance")
    logger.info("Проверка баланса токенов запущена")
    
    console.print("[bold cyan]Проверка баланса токенов KERNEL для всех кошельков...[/bold cyan]")
    
    table = Table(title="Балансы KERNEL")
    table.add_column("Адрес", style="cyan")
    table.add_column("Баланс KERNEL", style="yellow")
    
    confirmation = console.input("[bold yellow]Продолжить проверку? (y/n): [/bold yellow]")
    if confirmation.lower() != "y":
        return
    
    results = []
    
    # Создаем прогресс-бар
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[bold]{task.completed}/{task.total}"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("[cyan]Проверка баланса токенов...", total=len(wallets))
        
        for wallet in wallets:
            address = wallet["address"]
            
            progress.update(task, description=f"[cyan]Проверка баланса KERNEL для {address[:8]}...")
            
            try:
                balance = check_token_balance(address, TOKEN_ADDRESS)
                results.append((address, f"{balance:.4f}"))
                logger.info(f"Баланс KERNEL для {address}: {balance:.4f}")
                
            except Exception as e:
                results.append((address, f"Ошибка: {str(e)}"))
                logger.error(f"Ошибка при проверке баланса KERNEL для {address}: {str(e)}")
            
            progress.advance(task)
    
    # Заполняем таблицу результатами
    for row in results:
        table.add_row(*row)
    
    console.print(table)

def send_tokens_for_all(wallets: List[Dict[str, str]]):
    logger = logging.getLogger("token_sender")
    logger.info("Отправка токенов на биржу запущена")
    
    console.print("[bold cyan]Отправка токенов на биржу для всех кошельков...[/bold cyan]")
    
    if not wallets:
        console.print("[bold red]Нет доступных кошельков[/bold red]")
        return
    
    table = Table(title="Результаты отправки токенов")
    table.add_column("Адрес кошелька", style="cyan")
    table.add_column("Адрес биржи", style="yellow")
    table.add_column("Статус", style="green")
    table.add_column("Tx Hash", style="blue")
    
    # Первоначальное подтверждение
    confirmation = console.input("[bold yellow]Отправить токены с первого кошелька? (y/n): [/bold yellow]")
    if confirmation.lower() != "y":
        return
    
    results = []
    
    # Сначала отправляем с первого кошелька
    first_wallet = wallets[0]
    first_address = first_wallet["address"]
    first_private_key = first_wallet["private_key"]
    first_exchange_address = first_wallet.get("exchange_address")
    
    console.print(f"[bold cyan]Отправка с первого кошелька {first_address}...[/bold cyan]")
    
    first_result = None
    
    try:
        # Проверяем наличие адреса биржи для первого кошелька
        if not first_exchange_address:
            first_result = (first_address, "Не указан", "❌ Нет адреса биржи", "-")
            logger.warning(f"Не указан адрес биржи для первого кошелька {first_address}")
        else:
            # Отправляем токены с первого кошелька
            tx_hash = send_tokens_to_exchange(
                private_key=first_private_key,
                exchange_address=first_exchange_address,
                token_address=TOKEN_ADDRESS,
                amount=None  # Отправляем весь баланс
            )
            
            if tx_hash:
                first_result = (first_address, first_exchange_address, "✅ Отправлено", tx_hash)
                logger.info(f"Токены успешно отправлены с первого адреса {first_address} на {first_exchange_address}. Хеш: {tx_hash}")
            else:
                first_result = (first_address, first_exchange_address, "❌ Ошибка", "-")
                logger.error(f"Не удалось отправить токены с первого адреса {first_address}")
    except Exception as e:
        first_result = (first_address, first_exchange_address if first_exchange_address else "Не указан", f"❌ Ошибка: {str(e)}", "-")
        logger.error(f"Ошибка при отправке токенов с первого адреса {first_address}: {str(e)}")
    
    # Добавляем результат по первому кошельку
    if first_result:
        results.append(first_result)
        
    # Создаем временную таблицу с результатом первого кошелька
    temp_table = Table(title="Результаты отправки с первого кошелька")
    temp_table.add_column("Адрес кошелька", style="cyan")
    temp_table.add_column("Адрес биржи", style="yellow")
    temp_table.add_column("Статус", style="green")
    temp_table.add_column("Tx Hash", style="blue")
    temp_table.add_row(*first_result)
    console.print(temp_table)
    
    # Если кошельков больше одного, запрашиваем подтверждение для остальных
    if len(wallets) > 1:
        remaining_confirmation = console.input(f"[bold yellow]Отправить токены с остальных {len(wallets) - 1} кошельков? (y/n): [/bold yellow]")
        if remaining_confirmation.lower() != "y":
            # Если пользователь отказался, выводим только результат по первому кошельку
            console.print(temp_table)
            return
        
        # Создаем прогресс-бар для остальных кошельков
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[bold]{task.completed}/{task.total}"),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("[cyan]Отправка токенов...", total=len(wallets) - 1)
            
            # Обрабатываем оставшиеся кошельки начиная со второго (индекс 1)
            for wallet in wallets[1:]:
                address = wallet["address"]
                private_key = wallet["private_key"]
                exchange_address = wallet.get("exchange_address")
                
                progress.update(task, description=f"[cyan]Отправка с адреса {address[:8]}...")
                
                try:
                    # Проверяем наличие адреса биржи
                    if not exchange_address:
                        results.append((address, "Не указан", "❌ Нет адреса биржи", "-"))
                        logger.warning(f"Не указан адрес биржи для кошелька {address}")
                        progress.advance(task)
                        continue
                    
                    # Отправляем токены
                    tx_hash = send_tokens_to_exchange(
                        private_key=private_key,
                        exchange_address=exchange_address,
                        token_address=TOKEN_ADDRESS,
                        amount=None  # Отправляем весь баланс
                    )
                    
                    if tx_hash:
                        results.append((address, exchange_address, "✅ Отправлено", tx_hash))
                        logger.info(f"Токены успешно отправлены с адреса {address} на {exchange_address}. Хеш: {tx_hash}")
                    else:
                        results.append((address, exchange_address, "❌ Ошибка", "-"))
                        logger.error(f"Не удалось отправить токены с адреса {address}")
                    
                except Exception as e:
                    results.append((address, exchange_address if exchange_address else "Не указан", f"❌ Ошибка: {str(e)}", "-"))
                    logger.error(f"Ошибка при отправке токенов с адреса {address}: {str(e)}")
                
                progress.advance(task)
    
    # Заполняем итоговую таблицу результатами
    for row in results:
        table.add_row(*row)
    
    console.print(table)

def get_web3_provider() -> Web3:
    """
    Получает объект Web3 на основе RPC URL из .env файла
    
    Returns:
        Web3: Объект Web3 с подключенным провайдером
    """
    # Получаем RPC URL из переменных окружения
    rpc_url = os.getenv("RPC_URL") or os.getenv("ETH_RPC_URL", "https://eth.llamarpc.com")
    
    # Создаем Web3 объект
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Проверяем подключение
    if not web3.is_connected():
        raise ConnectionError(f"Не удалось подключиться к RPC провайдеру: {rpc_url}")
        
    return web3

if __name__ == "__main__":
    main() 