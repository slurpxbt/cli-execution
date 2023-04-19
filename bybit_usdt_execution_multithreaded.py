from pybit.unified_trading import HTTP
import time
import pandas as pd
import json
from pathlib import Path
from dhooks import Webhook


def load_weebhook():
    root = Path(".")
    file_path = f"{root}/webhook_config.json"

    with open(file_path) as file:
        file = file.read()
        webhook_config = json.loads(file)

        weebhook = webhook_config["bybit_exe_webhook"]

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

        api_key = credentials["bybit_api_key"]
        api_secret = credentials["bybit_secret_key"]

    return api_key, api_secret


def auth():
    api_key, api_secret = get_credentials()
    bybit_client = HTTP(testnet=False, api_key=api_key, api_secret=api_secret)

    return bybit_client


def get_usdt_balance(client):

    try:
        balances = client.get_wallet_balance(accountType="CONTRACT")["result"]["list"][0]["coin"]
        usdt_balance = None
        for balance in balances:
            if balance["coin"] == "USDT":
                usdt_balance = balance

        if usdt_balance is not None:
            total_balance = round(float(usdt_balance["equity"]))

            print(f"total usdt balance: {total_balance} USDT")

            return total_balance
    except:
        print("Error with requesting USDT balances")
        total_balance = None


        return total_balance


def get_usdt_tickers(client):

    symbols = client.get_instruments_info(category="linear")["result"]["list"]
    tickers = {}
    for row in symbols:
        symbol = row["symbol"]
        ticker = row["symbol"]
        if "USDT" in symbol:

            symbol = symbol.replace("USDT", "")

            if "10000" in symbol:
                symbol = symbol.replace("10000", "")
            elif "1000" in symbol:
                symbol = symbol.replace("1000", "")

            tickers[symbol] = ticker

    return tickers


def get_last_price(client, ticker):
    ticker_data = client.get_tickers(category="linear", symbol=ticker)["result"]["list"][0]
    last_price = float(ticker_data["lastPrice"])
    return last_price


def get_instrument_info(client, ticker):
    instrument_info = client.get_instruments_info(category="linear", symbol=ticker)["result"]["list"][0]

    min_size = float(instrument_info["lotSizeFilter"]["minOrderQty"])
    max_size = float(instrument_info["lotSizeFilter"]["maxOrderQty"])
    decimals = str(min_size)[::-1].find('.')
    # print(f"{ticker} | min: {min_size} coins | decimals: {decimals}")

    return max_size, min_size, decimals


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
    input_size = input("select position size[usdt] >>> ")
    try:
        input_size = int(input_size)
        return input_size
    except:
        print("Error selecting positions size: input must be number")
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


def select_close_id(positions):

    display_positions(positions)

    try:
        close_id = int(input("select ID of the position you wish to close >>> "))

        if close_id in positions.keys():
            position = positions[close_id]
            ticker = position["symbol"]
            side = position["side"]

            return close_id, ticker, side
    except:
        print("Error: ID must be number")


# --------------------------------------------


# ORDER/POSITION OVERVIEW FUNCTIONS
def get_open_positions(client):
    positions = client.get_positions(category="linear", settleCoin="USDT")["result"]["list"]
    open_positions = {}
    counter = 0
    for position in positions:
        size = float(position["size"])

        if size > 0:
            open_positions[counter] = position
            counter += 1

    if open_positions:
        return open_positions
    else:
        return open_positions


def display_positions(positions):

    print("\n")
    if positions:
        print("Current positions:")
        positions_df = pd.DataFrame.from_dict(positions, orient="index")
        positions_df = positions_df[["symbol", "side", "size", "positionValue", "avgPrice", "unrealisedPnl", "takeProfit", "stopLoss"]]
        print(positions_df.to_markdown())
    else:
        print("No open positions")
    print("\n")

def set_all_instruments_to_hedge_mode(usdt_tickers, client):
    for key, ticker in usdt_tickers.items():
        try:
            client.switch_position_mode(category="linear", symbol=ticker, mode=0)
        except:
            pass


