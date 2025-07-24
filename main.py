import requests
import time
from web3 import Web3, Account
from eth_account.messages import encode_defunct
from datetime import datetime
import random


PRIVATE_KEYS = [
    "0xYOUR_PRIVATE_KEY_1",
    "0xYOUR_PRIVATE_KEY_2",
    # Tambah private key lain di sini
]
DAILY_SETS = 1  # berapa set transaksi per hari
INCLUDE_ADD_LIQUIDITY = True  # True/False untuk add liquidity
# ===============================================

RPC_URL = 'https://evmrpc-testnet.0g.ai/'
CHAIN_ID = 16601
w3 = Web3(Web3.HTTPProvider(RPC_URL))

contracts = {
    'router': '0xb95B5953FF8ee5D5d9818CdbEfE363ff2191318c',
    'positionsNFT': '0x44f24b66b3baa3a784dbeee9bfe602f15a2cc5d9',
    'USDT': '0x3ec8a8705be1d5ca90066b37ba62c4183b024ebf',
    'BTC': '0x36f6414ff1df609214ddaba71c84f18bcf00f67d',
    'ETH': '0x0fE9B43625fA7EdD663aDcEC0728DD635e4AbF7c',
    'GIMO': '0xba2ae6c8cddd628a087d7e43c1ba9844c5bf9638'
}
tokenDecimals = {k: 18 for k in ['USDT', 'BTC', 'ETH', 'GIMO']}

def logger(msg, c="green"):
    colors = {"green": "\033[32m", "yellow": "\033[33m", "red": "\033[31m", "cyan": "\033[36m", "reset": "\033[0m"}
    print(f"{colors.get(c, '')}{msg}{colors['reset']}")

def encodeAddress(addr):
    return addr.lower().replace('0x', '').rjust(64, '0')

def encodeUint(n):
    return hex(int(n))[2:].rjust(64, '0')

def encodeInt(n):
    bn = int(n)
    bitmask = (1 << 256) - 1
    twosComplement = bn & bitmask
    return hex(twosComplement)[2:].rjust(64, '0')

def getRandomAmount(minv, maxv, precision=8):
    return round(random.uniform(minv, maxv), precision)

