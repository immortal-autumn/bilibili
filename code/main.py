#!/usr/bin/python3
from time import sleep
from selenium import webdriver

from bilibili.auto import tests

Auto = tests.Auto

from experimental_features import LiveByArea


if __name__ == '__main__':
    # IPython >>> %run -i main.py
    ## Cache the webdriver
    if 'browser' not in locals():
        browser = webdriver.Chrome()
    else:
        exit(0)
    # a = Auto(web_driver=browser, login=True)

    # 直播间留言
    browser.get('https://bilibili.com')
    input('Please login >>> ')
    live = LiveByArea(27)
    urls = dict()
    for url in live.urls:
        if url in urls:
            continue
        else:
            urls[url] = None
        try:
            browser.get(url)
            sleep(5)
            texts = (
                    '晚上记得按时吃饭呀，休息一下吧～',
            )
            for text in texts:
                browser.find_element_by_class_name('chat-input.border-box') \
                    .send_keys(text)
                sleep(3)
                browser.find_element_by_class_name('txt') \
                    .click()
        except:
            continue
        sleep(3)
