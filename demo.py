'''
Auther: littleherozzzx
Date: 2022-01-13 16:48:51
LastEditTime: 2022-03-08 12:42:39
'''
import base64
import json
import logging
import os.path
import sys
import threading
import time
import pandas as pd
import requests
import rsa
import yaml
from getpass4 import getpass
from bs4 import BeautifulSoup

import config

logging.basicConfig(level=logging.INFO)


class hdu_jwc:
    def __init__(self) -> None:
        self.username = ""
        self.password = ""
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
        self.session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0"
        self.session.trust_env = False
        self.xuanke = ""
        self.index = ""
        self.class_list = []
        self.dict = {
            "01": "E0BE1EB065FBFA29E0536264A8C04A31",
            "10": "E0BDC4C7604BD44BE0536264A8C0B7EC",
            "05": "E0BE43551AEB415FE0536164A8C06426",
        }
        self.cfg = config.Cfg()

    def load_cfg(self, cfg_file):
        try:
            if self.cfg.load_cfg(cfg_file) == 1:
                logging.info("配置文件加载成功！")
                return 1
        except FileNotFoundError:
            logging.error(f"配置文件加载失败！文件{cfg_file}不存在！")
            logging.info("请重新生成配置文件。")
            return 0
        except ValueError as error:
            logging.error("配置文件加载失败！")
            logging.error(error)
            logging.info("请重新生成配置文件。")
            return 0
        except KeyError as error:
            logging.error("配置文件加载失败！")
            logging.error(error)
            logging.info("请重新生成配置文件。")
            return 0

    def init_cfg(self):
        page_file = input("请输入网页文件路径（网页文件获取方式请查看readme）:\n")
        while (not os.path.exists(page_file)):
            page_file = input("文件不存在，请重新输入！")
        try:
            if self.cfg.init_cfg(page_file) == 1:
                print("配置文件生成成功！")
                return 1
        except KeyError as error:
            logging.error("配置文件生成失败！")
            logging.error(error)
            logging.info("请按照readme中要求获取网页文件，或手动在config.json中添加缺失项。")

    def set_pubKey(self):
        try:
            response = self.session.get(
                url=self.url + "/xtgl/login_getPublicKey.html?time={}".format(round(time.time() * 1000)))
            data = response.json()
            self.modulus = base64.b64decode(data["modulus"])
            self.exponent = base64.b64decode(data["exponent"])
            self.pub_key = rsa.PublicKey(int.from_bytes(
                self.modulus, 'big'), int.from_bytes(self.exponent, 'big'))
            logging.info("公钥设置成功!")
        except json.decoder.JSONDecodeError:
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
        page = BeautifulSoup(response.text, features="html.parser")
        self.cookies = response.cookies
        self.csrftoken = page.find("input", attrs={"id": "csrftoken"})["value"]
        logging.info("csrftoken设置成功!")

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
        except requests.exceptions.ConnectionError as error:
            logging.error(error)
            raise error
        try:
            if response.status_code == 302:
                self.index = self.session.get(url=response.headers["Location"])
                if self.username in self.index.text:
                    logging.info("登录成功")
                else:
                    raise RuntimeError("unknown error!")
            else:
                if "不正确" in response.text:
                    raise ValueError("学号或密码错误!")
        except ValueError as error:
            logging.error("当前学号为 {}, 当前密码为 {}".format(self.username, self.password))
            logging.error(error)
            raise error
        except RuntimeError as error:
            logging.error("当前学号为 {}, 当前密码为 {}".format(self.username, self.password))
            logging.error(error)
            raise error
        return

    def login_course_selection(self):
        page = BeautifulSoup(self.index.text, features="html.parser")
        link = page.find('a', text="自主选课")
                  
        link = link["onclick"].split("\'")
        gndm = link[1]
        url = self.url + link[3]
        params = {"gnmkdm": "index", "su": self.username, "layout": "default"}
        data = {"gndm": gndm}
        response = self.session.get(url=url, data=data, params=params)
        return response

    def logout(self):
        params = {"t": str(round(time.time() * 1000)), "login_type": ""}
        self.session.get(url=self.url + "/logout", params=params)
        pass

    def query_margin(self, jxb_id, kklxdm, rwlx="2", index=0):
        data1 = \
            {
                "xkly": "",
                "bklx_id": "",
                "sfkkjyxdxnxq": "",
                "xqh_id": "",
                "jg_id": "",
                "njdm_id_1": "",
                "zyh_id_1": "",
                "zyh_id": "",
                "zyfx_id": "",
                "njdm_id": "",
                "bh_id": "",
                "xbm": "",
                "xslbdm": "",
                "ccdm": "",
                "xsbj": "",
                "sfkknj": "",
                "sfkkzy": "",
                "kzybkxy": "",
                "sfznkx": "",
                "zdkxms": "",
                "sfkxq": "",
                "sfkcfx": "",
                "kkbk": "",
                "kkbkdj": "",
                "sfkgbcx": "",
                "sfrxtgkcxd": "",
                "tykczgxdcs": "",
                "xkxnm": "",
                "xkxqm": "",
                "rlkz": "",
                "xkzgbj": "",
                "jspage": "",
                "jxbzb": "",
                "mzm": "",
                "bbhzxjxb":"",
                "xz":""
            }
        data2 = \
            {
                "xkly": "",
                "bklx_id": "",
                "sfkkjyxdxnxq": "",
                "xqh_id": "",
                "jg_id": "",
                "zyh_id": "",
                "zyfx_id": "",
                "njdm_id": "",
                "bh_id": "",
                "xbm": "",
                "xslbdm": "",
                "ccdm": "",
                "xsbj": "",
                "sfkknj": "",
                "sfkkzy": "",
                "kzybkxy": "",
                "sfznkx": "",
                "zdkxms": "",
                "sfkxq": "",
                "sfkcfx": "",
                "kkbk": "",
                "kkbkdj": "",
                "xkxnm": "",
                "xkxqm": "",
                "xkxskcgskg": "",
                "rlkz": "",
                "jxbzcxskg": "",
                "cxbj": "",
                "fxbj": "",
                "mzm": "",
                "bbhzxjxb":"",
                "xz":""
                
            }
        self.cfg.get_data(data1)
        self.cfg.get_data(data2)
        data1["filter_list"] = [jxb_id]
        data1["rwlx"] = str(rwlx)
        data1["kklxdm"] = kklxdm
        data1["kspage"] = "1"


        params = {"gnmkdm": "N253512", "su": self.username}
        res1 = \
            self.session.post(url="http://newjw.hdu.edu.cn/jwglxt/xsxk/zzxkyzb_cxZzxkYzbPartDisplay.html", data=data1,
                              params=params).json()["tmpList"]
        data2["filter_list"] = [jxb_id]
        data2["rwlx"] = str(rwlx)
        data2["kklxdm"] = kklxdm
        data2["kch_id"] = res1[0]["kch_id"]
        data2["xkkz_id"] = self.dict[kklxdm]
        res2 = self.session.post(url="http://newjw.hdu.edu.cn/jwglxt/xsxk/zzxkyzbjk_cxJxbWithKchZzxkYzb.html",
                                 data=data2, params=params).json()
        if index > len(res1) or index > len(res2):
            raise IndexError("不存在该节课")
        return [res1[index], res2[index]]

    def query_by_class_id(self, jxb_id, kklxdm, rwlx="2"):
        data1 = \
            {
                "xkly": "",
                "bklx_id": "",
                "sfkkjyxdxnxq": "",
                "xqh_id": "",
                "jg_id": "",
                "njdm_id_1": "",
                "zyh_id_1": "",
                "zyh_id": "",
                "zyfx_id": "",
                "njdm_id": "",
                "bh_id": "",
                "xbm": "",
                "xslbdm": "",
                "ccdm": "",
                "xsbj": "",
                "sfkknj": "",
                "sfkkzy": "",
                "kzybkxy": "",
                "sfznkx": "",
                "zdkxms": "",
                "sfkxq": "",
                "sfkcfx": "",
                "kkbk": "",
                "kkbkdj": "",
                "sfkgbcx": "",
                "sfrxtgkcxd": "",
                "tykczgxdcs": "",
                "xkxnm": "",
                "xkxqm": "",
                "rlkz": "",
                "xkzgbj": "",
                "jspage": "",
                "jxbzb": "",
                "mzm": "",
                "bbhzxjxb":"",
                "xz":""
            }
        data2 = \
            {
                "xkly": "",
                "bklx_id": "",
                "sfkkjyxdxnxq": "",
                "xqh_id": "",
                "jg_id": "",
                "zyh_id": "",
                "zyfx_id": "",
                "njdm_id": "",
                "bh_id": "",
                "xbm": "",
                "xslbdm": "",
                "ccdm": "",
                "xsbj": "",
                "sfkknj": "",
                "sfkkzy": "",
                "kzybkxy": "",
                "sfznkx": "",
                "zdkxms": "",
                "sfkxq": "",
                "sfkcfx": "",
                "kkbk": "",
                "kkbkdj": "",
                "xkxnm": "",
                "xkxqm": "",
                "xkxskcgskg": "",
                "rlkz": "",
                "jxbzcxskg": "",
                "cxbj": "",
                "fxbj": "",
                "mzm": "",
                "bbhzxjxb":"",
                "xz":""
            }
        self.cfg.get_data(data1)
        self.cfg.get_data(data2)
        data1["filter_list"] = [jxb_id]
        data1["rwlx"] = str(rwlx)
        data1["kklxdm"] = kklxdm
        data1["kspage"] = "1"


        params = {"gnmkdm": "N253512", "su": self.username}
        res1 = \
            self.session.post(url="http://newjw.hdu.edu.cn/jwglxt/xsxk/zzxkyzb_cxZzxkYzbPartDisplay.html", data=data1,
                              params=params).json()["tmpList"]
        data2["filter_list"] = [jxb_id]
        data2["rwlx"] = str(rwlx)
        data2["kklxdm"] = kklxdm
        data2["kch_id"] = res1[0]["kch_id"] if len(res1)>0 else ""
        data2["xkkz_id"] = self.dict[kklxdm]
        res2 = self.session.post(url="http://newjw.hdu.edu.cn/jwglxt/xsxk/zzxkyzbjk_cxJxbWithKchZzxkYzb.html",
                                 data=data2, params=params).json()
        return [res1, res2]


    def qiangke(self, index, times=1000, interval=1):
        (res1, res2) = self.class_list[index]
        data = {
            "jxb_ids": res2["do_jxb_id"],
            "kch_id": res1["kch_id"],
            "kcmc": res1["kcmc"],  # not same completely
            "rwlx": rwlx,
            "rlkz": "0",
            "rlzlkz": "1",
            "sxbj": "1",
            "xxkbj": res1["xxkbj"],
            "qz": "0",
            "cxbj": res1["cxbj"],
            "xkkz_id": self.dict[kklxdm],
            "njdm_id": "2020",
            "zyh_id": "0523",
            "kklxdm": kklxdm,
            "xklc" : "2",
            "xkxnm": "2022",
            "xkxqm": "3"
        }
        # headers = {
        #    "Accept": "application/json, text/javascript, */*; q=0.01"
        #    "Accept-Encoding": "gzip, deflate"
        #    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8"
        #    "Connection": "keep-alive"
        #    "Content-Length": "552"
        #    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        #    "Cookie": "JSESSIONID=76EAADA342699A32AF7748779A92EC38; route=5063706ecbac8c9154cb45c088a91202"
        #    "Host": "newjw.hdu.edu.cn"
        #    "Origin": "http://newjw.hdu.edu.cn"
        #    "Referer": "http://newjw.hdu.edu.cn/jwglxt/xsxk/zzxkyzb_cxZzxkYzbIndex.html?gnmkdm=N253512&layout=default&su=20051336"
        #    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
        #    "X-Requested-With": XMLHttpRequest"
        # }
        params = {"gnmkdm": "N253512", "su": self.username}
        res = {"flag": 0}
        for cnt in range(times):
            res = self.session.post(url="http://newjw.hdu.edu.cn/jwglxt/xsxk/zzxkyzbjk_xkBcZyZzxkYzb.html", data=data,
                                    params=params).json()
            if res["flag"] == -1:
                logging.info("当前人数已满！")
            else:
                logging.info("cnt={}: ".format(cnt) + str(res))
            time.sleep(interval)
            if res["flag"] == "1":
                self.class_list.remove((res1, res2))
                return 1
        return -1

    def add_to_list(self, jxb_id, kklxdm, rwlx):
        [res1, res2] = self.query_by_class_id(jxb_id, rwlx=rwlx,  kklxdm=kklxdm)
        if len(res1) == 0 or len(res2) == 0:
            print(f"不存在课程代码为{jxb_id}的课程，请核对输入")
            return False
        teacher_name = [res["jsxx"] for res in res2]
        class_time = [res["sksj"] for res in res2]
        already_picked = [res["yxzrs"] for res in res1]
        total = [res["jxbrl"] for res in res2]
        pick_info = [f"{al}/{tltal}" for al, tltal in zip(already_picked, total)]
        data = pd.DataFrame()
        data["教师姓名"] = teacher_name
        data["上课时间"] = class_time
        data["选课人数"] = pick_info
        data.index = range(1, len(data) + 1)
        print(data)
        opt = input("课程查找成功！请输入需要添加的课程序号，输入0不添加。\n")
        if opt == "0":
            return False
        else:
            opt = int(opt)
            if opt not in data.index:
                print("序号超出范围，添加失败！")
                return False
            else:
                self.class_list.append((res1[opt - 1], res2[opt - 1]))
                print("添加成功！")
                return True

    def run(self):
        temp = []
        while len(self.class_list):
            for index in range(len(self.class_list)):
                th = threading.Thread(target=self.qiangke, args=[index])
                th.start()
                temp.append(th)
            for th in temp:
                th.join()
            temp.clear()
            self.logout()
            self.set_pubKey()
            self.set_csrftoken()
            self.login()
            self.login_course_selection()
        print("所有课均已选上！")


