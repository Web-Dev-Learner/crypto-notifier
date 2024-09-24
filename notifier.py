import redis
import requests
from datetime import timedelta
import os
from dotenv import load_dotenv


load_dotenv()
KEY = os.getenv('KEY')
MAIL = os.getenv('MAIL')
SANDBOX = os.getenv('SANDBOX')



API_HOST="https://api.coingecko.com/api/v3"
coin_to_notify_price={
    "bitcoin":35000,
    "ethereum":60000,
    "cardano":2.25
}

coin_ids=["bitcoin","ethereum","cardano"]

coin_query_String=",".join(coin_ids)

print(coin_query_String)
coin_data={coin_id:{} for coin_id in coin_ids}

# Fetch market data:
coin_json_response=requests.get(
    f"{API_HOST}/coins/markets?vs_currency=usd&ids={coin_query_String}"
).json()

# Parse and store coin data
for coin in coin_json_response:
    coin_id=coin["id"]
    coin_data[coin_id]["symbol"]=coin["symbol"]
    coin_data[coin_id]["name"]=coin["name"]
    coin_data[coin_id]["current_price"]=coin["current_price"]
    coin_data[coin_id]["high_24h"]=coin["high_24h"]
    coin_data[coin_id]["low_24h"]=coin["low_24h"]
    coin_data[coin_id]["price_change_percentage_24h"]=coin["price_change_percentage_24h"]
    
# Connect to Redis port 6379

r=redis.Redis(host="127.0.0.1",port=6379)

# Store coin prices in Redis
for coin_id,coin_detail in coin_data.items():
    
    r.set(f"{coin_id}|last_known_price",coin_detail["current_price"])
    if not r.exists(f"{coin_id}|price_5_minutes_ago"):
        r.setex(
            f"{coin_id}|price_5_minutes_ago",
            timedelta(minutes=5),
            coin_detail["current_price"]
        )
    if not r.exists(f"{coin_id}|price_30_minutes_ago"):
        r.setex(
            f"{coin_id}|price_30_minutes_ago",
            timedelta(minutes=30),
            coin_detail["current_price"]
        )
    if not r.exists(f"{coin_id}|price_60_minutes_ago"):
        r.setex(
            f"{coin_id}|price_60_minutes_ago",
            timedelta(minutes=60),
            coin_detail["current_price"]
        )
    if not r.exists(f"{coin_id}|lowest_in_24"):
        r.setex(
            f"{coin_id}|lowest_in_24",
            timedelta(hours=24),
            coin_detail["current_price"]
        )





for coin in coin_ids:
    print(coin)

# Check price and send email notification

    last_scraped_price=float(r.get(f"{coin}|last_known_price"))
    if last_scraped_price <= coin_to_notify_price[coin]:
        print("sending price drop below notification email")
        requests.post(
    f"https://api.mailgun.net/v3/{SANDBOX}/messages",
    auth=("api",f"{KEY}"),
          data={
              "from": f"Mailgun Sandbox <postmaster@{SANDBOX}>",
              "to": MAIL,
              "subject": "Buy the dip!",
              "text":f"Price for {coin} has reached below your notification price.It's currently {last_scraped_price}"

          }
        )
        

    last_known_24h_low = r.get(f"{coin}|lowest_24h")
    if last_known_24h_low is not None:
        last_known_24h_low = float(last_known_24h_low)
    else:
        last_known_24h_low = float('inf') 




    
    if last_scraped_price <= last_known_24h_low:
        print("sending  new 24h low notification email")
        requests.post(
    f"https://api.mailgun.net/v3/{SANDBOX}/messages",
    auth=("api",f"{KEY}"),
          data={
              "from": f"Mailgun Sandbox <postmaster@{SANDBOX}>",
              "to": MAIL,
              "subject": "New 24h Low reached",
              "text":f"Price for {coin} has reached new low for 24h..It's currently {last_scraped_price}. last known low was: {last_known_24h_low}"

          }
        )

       
       

        r.setex(
            f"{coin}|lowest_24h",  
            timedelta(hours=24),
            last_scraped_price
        )




# This script performs the following functions:
# - Calls the CoinGecko API for current prices.
# - Updates the Redis cache with the data.
# - Calculates increases/decreases in prices.
# - Sends notification emails if certain conditions are met.

# Install Redis on Windows using: Redis-x64-3.0.504.msi
# Start Redis server: C:\Program Files\Redis\redis-server
# Verify Redis is running: redis-cli ping

# Required packages:
# - redis: For interacting with a Redis database.
# - requests: To make HTTP requests to APIs.
# - python-dotenv: To load environment variables from a .env file.

# To set up the environment:
# 1. Create a virtual environment:
#    python -m venv env
# 2. Activate the virtual environment:
#    .\env\Scripts\activate
# 3. Install dependencies:
#    pip install -r requirements.txt

# Test queries sample:
# https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd
# Sample endpoint:
# https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=bitcoin,ethereum,cardano

# Sample JSON response:
# [
#   {
#     "id": "bitcoin",
#     "symbol": "btc",
#     "name": "Bitcoin",
#     "image": "https://coin-images.coingecko.com/coins/images/1/large/bitcoin.png?1696501400",
#     "current_price": 63085,
#     "market_cap": 1245504568680,
#     "market_cap_rank": 1,
#     "fully_diluted_valuation": 1323788570870,
#     "total_volume": 29200316228,
#     "high_24h": 63964,
#     "low_24h": 62742,
#     "price_change_24h": -878.695619859973,
#     "price_change_percentage_24h": -1.37373,
#     "market_cap_change_24h": -18961541468.4421,
#     "market_cap_change_percentage_24h": -1.49957,
#     "circulating_supply": 19758137,
#     "total_supply": 21000000,
#     "max_supply": 21000000,
#     "ath": 73738,
#     "ath_change_percentage": -14.55632,
#     "ath_date": "2024-03-14T07:10:36.635Z",
#     "atl": 67.81,
#     "atl_change_percentage": 92814.51524,
#     "atl_date": "2013-07-06T00:00:00.000Z",
#     "roi": null,
#     "last_updated": "2024-09-24T04:27:23.760Z"
#   }
# ]
