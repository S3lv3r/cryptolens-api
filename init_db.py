from database import engine, SessionLocal, Base
from models import Crypto
import models

Base.metadata.create_all(bind=engine)

# (symbol, nombre, cmc_id, coingecko_id)
TOP_CRYPTOS = [
    ("BTC",   "Bitcoin",            1,      "bitcoin"),
    ("ETH",   "Ethereum",           1027,   "ethereum"),
    ("USDT",  "Tether",             825,    "tether"),
    ("BNB",   "BNB",                1839,   "binancecoin"),
    ("SOL",   "Solana",             5426,   "solana"),
    ("USDC",  "USD Coin",           3408,   "usd-coin"),
    ("XRP",   "XRP",                52,     "ripple"),
    ("DOGE",  "Dogecoin",           74,     "dogecoin"),
    ("TRX",   "TRON",               1958,   "tron"),
    ("TON",   "Toncoin",            11419,  "the-open-network"),
    ("ADA",   "Cardano",            2010,   "cardano"),
    ("AVAX",  "Avalanche",          5805,   "avalanche-2"),
    ("SHIB",  "Shiba Inu",          5994,   "shiba-inu"),
    ("LINK",  "Chainlink",          1975,   "chainlink"),
    ("DOT",   "Polkadot",           6636,   "polkadot"),
    ("BCH",   "Bitcoin Cash",       1831,   "bitcoin-cash"),
    ("LTC",   "Litecoin",           2,      "litecoin"),
    ("UNI",   "Uniswap",            7083,   "uniswap"),
    ("NEAR",  "NEAR Protocol",      6535,   "near"),
    ("XLM",   "Stellar",            512,    "stellar"),
    ("SUI",   "Sui",                20947,  "sui"),
    ("APT",   "Aptos",              21794,  "aptos"),
    ("PEPE",  "Pepe",               24478,  "pepe"),
    ("ICP",   "Internet Computer",  8916,   "internet-computer"),
    ("STX",   "Stacks",             4847,   "blockstack"),
    ("IMX",   "Immutable",          10603,  "immutable-x"),
    ("OP",    "Optimism",           11840,  "optimism"),
    ("ARB",   "Arbitrum",           11841,  "arbitrum"),
    ("FIL",   "Filecoin",           2280,   "filecoin"),
    ("INJ",   "Injective",          7226,   "injective-protocol"),
    ("ATOM",  "Cosmos",             3794,   "cosmos"),
    ("VET",   "VeChain",            3077,   "vechain"),
    ("GRT",   "The Graph",          6719,   "the-graph"),
    ("ALGO",  "Algorand",           4030,   "algorand"),
    ("SAND",  "The Sandbox",        6210,   "the-sandbox"),
    ("MANA",  "Decentraland",       1966,   "decentraland"),
    ("AAVE",  "Aave",               7278,   "aave"),
    ("MKR",   "Maker",              1518,   "maker"),
    ("SNX",   "Synthetix",          2586,   "synthetix-network-token"),
    ("CRV",   "Curve DAO",          6538,   "curve-dao-token"),
    ("LDO",   "Lido DAO",           8000,   "lido-dao"),
    ("RUNE",  "THORChain",          4157,   "thorchain"),
    ("FTM",   "Fantom",             3513,   "fantom"),
    ("EGLD",  "MultiversX",         6892,   "elrond-erd-2"),
    ("FLOW",  "Flow",               4558,   "flow"),
    ("XTZ",   "Tezos",              2011,   "tezos"),
    ("EOS",   "EOS",                1765,   "eos"),
    ("THETA", "Theta Network",      2416,   "theta-token"),
    ("KCS",   "KuCoin Token",       2087,   "kucoin-shares"),
    ("ZEC",   "Zcash",              1437,   "zcash"),
]

db = SessionLocal()
for symbol, name, cmc_id, cg_id in TOP_CRYPTOS:
    exists = db.query(Crypto).filter(Crypto.symbol == symbol).first()
    if not exists:
        db.add(Crypto(symbol=symbol, name=name, cmc_id=cmc_id, coingecko_id=cg_id))
        print(f"Agregada: {symbol}")
    else:
        exists.cmc_id = cmc_id
        print(f"Actualizada: {symbol}")

db.commit()
db.close()

print("\nCargando datos iniciales...")
from tasks.scheduler import task_market_data, task_indicators_and_signals
from database import SessionLocal
from models import MarketData

task_market_data()

db = SessionLocal()
count = db.query(MarketData).count()
print(f"Registros en market_data: {count}")
db.close()

task_indicators_and_signals()
print("\nTodo listo")