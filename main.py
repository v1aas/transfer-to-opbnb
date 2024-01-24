import json
import time
import random
import inquirer
from web3 import Web3
from loguru import logger
from client import Client
from inquirer import prompt
from web3.middleware import geth_poa_middleware

with open('polyhedra_abi.json', 'r') as file:
    ABI = json.load(file)

BSC_RPC = "https://rpc.ankr.com/bsc"
OPBNB_RPC = "https://opbnb-mainnet-rpc.bnbchain.org"

web3_bsc = Web3(Web3.HTTPProvider(BSC_RPC))
web3_bsc.middleware_onion.inject(geth_poa_middleware, layer=0)
web3_opbsc = Web3(Web3.HTTPProvider(OPBNB_RPC))

def intro():
    business_card = """
    ╔════════════════════════════════════════╗
    ║        Createad by v1aas               ║
    ║                                        ║
    ║        https://t.me/v1aas              ║
    ║        https://github.com/v1aas        ║
    ║                                        ║
    ╚════════════════════════════════════════╝
    """
    print(business_card)

def get_wallets():
    with open('keys.txt', 'r') as file:
        return [line.strip() for line in file.readlines()]

def get_eip1559_gas(web3):
    latest_block = web3.eth.get_block('latest')
    max_fee_priotiry_gas = web3.eth.max_priority_fee
    max_fee_per_gas = int(latest_block['baseFeePerGas']) + max_fee_priotiry_gas
    return max_fee_priotiry_gas, max_fee_per_gas

def check_balance_on_bnb():
    keys = get_wallets()
    for num, key in enumerate(keys, start=1):
        client = Client(web3_bsc, key)
        balance = web3_bsc.from_wei(web3_bsc.eth.get_balance(client.address), 'ether')
        print(f"Баланс адреса {client.address}: {balance} BNB. {num}")
        if balance < 0.002:
            with open('need_balance.txt', 'a') as file:
                file.write(f"{client.address} \n")
    
def check_balance_on_opbnb():
    keys = get_wallets()
    for num, key in enumerate(keys, start=1):
        client = Client(web3_opbsc, key)
        balance = web3_opbsc.from_wei(web3_opbsc.eth.get_balance(client.address), 'ether')
        print(f"Баланс адреса {client.address}: {balance} opBNB. {num}")
                
def transfer_to_opbnb(client: Client):
    for key in get_wallets():
        client = Client(web3_bsc, key)
        contract = client.web3.eth.contract(address="0x51187757342914E7d94FFFD95cCCa4f440FE0E06", abi=ABI)
        amount = round(random.uniform(0.0007, 0.0001), 6)
        max_fee_priotiry_gas, max_fee_per_gas = get_eip1559_gas(client.web3)
        try:
            fee = contract.functions.estimateFee(10, 23, client.web3.to_wei(amount, 'ether')).call()
            tx = contract.functions.transferETH(
                23,
                client.web3.to_wei(amount, 'ether'),
                client.address
                ).build_transaction(
                    {
                        'nonce': client.web3.eth.get_transaction_count(client.address),
                        'gas': 105000,
                        'value': client.web3.to_wei(amount, 'ether') + fee,
                        'maxPriorityFeePerGas': max_fee_priotiry_gas,
                        'maxFeePerGas': max_fee_per_gas,
                    }
                )
            signed_txn = client.web3.eth.account.sign_transaction(tx, client.private_key)
            txn_hash = client.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            logger.info(f"Транзакция отправлена. Хэш: {txn_hash.hex()}")
            receipt = client.web3.eth.wait_for_transaction_receipt(txn_hash)
            if (receipt['status'] == 1):
                logger.success(f"Транзакция прошла успешно! Бридж в opBNB успешен! {client.address}")
            else:
                logger.error(f"Ошибка. Статус: {receipt['status']}")
        except Exception as e:
            logger.error(f"Ошибка {e}")
            with open('error_wallet.txt', 'a') as file:
                    file.write(f"\n{client.address}")
        sec = random.randint(30,60)
        logger.info(f"Сплю {sec} перед следующим кошельком")
        time.sleep(sec)

def main():
    intro()
    while True:
        questions = [
            inquirer.List('choice',
                        message="Доступные модули",
                        choices=[
                            'Проверка баланса BNB',
                            'Проверка баланса opBNB',
                            'Трансфер BNB to opBNB',
                            'Выход'
                            ])
        ]
        
        choice = prompt(questions)['choice']

        if choice == 'Проверка баланса BNB':
            check_balance_on_bnb()
        elif choice == 'Проверка баланса opBNB':
            check_balance_on_opbnb()
        elif choice == 'Трансфер BNB to opBNB':
            transfer_to_opbnb()
        else:
            print("Выход")
            break

if __name__ == '__main__':
    main()
