import json
from user_login import  login
from  crawer_data import thread_get_data
from fastapi import FastAPI
import base64
import exceptions
import requests
from mail import Mail
import traceback
app = FastAPI()

def url_change(way,host,port,content):
    url = "http://{}:{}/{}/{}".format(host,port,way,content)
    page = requests.get(url)
    return json.loads(page.text)


@app.get("/main/{json_data_bs64}")
def main(json_data_bs64:bytes):
    #解析json字符串
    try:
        json_data = base64.b64decode(json_data_bs64).decode("utf-8")
    except:
        return {"username": "0000", "school": "0000", "state": -1, "error_code": "ce2", "title": "内容错误","content": "重新获得参数"}


    fin_data = {}
    data_dic = json.loads(json_data)
    fin_data["username"] = data_dic["username"]
    #判断是哪个学校，不是进行转发
    if data_dic.get("school") == 4 or data_dic.get("school") == '4':
    #尝试登录

        try:
            if data_dic.get("system")==0 or data_dic.get("system")==1:
                session_objct = login(data_dic["username"],data_dic["password"],data_dic["school"],data_dic["system"])
            else:
                session_objct = login(data_dic["username"], data_dic["password"], data_dic["school"])

            fin_data.update(thread_get_data(session_objct,data_dic["username"],data_dic["data"]))
            return fin_data
        #再一次登录报错
        except requests.exceptions.ConnectionError:

            erro_dict = {"username": data_dic["username"], "state": -1, "error_code": "ce10", "title": "访问错误", "content":"学校系统没有响应"}
            return erro_dict

        except exceptions.CrawlerException as e:
            print(e)
            error = str(e).split(":")
            erro_dict = {"username": data_dic["username"], "state": -1, "error_code": error[0], "title": error[1],"content": error[2]}
            # print(erro_dict)
            return erro_dict

        except Exception as e:

            erro_dict = {"username": data_dic["username"], "state": -1, "error_code": "ce3", "title": "其他错误", "contend": e}
            with open("log.log","a+") as w:
                w.write(str(data_dic["username"])+str(e))
            mail = Mail()
            mail.send("错误人"+str(data_dic["username"]),str(e))
            return erro_dict

    else:
        if data_dic.get("school") == 3 or data_dic.get("school") == '3':##上海金融
            content = url_change('main','49.232.51.43',6060,json_data_bs64.decode("utf-8"))
            return content
        if data_dic.get("school") == 5 or data_dic.get("school") == '5':  ##杉达
            return 0
        if data_dic.get("school") == 7 or data_dic.get("school") == '7':##上海电力
            content = url_change('main','47.95.111.78',6060,json_data_bs64.decode("utf-8"))
            return content
        error = {"username": data_dic.get("username"), "school": data_dic["school"], "state": -1, "error_code": "ce14",
                "title": "学校暂未开通", "content": "改学校还未开通，请之后请耐心等待"}
        return error

@app.get("/login/{json_data_bs64}")
def user_login(json_data_bs64:bytes):

    try:
        json_data = base64.b64decode(json_data_bs64).decode("utf-8")
    except:

        return {"username": "0000", "school": "0000", "state": -1, "error_code": "ce2", "title": "内容错误","content": "重新获得参数"}

    data_dic = json.loads(json_data)#获得发送来的数据信息

    if data_dic.get("school") == 3:
        try:
            if data_dic.get("system"):#有system信息

                system = login(data_dic["username"],data_dic["password"],data_dic["school"],data_dic["system"])

            else:
                system = login(data_dic["username"], data_dic["password"], data_dic["school"])

            if system=="oa" or system=="eams":
                #返回是哪个系统
                system_list = {"oa":0,"eams":1}
                right_dict = {"username":data_dic["username"],"state":1,"school":data_dic["school"],"system":system_list[system]}

                return right_dict

            else:
                #其他学校返回格式
                right_dict = {"username": data_dic["username"], "state": 1, "school":data_dic["school"]}
                return right_dict

        except exceptions.CrawlerException as e:
            error = str(e).split(":")
            erro_dict = {"username":data_dic["username"],"school":data_dic["school"],"state":-1,"error_code":error[0],"title":error[1],"content":error[2]}
            return erro_dict

        except Exception as e:

            erro_dict = {"username": data_dic["username"],"school":data_dic["school"], "state": -1, "error_code": "ce3", "title": "其他错误","content": e}
            with open("log.log", "a+") as w:
                w.write(str(data_dic["username"]) + str(e))
            mail = Mail()
            mail.send("错误人" + str(data_dic["username"]), str(e))
            return erro_dict
    else:
        if data_dic.get("school") == 4 or data_dic.get("school") == '4':  ##上海金融
            content = url_change('login', '116.62.191.189', 6060, json_data_bs64.decode("utf-8"))
            return content

        if data_dic.get("school") == 5 or data_dic.get("school") == '5':  ##杉达
            return 0

        if data_dic.get("school") == 7 or data_dic.get("school") == '7':  ##上海电力
            content = url_change('login', '47.95.111.78', 6060, json_data_bs64.decode("utf-8"))
            return content

        error = {"username":data_dic.get("username"),"school":data_dic["school"],"state":-1,"error_code":"ce14","title":"学校暂未开通","content":"改学校还未开通，请之后请耐心等待"}
        return error

if __name__ == '__main__':

    json_data = {"username":20181885,"password":"Ljl2326645","school":7,"data":{"course":[15,163]}}
    json_1 = json.dumps(json_data,ensure_ascii=False)
    q = base64.b64encode(json_1.encode("utf-8"))
    print(q)
    # q = "eyJ1c2VybmFtZSI6IDIwMTcxMTEyNzIzLCAicGFzc3dvcmQiOiAiQDEyNi5jb20iLCAic2Nob29sIjogMywgInN5c3RlbSI6IDAsICJkYXRhIjogeyJjb3Vyc2UiOiBudWxsfX0="
    b = main(q)
    # print(b)

    json_data = {"username":20181885,"password":"Ljl2326645","school":7}
    json_1 = json.dumps(json_data)
    m = base64.b64encode(json_1.encode("utf-8"))
    print(m.decode('utf-8'))