# MODIFY Functions
def set_position_sl_tp(client):
    positions = get_open_positions(client=client)
    display_positions(positions)
    # print("Current positions")
    # for key, position in positions.items():
    #     print(f"id: {key} | {position['symbol']} | entry: {position['entry_price']} | side: {position['side']} | size: {position['size']} coins | pos value: {round(position['position_value'])} usd | pnl: {round(position['unrealised_pnl'])} usd")

    try:
        modify_id = int(input("select ID of the position you wish to modify >>> "))
    except:
        modify_id = None
        print("Error: ID must be number")


    try:
        print("What do you want to modify: 1=tp/sl, 2=tp, 3=sl")
        modify_type = int(input("Input the modification type you want[1, 2, 3] >>>"))
    except:
        modify_type = None
        print("Error: Modification type must me number")

    if modify_type is not None and modify_id is not None:
        if modify_id in positions.keys():

            position = positions[modify_id]
            ticker = position["symbol"]
            position_side = position["side"]

            takeProfit = position["takeProfit"]
            stopLoss = position["stopLoss"]

            last_price = get_last_price(client, ticker)
            print(f"{ticker} selected to modify")

            if position_side == "Buy":
                if modify_type == 1:
                    try:
                        new_tp_price = float(input("new TP price >>>  "))
                        if new_tp_price < last_price and new_tp_price != 0:
                            print("TP price below last price, TP won't be set/changed")
                            new_tp_price = None
                        else:
                            new_tp_price = str(new_tp_price)
                            takeProfit = new_tp_price
                    except:
                        print("TP price should be number")

                    try:
                        new_sl_price = float(input("new SL price >>>  "))

                        if new_sl_price > last_price:
                            print("SL price above last price, SL won't be set/changed")
                            new_sl_price = None
                        else:
                            new_sl_price = str(new_sl_price)
                            stopLoss = new_sl_price
                    except:
                        print("SL price should be number")

                    if new_tp_price is not None or new_sl_price is not None:
                        client.set_trading_stop(category="linear", symbol=ticker, takeProfit=takeProfit, tpTriggerBy="LastPrice",stopLoss=stopLoss, slTriggerBy="LastPrice", positionIdx=0)
                        print(f"{ticker} TP and SL modified >>> new TP: {takeProfit} | new SL: {stopLoss}")
                    else:
                        print("no modifications were made")

                elif modify_type == 2:
                    try:
                        new_tp_price = float(input("new TP price >>>  "))
                        if new_tp_price < last_price and new_tp_price != 0:
                            print("TP price below last price, TP won't be set/changed")
                            new_tp_price = None
                        else:
                            new_tp_price = str(new_tp_price)
                            takeProfit = new_tp_price
                    except:
                        print("TP price should be number")

                    if new_tp_price is not None:
                        client.set_trading_stop(category="linear", symbol=ticker, takeProfit=takeProfit, tpTriggerBy="LastPrice", stopLoss=stopLoss, slTriggerBy="LastPrice", positionIdx=0)
                        print(f"{ticker} TP modified >>> new TP: {takeProfit}")
                    else:
                        print("no modifications were made")

                elif modify_type == 3:
                    try:
                        new_sl_price = float(input("new SL price >>>  "))

                        if new_sl_price > last_price:
                            print("SL price above last price, SL won't be set/changed")
                            new_sl_price = None
                        else:
                            new_sl_price = str(new_sl_price)
                            stopLoss = new_sl_price

                    except:
                        print("SL price should be number")

                    if new_sl_price is not None:
                        client.set_trading_stop(category="linear", symbol=ticker, takeProfit=takeProfit, tpTriggerBy="LastPrice", stopLoss=stopLoss, slTriggerBy="LastPrice", positionIdx=0)
                        print(f"{ticker} SL modified >>> new TP: {stopLoss}")
                    else:
                        print("no modifications were made")

            elif position_side == "Sell":
                if modify_type == 1:
                    try:
                        new_tp_price = float(input("new TP price >>>  "))
                        if new_tp_price > last_price:
                            print("TP price above last price, TP won't be set/changed")
                            new_tp_price = None
                        else:
                            new_tp_price = str(new_tp_price)
                            takeProfit = new_tp_price
                    except:
                        print("TP price should be number")

                    try:
                        new_sl_price = float(input("new SL price >>>  "))

                        if new_sl_price < last_price and new_sl_price != 0:
                            print("SL price below last price, SL won't be set/changed")
                            new_sl_price = None
                        else:
                            new_sl_price = str(new_sl_price)
                            stopLoss = new_sl_price

                    except:
                        print("SL price should be number")

                    if new_tp_price is not None or new_sl_price is not None:
                        client.set_trading_stop(category="linear", symbol=ticker, takeProfit=takeProfit, tpTriggerBy="LastPrice", stopLoss=stopLoss, slTriggerBy="LastPrice", positionIdx=0)
                        print(f"{ticker} TP and SL modified >>> new TP: {takeProfit} | new SL: {stopLoss}")
                    else:
                        print("no modifications were made")

                elif modify_type == 2:
                    try:
                        new_tp_price = float(input("new TP price >>>  "))
                        if new_tp_price > last_price:
                            print("TP price above last price, TP won't be set/changed")
                            new_tp_price = None
                        else:
                            new_tp_price = str(new_tp_price)
                            takeProfit = new_tp_price

                    except:
                        print("TP price should be number")

                    if new_tp_price is not None:
                        client.set_trading_stop(category="linear", symbol=ticker, takeProfit=takeProfit, tpTriggerBy="LastPrice", stopLoss=stopLoss, slTriggerBy="LastPrice", positionIdx=0)
                        print(f"{ticker} TP modified >>> new TP: {takeProfit}")
                    else:
                        print("no modifications were made")

                elif modify_type == 3:
                    try:
                        new_sl_price = float(input("new SL price >>>  "))

                        if new_sl_price < last_price and new_sl_price != 0:
                            print("SL price below last price, SL won't be set/changed")
                            new_sl_price = None
                        else:
                            new_sl_price = str(new_sl_price)
                            stopLoss = new_sl_price

                    except:
                        print("SL price should be number")

                    if new_sl_price is not None:
                        client.set_trading_stop(category="linear", symbol=ticker, takeProfit=takeProfit, tpTriggerBy="LastPrice", stopLoss=stopLoss, slTriggerBy="LastPrice", positionIdx=0)
                        print(f"{ticker} SL modified >>> new TP: {stopLoss}")
                    else:
                        print("no modifications were made")

            else:
                print("ID not found in positions")


