import requests
import random
from bs4 import BeautifulSoup
import re
from lxml import etree
import threading
import exceptions


class LiXinSession:
    __login_page = "https://sso.lixin.edu.cn/authorize.php?client_id=ufsso_longmeng_portal_index&response_type=token&redirect_uri=https%3A%2F%2Fsso.lixin.edu.cn%2Findex.html&state=1q2w3e"

    def __init__(self, username, password):
        self.__username = username
        self.__password = password
        self.__session = requests.session()

        self.__session.headers.update({"X-Forwarded-For": "%d.%d.%d.%d" % (
            random.randint(120, 125), random.randint(1, 200), random.randint(1, 200), random.randint(1, 200)),
                                       "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
                                       "Connection": "close"})

        self.data = {
            "username": self.__username,
            "password": self.__password
        }

    def login(self):
        requests.packages.urllib3.disable_warnings()
        page = self.__session.post(url=self.__login_page, data=self.data,verify=False)
        # print(page.content.decode("utf-8"))
        if page.status_code == 200:
            if "密码错误" in page.text or "账户不存在" in page.text or "为空" in page.text:
                return False
            else:
                return True
        return False

    def get_session(self):
        return self.__session

    def get_username(self):
        return self.__username

    def get_password(self):
        return self.__password

class LiXinpaser:
    __course_table_url ="http://newjw.lixin.edu.cn/webapp/std/edu/lesson/timetable!courseTable.action"
    __course = "http://newjw.lixin.edu.cn/webapp/std/edu/lesson/timetable.action"
    __all_course_url = "http://newjw.lixin.edu.cn/webapp/std/edu/lesson/lesson-search!arrangeInfoList.action"
    __score = "http://newjw.lixin.edu.cn/webapp/std/edu/grade/course!innerIndex.action?projectId=5"
    __detail = "http://newjw.lixin.edu.cn/webapp/std/edu/student/index!innerIndex.action?projectId=5"
    def __init__(self,session):
        self.session = session.get_session()
        self.__username = session.get_username()
        self.__password = session.get_password()
        self.mutex = threading.Lock()

    def get_course_table(self,week=1,semester=1640420192):
        try:
            self.mutex.acquire()
            page = self.session.get(url=self.__course)
            if page.status_code != 200:
                raise exceptions.CrawlerException("ce14:教育系统崩溃了，请稍后在尝试")
            self.mutex.release()
            # print(page.content.decode("utf-8"))
            soup = BeautifulSoup(page.text, "html.parser")
            script = str(soup.find_all("script")[-1])
            #获取用户ids
            ids = re.findall("addInput.*\"(\d+)",script)[0]

            data = {
                "setting.kind":"std",
                "weekSpan": week,
                "project.id": 5,
                "semester.id":semester,
                "ids": ids
            }
            page = self.session.post(url=self.__course_table_url,data=data)

            html = page.content.decode("utf-8")
            html_contend = etree.HTML(html)

            course_list= []
            tr_list = html_contend.xpath("//tbody/tr")
            for tr in tr_list:
                course_id = tr.xpath("./td[2]/text()")[0]
                course_code = tr.xpath("./td[3]/text()")[0]
                course_list.append([course_id,course_code])

            # print(course_list)
            course_dict_list = []
            #查询课程时间
            for course in course_list:
                data = {
                    "lesson.semester.id":semester,
                    "lesson.project.id":5,
                    "lesson.no":course[0],
                    "lesson.course.code":course[1]
                }

                page = self.session.post(url=self.__all_course_url,data=data)

                # print(page.content.decode("utf-8"))
                html = page.content.decode("utf-8")
                # print(html)
                td_list = etree.HTML(html).xpath("//tbody//td")

                prepare_week = "".join(td_list[5].xpath(".//text()"))
                # print(prepare_week)
                # list = prepare_week.split(" ")
                # print(list)

                week = ";".join(re.findall("(星期.? \d{1,2}-\d{1,2})",prepare_week))

                place_list = re.findall("星期.?\s\d{1,2}-\d{1,2}\s(.*?\s.+?)\s",prepare_week)

                new_place_list = []

                num = 0  # 记录下面弄到第几个了

                for place in place_list:
                    num += 1
                    temp_samp = False
                    for i in range(num, len(place_list)):
                        if place == place_list[i]:
                            temp_samp = True
                    if not temp_samp:
                        new_place_list.append(place)

                place = ";".join(new_place_list)

                dic_course = {
                    "username":self.__username,
                    "course_id":course[0],
                    "course_code":course[1],
                    "date_time":week,
                    "week_place":place,
                    "course_name":td_list[3].xpath("./a/text()")[0],
                    "course_score":td_list[-2].xpath(".//text()")[0],
                    "duration":td_list[-1].xpath(".//text()")[0]
                }

                course_dict_list.append(dic_course)
            # print(course_dict_list)
            return {"course": {"state": 1, "data": course_dict_list}}
        except requests.exceptions.ConnectionError:
            self.mutex.release()
            return {"course": {"state": -1, "error_code": "ce10", "reason": "学校服务器对你的请求没有响应，访问失败"}}
        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            return {"course": {"state": -1, "error_code": error[0], "reason":error[1]}}
        except Exception as e:
            self.mutex.release()
            return {"course": {"state": -1, "error_code": "ce8", "reason": "其他错误:" + str(e)}}

    def get_all_score(self):
        try:
            self.mutex.acquire()
            page = self.session.get(url=self.__score)
            if page.status_code != 200:
                raise exceptions.CrawlerException("ce14:教育系统崩溃了，请稍后在尝试")
            self.mutex.release()
            html_contend = page.content.decode("utf-8")
            # print(html_contend)
            html = etree.HTML(html_contend)

            score_title = html.xpath("//h4/text()")
            # print(score_title)

            tbody_list = html.xpath("//tbody")[1:]

            score_dic_list = []
            title_num = 1
            for tbody in tbody_list:
                tr_list = tbody.xpath(".//tr")

                for tr in tr_list:
                    evaluation =tr.xpath(".//td")[-2].xpath("./text()")[0]
                    point = tr.xpath(".//td")[-1].xpath("./text()")[0]
                    score_dic = {
                    "semester":score_title[title_num][:score_title[title_num].find("学期")+2],
                    "username":self.__username,
                    "course_code":tr.xpath(".//td[2]/text()")[0],
                    "course_name":tr.xpath(".//td[3]/text()")[0],
                    "course_evaluation":re.findall("\d+.\d+",evaluation)[0] if re.findall("\d+.\d+",evaluation) else re.sub("\s+","",evaluation),
                    "course_score":re.findall("\d+.\d+",point)[0] if re.findall("\d+.\d+",point) else re.sub("\s+","",point)
                    }

                    score_dic_list.append(score_dic)
                title_num += 1

            # print(score_dic_list)
            return {"score": {"state": 1, "data": score_dic_list}}
        except requests.exceptions.ConnectionError:
            self.mutex.release()
            return {"score": {"state": -1, "error_code": "ce10", "reason": "学校服务器对你的请求没有响应，访问失败"}}
        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            return {"score": {"state": -1, "error_code": error[0], "reason":error[1]}}
        except Exception as e:
            self.mutex.release()
            return {"score": {"state": -1, "error_code": "ce8", "reason": "其他错误:" + str(e)}}

    def get_detail(self):
        try:
            self.mutex.acquire()
            page = self.session.get(url=self.__detail)
            if page.status_code != 200:
                raise exceptions.CrawlerException("ce14:教育系统崩溃了，请稍后在尝试")
            self.mutex.release()
            soup = BeautifulSoup(page.text, "html.parser")

            td = soup.find_all("td")

            html = etree.HTML(page.content.decode("utf-8"))

            td_page_2 = html.xpath("//div[@id='tabPage2']//td")

            username = td[2].string  # 学号
            name = td[4].string  # 姓名
            sex = td_page_2[2].xpath(".//text()")[0]  # 性别
            grade = td[7].string  # 年级
            level = td[11].string  # 学历
            department = td[15].string  # 院系
            profession = td[19].string  # 专业
            class_ = td[21].string  # 班级
            campus = td[27].string  # 校区
            birthday = td_page_2[4].xpath(".//text()")[0]  # 生日

            detail = {
                "username": username,
                "name": name,
                "sex": sex,
                "grade": grade,
                "level": level,
                "department": department,
                "profession": profession,
                "class": class_,
                "campus": campus,
                "birthday": birthday,
            }
            # print(detail)
            return {"detail": {"state": 1, "data": detail}}
        except requests.exceptions.ConnectionError:
            self.mutex.release()
            return {"detail": {"state": -1, "error_code": "ce10", "reason": "学校服务器对你的请求没有响应，访问失败"}}
        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            return {"detail": {"state": -1, "error_code": error[0], "reason":error[1]}}
        except Exception as e:
            self.mutex.release()
            return {"detail": {"state": -1, "error_code": "ce8", "reason": "其他错误:" + str(e)}}

    def get_all_semester_summary(self):
        try:
            self.mutex.acquire()
            page = self.session.get(url=self.__score)
            if page.status_code != 200:
                raise exceptions.CrawlerException("ce14:教育系统崩溃了，请稍后在尝试")
            self.mutex.release()
            soup = BeautifulSoup(page.text, "html.parser")

            tbody = soup.find_all("tbody")[0]

            trs = tbody.find_all("tr")

            average_grade_list = []
            length = len(trs)

            for i, tr in enumerate(trs):  # i:0,1,2,3,....   #tr:item
                tds = tr.find_all("td")
                if i < length - 1:
                    if i == length - 2:
                        all_semester_summary = {
                            "username": self.__username,
                            "school_year":"sum",
                            "lesson_num": tds[1].text,
                            "total_credit": tds[2].text,
                            "average_grade": tds[3].text,
                            "average_score":tds[4].text
                        }
                        average_grade_list.append(all_semester_summary)
                    else:

                        if tds:
                            a_semester_summary = {
                                "username": self.__username,
                                "school_year": tds[0].text,
                                "lesson_num": tds[1].text,
                                "total_credit": tds[2].text,
                                "average_grade": tds[3].text,
                                "average_score":tds[4].text
                            }
                            average_grade_list.append(a_semester_summary)

            return {"all_semester": {"state": 1, "data": average_grade_list}}
        except requests.exceptions.ConnectionError:
            self.mutex.release()
            return {"all_semester": {"state": -1, "error_code": "ce10", "reason": "学校服务器对你的请求没有响应，访问失败"}}
        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            return {"all_semester": {"state": -1, "error_code": error[0], "reason":error[1]}}
        except Exception as e:
            self.mutex.release()
            return {"all_semester": {"state": -1, "error_code": "ce8", "reason": "其他错误:" + str(e)}}


if __name__ == '__main__':
    li = LiXinSession(2016191245,"162619")
    li.login()
    LiXinpaser(li).get_course_table()
