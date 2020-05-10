"""
爬虫获取sspu中的一些课程信息
sspu排课查询中的所有课程的所有信息

"""
from OA import OASession
import re
import math
from lxml import etree


class CrawerData:
    def __init__(self,login_object):
        self.login_object = login_object
        self.__prepare_course_url = "https://jx.sspu.edu.cn/eams/scheduleSearch!index.action"

    def con_database(self):
        pass

    def check_login(self):
        pass

    def get_prepare_course_info(self,semester_code=722):

        post_data = {
            "pageNo": 1,
            "lesson.semester.id": semester_code
        }

        ##访问网页
        html = self.login_object.get_session().post(self.__prepare_course_url)
        html_content = html.content().decode("utf-8")
        ##获取页码数
        pag_all = re.findall(r"pageInfo(.*?);", html_content)

        if pag_all:
            page_num = math.ceil(float(re.match(".*,(\d*)\)$", pag_all[0]).group(1)) / 20)

        for page in range(1,page_num+1):
            post_data["pageNo"] = page
            html = self.login_object.get_session().post(self.__prepare_course_url)
            html_content = html.content().decode("utf-8")

            html_etree = etree.HTML(html_content)
            ##获取数据字典

            course_data = {
                "course_id":"",
                "course_code":"",
                "course_name":"",
                
            }

            tr_list = html_etree.xpath("//tbody//tr")

            ##遍历每一个tr
            for tr in tr_list:





if __name__ == '__main__':
    oa = OASession(20181130340,"wsg440295")
    oa.login()
    b = CrawerData(oa)