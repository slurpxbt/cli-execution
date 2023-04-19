import threading

import bybit_usdt_execution_multithreaded as bybit
import binance_spot_execution_multithreaded as binance_spot
from threading import Thread


def get_all_running_threads():
    if len(threading.enumerate()) == 1:
        print("No running proceses")
    else:
        print("Current running processes:")
        for thread in threading.enumerate():
            if thread.name != "MainThread":
                print(thread.name)

def binance_cli():
    client = binance_spot.auth()
    usdt_tickers = binance_spot.get_spot_tickers(client)

    connection_name = "Binance_SPOT"

    print("Connected to >> Binance SPOT")
    exit = False
    while not exit:

        print("What do you want to do:"
              "\n 1 >> display positions"
              "\n 2 >> buy/sell spot"
              "\n 0 >> exit - binance spot"
              "\n 99 >> restart client and refresh tickers"
              "\n 999 >> check current running processes")

        mode = int(input("input number >>> "))
        if mode == 0:
            exit = True
            print("Binance SPOT - closing")
        elif mode == 999:
            print("\n")
            get_all_running_threads()
            print("\n")
        elif mode == 1:
            open_positions = binance_spot.get_spot_balances(client)
            binance_spot.display_positions(open_positions)
        elif mode == 2:
            print("\n")
            print("Open position mode selected")
            print("Select order type:"
                  "\n 1 >> twap"
                  "\n 2 >> market order"
                  "\n 3 >> buy/sell by account/position %")
            order_mode = int(input("input number >>> "))
            if order_mode == 1:
                print("\n")
                print("twap mode selected")

                ticker = binance_spot.select_ticker(usdt_tickers)
                order_amount = binance_spot.select_order_amount()  # number or orders
                side = binance_spot.select_side()  # buy/sell
                total_size = binance_spot.select_usdt_size()  # usd amount
                twap_duration = binance_spot.select_duration()  # minutes

                twap_thread = Thread(target=binance_spot.basic_twap, args=(client, ticker, order_amount, side ,total_size, twap_duration ), name=f"{connection_name}_{ticker}_{side}_{total_size}_twap{twap_duration}min").start()

            elif order_mode == 2:
                print("\n")
                print("market order mode selected")

                ticker = binance_spot.select_ticker(usdt_tickers)
                side = binance_spot.select_side()  # buy/sell
                total_size = binance_spot.select_usdt_size()  # usd amount  (client, ticker:str, side:str, total_size:float)

                market_order_thread = Thread(target=binance_spot.market_order, args=(client, ticker, side, total_size), name=f"{connection_name}_{ticker}_{side}_{total_size}_market").start()

            elif order_mode == 3:
                print("\n")
                print("buy/sell by account/position % selected")
                side = binance_spot.select_side()  # buy/sell
                if side == "Buy":
                    ticker = binance_spot.select_ticker(usdt_tickers)
                    spot_balances = binance_spot.get_spot_balances(client)
                    if "USDT" in spot_balances.keys():
                        open_pct = binance_spot.select_open_pct()
                        twap_duration = binance_spot.select_duration()

                        open_by_pct_thread = Thread(target=binance_spot.open_spot_position_by_account_pct, args=(client, spot_balances, ticker, open_pct, twap_duration), name=f"{connection_name}_{ticker}_{side}_{open_pct}pct_{twap_duration}min_twap").start()
                    else:
                        print(f"No USDT available for Buying {ticker}")

                elif side == "Sell":
                    ticker = binance_spot.select_ticker(usdt_tickers)
                    spot_balances = binance_spot.get_spot_balances(client)
                    if ticker.replace("USDT", "") in spot_balances.keys():

                        close_pct = binance_spot.select_close_pct()
                        twap_duration = binance_spot.select_duration()

                        close_by_pct_thread = Thread(target=binance_spot.close_spot_position_by_pct, args=(client, spot_balances, ticker, close_pct, twap_duration), name=f"{connection_name}_{ticker}_{side}_{close_pct}pct_{twap_duration}min_twap").start()
                    else:
                        print(f"No coins available to sell for {ticker}")


            print("\n")
        elif mode == 99:
            print("\n")
            print("Reconnecting client and refreshing tickers")
            client = binance_spot.auth()
            usdt_tickers = binance_spot.get_spot_tickers(client)
            print("\n")


