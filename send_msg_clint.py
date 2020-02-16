import pymysql
import datetime
import traceback
from qcloudsms_py import SmsSingleSender
from qcloudsms_py.httpclient import HTTPError



def get_student(type):
    year = int(datetime.datetime.now().strftime('%Y'))
    student_year = [str(year-type)[-2:],str(year-type-4)[-2:]]#2012-2020
    sql = "select username,phone from username_phone where username in (select username from user_detail where class like '{}%' or class like '{}%')".format(student_year[0],student_year[1])
    user_and_phone = None
    connect = pymysql.connect(host='rm-uf6jej783pxakwxm1ao.mysql.rds.aliyuncs.com', port=3306, database='zhishu', user='zhishu', password='Sn5diphone6', charset='utf8')
    curior = connect.cursor()
    try:
        re = curior.execute(sql)
        print("已经取到大"+str(type)+"同学:"+str(re))

        if re>0:
            user_and_phone = curior.fetchall()
    except Exception as e:
        print(e)
        # traceback.print_exc()

    finally:
        curior.close()
        connect.close()

    return user_and_phone

def send_msg(user_phone):

    appid = 1400305377  #SDK AppID
    appkey = "b29e1a269eea116af74cb351cc0eaafa" #App Key
    template_id = 519567 #正文模板ID
    sms_sign = "知书黑板报" #签名类容
    ssender = SmsSingleSender(appid,appkey)

    select = input("是否启用原有模板yes启用，no重新输入:")

    while True:
        try:
            if select =="NO" or select =="no":
                appid = int(input("请输入SDK AppID:")) # SDK AppID
                appkey = input("请输入App Key:")  # App Key
                template_id = int(input("请输入正文模板ID:"))  # 正文模板ID
                sms_sign = input("请输入签名名称例如知书黑板报:")  # 签名名称
                ssender = SmsSingleSender(appid, appkey)
                break
            elif select =="YES" or select =="yes":
                break
            else:
                print("输入错误，重新输入")
        except Exception as e:
            print("输入错误哦，重新输入"+str(e))

    params = input("请输入你模板中的参数内容以空格隔开:")
    params_list = params.split(" ")
    num = 0
    error_num = 0

    for user_and_phone in user_phone:
        phone = user_and_phone[1]
        try:
            result = ssender.send_with_param(86, phone,template_id, params_list, sign=sms_sign, extend="", ext="")
            if result["errmsg"] == "OK":
                num += 1
            else:
                error_num +=1

                with open("error.text", "a+", newline="") as f:
                    f.write(str(user_and_phone)+"\n")

            print("\r成功发送" + str(num) + "人,未成功发送" + str(error_num) + "人",end=" ")
        except HTTPError as e:
            traceback.print_exc()
        except Exception as e:
            traceback.print_exc()

def main():
    while True:
        print("*"*50)
        print("请选择你要发送短信的对象:")
        print("1:大一同学","2:大二同学","3:大三同学","4：其他")
        print("begin:回到开始界面","exit:退出")
        print("*" * 50)
        while True:
            stu_year = input("选择功能：")
            if stu_year == "begin" or stu_year =="exit":
                break
            else:
                user_and_phone = get_student(int(stu_year))
                send_msg(user_and_phone)
        if stu_year == "exit":
            break

if __name__ == '__main__':
    main()