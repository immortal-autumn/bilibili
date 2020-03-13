#!/usr/bin/python3
from selenium import webdriver

from bilibili.model import Auto


if __name__ == '__main__':
    # IPython >>> %run -i main.py
    ## Cache the webdriver
    if 'browser' not in locals():
        browser = webdriver.Chrome()
    a = Auto(web_driver=browser, login=True)
