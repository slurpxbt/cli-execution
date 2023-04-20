from binance import Client
import time
import pandas as pd
import json
from pathlib import Path
from dhooks import Webhook
import decimal

def load_weebhook():
    root = Path(".")
    file_path = f"{root}/webhook_config.json"

    with open(file_path) as file:
        file = file.read()
        webhook_config = json.loads(file)

        weebhook = webhook_config["binance_exe_webhook"]

    return weebhook

def send_dis_msg(msg):

    api_key = load_weebhook()
    try:
        hook = Webhook(api_key)
    except Exception:
        pass

    try:
        hook.send(f"```{msg}```")
    except Exception:
        print("dis api error")


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
    input_duration = input("select duration [minutes] >>> ")
    try:
        input_duration = float(input_duration)
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


def select_close_pct():
    input_pct = input("select % of position you wish to close [1-100] >>> ")
    try:
        input_pct = float(input_pct)
        return input_pct
    except:
        print("Error selecting %: input must be number")
        return None


def select_open_pct():
    input_pct = input("select % of USDT you wish to use [1-100] >>> ")
    try:
        input_pct = float(input_pct)
        return input_pct
    except:
        print("Error selecting %: input must be number")
        return None

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

    min_notional = None
    decimals = None
    min_qty = None
    for row in instrument_info["filters"]:
        if row["filterType"] == "NOTIONAL":
            min_notional = float(row["minNotional"])
        elif row["filterType"] == "LOT_SIZE":

            min_qty = decimal.Decimal(row["minQty"]).normalize()
            decimals = abs(min_qty.as_tuple().exponent)

    return min_notional, decimals, float(min_qty)


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
    print("\n")
    if positions:
        print("Current positions:")
        positions_df = pd.DataFrame.from_dict(positions, orient="index")
        print(positions_df.to_markdown())
    else:
        print("No open positions")
    print("\n")


# ORDER EXECUTION functions
def market_order(client, ticker, side, total_size):

    spot_positions = get_spot_balances(client)
    error = False
    if ticker is not None and side is not None and total_size is not None:
        last_price = get_last_price(client, ticker)
        min_notional, decimals, min_qty = get_instrument_info(client, ticker)

        order_amount = 10
        seconds = 15
        second_interval = seconds / order_amount

        total_coin_size = round(total_size / last_price, decimals)
        order_size = round(total_coin_size / order_amount, decimals)
        if order_size * last_price < min_notional:
            print(f"Error: order size below minimum size >>> min notional is {min_notional} usd")
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
                    loop_start = time.time()
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

                    # print(f"fast twap running >>> Buy: {round(filled_usdt_amount, decimals)} / {total_size} usd | total avg price: {avg_fill}")

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
                            msg = f"{ticker} remaining size to low >>> unfilled size: {round(remaining_size, decimals)} usd"
                            send_dis_msg(msg)
                            # print(f"remaining size to low >>> unfilled size: {round(remaining_size, decimals)} usd")
                            break

                    if spot_balances < order_size:
                        if spot_balances > min_notional:
                            order_size = spot_balances
                        else:
                            # print(f"remaining size to low >>> unfilled size: {round(spot_balances, decimals)} coins")
                            msg = f"{ticker} remaining size to low >>> unfilled size: {round(spot_balances, decimals)} coins"
                            send_dis_msg(msg)
                            break

                    loop_end = time.time()
                    if loop_end - loop_start > second_interval:
                        pass
                    else:
                        interval = second_interval - (loop_end - loop_start)
                        time.sleep(interval)

                msg = f"{ticker} market BUY order executed >>> size: {round(filled_usdt_amount)} || coins: {round(filled_coin_amount, decimals)} || avg price: {avg_fill} $ "
                send_dis_msg(msg)

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
                    loop_start = time.time()
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

                    # print(f"fast twap running >>> Sell: {round(filled_usdt_amount, decimals)} / {total_size} usd | total avg price: {avg_fill}")

                    if ticker.replace("USDT", "") in get_spot_balances(client):
                        spot_balances = float(get_spot_balances(client)[ticker.replace("USDT", "")]["coin_amount"])
                    else:
                        spot_balances = 0

                    last_price = get_last_price(client, ticker)
                    if (order_size * last_price + filled_usdt_amount) > total_size:

                        remaining_size = total_size - filled_usdt_amount
                        if remaining_size > min_notional:
                            order_size = round(remaining_size / last_price , decimals)
                        else:
                            # print(f"remaining size to low >>> unfilled size: {round(remaining_size, decimals)} usd")
                            msg = f"{ticker} remaining size to low >>> unfilled size: {round(remaining_size, decimals)} usd"
                            send_dis_msg(msg)
                            break

                    if spot_balances < order_size:
                        if spot_balances > min_notional:
                            order_size = spot_balances
                        else:
                            # print(f"remaining size to low >>> unfilled size: {round(spot_balances, decimals)} coins")
                            msg = f"{ticker} remaining size to low >>> unfilled size: {round(spot_balances, decimals)} coins"
                            send_dis_msg(msg)
                            break

                    loop_end = time.time()
                    if loop_end - loop_start > second_interval:
                        pass
                    else:
                        interval = second_interval - (loop_end - loop_start)
                        time.sleep(interval)

                msg = f"{ticker} market SELL order executed >>> size: {round(filled_usdt_amount)} $ || coins: {round(filled_coin_amount, decimals)} || avg price: {avg_fill} $ "
                send_dis_msg(msg)


