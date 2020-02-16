from EAMS import EAMSSession
import  EAMS
from update_all_grade_summary import UpdateAllGradeSummary
from OA import OASession
from lxml import etree
from connect import Database
from proiexes import *
from log import Logger
import csv
import re
from  tx_send_msg import MsgSend
import time
import datetime
import random
import traceback
import replace
import exceptions
# import insert
####成绩实时查询

class Database(Database):

    def __del__(self):
        pass

class UpdateGradeSummary(UpdateAllGradeSummary):
    def __init__(self,eams_paser,username):
        UpdateAllGradeSummary.__init__(self)
        self.eams_parser = eams_paser
        self.username = username
    def update(self):

        rs_list = self.eams_parser.get_all_semester_summary()
        # print(rs_list)
        # print(rs_list)
        try:
            replace.insert_many_from_dic(self.insert_database, "semester_grade_summary", rs_list)
            self.number += 1
        except exceptions.DatabaseException:
            self.database_error_username.append(self.username)
        except:
            raise exceptions.DatabaseException("de4")




class Score:
    def __init__(self,semesterid):
        self.url = "https://jx.sspu.edu.cn/eams/teach/grade/course/person!historyCourseGrade.action?projectType=MAJOR"
        self.session = ""
        self.__username = ""
        self.__semesterid =semesterid
        self.user_score_data = {} #用户成绩数据记录{“学号”:[]}
        self.firstTimes = True
        self.database_cursor = ""
        self.conn = ""
        self.table_name = ""
        self.eams_parser = ""

    def databse_conect_create(self):
        conn = Database()
        # cnn = conn.get_cursor()
        try:
            sql = """create table if not exists score(
                  id int(11) NOT NULL PRIMARY KEY AUTHORIZATION ,
                  course_num VARCHAR(6) not null,
                  course_code VARCHAR(15) not NULL ,
                  course_name VARCHAR (30) not null,
                  course_type VARCHAR(20) not null,
                  course_score DECIMAL(3,2),
                  course_evaluation VARCHAR(5),
                  course_total VARCHAR(5),
                  course_points DECIMAL(4,2) not NULL ,
                  PRIMARY key(stu_id,course_code)
                  )"""
            conn.execute(sql)
            # conn.get_cursor().close()
            # conn.get_database().close()
        except Exception as e:
            print(e)
        finally:
            # del conn
            # log = Logger('all.log', level='info')
            # log.logger.warning('警告已经存在')
            # Logger('warning.log', level='warning').logger.warning('warning')
            conn.get_cursor().close()
        # print(result)
        #     conn.get_database().close()
        # return conn
        self.conn = conn.get_database()
        # self.database_cursor=cnn

    def database_connect(self):
        conn = Database()
        self.conn = conn.get_database()

    def user_login(self,semesterid,username,password,sysOE):#用户登录
        self.__lessionid = semesterid
        if sysOE == 1:
            # print("eams+系统")
            eams_session = EAMSSession(username, password)
            # eams_session.get_session().proxies = "20181130340:wsg440295.@https://vpn.sspu.edu.cn"
            login_state = eams_session.login()
            if login_state:
                self.eams_parser = EAMS.EAMSParser(eams_session)

            self.session = eams_session.get_session()
        elif sysOE==0:
            # print("oa+系统")
            oa_session = OASession(username,password)
            # oa_session.get_session().proxies = "20181130340:wsg440295.@https://vpn.sspu.edu.cn"
            login_state = oa_session.login()
            if login_state:
                self.eams_parser = EAMS.EAMSParser(oa_session)

            self.session = oa_session.get_session()
        else:
            print("输入错误")
            return False
        # print(login_state)
        return login_state

    def get_user(self,begin,num):#获得所有用户信息从本地  、、、、、
        conn = Database()
        sql = "select * from user limit {},{}".format(begin,num)
        try:
            user = conn.execute(sql)
            # user = []
            # with open("user.csv") as f:
            #     reder = csv.reader(f)
            #     for u in reder:
            #         user.append(u)
            # print(len(user))
            # print(user)
            if user>0:
                user = conn.get_cursor().fetchall()
                # print(user)
                # user = [["20154862120","252829",""]]
                # user = (('20181110713','cy.20000526','081029'),('20171261649','122619',None),('20181120626','1234567890qq',None))
                # user = (('20181120106','xy850850',None),)
                return user
        except Exception as e:
            traceback.print_exc()
            print(e)
            print(109)
            sava_text(e)
        finally:
            pass
            # conn.get_cursor().close()
            # conn.get_database().close()

    def save_dict_content(self, dic_file):
        with open("(总)学生考试成绩.csv", 'a+', newline="") as csvfile:  # 保存用户信息
            fieldnames = ["学号","课程序号", "课程代码","课程名称","课程类别","学分","总评","最终","绩点"
                          ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if self.firstTimes:
                writer.writeheader()
                self.firstTimes = False
            writer.writerow(dic_file)

    def hand_space(self,data):#处理、\t\n这种
        data = re.findall("\d+.\d+",data)[0] if re.findall("\d+.\d+",data) else re.sub("\s+","",data)
        return data

    def get_score_content(self):
        con = Database()
        state = False
        scor_url = "https://jx.sspu.edu.cn/eams/teach/grade/course/person!search.action"
        data = {
            "semesterId":self.__lessionid,
            "projectType":""
        }
        # try:
        html = self.session.post(scor_url,data=data)
        # except Exception as e:
        #     sava_text(e)
        #     while True:
        #         print("进入循环错误")
        #         try:
        #             quit_url()
        #         except Exception as e:
        #             sava_text(e)
        #         state = proiexes()
        #         if state:
        #             break
        #     if state:
        #         html = self.session.post(scor_url, data=data)

        html = etree.HTML(html.content.decode("utf-8"))
        # print(etree.tostring(html,encoding="utf-8").decode("utf-8"))
        # print(self.__username)
        tr_data = html.xpath("//table/tbody[contains(@id,'data')]//tr")
        score_data = []
        con = Database()

        for tr in tr_data:
            if not tr.xpath(".//td"):
                continue
            semester = "".join(tr.xpath(".//td[1]//text()"))
            try:
                sql = "select semester_id from semester_year where name='%s'" %semester
                rs = con.execute(sql)
                if rs>0:
                    semester =con.get_cursor().fetchone()[0]
            except Exception as e:
                print(e)
                print(172)
                semester = ""

            courseid = self.hand_space("".join(tr.xpath(".//td[3]//text()")))

            code = "".join(tr.xpath(".//td[2]//text()"))
            # print(code)
            if "/" in code:
                coursecode = re.sub("\W*", "", code) + "/"
            else:
                coursecode = re.sub("\W*", "", code)

            courseevaluation= self.hand_space("".join(tr.xpath(".//td")[-2].xpath(".//text()")))
            coursescore = self.hand_space("".join(tr.xpath(".//td")[-1].xpath(".//text()")))
            score_dic = {
                "semester":semester,
                "username":self.__username,
                "course_id": courseid,
                "course_code": coursecode,
                "course_evaluation": courseevaluation,
                "course_score": coursescore,
            }
            score_data.append(score_dic)  # 成绩列表

        con.get_cursor().close()
        con.get_database().close()
        return score_data

    def text_login(self,user_a_list,semesterid=662):#读取到一个用户判断登录方式
        # print(user_a_list)
        username = user_a_list[0]
        __passwordoa = user_a_list[1]
        __passwordeams = user_a_list[2]
        if __passwordoa and __passwordoa !='' and __passwordoa != 'NULL':
            # print(__passwordoa+"&&&&&")
            login_state = self.user_login(semesterid, username, __passwordoa, 0)
            if not login_state:# oa密码错误，但eams密码可以登录
                login_state = self.user_login(semesterid, username, __passwordoa, 1)

            if not login_state and __passwordeams:#oa密码错误尝试登录eams系统
                login_state = self.user_login(semesterid, username, __passwordeams, 1)

        elif __passwordeams and __passwordeams !='' and __passwordeams != 'NULL' :
            # print(__passwordeams + "******")
            login_state = self.user_login(semesterid, username, __passwordeams, 1)

            if not login_state:#eams登不上，可能oa可以登上
                login_state = self.user_login(semesterid, username, __passwordeams, 0)

        else:
            login_state = False

        if login_state:
            self.__username = username
        else:
            print(username+"没有登录成功")

        return login_state

    def insert_database_from_dic(self,score,text):
        # conn = Database()
        if not re.findall("\d+",score['course_score']):
            return

        conn = self.conn
        con =conn.cursor()
        # parms = [score['学号'],score['课程序号'],score['课程代码'],score['课程名称'],score['课程类别'],score['学分'],score['总评'],score['最终'],score['绩点']]
        parms = (score[k] for k in score if score[k] is not None)
        try:
            # insert.insert_from_dic(conn,'new_stu_score',score)
            check_sql = "select * from score where username='%s' and course_code='%s'" %(self.__username,score['course_code'])
            # print(check_sql)
            rs = con.execute(check_sql)
            # if rs>0:
            #     score = con.fetchone()[5]
            #     if score != parms[5]:
            #         sql = "replace into VALUES ('{0}','{1}','{2}','{3}','{4}','{5}')".format(parms)
            #         con.execute(sql)

            if rs<=0:
                sql = """insert into score (
                semester,username,course_id,course_code,course_evaluation,course_score)
                VALUES ('{0}','{1}','{2}','{3}','{4}','{5}')""" .format(*parms)
                con.execute(sql)
                return True
            else:
                course_score = con.fetchone()[5]
                # print(course_score)
                # print(score)
                if course_score != float(score['course_score']):
                    sql = """replace into score (
                semester,username,course_id,course_code,course_evaluation,course_score)
                VALUES ('{0}','{1}','{2}','{3}','{4}','{5}')""" .format(*parms)
                    con.execute(sql)
                return False
        except Exception as e:
            traceback.print_exc()
            log = Logger('all.log', level='info')
            log.logger.debug(e)
            Logger('debug.log', level='debug').logger.warning(str(e)+text)
            return False
        finally:
            # conn.commit()
            con.close()

    def get_every_user_score(self):#获取每个用户的成绩
        user_list = self.get_user()  # 用户
        for u in user_list:
            math = random.random()
            time.sleep(math)
            login_state = False
            # try:
            login_state = self.text_login(u,self.__semesterid)
            # except Exception as e:
            #     print("错误进入")
            #     sava_text(e)
            #     state = proiexes()
            #     if state:
            #         login_state = self.text_login(u, self.__semesterid)
            #     else:
            #         sava_text("已经登录可能未分配ip")
            #         quit_url()
            #         print("已经登录可能未分配ip")

            if login_state:
                print(self.__username+"登录完成，获取中")
                score_data = self.get_score_content()
                # print(score_data)
                for score in score_data:#保存到数据库
                    # self.save_dict_content(score)
                    text = self.__username
                    try:
                        self.insert_database_from_dic(score,text)
                    except Exception as E:
                        print(E)
                    finally:
                        self.conn.commit()
                    # log.logger().warning(text)
        return True

                # print(self.user_score_data)

    def get_evalution(self,course_score):
        course_score = float(course_score)
        evaution = {"1":["请相信山重水复疑无路",
                         "苦海无涯，回头是岸","您的发展空间还很大","奇迹是努力的另一个名字",
                         "黑暗吞噬不了光明的心灵","生活总会给你另一个机会","上帝从不埋怨人们的愚昧"],
                    "2":["不以物喜，不以己悲","分数万岁，再多浪费","惊喜惊喜，又惊又喜","恭喜您成功抵挡住考试的残酷","涉水浅者得鱼虾"],
                    "3":["上有黄鹂深树鸣","天地中间大，学中还需深","没有松柏恒，难得雪中青","亦将剩勇追穷寇"],
                    "4":["再接再厉，必成大器","恭喜学霸本霸","您本学霸，无限嚣张","苦尽甘来日"],
                    "5":["您简直是陈独秀本秀","学神驾到，请多指教","今日易晒成绩","今日是与成绩美丽的邂逅","入水深者得蛟龙"]
                    }
        if course_score <= 1:
            evl_list = evaution["1"]
            math = random.randint(0,len(evl_list)-1)
            # print(math)
            return evl_list[math]
        elif 1< course_score <= 2:
            evl_list = evaution["2"]
            math = random.randint(0, len(evl_list)-1)
            return evl_list[math]
        elif 2< course_score <= 3:
            evl_list = evaution["3"]
            math = random.randint(0, len(evl_list)-1)
            return evl_list[math]
        elif 3< course_score <= 4:
            evl_list = evaution["4"]
            math = random.randint(0, len(evl_list)-1)
            return evl_list[math]
        elif 4< course_score <= 5:
            evl_list = evaution["5"]
            math = random.randint(0, len(evl_list)-1)
            return evl_list[math]

    def get_course_name(self,course_code):
        conn = Database()
        try:
            check_sql = "select 课程名称 from au_2019_2020 where 课程代码 = '%s' " % course_code
            con = conn.get_cursor()
            rs = con.execute(check_sql)
            if rs > 0:
                course_name = con.fetchone()[0]
                return course_name

            return ""

        except Exception as e:
            print(e)
            print(320)
        finally:
            conn.get_cursor().close()
            conn.get_database().close()

    def get_phone(self,username):
        conn = Database()
        try:
            check_sql = "select phone from username_phone where username = '%s' " % username
            con = conn.get_cursor()
            rs = con.execute(check_sql)
            if rs > 0:
                user_phone = con.fetchone()[0]
                return user_phone

        except Exception as e:
            print(e)
            print(337)
        finally:
            conn.get_cursor().close()
            conn.get_database().close()

    def check_time(self,begin=0,num=1000000):
        url_list = self.get_user(begin,num)
        msg = MsgSend()
        for user in url_list:
            try:
                math = random.random()
                time.sleep(math)
                # login_state = False
                # try:
                login_state = self.text_login(user,self.__semesterid)
                # print(login_state)
                # except Exception as e:
                #     sava_text(e)
                #     state = proiexes()
                #     if state:
                #         login_state = self.text_login(user, self.__semesterid)
                #     else:
                #         sava_text("已经登录可能未分配ip")
                #         quit_url()
                #         print("已经登录可能未分配ip")
                add_list = []
                score_list = []
                if login_state:
                    updata = ""
                    try:
                        updata = UpdateGradeSummary(self.eams_parser, self.__username)
                        updata.update()
                    except Exception as e:
                        sava_text("\n434"+str(e))
                    try:
                        score_data = self.get_score_content()#获取新的课程成绩list
                        # sql = "select * from %s where stu_id=%s" % (self.table_name,self.__username)
                        # data = self.conn.execute(sql)
                        # if data.fetchall():
                        for score in score_data:
                            state = self.insert_database_from_dic(score,"错误")
                            if state:
                                try:
                                    add_list.append(self.get_course_name(score["course_code"]))
                                except Exception as E:
                                    traceback.print_exc()
                                    time.sleep(5)
                                    add_list.append(self.get_course_name(score["course_code"]))

                                score_list.append(self.get_evalution(score["course_score"]))

                        if len(add_list)>0:
                                course_list = "、".join(add_list)

                                if len(course_list)>12:
                                    course_list = course_list[0:11]+"等"

                                score ="、".join(score_list)

                                if len(score)>12:
                                    score = score[:11]+"."

                                params = [course_list,score]
                                print(params)
                                try:
                                    phone = self.get_phone(self.__username)
                                except Exception as e:
                                    time.sleep(5)
                                    phone = self.get_phone(self.__username)
                                if phone:
                                    result = msg.send_msg(params,phone)

                                    if result["errmsg"] != "OK":
                                        params = ["考试",score]
                                        msg.send_msg(params, phone)
                                        # msg.send_msg(params,phone1)
                                    print("学号："+self.__username+",".join(add_list)+"已出")
                                else:
                                    print("学号：" + self.__username + ",".join(add_list) + "已出,但没有手机号")
                    except Exception as E:
                        print(E)
                        self.conn.rollback()
                        sava_text(str(E)+str(410))
                    finally:
                        self.conn.commit()
            except Exception as e:
                sava_text("\n"+str(self.__username)+str(e))

if __name__ == '__main__':
    s = Score(662)#第一次获取602
    # s.databse_conect_create()
    # s.get_every_user_score()
    # s.database_connect()
    #
    # while True:
    #     s.check_time()
    #     dt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #     # 休眠多少5分钟
    #     print(dt + "休眠5分钟")
    #     time.sleep(300)
    #     dt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #     print("休眠结束，重新获取数据")

    # result = s.get_evalution(4.4)
    # print(result)

    # result = s.get_phone("20181130340")
    # print(result)