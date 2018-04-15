# encoding=utf-8

import base64
import requests
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging
from yumdama import identify
import json
import urllib, urllib2, cookielib

reload(sys)
sys.setdefaultencoding('utf8')
IDENTIFY = 1  # 验证码输入方式:        1:看截图aa.png，手动输入     2:云打码
COOKIE_GETWAY = 0 # 0 代表从https://passport.weibo.cn/sso/login 获取cookie   # 1 代表从https://weibo.cn/login/获取Cookie
dcap = dict(DesiredCapabilities.PHANTOMJS)  # PhantomJS需要使用老版手机的user-agent，不然验证码会无法通过
dcap["phantomjs.page.settings.userAgent"] = (
    "Mozilla/5.0 (Linux; U; Android 2.3.6; en-us; Nexus S Build/GRK39F) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1"
)
logger = logging.getLogger(__name__)
logging.getLogger("selenium").setLevel(logging.WARNING)  # 将selenium的日志级别设成WARNING，太烦人


"""
输入你的微博账号和密码，可去小号商场够买。http://www.xiaohao.shop/Home/CatGood/index/cat/5.html
建议买几十个，微博限制的严，太频繁了会出现302转移。
或者你也可以把时间间隔调大点。
"""
myWeiBo = [
    {'no': '13889845930', 'psw': '15510035701'}
]

def getCookie(account, password):
    if COOKIE_GETWAY == 0:
        return SinaWeibo_GetCookies(account,password)
    elif COOKIE_GETWAY ==1:
        return get_cookie_from_weibo_cn(account, password)
    else:
        logger.error("COOKIE_GETWAY Error!")

def SinaWeibo_GetCookies( username, password):
    sso_url = "https://passport.weibo.cn/sso/login"
    login_data = urllib.urlencode([
        ('username', username),
        ('password', password),
        ('entry', 'mweibo'),
        ('client_id', ''),
        ('savestate', '1'),
        ('ec', ''),
    ])

    req = urllib2.Request(sso_url)
    req.add_header('Origin', 'https://passport.weibo.cn')
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/10.0.601.0 Safari/534.14')
    req.add_header('Referer', 'https://passport.weibo.cn/signin/login?entry=mweibo&res=wel&wm=3349&r=http%3A%2F%2Fm.weibo.cn%2F')
    weibo_cookies = cookielib.CookieJar()

    handler = urllib2.HTTPCookieProcessor(weibo_cookies)
    opener = urllib2.build_opener(handler)
    opener.open(req, data=login_data)
    cookie = dict()
    if weibo_cookies._cookies.__contains__(".weibo.cn"):
        logging.info("获取密码成功："+str(username))
        weibo_cn_cookiejar = weibo_cookies._cookies[".weibo.cn"]["/"]
        cookie['SCF'] = weibo_cn_cookiejar['SCF'].value
        cookie['SSOLoginState'] = weibo_cn_cookiejar['SSOLoginState'].value
        cookie['SUB'] = weibo_cn_cookiejar['SUB'].value
        cookie['SUHB'] = weibo_cn_cookiejar['SUHB'].value
    else:
        logger.info("获取账号:"+str(username)+" 的cookie失败，原因：1. 账号或密码错误。 2. 微博登录次数过多，可以换网络登录或过4小时再登录！")
    return cookie


def get_cookie_from_weibo_cn(account, password):
    """ 获取一个账号的Cookie """
    try:
        browser = webdriver.PhantomJS(desired_capabilities=dcap)
        browser.get("https://weibo.cn/login/")
        time.sleep(1)

        failure = 0
        while "微博" in browser.title and failure < 5:
            failure += 1
            browser.save_screenshot("aa.png")
            username = browser.find_element_by_name("mobile")
            username.clear()
            username.send_keys(account)

            psd = browser.find_element_by_xpath('//input[@type="password"]')
            psd.clear()
            psd.send_keys(password)
            try:
                code = browser.find_element_by_name("code")
                code.clear()
                if IDENTIFY == 1:
                    code_txt = raw_input("请查看路径下新生成的aa.png，然后输入验证码:")  # 手动输入验证码
                else:
                    from PIL import Image
                    img = browser.find_element_by_xpath('//form[@method="post"]/div/img[@alt="请打开图片显示"]')
                    x = img.location["x"]
                    y = img.location["y"]
                    im = Image.open("aa.png")
                    im.crop((x, y, 100 + x, y + 22)).save("ab.png")  # 剪切出验证码
                    code_txt = identify()  # 验证码打码平台识别
                code.send_keys(code_txt)
            except Exception, e:
                pass

            commit = browser.find_element_by_name("submit")
            commit.click()
            time.sleep(3)
            if "我的首页" not in browser.title:
                time.sleep(4)
            if '未激活微博' in browser.page_source:
                print '账号未开通微博'
                return {}

        cookie = {}
        if "我的首页" in browser.title:
            for elem in browser.get_cookies():
                cookie[elem["name"]] = elem["value"]
            logger.warning("Get Cookie Success!( Account:%s )" % account)
        return json.dumps(cookie)
    except Exception, e:
        logger.warning("Failed %s!" % account)
        return ""
    finally:
        try:
            browser.quit()
        except Exception, e:
            pass



def getCookies(weibo):
    """ 获取Cookies """
    cookies = []
    for elem in weibo:
        account = elem['no']
        password = elem['psw']
        cookie  =  getCookie(account, password)
        if cookie!=None and len(cookie.keys())!=0:
            cookies.append(cookie)
    if len(cookie)==0:
        logger.info("没有cookie可以使用，爬虫系统将退出！")
        sys.exit(0)
    return cookies

cookies = getCookies(myWeiBo)
logger.warning("Get Cookies Finish!( Num:%d)" % len(cookies))
