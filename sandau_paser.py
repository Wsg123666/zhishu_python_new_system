import requests
import random
import base64
from bs4 import BeautifulSoup
import re
from lxml import etree
import threading

class SanDauSession:
    __login_page = "http://jw.sandau.edu.cn:8180/eams-shuju/login.action"

    def __init__(self, username, password):
        self.__username = username
        self.__password = password
        self.__session = requests.session()

        self.__session.headers.update({"X-Forwarded-For": "%d.%d.%d.%d" % (
            random.randint(120, 125), random.randint(1, 200), random.randint(1, 200), random.randint(1, 200)),
                                       "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
                                       "Connection": "close"})

        password = "ET03#16^%8W&" + str(self.__password)

        password = bytes(password, "utf-8")

        new_password = base64.b64encode(password)

        self.data = {
            "username": self.__username,
            "password": new_password.decode("utf-8"),
            "session_locale":"zh_CN",
        }

    def login(self):
        requests.packages.urllib3.disable_warnings()
        page = self.__session.post(url=self.__login_page, data=self.data)
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

class SanDauPaser:

    __course_table_url = "http://jw.sandau.edu.cn:8180/eams-shuju/courseTableForStd!courseTable.action"
    __detail = "http://jw.sandau.edu.cn:8180/eams-shuju/stdInfoToStudent.action"
    __all_score = "http://jw.sandau.edu.cn:8180/eams-shuju/teach/grade/course/person!historyCourseGrade.action"
    def __init__(self,session):
        self.session = session.get_session()
        self.__username = session.get_username()
        self.__password = session.get_password()
        self.stuid = ""
        self.mutex = threading.Lock()

    def get_stuid(self):
        page = self.session.get(url="http://jw.sandau.edu.cn:8180/eams-shuju/courseTableForStd.action")

        soup = BeautifulSoup(page.text, "html.parser")
        script = soup.find_all("script")[-1]
        # print(page.text)
        pattern = re.findall(r"bg.form.addInput\(form,\"ids\",\"(.*?)\"\);", str(script))
        self.stuid= int(pattern[0])
        # print(self.stuid)
        return pattern[0]

    def get_course_table(self,week=1,semester=271908):
        try:
            self.mutex.acquire()
            self.get_stuid()

            data = {
                 "ignoreHead": 1,
                "setting.kind": "std",
                "startWeek": week,
                "semester.id": semester,
                "ids": self.stuid
            }
            page = self.session.post(url=self.__course_table_url, data=data)
            self.mutex.release()
            html = page.content.decode("utf-8")
            html_contend = etree.HTML(html)

            course_list = []
            tr_list = html_contend.xpath("//tbody/tr")
            for tr in tr_list:
                place_information = tr.xpath("./td[13]//text()")
                # print(place_information)
                week =";".join(re.findall("(星期.?\s\d{1,2}-\d{1,2}节)","".join(place_information)))
                place_list = []
                for pl in place_information:
                    # print(pl)
                    temp = "".join(re.findall("节(.*\[\d{1,2}-\d{1,2}].*\S)",pl))
                    place_list.append(str(temp))
                new_place_list = []

                num = 0 #记录下面弄到第几个了

                for place in place_list:
                    num+=1
                    temp_samp = False
                    for i in range(num,len(place_list)):
                        if place == place_list[i]:
                            temp_samp = True
                    if not temp_samp:
                        new_place_list.append(place)

                place = ";".join(new_place_list)

                dic = {
                    "username": self.__username,
                    "course_id": "".join(tr.xpath("./td[6]/a/text()")),
                    "course_code": "".join(tr.xpath("./td[2]/text()")),
                    "week": week,
                    "place": place,
                    "course_name": "".join(tr.xpath("./td[3]//text()")),
                    "course_score": "".join(tr.xpath("./td[5]/text()")),
                    # "course_time": td_list[-1].xpath(".//text()")[0]
                }
                course_list.append(dic)
            print(course_list)
            return {"course": {"state": 1, "data": course_list}}
        except requests.exceptions.ConnectionError:
            self.mutex.release()
            return {"course": {"state": -1, "error_code": "ce10", "reason": "学校服务器对你的请求没有响应，访问失败"}}
        except Exception as e:
            self.mutex.release()
            return {"course": {"state": -1, "error_code": "ce8", "reason": "其他错误" + str(e)}}

    def get_detail(self):
        try:
            self.mutex.acquire()
            page = self.session.get(url=self.__detail)
            self.mutex.release()
            soup = BeautifulSoup(page.text, "html.parser")

            td = soup.find_all("td")

            username = td[2].string  # 学号
            name = td[4].string  # 姓名
            sex = td[9].string  # 性别
            grade = td[11].string  # 年级
            level = re.findall("(\S.*\S)",td[17].string)[0] # 学历
            department = td[21].string  # 院系
            profession = td[23].string  # 专业
            class_ = td[43].string  # 班级
            campus = td[45].string  # 校区
            birthday = re.findall("(\S.*\S)",td[63].string)[0]  # 生日

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
            return {"detail": {"state": 1, "data": detail}}
        except requests.exceptions.ConnectionError:
            self.mutex.release()
            return {"detail": {"state": -1, "error_code": "ce10", "reason": "学校服务器对你的请求没有响应，访问失败"}}

        except Exception as e:
            self.mutex.release()
            return {"detail": {"state": -1, "error_code": "ce8", "reason": "内部错误" + str(e)}}

    def get_all_semester_summary(self):
        try:
            data = {
                "projectType": "MAJOR"
            }
            self.mutex.acquire()
            page = self.session.post(url=self.__all_score, data=data)
            self.mutex.release()
            soup = BeautifulSoup(page.text, "html.parser")
            # print(page.text)
            tbodys = soup.find_all("tbody")[0]
            trs = tbodys.find_all("tr")
            average_grade_list = []
            length = len(trs)

            for i, tr in enumerate(trs):   # i:0,1,2,3,....   #tr:item
                if i < length-1:
                    if i == length-2:
                        ths = tr.find_all("th")
                        all_semester_summary = {
                            "username": self.__username,
                            "school_year": "sum",
                            "season": "sum",
                            "lesson_num": ths[1].text,
                            "total_credit": ths[2].text,
                            "average_grade": ths[3].text,
                            "average_point":ths[4].text
                        }
                        average_grade_list.append(all_semester_summary)
                    else:
                        tds = tr.find_all("td")
                        if tds:
                            a_semester_summary = {
                                "username": self.__username,
                                "school_year": tds[0].text,
                                "season": tds[1].text,
                                "lesson_num": tds[2].text,
                                "total_credit": tds[3].text,
                                "average_grade": tds[4].text,
                                "average_point":tds[5].text
                            }
                            average_grade_list.append(a_semester_summary)
            return {"all_semester": {"state": 1, "data": average_grade_list}}
        except requests.exceptions.ConnectionError:
            self.mutex.release()
            return {"all_semester": {"state": -1, "error_code": "ce10", "reason": "学校服务器对你的请求没有响应，访问失败"}}
        except Exception as e:
            self.mutex.release()
            return {"all_semester": {"state": -1, "error_code": "ce8", "reason": "其他错误" + str(e)}}

    def hand_space(self,data):#处理、\t\n这种
        data = re.findall("\d+.\d+",data)[0] if re.findall("\d+.\d+",data) else re.sub("\s+","",data)
        return data

    def get_all_score(self):
        try:
            data = {
                "projectType": "MAJOR"
            }
            self.mutex.acquire()
            html = self.session.post(self.__all_score, data=data)
            self.mutex.release()
            html = etree.HTML(html.content.decode("utf-8"))

            # print(etree.tostring(html, encoding="utf-8").decode("utf-8"))

            tr_data = html.xpath("//table/tbody[contains(@id,'data')]//tr")
            score_data = []
            for tr in tr_data:
                if not tr.xpath(".//td"):
                    continue
                semester = "".join(tr.xpath(".//td[2]//text()"))
                print("".join(tr.xpath(".//td[4]//text()")))
                courseid ="".join(re.findall("(\S.*\S)","".join(tr.xpath(".//td[4]//text()"))))
                code = "".join(tr.xpath(".//td[3]//text()"))
                if "/" in code:
                    coursecode = re.sub("\W*", "", code) + "/"
                else:
                    coursecode = re.sub("\W*", "", code)

                courseevaluation = self.hand_space("".join(tr.xpath(".//td")[-3].xpath(".//text()")))
                coursescore = self.hand_space("".join(tr.xpath(".//td")[-2].xpath(".//text()")))
                score_dic = {
                    "semester": semester,
                    "username": self.__username,
                    "course_id": courseid,
                    "course_code": coursecode,
                    "course_evaluation": courseevaluation,
                    "course_score": coursescore,
                }
                score_data.append(score_dic)  # 成绩列表
            return {"score": {"state": 1, "data": score_data}}
            # print(self.final_data)
        except requests.exceptions.ConnectionError:
            self.mutex.release()
            return {"score": {"state": -1, "error_code": "ce10", "reason": "学校服务器对你的请求没有响应，访问失败"}}
        except Exception as e:
            self.mutex.release()
            return {"score": {"state": -1, "error_code": "ce8", "reason": "其他错误" + str(e)}}


if __name__ == '__main__':
    san = SanDauSession("f18072106","073824")
    san.login()
    SanDauPaser(san).get_course_table()