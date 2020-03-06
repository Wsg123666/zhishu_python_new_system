from EAMS import EAMSParser
from sandau_paser import *
from shiep_school import *
from OA import Card
from OA import SportSystem
from OA import OASession
from EAMS import EAMSSession
from lx_paser import *
from concurrent.futures import ThreadPoolExecutor,as_completed
import requests
import traceback

def thread_get_data(session,username,data,thread_num=6):
    object_session = None
    ways = {}
    if isinstance(session,OASession) or isinstance(session,EAMSSession):#上海第二工业大学
        object_session = CarwerData(data,session,username)
        ways.update({"sport": object_session.get_sport,"card": object_session.get_card})

    elif isinstance(session,LiXinSession):#立信金融学院
        object_session = LiXinpaser(session)

    elif isinstance(session,SanDauSession):#上海杉达学院
        object_session = SanDauPaser(session)

    elif isinstance(session, SHIEPSession):  # 上海电力大学
        object_session = SHIEPPaser(session)

    if object_session:

        ways.update({"course": object_session.get_course_table,"detail": object_session.get_detail,
                 "all_semester": object_session.get_all_semester_summary,"score": object_session.get_all_score
                })

        pool = ThreadPoolExecutor(max_workers=thread_num)
        requests = []

        for way in data:
            # self.ways[way]()
            try:
                if data[way]:

                    task = pool.submit(ways[way], *(url for url in data[way]))
                    requests.append(task)
                else:

                    task = pool.submit(ways[way])
                    requests.append(task)
            except Exception as e:
                print(e)

        # num = len(data)#计数完成数量
        result = {}
        try:
            for future in as_completed(requests,100):
                result.update(future.result())
        except Exception as e:
            print(e)

        # while True:
        #
        #     temp = 0
        #     for i in requests:
        #         if i.done():
        #             temp += 1
        #     if temp == num:
        #         break
        #
        # for i in requests:
        #     result.update(i.result())

        return result


