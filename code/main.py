#!/usr/bin/python3
from time import sleep
from selenium import webdriver

from bilibili.model import Auto

from experimental_features import LiveByArea


if __name__ == '__main__':
    # IPython >>> %run -i main.py
    ## Cache the webdriver
    if 'browser' not in locals():
        browser = webdriver.Chrome()
    # a = Auto(web_driver=browser, login=True)

    # 直播间流言
    input('Please login >>> ')
    live = LiveByArea(27)
    for url in live.urls:
        browser.get(url)
        sleep(5)
        browser.find_element_by_class_name('chat-input.border-box') \
            .send_keys('串门～今天有没有好好学习呀，一起加油')
        sleep(3)
        try:
            browser.find_element_by_class_name('txt') \
                .click()
        except:
            continue
        sleep(3)
