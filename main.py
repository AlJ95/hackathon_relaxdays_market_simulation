import time

from models import *

# TODO: Readme

def main(argv):
    jan = Player(1000)

    working_day = WorkingDay(24 * 60 ** 2)

    while Market.counter < 10:
        time.sleep(1)
        Market.listen()

    while Market.counter > 0:
        for _ in range(5):
            time.sleep(1)

            time_progress = working_day.get_time_progress()
            money_vs_net_worth = jan.get_money() / (jan.money + jan.get_total_list_net_worth()) * 100

            while not Market.listen():
                time.sleep(1)

            if money_vs_net_worth > time_progress and jan.buy_cheap():
                for stock in jan.stocks:
                    jan.list_article(stock["article_id"], stock["stock"])
                break

            if time_progress > 97.5:
                for ind, row in Market.get_listings().query(f"player == {jan.me} and count > 0").iterrows():
                    jan.set_list_price(row.id, row.article, int(row["count"]), row.price, -row.price + 10)

        print()
        print(f"{working_day.get_time_progress()}%")
        print(jan)

if __name__ == "__main__":
    while True:
        try:
            main(None)
        except Exception as e:
            print("OOOPS. Start again.")
            print(e)
            continue