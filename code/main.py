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
    browser.get('https://bilibili.com')
    input('Please login >>> ')
    live = LiveByArea(27)
    for url in live.urls:
        try:
            browser.get(url)
            sleep(5)
            texts = (
                '记得早点休息呀，早起学习效率更高哟～',
                'UP 加油呀！ ^_^',
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
