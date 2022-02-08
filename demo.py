'''
Auther: littleherozzzx
Date: 2022-01-13 16:48:51
LastEditTime: 2022-01-15 22:03:06
'''
import base64
import logging
import time

import requests
import rsa
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)


class hdu_jwc:
    def __init__(self, username, password) -> None:
        self.username = username
        self.password = password
        self.url = "http://newjw.hdu.edu.cn/jwglxt"
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Content-Length": "477",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": "",
            "Host": "newjw.hdu.edu.cn",
            "Origin": "http://newjw.hdu.edu.cn",
            "Referer": "http://newjw.hdu.edu.cn/jwglxt/xtgl/login_slogin.html",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0"
        }
        self.cookies = ""
        self.modulus = ""
        self.exponent = ""
        self.pub_key = None
        self.csrftoken = ""
        self.session = requests.Session()
        self.xuanke = ""
        self.index = ""

    def set_pubKey(self):
        try:
            response = self.session.get(
                url=self.url + "/xtgl/login_getPublicKey.html?time={}".format(round(time.time() * 1000)))
            data = response.json()
            self.modulus = base64.b64decode(data["modulus"])
            self.exponent = base64.b64decode(data["exponent"])
            self.pub_key = rsa.PublicKey(int.from_bytes(
                self.modulus, 'big'), int.from_bytes(self.exponent, 'big'))
            logging.info("set pubKey success!")
        except requests.exceptions.JSONDecodeError:
            raise ConnectionError("connect failed")

    def encoded(self, s):
        encoded_pwd = rsa.encrypt(s, self.pub_key)
        return base64.b64encode(encoded_pwd)

    def set_csrftoken(self):
        response = self.session.get(
            url=self.url + "/xtgl/login_slogin.html?language=zh_CN&_t={}".format(round(time.time() * 1000)))
        self.headers["Cookie"] = "JSESSIONID={}; route={}".format(
            self.session.cookies["JSESSIONID"], self.session.cookies["route"])
        # self.headers["Cookie"]=self.session.cookies
        page = BeautifulSoup(response.text)
        self.cookies = response.cookies
        self.csrftoken = page.find("input", attrs={"id": "csrftoken"})["value"]
        logging.info("set csrftoken success!")

    def login(self):
        encoded_password = self.encoded(self.password).decode("utf-8")
        params = {
            "csrftoken": self.csrftoken,
            "language": "zh_CN",
            "yhm": self.username,
            "mm": [encoded_password, encoded_password]}
        try:
            response = self.session.post(url=self.url + "/xtgl/login_slogin.html?time={}".format(round(
                time.time() * 1000)), headers=self.headers, data=params, cookies=self.session.cookies,
                                         allow_redirects=False)
            self.cookies = response.cookies
            raise ConnectionError("connect failed!")
        except ConnectionError as error:
            logging.error(error)
            raise error
        try:
            if response.status_code == 302:
                self.index = self.session.get(url=response.headers["Location"])
                if self.username in self.index.text:
                    logging.info("login success")
                else:
                    raise RuntimeError("unknown error!")
            else:
                if "不正确" in response.text:
                    raise ValueError("username or password error!")
        except ValueError as error:
            logging.error("current username is {}, current password is {}".format(self.username, self.password))
            logging.error(error)
            raise error
        except RuntimeError as error:
            logging.error("current username is {}, current password is {}".format(self.username, self.password))
            logging.error(error)
            raise error
        return

    def login_course_selection(self):
        self.login()
        page = BeautifulSoup(self.index.text)
        link = page.find('a', text="自主选课")
        if len(link) == 0:
            logging.error("enter xuanke failed!")
        else:
            link = link["onclick"].split("\'")
            gndm = link[1]
            url = self.url + link[3]
            params = {"gnmkdm": "index", "su": self.username, "layout": "default"}
            data = {"gndm": gndm}
            response = self.session.get(url=url, data=data, params=params)
            return response

    def logout(self):
        pass

    def query_margin(self, jxb_id, rwlx="1", index=0):
        data1 = \
            {
                "filter_list": [jxb_id],
                "rwlx": str(rwlx),
                "xkly": "0",
                "bklx_id": "0",
                "sfkkjyxdxnxq": "0",
                "xqh_id": "1",
                "jg_id": "05",
                "njdm_id_1": "2020",
                "zyh_id_1": "0523",
                "zyh_id": "0523",
                "zyfx_id": "wfx",
                "njdm_id": "2020",
                "bh_id": "20052312",
                "xbm": "1",
                "xslbdm": "7",
                "ccdm": "8",
                "xsbj": "4294967296",
                "sfkknj": "1",
                "sfkkzy": "1",
                "kzybkxy": "0",
                "sfznkx": "0",
                "zdkxms": "0",
                "sfkxq": "0",
                "sfkcfx": "0",
                "kkbk": "0",
                "kkbkdj": "0",
                "sfkgbcx": "1",
                "sfrxtgkcxd": "1",
                "tykczgxdcs": "1",
                "xkxnm": "2021",
                "xkxqm": "12",
                "kklxdm": "01",
                "rlkz": "0",
                "xkzgbj": "0",
                "kspage": "1",
                "jspage": "10",
                "jxbzb": ""
            }
        data2 = \
            {
                "filter_list": [jxb_id],
                "rwlx": str(rwlx),
                "xkly": "0",
                "bklx_id": "0",
                "sfkkjyxdxnxq": "0",
                "xqh_id": "1",
                "jg_id": "05",
                "zyh_id": "0523",
                "zyfx_id": "wfx",
                "njdm_id": "2020",
                "bh_id": "20052312",
                "xbm": "1",
                "xslbdm": "7",
                "ccdm": "8",
                "xsbj": "4294967296",
                "sfkknj": "1",
                "sfkkzy": "1",
                "kzybkxy": "0",
                "sfznkx": "0",
                "zdkxms": "0",
                "sfkxq": "0",
                "sfkcfx": "0",
                "kkbk": "0",
                "kkbkdj": "0",
                "xkxnm": "2021",
                "xkxqm": "12",
                "xkxskcgskg": "0",
                "rlkz": "0",
                "kklxdm": "01",
                "kch_id": jxb_id,
                "jxbzcxskg": "0",
                "xkkz_id": "D3CA48E77A1A4CD8E0536164A8C05380",
                "cxbj": "0",
                "fxbj": "0"
            }
        params = {"gnmkdm": "N253512", "su": self.username}
        res1 = \
            self.session.post(url="http://newjw.hdu.edu.cn/jwglxt/xsxk/zzxkyzb_cxZzxkYzbPartDisplay.html", data=data1,
                              params=params).json()["tmpList"]
        res2 = self.session.post(url="http://newjw.hdu.edu.cn/jwglxt/xsxk/zzxkyzbjk_cxJxbWithKchZzxkYzb.html",
                                 data=data2, params=params).json()
        return [res1[index], res2[index]]

    def qiangke(self, jxb_id, rwlx=1, index=0, interval=1, times=1000):

        res = self.query_margin(jxb_id, rwlx, index)
        res1 = res[0]
        res2 = res[1]
        data = {
            "jxb_ids": res2["do_jxb_id"],
            "kch_id": res1["kch_id"],
            "kcmc": res1["kcmc"],  # not same completely
            "rwlx": str(rwlx),
            "rlkz": "0",
            "rlzlkz": "1",
            "sxbj": "1",
            "xxkbj": res1["xxkbj"],
            "qz": "0",
            "cxbj": res1["cxbj"],
            "xkkz_id": "D3CA48E77A1A4CD8E0536164A8C05380",
            "njdm_id": "2020",
            "zyh_id": "0523",
            "kklxdm": '01'
        }
        params = {"gnmkdm": "N253512", "su": self.username}
        res = {"flag": 0}
        for cnt in range(times):
            res = self.session.post(url="http://newjw.hdu.edu.cn/jwglxt/xsxk/zzxkyzbjk_xkBcZyZzxkYzb.html", data=data,
                                    params=params).json()
            logging.info("cnt={}: ".format(cnt) + str(res))
            cnt = cnt + 1
            time.sleep(interval)
        return res


if __name__ == "__main__":
    exit_flag = False
    while exit_flag == False:
        username = input("input your username:\n")
        password = bytes(input("input your password:\n"), encoding="utf-8")
        ex = hdu_jwc(username, password)
        try:
            ex.set_pubKey()
            ex.get_csrftoken()
            ex.login()
            ex.login_course_selection()
        except ValueError as error:
            print("username or password error, please check them and try again")
            print("=" * 100)
        except ConnectionError:
            print("connect fail, please try later")
            print("=" * 100)
            exit_flag = True