def basic_twap(client, ticker, order_amount, side, total_size, twap_duration):
    """
    Basic linear: you specify, order number, position size, duration and side, position is then opened in linear fashion with same intervals and size per interval
    """

    spot_positions = get_spot_balances(client)
    error = False
    if ticker is not None and side is not None and total_size is not None:
        last_price = get_last_price(client, ticker)
        min_notional, decimals, min_qty = get_instrument_info(client, ticker)

        seconds = twap_duration * 60
        second_interval = seconds / order_amount

        total_coin_size = round(total_size / last_price, decimals)
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

                msg = f"{ticker} {side} executing >>> total usd size: {total_size} $ | {order_size} coins each: {second_interval} seconds"
                send_dis_msg(msg)

                filled_usdt_amount = 0
                filled_coin_amount = 0
                fills = []

                while filled_usdt_amount < total_size:
                    loop_start = time.time()
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

                    # print(f"twap running >>> Buy: {round(filled_usdt_amount, decimals)} / {total_size} usd | total avg price: {avg_fill}")

                    if "USDT" in get_spot_balances(client).keys():
                        spot_balances = float(get_spot_balances(client)["USDT"]["coin_amount"])
                    else:
                        spot_balances = 0

                    last_price = get_last_price(client, ticker)
                    if (order_size * last_price + filled_usdt_amount) > total_size:

                        remaining_size = total_size - filled_usdt_amount
                        if remaining_size > min_notional:
                            order_size = round(remaining_size / last_price , decimals)
                        else:
                            # print(f"remaining size to low >>> unfilled size: {round(remaining_size, decimals)} usd")
                            msg = f"{ticker} remaining size to low >>> unfilled size: {round(remaining_size, decimals)} usd"
                            send_dis_msg(msg)
                            break

                    if spot_balances < order_size:
                        if spot_balances > min_notional:
                            order_size = spot_balances
                        else:
                            # print(f"remaining size to low >>> unfilled size: {round(spot_balances, decimals)} coins")
                            msg = f"{ticker} remaining size to low >>> unfilled size: {round(spot_balances, decimals)} coins"
                            send_dis_msg(msg)
                            break

                    loop_end = time.time()
                    if loop_end - loop_start > second_interval:
                        pass
                    else:
                        interval = second_interval - (loop_end - loop_start)
                        time.sleep(interval)

                msg = f"{ticker} twap BUY order executed >>> size: {round(filled_usdt_amount)} usd || coins: {round(filled_coin_amount, decimals)} || avg price: {avg_fill} $ "
                send_dis_msg(msg)

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
                    loop_start = time.time()
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

                    # print(f"twap running >>> Sell: {round(filled_usdt_amount, decimals)} / {total_size} usd | total avg price: {avg_fill}")

                    if ticker.replace("USDT", "") in get_spot_balances(client):
                        spot_balances = float(get_spot_balances(client)[ticker.replace("USDT", "")]["coin_amount"])
                    else:
                        spot_balances = 0

                    last_price = get_last_price(client, ticker)
                    if (order_size * last_price + filled_usdt_amount) > total_size:

                        remaining_size = total_size - filled_usdt_amount
                        if remaining_size > min_notional:
                            order_size = round(remaining_size / last_price , decimals)
                        else:
                            # print(f"remaining size to low >>> unfilled size: {round(remaining_size, decimals)} usd")
                            msg = f"{ticker} remaining size to low >>> unfilled size: {round(remaining_size, decimals)} usd"
                            send_dis_msg(msg)
                            break

                    if spot_balances < order_size:
                        if spot_balances > min_notional:
                            order_size = spot_balances
                        else:
                            # print(f"remaining size to low >>> unfilled size: {round(spot_balances, decimals)} coins")
                            msg = f"{ticker} remaining size to low >>> unfilled size: {round(spot_balances, decimals)} coins"
                            send_dis_msg(msg)
                            break

                    loop_end = time.time()
                    if loop_end - loop_start > second_interval:
                        pass
                    else:
                        interval = second_interval - (loop_end - loop_start)
                        time.sleep(interval)

                msg = f"{ticker} twap SELL order executed >>> size: {round(filled_usdt_amount)} || coins: {round(filled_coin_amount, decimals)} || avg price: {avg_fill} $ "
                send_dis_msg(msg)


