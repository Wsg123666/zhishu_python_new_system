import datetime
from pymysql import *

def get_lession_id(school=3):
    lession_id_dic = {}  # 存储获取的lession_id字典
    ##获取时间
    end_year = datetime.datetime.now().strftime("%Y")
    begin_year = str(int(end_year) - 3)

    ##连接数据库
    conn = connect(host='cdb-box97608.bj.tencentcdb.com', port=10188, database='zhishu_working', user='root',
                   password='19990206lyz', charset='utf8')
    ##获取semester信息
    cur = conn.cursor()
    lession_list = cur.execute("select * from semester where school_id=%s and semester_year BETWEEN %s and %s ",
                               (school, begin_year, end_year))

    for lession_data in cur.fetchall():
        lession_id_dic.setdefault(lession_data[5], lession_data[2])

    return lession_id_dic

re = get_lession_id(3)
print(re)