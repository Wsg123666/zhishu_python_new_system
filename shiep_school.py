import requests
import random
from bs4 import BeautifulSoup
import re
from lxml import etree
import traceback
import threading
import exceptions
from get_week import GetWeek

class SHIEPSession:

    __login_page = "http://ids.shiep.edu.cn/authserver/login"
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
            "password": self.__password,
            "lt":"",
            "dllt":"userNamePasswordLogin",
            "execution":"e2s1",
            "_eventId":"submit",
            "rmShown":"1"
        }

    def login(self):
        page_lt = self.__session.get(url=self.__login_page)
        # print(page_lt.text)
        # soup = BeautifulSoup(page_lt.text, "html.parser")
        # lt = soup.find_all("input")[3]

        html = etree.HTML(page_lt.content.decode("utf-8"))
        lt =  html.xpath("//input[@name='lt']/@value")[0]
        # print(lt)
        execution = html.xpath("//input[@name='execution']/@value")[0]

        self.data["lt"] = lt
        self.data["execution"] = execution
        # print(self.data)
        page = self.__session.post(url=self.__login_page, data=self.data)
        # print(page.content.decode("utf-8"))
        if page.status_code == 200:
            if "密码错误" in page.text or "账户不存在" in page.text or "为空" in page.text or "密码有误" in page.text :
                return False
            elif "请输入验证码" in page.text:
                raise exceptions.CrawlerException("ce13:验证码输入:需要输入验证码，本系统暂不支持自动输入验证码，请在学校网站登录一次你的用户和密码")
            else:
                return True
        return False

    def get_session(self):
        return self.__session

    def get_username(self):
        return self.__username

    def get_password(self):
        return self.__password

