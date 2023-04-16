from binance import Client
import time
import pandas as pd
import json
from pathlib import Path


def get_credentials():
    root = Path(".")
    file_path = f"{root}/credentials.json"

    with open(file_path) as file:

        file = file.read()
        credentials = json.loads(file)

        api_key = credentials["binance_api_key_spot"]
        api_secret = credentials["binance_api_secret_spot"]

    return api_key, api_secret


def auth():
    api_key, api_secret = get_credentials()
    binance_client = Client(testnet=False, api_key=api_key, api_secret=api_secret)

    return binance_client

# CLI inputs
def select_ticker(tickers):
    try:
        input_ticker = input("select ticker >>> ")
        ticker = tickers[input_ticker.upper()]
        print(f"{ticker} selected")
        return ticker
    except:
        print("Invalid ticker selected")
        return None


def select_order_amount():

    input_interval = input("select number of orders >>> ")
    try:
        input_interval = int(input_interval)
        return input_interval
    except:
        print("Error selecting number of orders: input must be number")
        return None


def select_usdt_size():
    input_size = input("select size[usdt] >>> ")
    try:
        input_size = int(input_size)
        return input_size
    except:
        print("Error selecting size: input must be number")
        return None


def select_duration():
    input_duration = input("select duration minutes >>> ")
    try:
        input_duration = int(input_duration)
        return input_duration
    except:
        print("Error selecting positions size: input must be number")
        return None


def select_side():
    input_side = input("select side b=Buy, s=Sell >>> ")
    if input_side.lower() == "b":
        input_side = "Buy"
    elif input_side.lower() == "s":
        input_side = "Sell"
    else:
        print("Error with selecting side")
        input_side = None

    return input_side


# market data functions
def get_spot_tickers(client):
    products = client.get_all_tickers()

    tickers = {}
    for row in products:
        symbol = row["symbol"]
        ticker = row["symbol"]
        if "USDT" in symbol:

            symbol = symbol.replace("USDT", "")

            tickers[symbol] = ticker

    return tickers


def get_last_price(client, ticker):
    products = client.get_all_tickers()
    for row in products:
        if ticker == row["symbol"]:
            last_price = float(row["price"])
            return last_price


def get_instrument_info(client, ticker):
    instrument_info = client.get_symbol_info(ticker)

    min_notional = float(instrument_info["filters"][2]["minNotional"])
    tick_size = float(instrument_info["filters"][0]["tickSize"])

    decimals = str(tick_size)[::-1].find('.')
    print(f"{ticker} | min: {min_notional} usd | decimals: {decimals}")

    return min_notional, decimals


# ORDER/POSITION OVERVIEW FUNCTIONS
def get_spot_balances(client):

    balances = client.get_account()["balances"]
    products = client.get_all_tickers()

    spot_positions = {}
    coin_prices = {}
    for row in products:
        ticker = row["symbol"].replace("USDT", "")
        price = float(row["price"])   # usd

        coin_prices[ticker] = price

    for balance in balances:
        coin = balance["asset"]
        coin_balance = float(balance["free"])

        if coin_balance > 0:
            if coin in coin_prices.keys() or coin in ["USDT", "USDC", "BUSD"]:

                if coin in ["USDT", "USDC", "BUSD"]:
                    usd_value = coin_balance
                else:
                    price = coin_prices[coin]
                    usd_value = round(coin_balance * price, 2)

                if usd_value > 5:
                    spot_positions[coin] = {"coin_amount": coin_balance, "usd_value": usd_value}

    return spot_positions


def display_positions(positions):

    if positions:
        print("Current positions")
        positions_df = pd.DataFrame.from_dict(positions, orient="index")
        print(positions_df.to_markdown())
    else:
        print("No open positions")