def close_spot_position_by_pct(client, spot_balances, ticker, close_pct ,twap_duration):
    """
    :param client:
    :param ticker: position you want to sell
    :param close_pct: % amopunt of position to close 1-100
    :param twap_duration: duration in minutes
    :return:
    """

    coin_amount = float(spot_balances[ticker.replace("USDT", "")]["coin_amount"])
    min_notional, decimals, min_qty = get_instrument_info(client, ticker)
    last_price = get_last_price(client, ticker)

    pct = close_pct / 100
    total_coin_size = round(coin_amount * pct, decimals)
    min_order_size = round(min_notional / last_price * 0.99, decimals)
    order_size = round((min_notional / last_price * 10), decimals)

    seconds = twap_duration * 60
    order_amount = round(total_coin_size / order_size)
    second_interval = seconds / order_amount

    if second_interval < 1:
        order_amount = seconds
        second_interval = 1
        order_size = round(total_coin_size / order_amount, decimals)

    if order_size * 2 > (total_coin_size * 0.99):
        order_size = round(order_size / 2, decimals)

    filled_usdt_amount = 0
    filled_coin_amount = 0
    fills = []

    if total_coin_size < order_size:
        msg = f"{ticker} twap Sell {close_pct} % - size to low, close manualy"
        send_dis_msg(msg)

    msg = f"{ticker} twap Sell {close_pct} % initiated || size: {total_coin_size} coins"
    send_dis_msg(msg)
    break_ = False
    while filled_coin_amount < total_coin_size:
        loop_start = time.time()
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
        if break_:
            break

        # print(f"twap running >>> Sell: {round(filled_usdt_amount, decimals)} / {total_size} usd | total avg price: {avg_fill}")

        if ticker.replace("USDT", "") in get_spot_balances(client):
            spot_balance = float(get_spot_balances(client)[ticker.replace("USDT", "")]["coin_amount"])
        else:
            spot_balance = 0

        if (total_coin_size - filled_coin_amount) < order_size:
            order_size = round(total_coin_size - filled_coin_amount, decimals)
            if (total_coin_size - filled_coin_amount) < min_order_size:
                break

        if (spot_balance - order_size - min_order_size) < min_order_size and spot_balance != 0:
            order_size = round(spot_balance * 0.985, decimals)
            break_ = True

        loop_end = time.time()
        if loop_end - loop_start > second_interval:
            pass
        else:
            interval = second_interval - (loop_end - loop_start)
            time.sleep(interval)

    msg = f"{ticker} twap Sell {close_pct} % >>> size: {round(filled_usdt_amount)} || coins: {round(filled_coin_amount, decimals)} || avg price: {avg_fill} $ "
    send_dis_msg(msg)