# ORDER EXECUTION functions
def market_order(client, ticker, side, position_size):
    """
    market order, it  uses short tvwap over 15seconds with 10 orders
    """

    error = False
    if ticker is not None and side is not None and position_size is not None:
        last_price = get_last_price(client=client, ticker=ticker)
        max_size, min_size, decimals = get_instrument_info(client=client, ticker=ticker)

        order_amount = 10
        seconds = 15
        second_interval = seconds / order_amount

        total_coin_size = round(position_size / last_price * 0.995, decimals)
        if total_coin_size > max_size:
            print("Error: Exceded max position size")
            error = True

        order_size = round(total_coin_size / order_amount, decimals)
        if order_size < min_size:
            print("Error: ordes size below minimum size")
            error = True

        if not error:
            # print(f"total size: {position_size} usd")
            # print(f"executing >>> {order_size} coins | each: {second_interval} seconds")
            msg = f"{ticker} {side} executing >>> {total_coin_size} coins | usd size: {position_size} $"
            send_dis_msg(msg)

            prev_position = client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]
            prev_position_side = prev_position["side"]
            if prev_position_side == "None":
                prev_size = 0
                prev_coin_size = 0
            else:
                prev_size = float(prev_position["positionValue"])
                prev_coin_size = float(prev_position["size"])

            open_size = 0
            coin_size = 0
            while open_size < position_size:

                client.place_order(category="linear", symbol=ticker, side=side, orderType="Market", qty=round(order_size, decimals), timeInForce="IOC", reduceOnly=False)

                if (side == "Buy" and prev_position_side == "Buy") or (side == "Sell" and prev_position_side == "Sell") or prev_position_side == "None":
                    position = client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]
                    open_size = float(position["positionValue"]) - prev_size
                    coin_size = float(position["size"]) - prev_coin_size

                elif prev_position_side == "Buy" and side == "Sell":
                    position = client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]
                    open_size = prev_size - float(position["positionValue"])
                    coin_size = prev_coin_size - float(position["size"])

                elif prev_position_side == "Sell" and side == "Buy":
                    position = client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]
                    open_size = abs(prev_size) - float(position["positionValue"])
                    coin_size = abs(prev_coin_size) - float(position["size"])

                # print(f"fast twap running >>> opened: {round(open_size, decimals)} / {position_size} usd | side: {side}")

                if (coin_size + order_size) > total_coin_size:
                    order_size = total_coin_size - coin_size

                    if order_size < min_size:
                        if order_size > 0:
                            # print(f"remaining size to low >>> unfilled size: {round(order_size, decimals)} coins")
                            msg = f"{ticker} remaining size to low >>> unfilled size: {round(order_size, decimals)} coins"
                            send_dis_msg(msg)
                            break
                        else:
                            break

                time.sleep(second_interval)

            # print("market order executed")
            msg = f"{ticker} market {side} executed >>> size: {round(open_size)} || coins: {coin_size} || avg price: {position['avgPrice']} $ "
            send_dis_msg(msg)


