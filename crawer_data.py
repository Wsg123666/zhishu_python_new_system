"""
@descript 多线程分配爬虫，sspu数据爬取。
"""


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
import datetime
import traceback
from lxml import etree
from snapshot import ScreenShot

def thread_get_data(session,username,data,thread_num=6):
    object_session = None
    ways = {}
    if isinstance(session,OASession) or isinstance(session,EAMSSession):#上海第二工业大学
        object_session = CarwerData(data,session,username)
        ways.update({"sport": object_session.get_sport,"card": object_session.get_card,
                     "course_simple": object_session.get_course_table,"score_simple": object_session.get_all_score,
                     "plan_content":object_session.get_myplan_content,"plan_snapshot":object_session.get_myplan_snap,
                     "plan_compl_snapshot":object_session.get_myplan_compl_snap})

    elif isinstance(session,LiXinSession):#立信金融学院
        object_session = LiXinpaser(session)

    elif isinstance(session,SanDauSession):#上海杉达学院
        object_session = SanDauPaser(session)

    elif isinstance(session, SHIEPSession):  # 上海电力大学
        object_session = SHIEPPaser(session)

    if object_session:

        if isinstance(object_session,CarwerData):
            ways.update({"detail": object_session.get_detail,"all_semester": object_session.get_all_semester_summary})
        else:
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

        for future in as_completed(requests,1000):
            result.update(future.result())


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
        self.session.get_session().headers.update({
                                       "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
                                       })
        self.mutex = threading.Lock()

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


    def get_second_activity(self):
        session = self.session.get_session()


        advance_url = "https://oa.sspu.edu.cn/interface/Entrance.jsp?id=xsxgbbxt"


        ##需要两遍才能
        session.get(advance_url)

        session.get(advance_url)


        new_url = "https://xgbb.sspu.edu.cn/sharedc/sso/fore-login.do?sysadmin=20181130340"

        session.get(new_url)

        ###第二课堂
        #
        # seconde_url = "https://xgbb.sspu.edu.cn/sharedc/core/home/index.do?menuNum=2&tophomeurl="
        #
        # result = session.get(seconde_url)
        #
        # hook_tag = re.findall("var request_token=(.*?);",result.content.decode("utf-8"))[0]
        #
        #
        # post_data = {
        #     "hook_tag":hook_tag
        # }

        second_url = "https://xgbb.sspu.edu.cn/sharedc/dc/studentxfform/index.do"


        second_result = session.get(second_url)



        html_xpath = etree.HTML(second_result.content.decode("utf-8"))

        input_list = html_xpath("//input[@id='value' and @value]/@value")

        for value in  input_list:
            print(value)


    def hand_seconde(self):
        pass


        # with open("result.html","w",encoding="utf-8") as f:
        #     f.write(result.content.decode("utf-8"))




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
            traceback.print_exc()
            return {"detail":{"state":-1,"error_code":"ce8","reason":"其他错误:"+str(e)}}

    def get_myplan_content(self):
        """
        得到我的计划文字内容
        :return:
        """
        try:
            url = "https://jx.sspu.edu.cn/eams/myPlan.action"

            html = self.session.get_session().get(url)
            html_content = html.content.decode("utf-8")

            #获取tr
            etree_html = etree.HTML(html_content)

            tr_list = etree_html.xpath("//table[contains(@id,'planInfoTable')]//tbody//tr")

            #遍历tr

            myplan = []

            for tr in tr_list:
                try:
                    sug_semesters = "".join(tr.xpath(".//td")[-3].xpath(".//text()")).replace("\xa0","")
                    sug_semesters = "".join(re.findall("^\s*(.*)\s*", sug_semesters))
                except Exception as e:
                    continue
                if sug_semesters=="":##去掉没有的
                    continue
                course_code = "".join(tr.xpath(".//td")[-11].xpath(".//text()")).replace("\xa0","")
                course_name = "".join(tr.xpath(".//td")[-10].xpath(".//text()")).replace("\xa0","")
                course_score = "".join(tr.xpath(".//td")[-9].xpath(".//text()")).replace("\xa0","")



                temp_plan = {
                    "course_code":course_code,
                    "course_name":course_name,
                    "course_score":course_score,
                    "sug_semesters":sug_semesters
                }

                myplan.append(temp_plan)

            return {"plan_content":{"state": 1,"data":myplan}}
        except requests.exceptions.ConnectionError:
            return {"plan_content": {"state": -1, "error_code":"ce10","reason":"学校服务器对你的请求没有响应，访问失败"}}
        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            return {"plan_content": {"state": -1, "error_code": error[0], "reason":error[1]}}
        except Exception as e:
            print(traceback.print_exc())
            return {"plan_content": {"state": -1,  "error_code": "ce8", "reason": "其他错误:"+str(e)}}

    def get_course_table(self,week=1,semester=682):
        try:
            paser = EAMSParser(self.session)
            isget = paser.get_stuid()
            if isget != -1:
                course_dic_list = paser.get_course_table(week,semester)
                return {"course_simple":{"state": 1, "data": course_dic_list}}
            else:
                course_dic_list = paser.get_course_table_another_way()
                return {"course_simple":{"state": 1, "data": course_dic_list}}
        except requests.exceptions.ConnectionError:
            return {"course_simple": {"state": -1, "error_code":"ce10","reason":"学校服务器对你的请求没有响应，访问失败"}}
        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            return {"course_simple": {"state": -1, "error_code": error[0], "reason":error[1]}}
        except Exception as e:
            return {"course_simple":{"state": -1, "error_code": "ce8", "reason": "其他错误:"+str(e)}}

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
            return {"score_simple":{"state": 1, "data": score_data}}
            # print(self.final_data)
        except requests.exceptions.ConnectionError:
            return {"score_simple": {"state": -1, "error_code": "ce10", "reason": "学校服务器对你的请求没有响应，访问失败"}}
        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            return {"score_simple": {"state": -1, "error_code": error[0], "reason":error[1]}}
        except Exception as e:
            return {"score_simple": {"state": -1, "error_code": "ce8", "reason": "其他错误:" + str(e)}}

    def get_card(self,begin_data=None,end_data=None):
        try:
            if not (begin_data or end_data):
                date1 = datetime.date.today()  # 今天的时间
                tdelta = datetime.timedelta(days=20) # 可以相加减的时间
                begin_data = str(date1 - tdelta)
                end_data = str(date1)
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
            traceback.print_exc()
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

    def get_myplan_compl_snap(self):
        try:
            snap = ScreenShot(self.session,3,self.mutex) #创建获取快照对象
            photo_url = snap.get_myplan_compl()
            return {"plan_compl_snapshot":{"state":1,"data":{"img_url":photo_url}}}
        except requests.exceptions.ConnectionError:
            return {"plan_compl_snapshot": {"state": -1, "error_code":"ce10","reason":"学校服务器对你的请求没有响应，访问失败"}}
        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            return {"plan_compl_snapshot": {"state": -1, "error_code": error[0], "reason":error[1]}}
        except Exception as e:
            print(traceback.print_exc())
            return {"plan_compl_snapshot":{"state": -1, "error_code": "ce8", "reason": "其他错误:"+str(e)}}

    def get_myplan_snap(self):
        try:
            snap = ScreenShot(self.session,3,self.mutex) #创建获取快照对象
            photo_url = snap.get_myplan()
            return {"plan_snapshot":{"state":1,"data":{"img_url":photo_url}}}
        except requests.exceptions.ConnectionError:
            return {"plan_snapshot": {"state": -1, "error_code":"ce10","reason":"学校服务器对你的请求没有响应，访问失败"}}
        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            return {"plan_snapshot": {"state": -1, "error_code": error[0], "reason":error[1]}}
        except Exception as e:
            print(traceback.print_exc())
            return {"plan_snapshot":{"state": -1, "error_code": "ce8", "reason": "其他错误:"+str(e)}}



if __name__ == '__main__':
    oa = OASession("20181130340","wsg440295")
    oa.login()
    m = CarwerData("",oa,20181130340)
    re = m.get_card("2019-12-04","2020-06-18")

    print(re)