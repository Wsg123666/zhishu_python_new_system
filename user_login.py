from OA import OASession
from EAMS import EAMSSession
from lx_paser import LiXinSession
from sandau_paser import SanDauSession
from shiep_school import SHIEPSession
import exceptions
import requests


def login(username,password,school,system=None):

    if school == 3:#上海第二工业大学
        try:
            if system == 0:
                oa = OASession(username, password)
                login_state = oa.login()
                if login_state:
                    return oa
                elif login_state == 503:
                    raise exceptions.CrawlerException("ce9:内部错误:oa系统访问失败稍后重试")
                else:
                    raise exceptions.CrawlerException("ce3:登陆错误:oa密码错误")

            elif system == 1:
                eams = EAMSSession(username, password)
                eams_state = eams.login()
                if eams_state and eams_state !=503:
                    return eams
                elif eams_state == 503:
                    raise exceptions.CrawlerException("ce9:内部错误:教务系统访问失败稍后重试")
                else:
                    raise exceptions.CrawlerException("ce4:登陆错误:eams密码错误")

            if not system:
                oa = OASession(username, password)
                login_state = oa.login()
                if login_state:
                    return "oa"

                eams = EAMSSession(username, password)
                eams_state = eams.login()
                if eams_state:
                    return "eams"
                if eams_state == 503:
                    raise exceptions.CrawlerException("ce9:内部错误:教务系统访问失败稍后重试")
                raise exceptions.CrawlerException("ce1:登陆错误:用户提供的用户名、密码对错误，oa,eams系统都登陆不上")

        except requests.exceptions.ConnectionError:
            raise exceptions.CrawlerException("ce10:访问失败:学校服务器对你的请求没有响应，访问失败")
        except exceptions.CrawlerException as e:
            raise e
        except Exception as e:
            raise e

    elif school == 4:#上海金融学院
        if not system:
            try:

                li_session = LiXinSession(username,password)
                li_state = li_session.login()
                if li_state:
                    return li_session
                else:
                    raise exceptions.CrawlerException("ce1:密码错误:请检查你输入的密码是否正确")

            except requests.exceptions.ConnectionError:
                raise exceptions.CrawlerException("ce10:访问失败:学校服务器对你的请求没有响应，访问失败")
            except Exception as e:
                raise e

    elif school == 5:  # 上海杉达学院
        if not system:
            try:

                san_seesion = SanDauSession(username, password)
                san_state = san_seesion.login()
                if san_state:
                    return san_seesion
                else:
                    raise exceptions.CrawlerException("ce1:密码错误:请检查你输入的密码是否正确")

            except requests.exceptions.ConnectionError:
                raise exceptions.CrawlerException("ce10:访问失败:学校服务器对你的请求没有响应，访问失败")
            except Exception as e:
                raise e

    elif school == 7:  # 上海电力大学
        if not system:
            try:

                ship_session = SHIEPSession(username,password)
                ship_state = ship_session.login()
                if ship_state:
                    return ship_session
                else:
                    raise exceptions.CrawlerException("ce1:密码错误:请检查你输入的密码是否正确")

            except requests.exceptions.ConnectionError:
                raise exceptions.CrawlerException("ce10:访问失败:学校服务器对你的请求没有响应，访问失败")

            except Exception as e:
                raise e