client = auth()
ticker = "BTCUSDT"
market_order(client, ticker, "Buy", 300)

def market_close(client, positions, close_id):
    """
    market close order, it uses short tvwap over 15seconds with 10 orders
    """

    if close_id in positions.keys():
        position = positions[close_id]
        ticker = position["symbol"]
        side = position["side"]
        size = float(position["size"])

        max_size, min_size, decimals = get_instrument_info(client=client, ticker=ticker)

        if side == "Buy":
            reduce_side = "Sell"
        elif side == "Sell":
            reduce_side = "Buy"

        order_amount = 10
        seconds = 15
        msg = f"{ticker} market close initiated"
        send_dis_msg(msg)

        if (size / order_amount) > min_size:
            order_size = size / order_amount
            second_interval = seconds / order_amount

            open_size = float(client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"])
            while open_size > 0:

                client.place_order(category="linear", symbol=ticker, side=reduce_side, orderType="Market", qty=round(order_size, decimals), timeInForce="IOC", reduceOnly=True)
                open_size = float(client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"])

                # print(f"fast twap running >>> size remaining: {round(open_size, decimals)} {ticker} | side: {reduce_side}")

                if (open_size - order_size) < 0:
                    order_size = open_size

                time.sleep(second_interval)

            # print("market order executed")
            msg = f"{ticker} {position['side']} market close executed"
            send_dis_msg(msg)

        else:
            # print("orders to small, order amount halved")
            msg = f"{ticker} market orders to small, order amount halved"
            send_dis_msg(msg)

            order_amount = 5
            order_size = size / order_amount
            second_interval = seconds / order_amount

            open_size = float(client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"])
            while open_size > 0:

                open_size = float(client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"])
                if open_size > 0:
                    client.place_order(category="linear", symbol=ticker, side=reduce_side, orderType="Market", qty=round(order_size, decimals), timeInForce="IOC", reduceOnly=True)
                    open_size = float(client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"])

                # print(f"fast twap running >>> size remaining: {open_size} {ticker} | side: {reduce_side}")

                if (open_size - order_size) < 0:
                    order_size = open_size

                time.sleep(second_interval)

            # print("market order executed")
            msg = f"{ticker} {position['side']} market close executed"
            send_dis_msg(msg)

    else:
        print("Error: Wrong ID selected")


def basic_twap(client, ticker, order_amount, position_size, twap_duration, side):
    """
    Basic linear: you specify, order number, position size, duration and side, position is then opened in linear fashion with same intervals and size per interval

    """

    error = False
    if ticker is not None and order_amount is not None and position_size is not None and twap_duration is not None and side is not None:
        last_price = get_last_price(client=client, ticker=ticker)
        max_size, min_size, decimals = get_instrument_info(client=client, ticker=ticker)

        seconds = twap_duration * 60
        total_coin_size = round(position_size / last_price * 0.995, decimals)
        if total_coin_size > max_size:
            print("Error: Exceded max position size")
            error = True

        order_size = round(total_coin_size / order_amount, decimals)
        if order_size < min_size:
            print("Error: ordes size below minimum size")
            error = True

        second_interval = seconds / order_amount

        if not error:
            # print(f"total size: {position_size} usd")
            # print(f"executing >>> {order_size} coins | each: {second_interval} seconds")

            msg = f"{ticker} {side} executing >>> total usd size: {position_size} $ | {order_size} coins each: {second_interval} seconds"
            send_dis_msg(msg)

            prev_position = client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]
            prev_position_side = prev_position["side"]
            if prev_position_side == "None":
                prev_size = 0
                prev_coin_size = 0
            else:
                prev_size = float(prev_position["positionValue"])
                prev_coin_size = float(prev_position["size"])

            open_size = 0
            coin_size = 0
            while open_size < position_size:

                client.place_order(category="linear", symbol=ticker, side=side, orderType="Market", qty=round(order_size, decimals), timeInForce="IOC", reduceOnly=False)

                if (side == "Buy" and prev_position_side == "Buy") or (side == "Sell" and prev_position_side == "Sell") or prev_position_side == "None":
                    position = client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]
                    open_size = float(position["positionValue"]) - prev_size
                    coin_size = float(position["size"]) - prev_coin_size

                elif prev_position_side == "Buy" and side == "Sell":
                    position = client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]
                    open_size = prev_size - float(position["positionValue"])
                    coin_size = prev_coin_size - float(position["size"])

                elif prev_position_side == "Sell" and side == "Buy":
                    position = client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]
                    open_size = abs(prev_size) - float(position["positionValue"])
                    coin_size = abs(prev_coin_size) - float(position["size"])

                # print(f"twap running >>> opened: {round(open_size, decimals)} / {position_size} usd | side: {side}")

                if (coin_size + order_size) > total_coin_size:
                    order_size = total_coin_size - coin_size

                    if order_size < min_size:
                        if order_size > 0:
                            # print(f"remaining size to low >>> unfilled size: {round(order_size, decimals)}  coins")
                            msg = f"{ticker} remaining size to low >>> unfilled size: {round(order_size, decimals)} coins"
                            send_dis_msg(msg)
                            break
                        else:
                            break

                time.sleep(second_interval)

            # print("twap finished")
            msg = f"{ticker} twap {side} executed >>> size: {round(open_size)} || coins: {coin_size} || avg price: {position['avgPrice']} $ "
            send_dis_msg(msg)


def basic_twap_close(client, positions, close_id, order_amount, twap_duration):
    """
       Basic linear close: you specify, order number, duration and side, position is then opened in linear fashion with same intervals and size per interval

    """
    if close_id in positions.keys():
        position = positions[close_id]
        ticker = position["symbol"]
        side = position["side"]
        size = float(position["size"])

        # print(f"{ticker} position selected to close")
        max_size, min_size, decimals = get_instrument_info(client=client, ticker=ticker)
        seconds = twap_duration * 60

        if side == "Buy":
            reduce_side = "Sell"
        elif side == "Sell":
            reduce_side = "Buy"

        error = False
        if order_amount is not None and twap_duration is not None:

            order_size = size / order_amount
            second_interval = seconds / order_amount

            if order_size < min_size:
                print("Error: orde size below minimum size")
                error = True

            if not error:
                msg = f"{ticker} twap close initiated"
                send_dis_msg(msg)

                open_size = float(client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"])
                while open_size > 0:

                    open_size = float(client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"])
                    if open_size > 0:
                        client.place_order(category="linear", symbol=ticker, side=reduce_side, orderType="Market", qty=round(order_size, decimals), timeInForce="IOC", reduceOnly=True)
                        open_size = float(client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"])

                    # print(f"fast twap running >>> size remaining: {round(open_size, decimals)} {ticker} | side: {reduce_side}")

                    if (open_size - order_size) < 0:
                        order_size = open_size

                    time.sleep(second_interval)

                # print("twap finished")
                msg = f"{ticker} {position['side']} twap close executed "
                send_dis_msg(msg)

    else:
        print("Error: Wrong ID selected")
# --------------------------------------------




