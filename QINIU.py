"""
七牛云上传程序
"""


from qiniu import Auth, put_file, etag
import qiniu.config

class QiNiu:
    def __init__(self):
        self.access_key = "J0GPlnBpthLQW3DyK2OOwJ8rt0zRf1CBreBvbPqE"
        self.secret_key = "-pEAftIS-_PZNTS12Vrv_LIUjXetRorJ_F4y-r5u"
        self.qiniu = Auth(self.access_key, self.secret_key)
    def photo_upload(self,bucket_name,key,localfile):
        """
        :param bucket_name: 上传空间名
        :param key: 上传后保存的文件名
        :param localfile: 上传文件的本地路径
        :return:
        """
        token = self.qiniu.upload_token(bucket_name, key, 3600)
        ret, info = put_file(token, key, localfile)
        assert ret['key'] == key
        assert ret['hash'] == etag(localfile)

        return info