class CarwerData:
    def __init__(self,data,session,username):
        self.username = username
        self.data = data
        self.session = session

    def hand_space(self,data):#处理、\t\n这种
        data = re.findall("\d+.\d+",data)[0] if re.findall("\d+.\d+",data) else re.sub("\s+","",data)
        return data

    # def hand_data(self,num):
    #     # t1 = threading.Thread(target=self.get_all_score)
    #     # t1.start()
    #
    #     pool = ThreadPoolExecutor(max_workers=2)
    #     requests = []
    #     for way in self.data:
    #         # self.ways[way]()
    #         try:
    #            if self.data[way]:
    #                task = pool.submit(self.ways[way],*(url for url in self.data[way]))
    #                requests.append(task)
    #            else:
    #                task = pool.submit(self.ways[way])
    #                requests.append(task)
    #         except Exception as e:
    #             print(e)
    #
    #     num = len(self.data)
    #     result = {}
    #     while True:
    #         temp = 0
    #         for i in requests:
    #             if i.done():
    #                 temp+=1
    #         if temp == num:
    #             break
    #
    #     for i in requests:
    #         result.update(i.result())
    #
    #     return result

    def get_detail(self):
        try:
            paser = EAMSParser(self.session)
            detail = paser.get_user_detail()
            return {"detail":{"state":1,"data":detail}}
        except requests.exceptions.ConnectionError:
            return {"detail":{"state":-1,"error_code":"ce10","reason":"学校服务器对你的请求没有响应，访问失败"}}
        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            return {"detail": {"state": -1, "error_code": error[0], "reason":error[1]}}
        except Exception as e:
            return {"detail":{"state":-1,"error_code":"ce8","reason":"其他错误:"+str(e)}}

    def get_course_table(self,week=1,semester=682):
        try:
            paser = EAMSParser(self.session)
            isget = paser.get_stuid()
            if isget != -1:
                course_dic_list = paser.get_course_table(week,semester)
                return {"course":{"state": 1, "data": course_dic_list}}
            else:
                course_dic_list = paser.get_course_table_another_way()
                return {"course":{"state": 1, "data": course_dic_list}}
        except requests.exceptions.ConnectionError:
            return {"course": {"state": -1, "error_code":"ce10","reason":"学校服务器对你的请求没有响应，访问失败"}}
        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            return {"course": {"state": -1, "error_code": error[0], "reason":error[1]}}
        except Exception as e:
            return {"course":{"state": -1, "error_code": "ce8", "reason": "其他错误:"+str(e)}}

    def get_all_semester_summary(self):
        try:
            paser = EAMSParser(self.session)
            average_grade_list = paser.get_all_semester_summary()
            return {"all_semester":{"state": 1, "data": average_grade_list}}
        except requests.exceptions.ConnectionError:
            return {"all_semester": {"state": -1, "error_code":"ce10","reason":"学校服务器对你的请求没有响应，访问失败"}}
        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            return {"all_semester": {"state": -1, "error_code": error[0], "reason":error[1]}}
        except Exception as e:
            return {"all_semester": {"state": -1,  "error_code": "ce8", "reason": "其他错误:"+str(e)}}

    def get_all_score(self):
        try:
            scor_url = "https://jx.sspu.edu.cn/eams/teach/grade/course/person!historyCourseGrade.action?projectType=MAJOR"
            data = {
                "projectType": "MAJOR"
            }
            html = self.session.get_session().post(scor_url, data=data)
            if html.status_code != 200:
                raise exceptions.CrawlerException("ce14:教育系统崩溃了，请稍后在尝试")
            html = etree.HTML(html.content.decode("utf-8"))
            # print(etree.tostring(html, encoding="utf-8").decode("utf-8"))
            tr_data = html.xpath("//table/tbody[contains(@id,'data')]//tr")
            score_data = []
            for tr in tr_data:
                if not tr.xpath(".//td"):
                    continue
                semester = "".join(tr.xpath(".//td[1]//text()"))
                courseid = self.hand_space("".join(tr.xpath(".//td[3]//text()")))
                code = "".join(tr.xpath(".//td[2]//text()"))
                if "/" in code:
                    coursecode = re.sub("\W*", "", code) + "/"
                else:
                    coursecode = re.sub("\W*", "", code)

                courseevaluation = self.hand_space("".join(tr.xpath(".//td")[-2].xpath(".//text()")))
                coursescore = self.hand_space("".join(tr.xpath(".//td")[-1].xpath(".//text()")))
                score_dic = {
                    "semester": semester,
                    "username": self.username,
                    "course_id": courseid,
                    "course_code": coursecode,
                    "course_evaluation": courseevaluation,
                    "course_score": coursescore,
                }
                score_data.append(score_dic)  # 成绩列表
            # print(self.final_data)
            return {"score":{"state": 1, "data": score_data}}
            # print(self.final_data)
        except requests.exceptions.ConnectionError:
            return {"score": {"state": -1, "error_code": "ce10", "reason": "学校服务器对你的请求没有响应，访问失败"}}
        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            return {"score": {"state": -1, "error_code": error[0], "reason":error[1]}}
        except Exception as e:
            return {"score": {"state": -1, "error_code": "ce8", "reason": "其他错误:" + str(e)}}

    def get_card(self,begin_data,end_data):
        try:
            card = Card(self.session.get_session(), begin_data, end_data)
            tran_list = card.transaction()
            return {"card":{"state":1, "data": tran_list}}
        except requests.exceptions.ConnectionError:
            return {"card": {"state": -1, "error_code": "ce10", "reason": "学校服务器对你的请求没有响应，访问失败"}}
        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            return {"card": {"state": -1, "error_code": error[0], "reason":error[1]}}
        except Exception as e:
            if "Exceeded 30" in str(e):
                return {"card": {"state": -1, "error_code": "ce15", "reason": "页面重定向，转移，现在不能访问"}}
            return {"card": {"state": -1, "error_code": "ce8", "reason": "其他错误:" + str(e)}}

    def get_sport(self):
        try:
            sport = SportSystem(self.session)
            sport.login_sport_system()
            final_dic = sport.morning_run()
            return {"sport":{"state": 1, "data": final_dic}}
        except AttributeError:
            return {"sport": {"state": -1, "error_code": "ce11", "reason": "查询晨跑记录并不支持eams系统，请用oa密码重新登陆"}}
        except requests.exceptions.ConnectionError:
            return {"sport": {"state": -1, "error_code": "ce10", "reason": "学校服务器对你的请求没有响应，访问失败"}}
        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            return {"sport": {"state": -1, "error_code": error[0], "reason":error[1]}}
        except Exception as e:
            traceback.print_exc()
            return {"sport": {"state": -1, "error_code": "ce8", "reason": "其他错误:" + str(e)}}