def bybit_cli():
    client = bybit.auth()
    usdt_tickers = bybit.get_usdt_tickers(client)

    connection_name = "Bybit_USDT_PERPS"

    print("Connected to >> Bybit USDT perps")
    exit = False
    while not exit:

        print("What do you want to do:"
              "\n 1 >> display positions"
              "\n 2 >> open position"
              "\n 3 >> close position"
              "\n 4 >> modify positions"
              "\n 0 >> exit - bybit usdt perps"
              "\n 99 >> restart client and refresh tickers"
              "\n 999 >> check current running processes")

        mode = int(input("input number >>> "))

        if mode == 0:
            exit = True
            print("Bybit USDT perps - closing")
        elif mode == 999:
            print("\n")
            get_all_running_threads()
            print("\n")
        elif mode == 1:
            open_positions = bybit.get_open_positions(client)
            bybit.display_positions(open_positions)
        elif mode == 2:
            print("\n")
            print("Open position mode selected")
            print("Select order type:"
                  "\n 1 >> twap"
                  "\n 2 >> market order")
            order_mode = int(input("input number >>> "))
            if order_mode == 1:
                print("twap mode selected")

                ticker = bybit.select_ticker(usdt_tickers)
                order_amount = bybit.select_order_amount()  # number or orders
                position_size = bybit.select_usdt_size()  # usd amount
                twap_duration = bybit.select_duration()  # minutes
                side = bybit.select_side()  # buy/sell

                twap_thread = Thread(target=bybit.basic_twap, args=(client, ticker, order_amount, position_size, twap_duration, side), name=f"{connection_name}_{ticker}_{side}_{position_size}_twap{twap_duration}min").start()

            elif order_mode == 2:
                print("market order mode selected")

                ticker = bybit.select_ticker(usdt_tickers)
                side = bybit.select_side()  # buy/sell
                position_size = bybit.select_usdt_size()  # usd amount

                market_order_thread = Thread(target=bybit.market_order, args=(client, ticker, side, position_size), name=f"{connection_name}_{ticker}_{side}_{position_size}_market").start()

            print("\n")
        elif mode == 3:
            print("\n")
            print("Close position mode selected")
            print("Select order type:"
                  "\n 1 >> twap"
                  "\n 2 >> market order")
            order_mode = int(input("input number >>> "))
            if order_mode == 1:
                print("twap mode selected")

                positions = bybit.get_open_positions(client=client)
                close_id, ticker, side = bybit.select_close_id(positions=positions)
                order_amount = bybit.select_order_amount()  # number or orders
                twap_duration = bybit.select_duration()  # minutes  (client, positions, close_id, order_amount:int, twap_duration:int)

                twap_close_thread = Thread(target=bybit.basic_twap_close, args=(client, positions, close_id, order_amount, twap_duration), name=f"{connection_name}_CLOSE_{ticker}_{side}_twap{twap_duration}min").start()


            elif order_mode == 2:
                print("market order mode selected")

                positions = bybit.get_open_positions(client=client)
                close_id, ticker, side = bybit.select_close_id(positions=positions)

                market_close_thread = Thread(target=bybit.market_close, args=(client, positions, close_id), name=f"{connection_name}_CLOSE_{ticker}_{side}_market").start()

            print("\n")
        elif mode == 4:
            print("\n")
            print("Modify mode selected")
            bybit.set_position_sl_tp(client)
            print("\n")
        elif mode == 99:
            print("Reconnecting client and refreshing tickers")
            client = bybit.auth()
            usdt_tickers = bybit.get_usdt_tickers(client)
            print("\n")


def main():

    exit = False
    while not exit:
        print("\n")
        print("Select exchange:"
              "\n 1 >> Binance SPOT"
              "\n 2 >> Bybit USDT perps"
              "\n 999 >> check current running processes"
              "\n 0 >> exit terminal")

        mode = int(input("input number >>> "))

        if mode == 0:
            exit = True
            print("\n")
            print("Terminal closing")
        elif mode == 999:
            print("\n")
            get_all_running_threads()
            print("\n")
        elif mode == 1:
            print("\n")
            binance_cli()
        elif mode == 2:
            print("\n")
            bybit_cli()




if __name__ == "__main__":
    main()