# ORDER EXECUTION functions
def market_order(client, tickers):

    ticker = select_ticker(tickers)
    side = select_side()  # buy/sell
    total_size = select_usdt_size()  # usd amount

    spot_positions = get_spot_balances(client)
    error = False
    if ticker is not None and side is not None and total_size is not None:
        last_price = get_last_price(client, ticker)
        min_notional, decimals = get_instrument_info(client, ticker)

        order_amount = 10
        seconds = 15
        second_interval = seconds / order_amount

        total_coin_size = round(total_size / last_price * 0.995, decimals)
        order_size = round(total_coin_size / order_amount, decimals)
        if order_size * last_price < min_notional:
            print(f"Error: ordes size below minimum size >>> min notional is {min_notional} usd")
            error = True

        if side == "Buy":
            if "USDT" in spot_positions.keys():
                usdt_amount = spot_positions["USDT"]["usd_value"]
                if usdt_amount < total_size:
                    print("Not enough USDT for selected size")
                    error = True
            else:
                error = True
                print("No USDT available for buying")

            if not error:

                filled_usdt_amount = 0
                filled_coin_amount = 0
                fills = []

                while filled_usdt_amount < total_size:

                    filled_order = client.order_market_buy(symbol=ticker, quantity=order_size)

                    for fill in filled_order["fills"]:
                        fills.append(fill)

                    total_qty = 0
                    total_price_qty = 0
                    for fill in fills:
                        price = float(fill["price"])
                        qty = float(fill["qty"])
                        price_qty = price * qty

                        total_qty += qty
                        total_price_qty += price_qty

                        avg_fill = round(total_price_qty / total_qty, decimals)

                    filled_usdt_amount += float(filled_order["cummulativeQuoteQty"])
                    filled_coin_amount += float(filled_order["executedQty"])

                    print(f"fast twap running >>> Buy: {round(filled_usdt_amount, decimals)} / {total_size} usd | total avg price: {avg_fill}")

                    if "USDT" in get_spot_balances(client).keys():
                        spot_balances = float(get_spot_balances(client)["USDT"]["coin_amount"])
                    else:
                        spot_balances = 0
                    last_price = get_last_price(client, ticker)

                    if (order_size * last_price + filled_usdt_amount) > total_size:

                        remaining_size = total_size - filled_usdt_amount
                        if remaining_size > min_notional:
                            order_size = round(remaining_size / last_price ,decimals)
                        else:
                            print(f"remaining size to low >>> unfilled size: {round(remaining_size, decimals)} usd")
                            break

                    if spot_balances < order_size:
                        if spot_balances > min_notional:
                            order_size = spot_balances
                        else:
                            print(f"remaining size to low >>> unfilled size: {round(spot_balances, decimals)} coins")
                            break

                    time.sleep(second_interval)

        elif side == "Sell":
            if ticker.replace("USDT", "") in spot_positions.keys():
                usdt_amount = spot_positions[ticker.replace("USDT", "")]["usd_value"]
                if usdt_amount < total_size:
                    print("Not enough coins for selected size")
                    error = True
            else:
                error = True
                print(f"No available coins for selected ticker: {ticker}")

            if not error:

                filled_usdt_amount = 0
                filled_coin_amount = 0
                fills = []

                while filled_usdt_amount < total_size:

                    filled_order = client.order_market_sell(symbol=ticker, quantity=order_size)
                    for fill in filled_order["fills"]:
                        fills.append(fill)

                    total_qty = 0
                    total_price_qty = 0
                    for fill in fills:
                        price = float(fill["price"])
                        qty = float(fill["qty"])
                        price_qty = price * qty

                        total_qty += qty
                        total_price_qty += price_qty

                        avg_fill = round(total_price_qty / total_qty, decimals)

                    filled_usdt_amount += float(filled_order["cummulativeQuoteQty"])
                    filled_coin_amount += float(filled_order["executedQty"])

                    print(f"fast twap running >>> Sell: {round(filled_usdt_amount, decimals)} / {total_size} usd | total avg price: {avg_fill}")

                    spot_balances = float(get_spot_balances(client)[ticker.replace("USDT", "")]["coin_amount"])

                    last_price = get_last_price(client, ticker)
                    if (order_size * last_price + filled_usdt_amount) > total_size:

                        remaining_size = total_size - filled_usdt_amount
                        if remaining_size > min_notional:
                            order_size = round(remaining_size / last_price ,decimals)
                        else:
                            print(f"remaining size to low >>> unfilled size: {round(remaining_size, decimals)} usd")
                            break

                    if spot_balances < order_size:
                        if spot_balances > min_notional:
                            order_size = spot_balances
                        else:
                            print(f"remaining size to low >>> unfilled size: {round(spot_balances, decimals)} coins")
                            break

                    time.sleep(second_interval)