def open_spot_position_by_account_pct(client, spot_balances, ticker, open_pct ,twap_duration):
    """

    :param client:
    :param spot_balances:
    :param ticker:  ticker you want to buy
    :param close_pct: % of usdt to use for buying specific ticker
    :param twap_duration: duration in which you want to buy
    :return:
    """

    coin_amount = round(float(spot_balances["USDT"]["coin_amount"]))
    min_notional, decimals, min_qty = get_instrument_info(client, ticker)
    last_price = get_last_price(client, ticker)

    pct = open_pct / 100
    total_usdt_size = round(coin_amount * pct, decimals)
    min_order_size = round(min_notional / last_price * 0.99, decimals)

    order_size_usd = min_notional * 10
    order_size = round((min_notional / last_price * 10), decimals)

    order_amount = round((total_usdt_size / last_price) / order_size)

    seconds = twap_duration * 60
    second_interval = seconds / order_amount

    if second_interval < 1:
        order_amount = seconds
        second_interval = 1

        order_size_usd = round(total_usdt_size / order_amount,1)
        order_size = round((order_size_usd / last_price), decimals)

    if order_size * last_price * 2 > (total_usdt_size * 0.99):
        order_size = round(order_size / 2, decimals)

    filled_usdt_amount = 0
    filled_coin_amount = 0
    fills = []

    if round(total_usdt_size / last_price, decimals) < order_size:
        msg = f"{ticker} twap Buy {open_pct} % - size to low, close manualy"
        send_dis_msg(msg)

    msg = f"{ticker} twap Buy {open_pct} % initiated || size {total_usdt_size} $"
    send_dis_msg(msg)
    break_ = False
    while filled_usdt_amount < total_usdt_size:

        loop_start = time.time()

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
        if break_:
            break

        # print(f"twap running >>> Sell: {round(filled_usdt_amount, decimals)} / {total_size} usd | total avg price: {avg_fill}")

        if "USDT" in get_spot_balances(client):
            spot_balance = float(get_spot_balances(client)["USDT"]["coin_amount"])
        else:
            spot_balance = 0

        if (total_usdt_size - filled_usdt_amount) < order_size_usd:
            last_price = get_last_price(client, ticker)
            order_size = round((total_usdt_size - filled_usdt_amount) / last_price , decimals)
            if (total_usdt_size - filled_usdt_amount) < min_notional:
                break

        if (spot_balance - order_size_usd - min_notional) < min_notional:
            if spot_balance != 0:
                order_size = round(spot_balance / last_price * 0.985, decimals)
                break_ = True
            else:
                break


        loop_end = time.time()
        if loop_end - loop_start > second_interval:
            pass
        else:
            interval = second_interval - (loop_end - loop_start)
            time.sleep(interval)

    msg = f"{ticker} twap Buy {open_pct} % >>> size: {round(filled_usdt_amount)} || coins: {round(filled_coin_amount, decimals)} || avg price: {avg_fill} $ "
    send_dis_msg(msg)

