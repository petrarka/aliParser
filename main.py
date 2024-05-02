import os
import sys
import time

from dotenv import load_dotenv
import requests as re
from dataclasses import dataclass
from bs4 import BeautifulSoup

ALI_DOMAIN = "aliexpress.ru"
WEB_ORDER_LIST = "https://aliexpress.ru/aer-jsonapi/bx/orders/v3/web-order-list"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
ACTIVE_TAB = "active"
ARCHIVE_TAB = "archive"
DISPUT_TAB = "dispute"


@dataclass
class Item:
    name: str
    attrs: str
    status: str
    img: str


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
    for mode in [ACTIVE_TAB, ARCHIVE_TAB, DISPUT_TAB]:
        page = 1
        while True:
            time.sleep(SLEEP_TIME)
            dataRaw, next = getItems(s, mode, page, PAGE_SIZE)

            data = parseItem(s, dataRaw)
            itemsToFile(data, f"./{mode}.csv")
            print(f"Done: page: {page}, mode: {mode}")
            if not next: break
            page += 1
    print("All done!")


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
            name, attrs = getAttrsFromURL(s, order["url"]["pc"])
            imageURL = order["imageUrls"][0]
            status = order["statusInfo"]["title"].replace("\xa0", " ")  # fix nbsp
            res.append(Item(name, attrs, status, imageURL))
    return res


def getAttrsFromURL(s: re.Session, url: str) -> (str, str):
    resp = s.get(url)
    text = resp.text
    soup = BeautifulSoup(text, "html.parser")
    rootDiv = soup.find_all("div", {"class": "RedOrderDetailsProducts_Product__content__1tmn5"})[0]
    name = rootDiv.contents[0].contents[0].text  # black magic, I hope it works
    attrs = rootDiv.contents[1].text
    return name, attrs


def createReqJson(tabType: str, page: int, pageSize: int):
    return {"tabType": tabType, "page": page, "pageSize": pageSize}


def itemsToFile(items: list[Item], path: str):
    f = open(path, "a", encoding='utf-8')
    for item in items:
        f.write(f"'{item.name}'\t'{item.attrs}'\t'{item.status}'\t'{item.img}'\n")
    f.close()


if __name__ == "__main__":
    main()