def create_headers(accessToken=None):
    h = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.8",
        "content-type": "application/json",
        "priority": "u=1, i",
        "sec-ch-ua": "Mozilla/5.0",
        "Referer": "https://test.jaine.app/",
    }
    if accessToken:
        h["authorization"] = f"Bearer {accessToken}"
        h["apikey"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzQ3NzYwNDAwLCJleHAiOjE5MDU1MjY4MDB9.gfxfHjuyAN0wDdTQ_z_YTgIEoDCBVWuAhBC6gD3lf_8"
    return h

def sign_message(account, message):
    message_encoded = encode_defunct(text=message)
    signed = w3.eth.account.sign_message(message_encoded, private_key=account.key)
    return signed.signature.hex()

def login(account):
    logger(f"Login wallet {account.address}", "yellow")
    # Step 1: Get nonce
    nonce_url = 'https://siwe.zer0.exchange/nonce'
    payload = {
        "provider": "siwe",
        "chain_id": CHAIN_ID,
        "wallet": account.address,
        "ref": "",
        "connector": {"name": "OKX Wallet", "type": "injected", "id": "com.okex.wallet"}
    }
    r = requests.post(nonce_url, headers=create_headers(), json=payload)
    nonce = r.json().get('nonce')
    if not nonce:
        logger("Nonce error", "red")
        return None
    issuedAt = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    message = f"test.jaine.app wants you to sign in with your Ethereum account:\n{account.address}\n\n\nURI: https://test.jaine.app\nVersion: 1\nChain ID: {CHAIN_ID}\nNonce: {nonce}\nIssued At: {issuedAt}"
    signature = sign_message(account, message)
    # Step 2: Send signature for verification
    signin_url = 'https://siwe.zer0.exchange/sign-in'
    payload2 = {
        "provider": "siwe",
        "chain_id": CHAIN_ID,
        "wallet": account.address,
        "message": message,
        "signature": signature
    }
    r2 = requests.post(signin_url, headers=create_headers(), json=payload2)
    j2 = r2.json()
    token = j2.get("token")
    email = j2.get("email")
    if not token:
        logger("Sign-in error", "red")
        return None
    # Step 3: Auth verify
    verify_url = 'https://app.zer0.exchange/auth/v1/verify'
    payload3 = {
        "type": "email",
        "email": email,
        "token": token,
        "gotrue_meta_security": {}
    }
    r3 = requests.post(verify_url, headers=create_headers(token), json=payload3)
    access_token = r3.json().get('access_token')
    if not access_token:
        logger("Access token error", "red")
        return None
    logger(f"Login success: {account.address}")
    return access_token

def addLiquidity(account):
    btcAmount = "0.000001"
    usdtAmount = "0.086483702551157391"
    token0Address = contracts['BTC']
    token1Address = contracts['USDT']
    token0Decimals = tokenDecimals['BTC']
    token1Decimals = tokenDecimals['USDT']
    logger(f"Add liquidity {btcAmount} BTC + {usdtAmount} USDT", "cyan")

    methodId = '0x88316456'
    fee = 100
    tickLower = -887272
    tickUpper = 887272
    amount0Desired = int(float(btcAmount) * (10 ** token0Decimals))
    amount1Desired = int(float(usdtAmount) * (10 ** token1Decimals))
    amount0Min = int(amount0Desired * 0.95)
    amount1Min = int(amount1Desired * 0.95)
    deadline = int(time.time()) + 60 * 20
    calldata = (
        methodId +
        encodeAddress(token0Address) +
        encodeAddress(token1Address) +
        encodeUint(fee) +
        encodeInt(tickLower) +
        encodeInt(tickUpper) +
        encodeUint(amount0Desired) +
        encodeUint(amount1Desired) +
        encodeUint(amount0Min) +
        encodeUint(amount1Min) +
        encodeAddress(account.address) +
        encodeUint(deadline)
    )

    nonce = w3.eth.get_transaction_count(account.address)
    tx = {
        'to': contracts['positionsNFT'],
        'data': calldata,
        'chainId': CHAIN_ID,
        'gas': 600000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
        'value': 0,
    }
    signed = w3.eth.account.sign_transaction(tx, private_key=account.key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    logger(f"Add liquidity tx: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 1:
        logger("Add liquidity success!", "green")
    else:
        logger("Add liquidity failed!", "red")

def executeSwap(account, tokenInName, tokenOutName, amount):
    tokenInAddress = contracts[tokenInName]
    tokenOutAddress = contracts[tokenOutName]
    tokenInDecimals = tokenDecimals[tokenInName]
    logger(f"Swap {amount} {tokenInName} -> {tokenOutName}", "yellow")

    methodId = '0x414bf389'
    fee = 500 if 'USDT' in (tokenInName, tokenOutName) else 100
    amountIn = int(float(amount) * (10 ** tokenInDecimals))
    deadline = int(time.time()) + 60 * 20
    amountOutMinimum = 0
    calldata = (
        methodId +
        encodeAddress(tokenInAddress) +
        encodeAddress(tokenOutAddress) +
        encodeUint(fee) +
        encodeAddress(account.address) +
        encodeUint(deadline) +
        encodeUint(amountIn) +
        encodeUint(amountOutMinimum) +
        "0" * 64
    )

    nonce = w3.eth.get_transaction_count(account.address)
    tx = {
        'to': contracts['router'],
        'data': calldata,
        'chainId': CHAIN_ID,
        'gas': 300000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
        'value': 0,
    }
    signed = w3.eth.account.sign_transaction(tx, private_key=account.key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    logger(f"Swap tx: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 1:
        logger("Swap success!", "green")
    else:
        logger("Swap failed!", "red")

def main():
    accounts = [Account.from_key(pk) for pk in PRIVATE_KEYS]
    access_tokens = []
    for acc in accounts:
        token = login(acc)
        access_tokens.append(token)
        if not token:
            logger("Some wallet failed to login. STOP.", "red")
            return
    logger(f"{len(accounts)} wallet(s) login success", "green")
    set_count = DAILY_SETS
    logger(f"Running {set_count} daily set(s), addLiquidity={INCLUDE_ADD_LIQUIDITY}")
    while True:
        for i in range(set_count):
            logger(f"-- Daily Transaction Set {i+1}/{set_count} --", "cyan")
            for acc in accounts:
                logger(f"Wallet: {acc.address}", "yellow")
                if INCLUDE_ADD_LIQUIDITY:
                    addLiquidity(acc)
                    time.sleep(5)
                btcAmount = getRandomAmount(0.000000095, 0.00000020, 8)
                executeSwap(acc, 'BTC', 'USDT', btcAmount)
                time.sleep(5)
                usdtToBtcAmount = getRandomAmount(1, 2, 3)
                executeSwap(acc, 'USDT', 'BTC', usdtToBtcAmount)
                time.sleep(5)
                usdtToGimoAmount = getRandomAmount(99, 105, 50)
                executeSwap(acc, 'USDT', 'GIMO', usdtToGimoAmount)
                time.sleep(5)
                gimoAmount = getRandomAmount(0.0001, 0.00015, 5)
                executeSwap(acc, 'GIMO', 'USDT', gimoAmount)
                time.sleep(10)
        logger("Semua cycle harian selesai. Tidur 24 jam...", "cyan")
        for s in range(86400, 0, -1):
            h, m, sec = s//3600, (s%3600)//60, s%60
            print(f"\r[⏳] Next cycle: {h}h {m}m {sec}s", end="")
            time.sleep(1)
        print()

if __name__ == "__main__":
    main()
