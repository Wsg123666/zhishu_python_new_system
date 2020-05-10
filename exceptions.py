class CrawlerException(Exception):
    def __init__(self, reason):
        self.reason = reason
# ce1: 用户提供的用户名、密码对错误
# ce2: 用户名或密码为空
# ce3: OA系统密码错误
# ce4: EAMS密码错误
# ce5: 用户没有课表
# ce6: 用户校园卡在指定时间段无交易数据
# ce7: 没有评估导师，无法获取课表
# ce8: 内部错误
# ce9: 内部错误，教务系统访问失败稍后重试
# ce10:学校服务器对你的请求没有响应，访问失败
# ce11:查询晨跑记录并不支持eams系统，请用oa密码重新登陆
# ce12:校卡余额并不能被eams密码查到，请用oa密码登陆
# ce13:需要输入验证码，本系统暂不支持自动输入验证码，请在学校网站登录一次你的用户和密码
# ce14:教务系统崩溃了，请稍后重试。
class DatabaseException(Exception):
    def __init__(self, reason):
        self.reason = reason
# de1: 用户名密码正确，user表存储出错
# de2: user_detail表保存错误
# de3: username_courseid表保存错误
# de4: 保存用户成绩summery错误
# de5: 保存session错误