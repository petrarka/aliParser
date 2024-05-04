import os
import sys
import time
import typing

from dotenv import load_dotenv
import requests as re
from dataclasses import dataclass
from bs4 import BeautifulSoup

ALI_DOMAIN = "aliexpress.ru"
WEB_ORDER_LIST = "https://aliexpress.ru/aer-jsonapi/bx/orders/v3/web-order-list?_bx-v=2.5.11"
#UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
UA = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0"
ACTIVE_TAB = "active"
ARCHIVE_TAB = "archive"
DISPUTE_TAB = "dispute"


@dataclass
class Item:
    name: str
    attrs: str
    status: str
    img: str
    q: str


def main():
    SLEEP_TIME = 0
    if len(sys.argv) > 1:
        SLEEP_TIME = int(sys.argv[1])
    PAGE_SIZE = 20
    if len(sys.argv) > 2:
        PAGE_SIZE = int(sys.argv[2])
    load_dotenv()
    xman_f = os.getenv("XMAN_F")
    xman_t = os.getenv("XMAN_T")
    x_aer_token = os.getenv("X_AER_TOKEN")
    s = re.session()
    s.cookies.set("xman_f", xman_f, domain=ALI_DOMAIN)
    s.cookies.set("xman_t", xman_t, domain=ALI_DOMAIN)
    s.cookies.set("x_aer_token", x_aer_token, domain=ALI_DOMAIN)
    s.headers.update({"User-Agent": UA})
    files = {ACTIVE_TAB: open(f"./{ACTIVE_TAB}.csv", "a"), ARCHIVE_TAB: open(f"./{ARCHIVE_TAB}.csv", "a"), DISPUTE_TAB: open(f"./{DISPUTE_TAB}.csv", "a")}
    for file in files.items():
        file[1].write("'name'\t'options'\t'status'\t'img'\t'quantity'\n")
    for mode in [ACTIVE_TAB, ARCHIVE_TAB, DISPUTE_TAB]:
        page = 1
        while True:
            time.sleep(SLEEP_TIME)
            dataRaw, next = getItems(s, mode, page, PAGE_SIZE)

            data = parseItem(s, dataRaw)
            itemsToFile(data, files[mode])
            print(f"Done: page: {page}, mode: {mode}")
            if not next: break
            page += 1
    print("All done!")
    for file in files.items():
        file[1].close()


def getItems(s: re.Session, tabType: str, page: int, pageSize: int) -> tuple:
    items = []
    resp = s.post(WEB_ORDER_LIST, json=createReqJson(tabType, page, pageSize))
    respJSON = resp.json()["data"]
    items.append(respJSON["items"])
    return items, respJSON["hasMore"]


def parseItem(s: re.Session, items: list[dict]) -> list[Item]:
    res = []
    for item in items[0]:
        for order in item["orders"]:
            name, attrs , q= getAttrsFromURL(s, order["url"]["pc"])
            imageURL = order["imageUrls"][0]
            status = order["statusInfo"]["title"].replace("\xa0", " ")  # fix nbsp
            res.append(Item(name, attrs, status, imageURL, q))
    return res


def getAttrsFromURL(s: re.Session, url: str) -> (str, str, str):
    resp = s.get(url)
    text = resp.text
    soup = BeautifulSoup(text, "html.parser")
    rootDiv = soup.find_all("div", {"class": "RedOrderDetailsProducts_Product__content__1tmn5"})[0]
    name = rootDiv.contents[0].contents[0].text  # black magic, I hope it works
    attrs = rootDiv.contents[1].text
    q = soup.find_all("div", {"class": "RedOrderDetailsProducts_Product__quantityText__1tmn5"})[0].text
    return name, attrs, q


def createReqJson(tabType: str, page: int, pageSize: int):
    return {"tabType": tabType, "page": page, "pageSize": pageSize}


def itemsToFile(items: list[Item], f: typing.IO):
    for item in items:
        f.write(f"'{item.name}'\t'{item.attrs}'\t'{item.status}'\t'{item.img}'\t'{item.q}'\n")


if __name__ == "__main__":
    main()
