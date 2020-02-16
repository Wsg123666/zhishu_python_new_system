from get_score import Score
from proiexes import *
from lxml import etree
import  re
import traceback


###不爬取662的全部爬取器

from connect import Database

class Database(Database):

    def __del__(self):
        pass

class GetAllScore(Score):
    def __init__(self):
        self.url = "https://jx.sspu.edu.cn/eams/teach/grade/course/person!historyCourseGrade.action?projectType=MAJOR"
        Score.__init__(self,662)
        self.conn = ""

    # def database_connect(self):
    #     conn = Database()
    #     self.conn = conn.get_database()

    def get_score_content(self,username):
        scor_url = self.url
        data = {
          "projectType":"MAJOR"
        }
        html = self.session.post(scor_url, data=data)

        html = etree.HTML(html.content.decode("utf-8"))
        # print(etree.tostring(html, encoding="utf-8").decode("utf-8"))
        tr_data = html.xpath("//table/tbody[contains(@id,'data')]//tr")
        score_data = []
        conn = Database()
        for tr in tr_data:
            if not tr.xpath(".//td"):
                continue
            semester = "".join(tr.xpath(".//td[1]//text()"))
            try:
                sql = "select semester_id from semester_year where name='%s'" %semester
                rs = conn.execute(sql)
                if rs>0:
                    semester =conn.get_cursor().fetchone()[0]
            except Exception as e:
                print(e)
                semester = ""
            courseid = self.hand_space("".join(tr.xpath(".//td[3]//text()")))
            code = "".join(tr.xpath(".//td[2]//text()"))
            if "/" in code:
                coursecode = re.sub("\W*", "", code) + "/"
            else:
                coursecode = re.sub("\W*", "", code)

            courseevaluation= self.hand_space("".join(tr.xpath(".//td")[-2].xpath(".//text()")))
            coursescore = self.hand_space("".join(tr.xpath(".//td")[-1].xpath(".//text()")))
            score_dic = {
                "semester":semester,
                "username":username,
                "course_id": courseid,
                "course_code": coursecode,
                "course_evaluation": courseevaluation,
                "course_score": coursescore,
            }
            score_data.append(score_dic)  # 成绩列表
        return score_data

    def save_dict_content(self,dic_file):
        with open("(总)new学生考试成绩.csv", 'a+', newline="") as csvfile:  # 保存用户信息
            fieldnames = ["semester","username","course_id","course_code","course_evaluation","course_score"
                          ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if self.firstTimes:
                writer.writeheader()
                self.firstTimes = False
            writer.writerows(dic_file)

    def insert_database_from_dic(self, score, text):
        if not re.findall("\d+", score['course_score']):
                return
        # conn = Database()
        conn = self.conn
        con = conn.cursor()
        # parms = [score['学号'],score['课程序号'],score['课程代码'],score['课程名称'],score['课程类别'],score['学分'],score['总评'],score['最终'],score['绩点']]
        parms = (score[k] for k in score if score[k] is not None)

        try:
            # insert.insert_from_dic(conn,'new_stu_score',score)
            # check_sql = "select * from score where username='%s' and course_code='%s'" % (
            # text, score['course_code'])
            # print(check_sql)
            # rs = con.execute(check_sql)
            # if rs <= 0:
            sql_forwer = """insert into score (
               semester,username,course_id,course_code,course_evaluation,course_score)
               select '{0}','{1}','{2}','{3}','{4}','{5}' from dual """.format(*parms)
            sql_over = " where NOT EXISTS (select * from score where username='%s' and course_code='%s')" % (
            text, score['course_code'])
            sql = sql_forwer + sql_over

            con.execute(sql)
            return True
            # else:
            #     return False
        except Exception as e:
            print("错误")
            print(e)
            print(233)
            sava_text(str(e)+str(87))
            return False
        finally:
            # conn.commit()
            con.close()

    def get_all_score(self):
        user_list = super().get_user(0,1000000)
        try:
            self.database_connect()
        # print(user_list[2])
            for user in user_list:
                username = user[0]
                print("正在进行"+username)
                login_state = True
                while login_state:
                    try:
                        login_state = self.text_login(user)
                        if login_state:
                            score = self.get_score_content(username)
                            print(score)
                            text = username
                            for A_score in score:
                                try:

                                     self.insert_database_from_dic(A_score,text)
                                except Exception as e:
                                    print(str(e)+str(125))
                                finally:
                                    try:
                                        self.conn.commit()#如果服务器断开连接
                                    except Exception as e:
                                        print(e)
                                        sava_text(e)
                                        self.database_connect()
                        login_state = False
                    except Exception as e:
                        login_state = True
                        print(e)
                        time.sleep(10)
                        print("休息10秒")
        except Exception as e:
            print(str(e)+str(127))
            sava_text(e)
            traceback.print_exc()
        finally:
            self.conn.close()


if __name__ == '__main__':
    score = GetAllScore()
    score.get_all_score()