def basic_twap(client, tickers):
    """
    Basic linear: you specify, order number, position size, duration and side, position is then opened in linear fashion with same intervals and size per interval
    """

    ticker = select_ticker(tickers)
    order_amount = select_order_amount()  # number or orders
    side = select_side()  # buy/sell
    total_size = select_usdt_size()  # usd amount
    twap_duration = select_duration()  # minutes

    spot_positions = get_spot_balances(client)
    error = False
    if ticker is not None and side is not None and total_size is not None:
        last_price = get_last_price(client, ticker)
        min_notional, decimals = get_instrument_info(client, ticker)

        seconds = twap_duration * 60
        second_interval = seconds / order_amount

        total_coin_size = round(total_size / last_price * 0.995, decimals)
        order_size = round(total_coin_size / order_amount, decimals)
        if order_size * last_price < min_notional:
            print(f"Error: ordes size below minimum size >>> min notional is {min_notional} usd")
            error = True

        if side == "Buy":
            if "USDT" in spot_positions.keys():
                usdt_amount = spot_positions["USDT"]["usd_value"]
                if usdt_amount < total_size:
                    print("Not enough USDT for selected size")
                    error = True
            else:
                error = True
                print("No USDT available for buying")

            if not error:

                filled_usdt_amount = 0
                filled_coin_amount = 0
                fills = []

                while filled_usdt_amount < total_size:

                    filled_order = client.order_market_buy(symbol=ticker, quantity=order_size)

                    for fill in filled_order["fills"]:
                        fills.append(fill)

                    total_qty = 0
                    total_price_qty = 0
                    for fill in fills:
                        price = float(fill["price"])
                        qty = float(fill["qty"])
                        price_qty = price * qty

                        total_qty += qty
                        total_price_qty += price_qty

                        avg_fill = round(total_price_qty / total_qty, decimals)

                    filled_usdt_amount += float(filled_order["cummulativeQuoteQty"])
                    filled_coin_amount += float(filled_order["executedQty"])

                    print(f"twap running >>> Buy: {round(filled_usdt_amount, decimals)} / {total_size} usd | total avg price: {avg_fill}")

                    if "USDT" in get_spot_balances(client).keys():
                        spot_balances = float(get_spot_balances(client)["USDT"]["coin_amount"])
                    else:
                        spot_balances = 0

                    last_price = get_last_price(client, ticker)
                    if (order_size * last_price + filled_usdt_amount) > total_size:

                        remaining_size = total_size - filled_usdt_amount
                        if remaining_size > min_notional:
                            order_size = round(remaining_size / last_price ,decimals)
                        else:
                            print(f"remaining size to low >>> unfilled size: {round(remaining_size, decimals)} usd")
                            break

                    if spot_balances < order_size:
                        if spot_balances > min_notional:
                            order_size = spot_balances
                        else:
                            print(f"remaining size to low >>> unfilled size: {round(spot_balances, decimals)} coins")
                            break

                    time.sleep(second_interval)

        elif side == "Sell":
            if ticker.replace("USDT", "") in spot_positions.keys():
                usdt_amount = spot_positions[ticker.replace("USDT", "")]["usd_value"]
                if usdt_amount < total_size:
                    print("Not enough coins for selected size")
                    error = True
            else:
                error = True
                print(f"No available coins for selected ticker: {ticker}")

            if not error:

                filled_usdt_amount = 0
                filled_coin_amount = 0
                fills = []

                while filled_usdt_amount < total_size:

                    filled_order = client.order_market_sell(symbol=ticker, quantity=order_size)
                    for fill in filled_order["fills"]:
                        fills.append(fill)

                    total_qty = 0
                    total_price_qty = 0
                    for fill in fills:
                        price = float(fill["price"])
                        qty = float(fill["qty"])
                        price_qty = price * qty

                        total_qty += qty
                        total_price_qty += price_qty

                        avg_fill = round(total_price_qty / total_qty, decimals)

                    filled_usdt_amount += float(filled_order["cummulativeQuoteQty"])
                    filled_coin_amount += float(filled_order["executedQty"])

                    print(f"twap running >>> Sell: {round(filled_usdt_amount, decimals)} / {total_size} usd | total avg price: {avg_fill}")

                    spot_balances = float(get_spot_balances(client)[ticker.replace("USDT", "")]["coin_amount"])

                    last_price = get_last_price(client, ticker)
                    if (order_size * last_price + filled_usdt_amount) > total_size:

                        remaining_size = total_size - filled_usdt_amount
                        if remaining_size > min_notional:
                            order_size = round(remaining_size / last_price ,decimals)
                        else:
                            print(f"remaining size to low >>> unfilled size: {round(remaining_size, decimals)} usd")
                            break

                    if spot_balances < order_size:
                        if spot_balances > min_notional:
                            order_size = spot_balances
                        else:
                            print(f"remaining size to low >>> unfilled size: {round(spot_balances, decimals)} coins")
                            break

                    time.sleep(second_interval)





