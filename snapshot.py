from selenium import webdriver
from PIL import Image
import time
from OA import OASession
from selenium.webdriver.support.wait import WebDriverWait
import io
import QINIU


class ScreenShot:
    def __init__(self,login_object,school):
        self.loginObject = login_object ##获取登录对象
        self.login_check()
        self.school = school

    def plan_snapshot(self,url,cookies):
        """
        保存快照
        :param url: this is get url 地址
        :return:img url content
        """
        brower = webdriver.PhantomJS()

        brower.get("http://id.sspu.edu.cn/cas/login")

        for cookie,value in cookies.items():
            c = {
                "domain": '.sspu.edu.cn',
                "name": cookie,
                "path": '/',
                "value": value
            }
            brower.add_cookie(c)



        brower.get(url)
        brower.get(url)

        brower.maximize_window()

        if "ompl" not in url:
            wait = WebDriverWait(brower,10,0.5)

            wait.until(lambda brower: brower.find_element_by_tag_name("ul"))

            brower.find_element_by_xpath("//div//ul//li[2]//a").click()


        byte_data = brower.get_screenshot_as_png()

        brower.close()

        return io.BytesIO(byte_data)

    def login_check(self):
        """
        检查登录状态
        :return:
        """
        if not self.loginObject.login_state:
            self.loginObject.login()

    def add_photo(self,image,watermark):
        rgba_image = image.convert('RGBA')
        rgba_watermark = watermark.convert('RGBA')



        image_x, image_y = rgba_image.size
        watermark_x, watermark_y = rgba_watermark.size

        p = Image.new('RGBA', rgba_image.size, (255, 255, 255))
        p.paste(rgba_image, (0, 0, image_x, image_y), rgba_image)

        rgba_image = p

        # 缩放图片
        scale = 10
        watermark_scale = max(image_x / (scale * watermark_x), image_y / (scale * watermark_y))
        new_size = (int(watermark_x * watermark_scale), int(watermark_y * watermark_scale))
        rgba_watermark = rgba_watermark.resize(new_size, resample=Image.ANTIALIAS)
        # 透明度
        rgba_watermark_mask = rgba_watermark.convert("L").point(lambda x: min(x, 60))
        rgba_watermark.putalpha(rgba_watermark_mask)

        watermark_x, watermark_y = rgba_watermark.size
        # 水印位置

        rgba_image.paste(rgba_watermark, ((image_x - watermark_x)//2, image_y//2), rgba_watermark_mask)

        return rgba_image

    def get_myplan_compl(self):
        url = "https://jx.sspu.edu.cn/eams/myPlanCompl.action"
        date = time.time()
        file_name = "sha1({}+{}+{}+sha1(zhishu.app))".format(self.loginObject.get_username(),self.school,int(date))
        cookies = {}
        #获取登录cookies
        for cookie,value in self.loginObject.get_session().cookies.items():
            cookies.setdefault(cookie,value)
        byte_data = self.plan_snapshot(url,cookies)
        im_before = Image.open(byte_data)#从截图中获取的二进制文件。
        #水印文件
        im_watermark = Image.open("./photo/zhishu.png")
        im_after = text.add_photo(im_before, im_watermark)
        ##保存图片
        im_after = im_after.convert("RGB")
        im_after.save("./photo/myplancompl/"+file_name+".jpg")

        ##上传文件
        re = self.photo_upload("user-snapshots","plan_compl_snapshot/"+file_name,"./photo/myplancompl/"+file_name+".jpg")
        ##返回价格
        if int(re)==200:
            return "http://zhishu-user-img.pixeldesert.com/plan_compl_snapshot/"+file_name

    def photo_upload(self,bucket_name,filename,localfile):
        """
        :param filename: 保存文件名
        :param localfile: 上传文件地址
        :return:
        """
        qiniu = QINIU.QiNiu()
        re = qiniu.photo_upload(bucket_name,filename,localfile)
        return  re.status_code

    def get_myplan(self):
        url = "https://jx.sspu.edu.cn/eams/myPlan.action"
        date = time.time()
        file_name = "sha1({}+{}+{}+sha1(zhishu.app))".format(self.loginObject.get_username(), self.school, int(date))
        cookies = {}
        # 获取登录cookies
        for cookie, value in self.loginObject.get_session().cookies.items():
            cookies.setdefault(cookie, value)
        byte_data = self.plan_snapshot(url, cookies)
        im_before = Image.open(byte_data)  # 从截图中获取的二进制文件。
        # 水印文件
        im_watermark = Image.open("./photo/zhishu.png")
        im_after = text.add_photo(im_before, im_watermark)
        ##保存图片
        im_after = im_after.convert("RGB")
        im_after.save("./photo/myplan/" + file_name + ".jpg")

        ##上传文件
        re = self.photo_upload("user-snapshots", "plan_snapshot/" + file_name, "./photo/myplan/" + file_name + ".jpg")
        ##返回价格
        if int(re) == 200:
            return "http://zhishu-user-img.pixeldesert.com/plan_snapshot/" + file_name

if __name__ == '__main__':
    oa = OASession(20181130340,"wsg440295")
    oa.login()
    text = ScreenShot(oa,3)
    comurl = text.get_myplan_compl()
    print(comurl)
    url = text.get_myplan()
    print(url)


    # text = ScreenShot("jj")
    # # text.plan_snapshot("https://blog.csdn.net/itest_2016/article/details/76682643")
    # im_before = Image.open("./photo/text.png")
    # im_watermark = Image.open("./photo/zhishu.png")
    # im_after = text.add_photo(im_before, im_watermark)
    # im_after.show()
    #https://jx.sspu.edu.cn/eams/scheduleSearch.action  project.id: 1  semester.id: 722

