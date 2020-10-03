from selenium import webdriver
import os
from selenium.webdriver.support.wait import WebDriverWait
import time
import datetime
import csv
import random
import requests
def sava_text(text):
    dt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open("error.log", "a+", newline="") as f:
        f.write(str(text) + "\n"+str(dt))

class NoSuchElementException(Exception):
    def __init__(self,message="元素异常",args=("元素未找到",)):
        self.args = args
        self.message = message

def get_user():
    user = []
    with open("user-os.csv") as f:
        reder = csv.reader(f)
        for u in reder:
            user.append(u)
    user_x = random.randint(1,92)
    return user[user_x]

def proiexes():
    try:
        # driver = webdriver.PhantomJS("C:/Users/Administrator/Desktop/phantomjs-2.1.1-windows/bin/phantomjs.exe")
        username = "20181885"
        userpassword = "Ljl2326645"
        driver = webdriver.Chrome()
        driver.get("http://vpn.shiep.edu.cn/")
        driver.find_element_by_id("svpn_name").send_keys(username)
        driver.find_element_by_id("svpn_password").send_keys(userpassword)
        driver.find_element_by_id("logButton").click()
        wait = WebDriverWait(driver, 100, 1)
        state = wait.until(lambda diver:driver.find_elements_by_class_name("aline"))
        time.sleep(4)
        driver.quit()
        print(state)
        return True
    except NoSuchElementException as e:
        print(e)
    except Exception as e:
        if "Unable to locate element" in str(e):
            print("已经连接上")
            return False
        print(e)
    finally:
        driver.quit()


def quit_url():
    os.system('TASKKILL /F /IM SangforCSClient.exe /T')

if __name__ == '__main__':
    proiexes()
    # while True:
    #     try:
    #         url = "http://jw.shiep.edu.cn/eams/home.action"
    #         requests.get(url,timeout=3)
    #     except requests.exceptions.ConnectionError:
    #         now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #         print("连接中...",now_time)
    #         proiexes()
    #     except Exception as e:
    #         print(e)
    #     time.sleep(5)
    # quit_url()


