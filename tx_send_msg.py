"""
腾讯发送短信

"""


from qcloudsms_py import SmsSingleSender
from qcloudsms_py.httpclient import HTTPError


class MsgSend:
    def __init__(self):
        self.__appid=1400305377
        self.__appkey = "b29e1a269eea116af74cb351cc0eaafa"
        self.template_id = 519567
        self.sms_sign = "知书黑板报"

    def send_msg(self,params,phone):
        ssender = SmsSingleSender(self.__appid, self.__appkey)
        try:
            result = ssender.send_with_param(86, phone,self.template_id,params, sign=self.sms_sign, extend="", ext="")
        except HTTPError as e:
            self.sava_text(str(e))
            print(e)
        except Exception as e:
            self.sava_text(str(e))
            print(e)
        # print(result)
        return result

    def sava_text(self,e):
        with open("send.log","a+",newline="") as f:
            f.write(e+"\n")

if __name__ == '__main__':
    list = ["xxx","你简直是学霸"]
    MsgSend().send_msg(list,"18223931471")
# {'result': 0, 'errmsg': 'OK', 'ext': '', 'sid': '8:UzX1oz4sTMyw9z9vDC620191213', 'fee': 1}
#     MsgSend().sava_text("hahah")
#     MsgSend().sava_text("hahah")