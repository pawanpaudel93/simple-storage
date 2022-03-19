from solcx import compile_standard, install_solc
from web3 import Web3
from web3.middleware import geth_poa_middleware
from decouple import config
import json


install_solc("0.6.0")

with open("SimpleStorage.sol", "r") as file:
    simple_storage_file = file.read()


compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"SimpleStorage.sol": {"content": simple_storage_file}},
        "settings": {
            "outputSelection": {
                "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
            }
        },
    },
    solc_version="0.6.0",
)

with open("compiled_code.json", "w") as f:
    json.dump(compiled_sol, f)

bytecode = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["evm"][
    "bytecode"
]["object"]

abi = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["abi"]
w3 = Web3(Web3.HTTPProvider(config("HTTP_PROVIDER")))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
chain_id = config("CHAIN_ID")
my_address = config("MY_ADDRESS")
private_key = config("PRIVATE_KEY")

# Create contract
SimpleStorage = w3.eth.contract(abi=abi, bytecode=bytecode)

# Get transaction nonce
nonce = w3.eth.get_transaction_count(my_address)
print(nonce)

# 1. Build transaction
# 2. Sign transaction
# 3. Send transaction
transaction = SimpleStorage.constructor().buildTransaction(
    {
        # "chainId": chain_id,
        "from": my_address,
        "nonce": nonce,
    }
)
signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)

# Send the signed transaction
# print(signed_txn.rawTransaction, transaction)
print("Deploying contract...")
tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print("Deployed Contract address:", tx_receipt.contractAddress)

# Working with the contract
simple_storage = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
print(simple_storage.functions.retrieve().call())

print("Updating contract...")
store_transaction = simple_storage.functions.store(42).buildTransaction(
    {
        # "chainId": chain_id,
        "from": my_address,
        "nonce": nonce + 1,
    }
)
signed_store_txn = w3.eth.account.sign_transaction(
    store_transaction, private_key=private_key
)
tx_hash = w3.eth.send_raw_transaction(signed_store_txn.rawTransaction)
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print("Updated...")
print(simple_storage.functions.retrieve().call())
