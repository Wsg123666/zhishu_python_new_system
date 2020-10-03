"""
爬虫获取sspu中的一些课程信息
sspu排课查询中的所有课程的所有信息

"""
from OA import OASession
import time
from EAMS import EAMSSession
import re
import math
from lxml import etree
from multiprocessing import Manager,Pool,Process
from pymysql import *
import datetime

class CrawerData:
    def __init__(self,login_object):
        self.login_object = login_object
        self.__prepare_course_url = "https://jx.sspu.edu.cn/eams/scheduleSearch!search.action"
        self.queen = Manager().Queue()
        # self.login_check()
        self.lession_id_lsit = None

    def con_database(self):
        ##连接数据库
        conn = connect(host='cdb-box97608.bj.tencentcdb.com', port=10188, database='zhishu_working', user='root',
                       password='19990206lyz', charset='utf8')
        return conn

    # def login_check(self):
    #     """
    #     检查登录状态
    #     :return:
    #     """
    #     if not self.login_object.login_state:
    #         self.login_object.login()

    def get_prepare_course_info(self,semester_code="722"):
        if len(semester_code)<1:
            return
        post_data = {
            "pageNo": 1,
            "lesson.semester.id": semester_code
        }

        ##访问网页

        pag_all = None

        try:
            html = self.login_object.get_session().post(self.__prepare_course_url,post_data)
            html_content = html.content.decode("utf-8")

            ##获取页码数
            pag_all = re.findall(r"pageInfo(.*?);", html_content)
        except Exception as e:
            pass

        page_num = 1

        if pag_all:
            page_num = math.ceil(float(re.match(".*,(\d*)\)$", pag_all[0]).group(1)) / 20)
        success_count = 0
        for page in range(1,page_num+1):
            success_count+=1
            post_data["pageNo"] = page
            try:
                html = self.login_object.get_session().post(self.__prepare_course_url,post_data)

                html_content = html.content.decode("utf-8")

                html_etree = etree.HTML(html_content)
                ##获取数据字典



                tr_list = html_etree.xpath("//tbody//tr")

                ##遍历每一个tr
                for tr in tr_list:
                    course_id = "".join(tr.xpath(".//td[2]/text()"))
                    course_code = "".join(tr.xpath(".//td[3]/text()"))
                    course_name = "".join(tr.xpath(".//td[4]/a/text()"))
                    teacher = "".join(tr.xpath(".//td[5]/text()"))
                    arrangement = "".join(tr.xpath(".//td[6]/text()"))
                    course_type = "".join(tr.xpath(".//td[7]/text()"))
                    teach_class = "".join(tr.xpath(".//td[8]/text()"))
                    real_student_num = "".join(tr.xpath(".//td[9]/text()"))
                    max_student_num = "".join(tr.xpath(".//td[10]/a/text()"))
                    course_hours = "".join(tr.xpath(".//td[11]/text()"))
                    try:
                        begin_week = int("".join(tr.xpath(".//td[13]/text()")))
                        end_week = begin_week+int("".join(tr.xpath(".//td[14]/text()")))-1
                    except Exception as m:
                        begin_week = ""
                        end_week = ""

                    course_data = {
                        "course_id": course_id,
                        "course_code": course_code,
                        "course_name": course_name,
                        "teacher": teacher,
                        "arrangement": arrangement,
                        "course_type": course_type,
                        "teach_class": teach_class,
                        "real_student_num": real_student_num,
                        "max_student_num": max_student_num,
                        "course_hours": course_hours,
                        "begin_week": begin_week,
                        "end_week": end_week,
                        "semester_code": semester_code
                    }



                    self.queen.put(course_data)##存入队列中
            except Exception as e:
                print(e)

            print("\r完成页数成度{:.2f}".format((success_count/page_num)*100),end="")


    def get_lession_id(self,school):
        """
        获取所有id
        :param school:
        :return:list
        """
        lession_id_list = []#存储获取的lession_id字典

        try:
            ##连接数据库
            conn = connect(host='cdb-box97608.bj.tencentcdb.com', port=10188, database='zhishu_working', user='root',
                           password='19990206lyz', charset='utf8')
            ##获取semester信息
            cur = conn.cursor()
            cur.execute("select * from semester where school_id=%s ",school)
            ##存储数据进入lession_id_list中
            for lession_data in cur.fetchall():
                lession_id_list.append(lession_data[2])
        finally:
            cur.close()
            conn.close()
        lession_id_list.sort(reverse=True)
        self.lession_id_lsit = lession_id_list
        return lession_id_list

    def get_all_course_info(self):
        """遍历所有的lession_id"""
        lession_id_list = self.get_lession_id(3)
        save = Pool(6)
        for lession_id in lession_id_list:
            print("\n正在获取"+str(lession_id))
            save.apply_async(self.save_to_database,(self.queen,))
            self.get_prepare_course_info(lession_id)
        save.close()
        save.join()


    def check_today_year_course(self,school=3):
        self.get_lession_id(school) ##更新现在lession_id
        today_year_lession_id = self.lession_id_lsit[0]
        save = Process(target=self.save_to_database, args=(self.queen,))##创建进程。
        save.start()
        self.get_prepare_course_info(today_year_lession_id)
        self.queen.put("ok")  ##完成标志
        save.join()

    def save_to_database(self,queen):
        """
        保存在数据库中
        :param queen:
        :return:
        """
        conn = self.con_database()
        cousor = conn.cursor()
        ##查询已有信息
        while True:
            print("\r待检测数据剩余{}".format(queen.qsize()),end="")
            try:
                course_data = queen.get(True, timeout=60)
            except Exception as e:
                break  ##超过十分钟没有获取到就退出


            try:
                cousor.execute("select * from crawling_raw_course_3 where course_id=%s and semester_code=%s",
                               (course_data["course_id"], course_data["semester_code"]))
                fetch_data = cousor.fetchone()
                if fetch_data:
                    is_change = False
                    fetch_data = [str(x) for x in fetch_data]
                    ##检查数据是否改变
                    for key, value in course_data.items():
                        if str(value) not in fetch_data:
                            print(str(value),"*"*10,fetch_data, "已经重复")
                            is_change = True

                    if is_change:
                        sql = """update crawling_raw_course_3 set course_code=%(course_code)s,
                                              course_name=%(course_name)s,teacher=%(teacher)s,arrangement=%(arrangement)s,
                                              course_type=%(course_type)s,teach_class=%(teach_class)s,real_student_num=%(real_student_num)s,
                                              max_student_num=%(max_student_num)s,course_hours=%(course_hours)s,begin_week=%(begin_week)s,
                                              end_week=%(end_week)s where course_id =%(course_id)s and semester_code=%(semester_code)s"""
                        cousor.execute(sql, course_data)
                else:
                    ##插入新的数据
                    sql = """insert into crawling_raw_course_3(course_id,course_code,course_name,teacher,arrangement,
                                          course_type,teach_class,real_student_num,max_student_num,course_hours,begin_week,end_week,semester_code)
                                           VALUES (%(course_id)s,%(course_code)s,%(course_name)s,%(teacher)s,%(arrangement)s,%(course_type)s,
                                           %(teach_class)s,%(real_student_num)s,%(max_student_num)s,%(course_hours)s,%(begin_week)s,%(end_week)s
                                           ,%(semester_code)s)"""
                    cousor.execute(sql, course_data)
                conn.commit()
            except DatabaseError as e:
                print(course_data)
                print(e)
                conn = self.con_database()
                cousor = conn.cursor()
                try:
                    queen.put(course_data)  ##重新插入数据
                except Exception as e:
                    print(str(e) + str(208))

            ##退出条件
            if queen.empty():
                break  ##空的时候退出

        try:
            cousor.close()
            conn.close()
        except Exception as e:
            print(str(e) + str(208))


    def check_all_course_every_time(self):
        while True:
            time_ = datetime.datetime.now().strftime("%H")
            time_2 = datetime.datetime.now().strftime("%H:%M")
            if int(time_)==1:
                print("现在时间是{}".format(time_2))
                self.login_object.login()
                self.get_all_course_info()
                print("检查完毕")
                ##写入时间
                try:
                    con = self.con_database()
                    cursor = con.cursor()
                    cursor.execute("update update_time set update_timestamp=%s where entity_name=%s",[int(time.time()),"crawling_raw_course_3_crawling"])
                    con.commit()
                except Exception as e:
                    print(e)
                finally:
                    cursor.close()
                    con.close()
            time.sleep(3600)


if __name__ == '__main__':
    print("程序以及运行")
    eams_session = EAMSSession("1432", "010022")
    b = CrawerData(eams_session)
    b.check_all_course_every_time()