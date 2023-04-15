import bybit_usdt_execution as bybit




def main():

    client = bybit.auth()
    usdt_tickers = bybit.get_usdt_tickers(client)

    exit = False
    while not exit:

        print("What do you want to do:"
              "\n 1 >> display positions"
              "\n 2 >> open position"
              "\n 3 >> close position"
              "\n 4 >> modify positions"
              "\n 0 >> exit"
              "\n 99 >> restart client and refresh tickers")

        mode = int(input("input number >>> "))

        if mode == 0:
            exit = True
            print("Terminal closing")
        else:
            if mode == 1:
                print("Current positions")
                open_positions = bybit.get_open_positions(client)
                bybit.display_positions(open_positions)
            elif mode == 2:
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
            elif mode == 3:
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
            elif mode == 4:
                print("Modify mode selected")
                bybit.set_position_sl_tp(client)
            elif mode == 99:
                print("Reconnecting client and refreshing tickers")
                client = bybit.auth()
                usdt_tickers = bybit.get_usdt_tickers(client)


if __name__ == "__main__":
    main()