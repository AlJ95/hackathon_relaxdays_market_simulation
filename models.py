import os
import time
import pandas as pd
from api_handler import API


class Runtime:
    start_time = time.time()
    end_time = start_time

    def __init__(self, duration=24 * 60 ** 2):
        self.duration = duration

    def get_time_progress(self):
        return (time.time() - Runtime.start_time) / self.duration * 100


class Market:
    DATA_PATH = f"{os.path.dirname(__file__)}/data/{'{}'}.pickle"
    REST_IN_SEC = 5
    LAST_UPDATE = 0

    listings = pd.DataFrame([])
    supplier = pd.DataFrame([])
    tags = pd.DataFrame([])
    counter = 0
    quantile_lower, lower = 0, 0.05
    quantile_higher, higher = 9999, 0.525
    updates = {}

    @staticmethod
    def listen():
        if API.REST_TIME + API.LAST_REQUEST - time.time() < 0:
            API.LAST_REQUEST = time.time()

            updates = {"listing": API.get_all_listings(),
                       "tags": API.get_all_tags(),
                       "supplier":API.get_all_suppliers()}

            if updates != Market.updates:
                Market.counter += 1
                # print(f"Market Update: {Market.counter}")
                Market.updates = updates

                Market.listings = pd.concat([pd.DataFrame(updates["listing"]).assign(counter=Market.counter),
                                             Market.listings], ignore_index=True)\
                    .query(f'counter > {Market.counter - 300}')

                Market.tags = pd.concat([pd.DataFrame([{Market.counter, tag_data["id"], int(tag)}
                                                       for tag_data in updates["tags"]
                                                       for tag in tag_data["similar_tags"]],
                                                      columns=["counter", "id", "tag"]),
                                         Market.tags
                                         ], ignore_index=True).query(f'counter > {Market.counter - 100}')

                Market.supplier = pd.concat([pd.DataFrame(
                    [{"counter": Market.counter, "id": supplier["id"], "article_id": stock["article_id"],
                      "stock": stock["stock"], "price": stock["price"]}
                     for supplier in API.get_all_suppliers() for stock in supplier["stock"]]),
                    Market.supplier
                ], ignore_index=True).query(f'counter > {Market.counter - 100}')

                Market.quantile_lower = Market.supplier.price.quantile(Market.lower)
                Market.quantile_higher = Market.supplier.price.quantile(Market.higher)
                return True

    @staticmethod
    def get_listings(player_id=None):
        player_id = f"and player == '{player_id}'" if player_id else ""
        Market.listen()
        return Market.listings.query(f"counter=={Market.listings.counter.max()} {player_id}")

    @staticmethod
    def get_tags():
        Market.listen()
        return Market.tags.query(f"counter=={Market.tags.counter.max()}")

    @staticmethod
    def get_supplier():
        Market.listen()
        return Market.supplier.query(f"counter=={Market.supplier.counter.max()}")


class Player:

    def __init__(self, start_money):
        self.me, self.money, self.stocks, self.start_money = 9999, 9999, [], None
        self.update()
        self.start_money = self.money if not start_money else start_money

    def __repr__(self):
        return f"Robot-Player Bot-Bob {self.me} with {self.money: 8.0f}$ and " \
               f"stock-net-worth:{self.get_total_list_net_worth(): 8.0f}\n" \
               f"It buys every item from every supplier below {Market.quantile_lower}.\n" \
               f"and sells it for {Market.quantile_higher}\n"

    def update(self):
        self.me, self.money, self.stocks = API.get_self()[-1].values()
        if self.start_money:
            if self.money > self.start_money * 25:
                Market.lower, Market.higher = 0.35, 0.85
            elif self.money > self.start_money * 10:
                Market.lower, Market.higher = 0.275, 0.75
            elif self.money > self.start_money * 5:
                Market.lower, Market.higher = 0.2, 0.65

    def get_money(self):
        self.update()
        return self.money

    def buy(self, supplier_id, article_id, count, price):
        if price:
            if price < self.get_money():
                resp = API.buy(supplier_id=supplier_id, stock_id=article_id,
                               json={"count": int(count), "price_per_unit": price})
                if resp:
                    return bool(resp)
            else:
                Market.lower = max(Market.lower - 0.075, 0.1)
                Market.higher = max(Market.higher - 0.1, 0.6)

    def list_article(self, article_id, count):
        price = Market.quantile_higher

        if len(Market.get_listings().query("article==@article_id")) == 0:
            price = price * 2

        resp = API.make_listing({"article": int(article_id), "count": int(count), "price": price})
        if resp:
            print(f"List {int(count)}x {int(article_id)} at price: {price}$.")

    def get_purchasable_stock_size(self, supply_data: pd.Series, percent_of_money=0.05):
        return (self.money * percent_of_money) // supply_data.price

    def buy_cheap(self):
        supplier_data = Market.get_supplier().query(f"price <= {Market.quantile_lower} and stock > 0")

        if len(supplier_data) == 0:
            print("Nothing to buy ...")
            return False

        for index, row in supplier_data.sample(len(supplier_data),
                                               weights=1/Market.supplier.price).iterrows():
            if row.stock > 0:
                count = min(row.stock, self.get_purchasable_stock_size(row))
                print(f"Buy {count: 3.0f} Articles {row.article_id: 3.0f} from Supplier {row.id: 3.0f}"
                      f" for {row.price}$.")
                if self.buy(row.id, row.article_id, count, row.price):
                    self.money -= count * row.price
                else:
                    return True

        return True

    def get_total_list_net_worth(self):
        return Market.listings.query(f"player == {self.me} and count > 0 and counter == {Market.listings.counter.max()}") \
            .assign(total=lambda x: x.price * x["count"]).sum().total

    def set_list_price(self, listing_id, article_id, count, price, price_change):
        resp = API.put_listing(listing_id=listing_id, json={"count": count, "price": price + price_change})
        if resp:
            print(f"Reduced List Price of Article {article_id} from {price}$ to {price + price_change}$.")


if __name__ == "__main__":
    jan = Player(1000)

    for _ in range(10000):
        time.sleep(3)
        print(Market.get_listings().groupby("player").sum().price)
