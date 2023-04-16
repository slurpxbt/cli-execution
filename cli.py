import bybit_usdt_execution as bybit
import binance_spot_execution as binance_spot

def binance_cli():
    client = binance_spot.auth()
    usdt_tickers = binance_spot.get_spot_tickers(client)

    print("Connected to >> Binance SPOT")
    exit = False
    while not exit:

        print("What do you want to do:"
              "\n 1 >> display positions"
              "\n 2 >> buy/sell spot"
              "\n 0 >> exit - binance spot"
              "\n 99 >> restart client and refresh tickers")

        mode = int(input("input number >>> "))

        if mode == 0:
            exit = True
            print("Binance SPOT - closing")
        else:
            if mode == 1:
                print("\n")
                print("Current positions")
                open_positions = binance_spot.get_spot_balances(client)
                binance_spot.display_positions(open_positions)
                print("\n")
            elif mode == 2:
                print("\n")
                print("Open position mode selected")
                print("Select order type:"
                      "\n twap >> 1"
                      "\n market order >> 2")
                order_mode = int(input("input number >>> "))
                if order_mode == 1:
                    print("twap mode selected")
                    binance_spot.basic_twap(client, usdt_tickers)
                elif order_mode == 2:
                    print("market order mode selected")
                    binance_spot.market_order(client, usdt_tickers)
                print("\n")
            elif mode == 3:
                print("\n")
                print("Close position mode selected")
                print("Select order type:"
                      "\n twap >> 1"
                      "\n market order >> 2")
                order_mode = int(input("input number >>> "))
                if order_mode == 1:
                    print("twap mode selected")
                    bybit.basic_twap_close(client)
                elif order_mode == 2:
                    print("market order mode selected")
                    bybit.market_close(client)
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

    print("Connected to >> Bybit USDT perps")
    exit = False
    while not exit:

        print("What do you want to do:"
              "\n 1 >> display positions"
              "\n 2 >> open position"
              "\n 3 >> close position"
              "\n 4 >> modify positions"
              "\n 0 >> exit - bybit usdt perps"
              "\n 99 >> restart client and refresh tickers")

        mode = int(input("input number >>> "))

        if mode == 0:
            exit = True
            print("Bybit USDT perps - closing")
        else:
            if mode == 1:
                print("\n")
                print("Current positions")
                open_positions = bybit.get_open_positions(client)
                bybit.display_positions(open_positions)
                print("\n")
            elif mode == 2:
                print("\n")
                print("Open position mode selected")
                print("Select order type:"
                      "\n twap >> 1"
                      "\n market order >> 2")
                order_mode = int(input("input number >>> "))
                if order_mode == 1:
                    print("twap mode selected")
                    bybit.basic_twap(client, usdt_tickers)
                elif order_mode == 2:
                    print("market order mode selected")
                    bybit.market_order(client, usdt_tickers)
                print("\n")
            elif mode == 3:
                print("\n")
                print("Close position mode selected")
                print("Select order type:"
                      "\n twap >> 1"
                      "\n market order >> 2")
                order_mode = int(input("input number >>> "))
                if order_mode == 1:
                    print("twap mode selected")
                    bybit.basic_twap_close(client)
                elif order_mode == 2:
                    print("market order mode selected")
                    bybit.market_close(client)
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
              "\n 0 >> exit terminal")

        mode = int(input("input number >>> "))

        if mode == 0:
            exit = True
            print("Terminal closing")
        elif mode == 1:
            print("\n")
            binance_cli()
        elif mode == 2:
            print("\n")
            bybit_cli()




if __name__ == "__main__":
    main()