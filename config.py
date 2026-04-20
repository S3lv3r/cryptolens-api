from dotenv import load_dotenv
import os

load_dotenv()

# Base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/crypto_db")

# CoinMarketCap
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY", "")
COINMARKETCAP_BASE_URL = os.getenv("COINMARKETCAP_BASE_URL", "https://pro-api.coinmarketcap.com/v1")

# Cryptometer
CRYPTOMETER_API_KEY = os.getenv("CRYPTOMETER_API_KEY", "")
CRYPTOMETER_BASE_URL = os.getenv("CRYPTOMETER_BASE_URL", "https://cryptometer.io/api")

# App
APP_ENV = os.getenv("APP_ENV", "development")
SECRET_KEY = os.getenv("SECRET_KEY", "cambia_esto")