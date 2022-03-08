'''
Auther: littleherozzzx
Date: 2022-02-27 10:49:03
LastEditTime: 2022-03-08 12:15:37
'''
import json
import os

import bs4


class Cfg:
    def __init__(self):
        self.data = {'xkly': '', 'bklx_id': '', 'sfkkjyxdxnxq': '', 'xqh_id': '', 'jg_id_1': '', 'njdm_id_1': '',
                     'zyh_id_1': '', 'zyh_id': '', 'zyfx_id': '', 'njdm_id': '', 'bh_id': '', 'xbm': '',
                     'xslbdm': '', 'ccdm': '', 'xsbj': '', 'sfkknj': '', 'sfkkzy': '', 'kzybkxy': '', 'sfznkx': '',
                     'zdkxms': '', 'sfkxq': '', 'sfkcfx': '', 'kkbk': '', 'kkbkdj': '', 'sfkgbcx': '', 'sfrxtgkcxd': '',
                     'tykczgxdcs': '', 'xkxnm': '', 'xkxqm': '', 'rlkz': '', 'xkzgbj': '', 'jspage': '', 'jxbzb': '',"bbhzxjxb": "",
                     'xkxskcgskg': '', 'jxbzcxskg': '',"cxbj":"","fxbj":"","mzm":"",
                     }

    def load_cfg(self, path="./config.json"):
        if not os.path.exists(path):
            raise FileNotFoundError
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f, parse_int=str)
            for key in self.data.keys():
                if key not in data.keys():
                    raise KeyError(f"配置文件中缺少{key}！")
                if not data[key] and key != "jxbzb":
                    raise ValueError(f"配置文件中{key}为空！")
            self.data = data
            self.data["jg_id"] = self.data["jg_id_1"]
        return 1

    def init_cfg(self, page_path, cfg_path="config.json"):
        page = ""
        with open(page_path, "r", encoding="utf-8") as f:
            page = f.read().encode("utf-8")
        page = bs4.BeautifulSoup(page, features="html.parser")
        for key in self.data.keys():
            find_key = page.find("input", attrs={"name": key})
            if not find_key:
                raise KeyError(f"网页文件中不存在{key}")
            self.data[key] = str(find_key["value"])
        with open(cfg_path, "w+", encoding="utf-8") as f:
            f.write(json.dumps(self.data, indent=4))
        return 1

    def get_data(self, data):
        for key in data.keys():
            data[key] = self.data[key]


if __name__ == "__main__":
    ex = Cfg()
    ex.load_cfg()
    print(ex.data)