if __name__ == "__main__":
    flag = 0
    exit_flag = True
    init_cfg_flag = False

    ex = hdu_jwc()
    if os.path.exists("./config.json"):
        init_cfg_flag = (input("当前目录下存在配置文件，是否需要重新生成（输入yes以重新生成，否则将加载该配置文件）:\n") == "yes")
    else:
        print("当前目录下不存在配置文件，将重新生成该文件")
        init_cfg_flag = True
    if init_cfg_flag:
        ex.init_cfg()
    while True:
        if ex.load_cfg("./config.json") == 1:
            break
        else:
            print("将重新生成配置文件！")
            sys.stdout.flush()
            ex.init_cfg()
    while flag == 0:
        username = input("请输入学号:\n")
        password = getpass("请输入密码:\n")
        password = bytes(password, encoding="utf-8")
        ex.username = username
        ex.password = password
        try:
            ex.set_pubKey()
            ex.set_csrftoken()
            ex.login()
            ex.login_course_selection()
            flag = 1
        except ValueError as error:
            print("username or password error, please check them and try again")
            print("=" * 100)
            continue
        except ConnectionError:
            print("connect fail, please try later!")
            print("=" * 100)
            exit_flag = True
            exit(0)
            continue
    class_cnt = int(input("请输入待选课数量：\n"))
    class_real_cnt = 0
    while class_cnt != class_real_cnt:
        jxb_id = input("请输入课程代码：\n")
        rwlx = input("请输入任务类型代码（主修为1，其它为2）：\n")
        kklxdm = input("请输入开课类型代码（主修是01，通识选修是10，体育是05，特殊是09）：\n")
        if ex.add_to_list(jxb_id, rwlx=rwlx, kklxdm=kklxdm) == 1:
            class_real_cnt = class_real_cnt + 1
    ex.run()
