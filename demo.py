'''
Auther: littleherozzzx
Date: 2022-01-13 16:48:51
LastEditTime: 2022-02-18 22:45:07
'''
import base64
import json
import logging
import threading
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
        self.class_list = []
        self.dict = {
            "01": "D3CA48E77A1A4CD8E0536164A8C05380",
            "10": "D3C989F2C90BEA2DE0536164A8C0923B",
            "05": "D3DDE00D83CA15A1E0536264A8C0CBAE",
        }

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
        except requests.exceptions.ConnectionError as error:
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
        page = BeautifulSoup(self.index.text, features="html.parser")
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
        params = {"t": str(round(time.time() * 1000)), "login_type": ""}
        self.session.get(url=self.url + "/logout", params=params)
        pass

    def query_margin(self, jxb_id, kklxdm, rwlx="2", index=0):
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
                "kklxdm": kklxdm,
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
                "kklxdm": kklxdm,
                "kch_id": jxb_id,
                "jxbzcxskg": "0",
                "xkkz_id": self.dict[kklxdm],
                "cxbj": "0",
                "fxbj": "0"
            }
        params = {"gnmkdm": "N253512", "su": self.username}
        res1 = \
            self.session.post(url="http://newjw.hdu.edu.cn/jwglxt/xsxk/zzxkyzb_cxZzxkYzbPartDisplay.html", data=data1,
                              params=params).json()["tmpList"]
        res2 = self.session.post(url="http://newjw.hdu.edu.cn/jwglxt/xsxk/zzxkyzbjk_cxJxbWithKchZzxkYzb.html",
                                 data=data2, params=params).json()
        if index >= len(res1) or index >= len(res2):
            raise IndexError("不存在该节课")
        return [res1[index], res2[index]]

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
            "kklxdm": kklxdm
        }
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

    def add_to_list(self, jxb_id, index, kklxdm, rwlx):
        try:
            [res1, res2] = self.query_margin(jxb_id, rwlx=rwlx, index=index - 1, kklxdm=kklxdm)
        except IndexError as error:
            logging.warning("课程编号为{}的课程中不存在第{}个教学班".format(jxb_id, index))
            print("课程编号为{}的课程中不存在第{}个教学班".format(jxb_id, index))
            return -1
        teacher_name = res2["jsxx"]
        class_time = res2["sksj"]
        already_picked = res1["yxzrs"]
        total = res2["jxbrl"]
        print("课程查找成功！\n请确认信息是否正确：")
        print("\n" * 2)
        print(
            "课程编号为{}\n教师姓名为：{}\n上课时间为：{}\n已选/容量：{}/{}".format(jxb_id, teacher_name, class_time, already_picked, total))
        print("\n" * 2)
        if input("输入yes以确认：") == "yes":
            self.class_list.append((res1, res2))
            print("添加成功！")
            return 1

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
    while flag == 0:
        username = input("input your username:\n")
        password = bytes(input("input your password:\n"), encoding="utf-8")
        ex = hdu_jwc(username, password)
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
    class_cnt = int(input("请输入待选课数量："))
    class_real_cnt = 0
    while class_cnt != class_real_cnt:
        jxb_id = input("请输入课程代码：")
        rwlx = input("请输入任务类型代码（主修为1，其它为2）：")
        kklxdm = input("请输入开课类型代码（主修是01，通识选修是10，体育是05，特殊是09）：")
        index = input("请输入待选课在本代码中的次序（选课系统中的位次，从1开始）：")
        if ex.add_to_list(jxb_id, int(index), rwlx=rwlx, kklxdm=kklxdm) == 1:
            class_real_cnt = class_real_cnt + 1
    ex.run()