class SHIEPPaser:

    __course_stuid_page = "http://jw.shiep.edu.cn/eams/courseTableForStd.action"
    __user_detail_page = "http://jw.shiep.edu.cn/eams/stdDetail.action"
    __course_table_page = "http://jw.shiep.edu.cn/eams/courseTableForStd!courseTable.action"
    __all_score = "http://jw.shiep.edu.cn/eams/teach/grade/course/person!historyCourseGradeByWwyt.action?projectType1=MAJOR"
    def __init__(self, session):  # 传入EAMSSession类
        # 只有运行get_user_detail才会有stuid的值
        self.__session = session.get_session()
        self.__stuid = None
        self.__username = session.get_username()
        self.__password = session.get_password()
        self.mutex = threading.Lock()

    def get_stuid(self):
        page = self.__session.get(url=self.__course_stuid_page)
        # print(page.text)
        soup = BeautifulSoup(page.text, "html.parser")
        script = soup.find_all("script")[-1]
        pattern = re.findall(r"bg.form.addInput\(form,\"ids\",\"(.*?)\"\);", str(script))
        # print(pattern)
        self.__stuid = int(pattern[0])
        return pattern[0]

    def save_photo(self):
        url = "http://jw.shiep.edu.cn/eams/avatar/my.action"
        photo = self.__session.get(url)
        if photo is None:
            return -1   # no photo
        else:
            with open('./photo/' + self.__username + ".jpg", 'wb') as file:
                file.write(photo.content)
            return 0  # successfully

    def get_detail(self):  # 可获取studentID <input type="hidden" name="studentId" value="246944"/>
        try:
            self.mutex.acquire()
            page = self.__session.get(url=self.__user_detail_page)
            if page.status_code != 200:
                raise exceptions.CrawlerException("ce14:教育系统崩溃了，请稍后在尝试")
            self.mutex.release()
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
            birthday = td[47].string  # 生日
            phone = td[56].string
            photo_state = self.save_photo()

            if photo_state == -1:
                detail = {
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
                    "phone":phone,
                    "photo": None,
                    "avatar": "/static/media/avatar/default.png"
                }
            else:
                detail = {
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
            traceback.print_exc()
            return {"detail": {"state": -1, "error_code": "ce8", "reason": "其他错误:" + str(e)}}

    def get_course_table(self, from_week=1, semester=163):
        try:
            self.mutex.acquire()
            self.get_stuid()
            data = {
                "ignoreHead": 1,
                "setting.kind": "std",
                "startWeek": from_week,
                "semester.id": semester,
                "ids": self.__stuid
            }
            page = self.__session.post(url=self.__course_table_page, data=data)
            if page.status_code != 200:
                raise exceptions.CrawlerException("ce14:教育系统崩溃了，请稍后在尝试")
            self.mutex.release()
            soup = BeautifulSoup(page.text, "html.parser")
            script = str(soup.find_all("script")[-3])
            # print(script)
            course_dic_list = []
            course_all_list = script.split("activity = new TaskActivity")
            for i in range (1,len(course_all_list)):
                course_list = re.match("\((.+)\)",course_all_list[i]).group()
                cour_aoccpy_week = course_list.split(",\"")[-1][:-2]
                course_id = re.findall("(.*)\)",course_list.split("(")[2])[0]
                place = course_list.split(',"')[5][:-1]
                vally_time = GetWeek()
                result = vally_time.marshal(cour_aoccpy_week, 2, from_week, 19)
                name = re.match("(.+)\(\d{2}",course_list.split(',"')[3]).group(1)

                course_week_time_list = re.findall("index\s=(.*);?",course_all_list[i])
                week = []
                time = []
                for week_time in course_week_time_list:
                    week_time = re.findall("\d{1,2}",week_time)
                    week.append(str(int(week_time[0]) + 1))
                    time.append(str(int(week_time[1]) + 1))
                dic = {
                    "username": self.__username,
                    "course_id": course_id,  # 课程序号
                    "course_code": str(course_id).split(".")[0] if "." in str(course_id) else course_id,#课程代码
                    "week_place":place,#地点
                    "name":name,#名字,
                    "duration":result,
                    "week":";".join(list(set(week))),#星期几
                    "week__pitch":"-".join(time) if len(time) <= 2 else time[0] + "-"+time[len(time)-1],#第几节
                    "semester": semester
                }

                course_dic_list.append(dic)
            # index = 0
            # for course_list_con in course_dic_list:
            #     for other_course in course_dic_list:
            #         if course_list_con["name"] == other_course["name"] and course_list_con["time"] != other_course["time"]:
            #             if course_list_con["time"][0] == other_course["time"][0]:
            #                 if course_list_con["time"][len(course_list_con["time"]-1)] < other_course["time"][len(other_course["time"]-1)]:
            #                     course_list_con["get_time"] = course_list_con["time"].spilt("-")[0] + other_course["get_time"].spilt("-")[1]


            # print(course_dic_list)
            return {"course": {"state": 1, "data": course_dic_list}}
        except requests.exceptions.ConnectionError:
            self.mutex.release()
            return {"course": {"state": -1, "error_code": "ce10", "reason": "学校服务器对你的请求没有响应，访问失败"}}
        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            return {"course": {"state": -1, "error_code": error[0], "reason":error[1]}}
        except Exception as e:
            self.mutex.release()
            traceback.print_exc()
            return {"course": {"state": -1, "error_code": "ce8", "reason": "其他错误:" + str(e)}}


            # course_list = re.findall("activity\s=\snew\sTaskActivity\((.*);?\)", script)
            # print(course_list)
            # course_id_list = []
            # if len(course_list) != 0:
            #     for course in course_list:
            #         course_id = str(course).split("(")[1]
            #         course_id_list.append(course_id)
            #     course_id_list = list(set(course_id_list))  # list去重, 得到课程id list
            #     course_dic_list = []   # 课程id的list => 课程id字典的list
            #     for course_id in course_id_list:
            #         dic = {
            #             "username": self.__username,
            #             "course_id": course_id,#课程序号
            #             "course_code":str(course_id).split(".")[0] if "." in str(course_id) else course_id,
            #             "semester": semester
            #         }
            #         course_dic_list.append(dic)
            #     print(course_dic_list)
            #     return course_dic_list
            # else:
            #     return None

    def hand_space(self,data):#处理、\t\n这种
        data = re.findall("\d+.\d+",data)[0] if re.findall("\d+.\d+",data) else re.sub("\s+","",data)
        return data

    def get_all_score(self):
        try:
            data = {
                "projectType1": "MAJOR"
            }
            self.mutex.acquire()
            html = self.__session.post(self.__all_score, data=data)
            if html.status_code != 200:
                raise exceptions.CrawlerException("ce14:教育系统崩溃了，请稍后在尝试")
            self.mutex.release()
            html = etree.HTML(html.content.decode("utf-8"))

            # print(etree.tostring(html, encoding="utf-8").decode("utf-8"))

            tr_data = html.xpath("//table/tbody[contains(@id,'data')]//tr")
            score_data = []
            for tr in tr_data:
                if not tr.xpath(".//td"):
                    continue
                semester = "".join(tr.xpath(".//td[1]//text()"))
                # print("".join(tr.xpath(".//td[4]//text()")))
                courseid ="".join(re.findall("(\S.*\S)","".join(tr.xpath(".//td[2]//text()"))))
                course_name = "".join(re.findall("(\S.*\S)","".join(tr.xpath(".//td[4]//text()"))))
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
                    "course_name":course_name,
                    "course_code": coursecode,
                    "course_evaluation": courseevaluation,
                    "course_score": coursescore,
                }
                score_data.append(score_dic)  # 成绩列表
            # print(score_data)
            return {"score": {"state": 1, "data": score_data}}
            # print(self.final_data)
        except requests.exceptions.ConnectionError:
            self.mutex.release()
            return {"score": {"state": -1, "error_code": "ce10", "reason": "学校服务器对你的请求没有响应，访问失败"}}
        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            return {"score": {"state": -1, "error_code": error[0], "reason": error[1]}}
        except Exception as e:
            self.mutex.release()
            return {"score": {"state": -1, "error_code": "ce8", "reason": "其他错误:" + str(e)}}

    def get_all_semester_summary(self):
        try:
            data = {
                "projectType": "MAJOR"
            }
            self.mutex.acquire()
            page = self.__session.post(url=self.__all_score, data=data)
            if page.status_code != 200:
                raise exceptions.CrawlerException("ce14:教育系统崩溃了，请稍后在尝试")
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
                            "lesson_num": ths[1].text,
                            "total_credit": ths[2].text,
                            "average_score":ths[3].text
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
                                "average_score":tds[4].text
                            }
                            average_grade_list.append(a_semester_summary)
            # print(average_grade_list)
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
    bsession = SHIEPSession("20181885","Ljl2326645")
    bsession.login()
    m = SHIEPPaser(bsession)
    m.get_all_semester_summary()
