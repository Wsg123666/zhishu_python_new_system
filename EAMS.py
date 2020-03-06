import requests
from bs4 import BeautifulSoup
import random
import re
import exceptions
import base64
from PIL import Image
import traceback
from mail import Mail




class EAMSSession:

    __login_page = "https://jx.sspu.edu.cn/eams/login.action"

    def __init__(self, username, password):
        self.__username = username
        self.__password = password
        self.__session = requests.session()

        self.__session.headers.update({"X-Forwarded-For": "%d.%d.%d.%d" % (
            random.randint(120, 125), random.randint(1, 200), random.randint(1, 200), random.randint(1, 200)),
                          "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
                        "Connection":"close"})

        self.data = {
            "username": self.__username,
            "password": self.__password
        }

    def login(self):
        try:
            page = self.__session.post(url=self.__login_page, data=self.data)
            # print(page.content.decode("utf-8"))
            if page.status_code == 200:
                if "密码错误" in page.text or "账户不存在" in page.text or "为空" in page.text:
                    return False
                else:
                    return True
            else:
                return 503
        except Exception as e:
            raise e

    def get_session(self):
        return self.__session

    def get_username(self):
        return self.__username

    def get_password(self):
        return self.__password

class EAMSParser:
    __login_page = "https://jx.sspu.edu.cn/eams/login.action"
    __user_detail_page = "https://jx.sspu.edu.cn/eams/studentDetail.action"
    __semester_calendar_url = "https://jx.sspu.edu.cn/eams/dataQuery.action"
    __course_table_page = "https://jx.sspu.edu.cn/eams/courseTableForStd!courseTable.action"
    __each_grade_page = "https://jx.sspu.edu.cn/eams/teach/grade/course/person!search.action"
    __all_grade_page = "https://jx.sspu.edu.cn/eams/teach/grade/course/person!historyCourseGrade.action"
    __plan_page = "https://jx.sspu.edu.cn/eams/myPlan.action"
    __another_course_table_page = "https://jx.sspu.edu.cn/eams/courseTableForStudent!courseTable.action"

    def __init__(self, session):   # 传入EAMSSession类
        # 只有运行get_user_detail才会有stuid的值
        self.__session = session.get_session()
        self.__stuid = None
        self.__username = session.get_username()
        self.__password = session.get_password()

    def get_console_page(self):
        page = self.__session.get(url=self.__login_page)
        print(page.text)

    def get_stuid(self):
        try:
            page = self.__session.get(url="https://jx.sspu.edu.cn/eams/courseTableForStd.action")
            if page.status_code != 200:
                raise exceptions.CrawlerException("ce14:教育系统崩溃了，请稍后在尝试")
            # if "未进行导师评估，不能进行此操作" in page.text:
            #     raise exceptions.CrawlerException("ce7")

            soup = BeautifulSoup(page.text, "html.parser")
            script = soup.find_all("script")[-1]
            pattern = re.findall(r"bg.form.addInput\(form,\"ids\",\"(.*?)\"\);", str(script))
            self.__stuid = int(pattern[0])
            return pattern[0]
        except Exception as e:
            with open("log.log","a+") as f:
                f.write(str(self.__username)+"place error"+str(e)+"\n")
            return -1    # 若出错，stuid为-1

    def get_user_detail(self):  # 可获取studentID <input type="hidden" name="studentId" value="246944"/>
        page = self.__session.get(url=self.__user_detail_page)
        if page.status_code !=200:
            raise exceptions.CrawlerException("ce14:教育系统崩溃了，请稍后在尝试")
        soup = BeautifulSoup(page.text, "html.parser")

        td = soup.find_all("td")

        stuid = self.get_stuid()  # student ID
        username = td[2].string  # 学号
        self.__username = username
        name = td[4].string  # 姓名
        sex = td[9].string  # 性别
        grade = td[11].string  # 年级
        level = td[17].string  # 学历
        department = td[21].string  # 院系
        profession = td[23].string  # 专业
        class_ = td[43].string  # 班级
        campus = td[45].string  # 校区
        birthday = td[56].string  # 生日
        photo_state = self.save_photo()

        if photo_state == -1:
            dic = {
                "username": username,
                "stuid": int(stuid),
                "name": name,
                "sex": sex,
                "grade": grade,
                "level": level,
                "department": department,
                "profession": profession,
                "class": class_,
                "campus": campus,
                "birthday": birthday,
                "photo": None,
                "avatar": "/static/media/avatar/default.png"
            }
        else:
            dic = {
                "username": username,
                "stuid": int(stuid),
                "name": name,
                "sex": sex,
                "grade": grade,
                "level": level,
                "department": department,
                "profession": profession,
                "class": class_,
                "campus": campus,
                "birthday": birthday,
                "photo": photo_state,
                "avatar": None
            }
        return dic

    # def get_semester_calendar(self):
    #     data = {
    #         "dataType": "semesterCalendar"
    #     }
    #     page = self.__session.post(url=self.__semester_calendar_url, data=data)
    #     print(page.text)

    def get_course_table(self, week=1, semester=662):
        data = {
            "ignoreHead": 1,
            "setting.kind": "std",
            "startWeek": week,
            "semester.id": semester,
            "ids": self.__stuid
        }
        page = self.__session.post(url=self.__course_table_page, data=data)
        if page.status_code !=200:
            raise exceptions.CrawlerException("ce14:教育系统崩溃了，请稍后在尝试")
        soup = BeautifulSoup(page.text, "html.parser")
        script = str(soup.find_all("script")[-2])
        # print(script)
        course_list = re.findall("activity\s=\snew\sTaskActivity\((.*?)\)", script)
        # print(course_list)
        course_id_list = []
        if len(course_list) != 0:
            for course in course_list:
                course_id = re.findall("\S+\((.+)",str(course).split('",')[2])[0]
                course_id_list.append(course_id)
            course_id_list = list(set(course_id_list))  # list去重, 得到课程id list
            course_dic_list = []   # 课程id的list => 课程id字典的list
            for course_id in course_id_list:
                dic = {
                    "username": self.__username,
                    "course_id": course_id,
                    "semester": semester
                }
                course_dic_list.append(dic)
            # print(course_dic_list)
            return course_dic_list
        else:
            return None

    def get_course_table_another_way(self):   # 免登录，不会出现评教提醒
        url = self.__another_course_table_page+"?stdCode="+self.__username
        page = self.__session.get(url)
        if page.status_code !=200:
            raise exceptions.CrawlerException("ce14:教育系统崩溃了，请稍后在尝试")
        soup = BeautifulSoup(page.text, "html.parser")
        script = str(soup.find_all("script")[-1])
        course_list = re.findall("activity\s=\snew\sTaskActivity\((.*?)\)", script)
        course_id_list = []
        if len(course_list) != 0:
            for course in course_list:
                course_id = str(course).split("(")[1]
                course_id_list.append(course_id)
            course_id_list = list(set(course_id_list))  # list去重, 得到课程id list
            course_dic_list = []  # 课程id的list => 课程id字典的list
            for course_id in course_id_list:
                dic = {
                    "username": self.__username,
                    "course_id": course_id,
                    "semester": 662
                }
                course_dic_list.append(dic)
            return course_dic_list
        else:
            return None


    # def get_each_grade(self, semester=622):
    #     data = {
    #         "semesterId": semester
    #     }
    #     page = self.__session.post(url=self.__each_grade_page, data=data)
    #     print(page.text)
    #
    # def get_all_grade(self):
    #     data = {
    #         "projectType": "MAJOR"
    #     }
    #     page = self.__session.post(url=self.__all_grade_page, data=data)
    #
    #     print(page.text)

    def get_all_semester_summary(self):
        data = {
            "projectType": "MAJOR"
        }
        page = self.__session.post(url=self.__all_grade_page, data=data)
        if page.status_code !=200:
            raise exceptions.CrawlerException("ce14:教育系统崩溃了，请稍后在尝试")
        soup = BeautifulSoup(page.text, "html.parser")
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
                        "lesson_num": ths[1].text,
                        "total_credit": ths[2].text,
                        "average_score": ths[3].text#平均绩点
                    }
                    average_grade_list.append(all_semester_summary)
                else:
                    tds = tr.find_all("td")
                    if tds:
                        a_semester_summary = {
                            "username": self.__username,
                            "school_year": tds[0].text+" "+tds[1].text,
                            "lesson_num": tds[2].text,
                            "total_credit": tds[3].text,
                            "average_score": tds[4].text#平均绩点
                        }
                        average_grade_list.append(a_semester_summary)

        return average_grade_list

    # def get_plan(self):
    #     page = self.__session.get(url=self.__plan_page)
    #     print(page.text)

    def save_photo(self):
        url = "https://jx.sspu.edu.cn/eams/avatar/user.action?user.name="+self.__username
        photo = self.__session.get(url)
        if photo is None:
            return -1   # no photo
        else:
            with open('./photo/' + self.__username + ".jpg", 'wb') as file:
                file.write(photo.content)
            return 0  # successfully

    def get_course_table_with_stuid(self, stuid, week=1, semester=662):
        data = {
            "ignoreHead": 1,
            "setting.kind": "std",
            "startWeek": week,
            "semester.id": semester,
            "ids": stuid
        }
        page = self.__session.post(url=self.__course_table_page, data=data)
        if page.status_code !=200:
            raise exceptions.CrawlerException("ce14:教育系统崩溃了，请稍后在尝试")
        soup = BeautifulSoup(page.text, "html.parser")
        script = str(soup.find_all("script")[-2])
        course_list = re.findall("activity\s=\snew\sTaskActivity\((.*?)\)", script)
        course_id_list = []
        if len(course_list) != 0:
            for course in course_list:
                course_id = str(course).split("(")[1]
                course_id_list.append(course_id)
            course_id_list = list(set(course_id_list))  # list去重, 得到课程id list
            course_dic_list = []   # 课程id的list => 课程id字典的list
            for course_id in course_id_list:
                dic = {
                    "username": self.__username,
                    "course_id": course_id,
                    "semester": semester
                }
                course_dic_list.append(dic)
            return course_dic_list
        else:
            return None

