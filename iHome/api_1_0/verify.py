#-*- coding:utf-8 -*-
from . import api
from flask import request,abort,jsonify,make_response,current_app
from iHome.utils.captcha.captcha import captcha
from iHome import redis_store
from iHome import constants
from iHome.utils.response_code import RET
import json
import re
import random


@api.route('/sms_code',methods =['POST'])
def send_sms_code():
    """
    发送的短信的验证码
    1：接收参数 手机号码 图片验证码 uuid
    2：判断参数是否缺少，并且对于手机号码进行校验
    3：获取服务器存储的图片验证码，uuid作为key
    4：与客户端的传入的图片验证码对比，如果对比成功
    5：发送短信给用户
    6：响应短信发送的结果
    """
    json_str = request.data
    json_dict =json.loads(json_str)
    mobile = json_dict.get('mobile')
    imageCode_client = json_dict.get('imagecode')
    uuid = json_dict.get('uuid')
    # 判断参数
    if not all([mobile,imageCode_client,uuid]):
        return jsonify(errno = RET.PARAMERR,errmsg='缺少参数')
    if not re.match(r'^1([358][0-9]|4[579]|66|7[0135678]|9[89])[0-9]{8}$',mobile):
        return jsonify(errno = RET.PARAMERR,errmsg='手机号码格式有误')
    # 获取服务器中的图片的验证吗
    try:
        imageCode_server = redis_store.get('ImageCode:'+uuid)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询服务器的验证码失败')
    # 判断是否为空或者过期
    if not imageCode_server:
        return jsonify(errno=RET.NODATA,errmsg='查询服务器的验证码为空')
    # 客户端的传入的图片验证码对比，如果对比成功
    if imageCode_client.lower() != imageCode_server.lower():
        return jsonify(errno=RET.DBERR,errmsg ='得到的图片验证码和服务器的验证码不一样')

    # 5.生成短信的验证码
    sms_code  = '%06d'%random.randint(0,999999)
    current_app.logger.debug('短信验证码为：'+sms_code)
    # # 6:使用云通讯将短信验证码发送到注册用户手中
    # result = CCP().sendTemplateSMS(mobile,[sms_code,constants.SMS_CODE_REDIS_EXPIRES/60],'1')
    # if result !=1:
    #     return jsonify(errno=RET.THIRDERR,errmsg='发送短信验证码失败')
    # 7：存储短信验证码到redis中:短信验证码在redis中的有效期一定要和短信验证的提示信息一样
    try:
        redis_store.set('Mobile:'+mobile,sms_code,constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='存储短信验证码失败')

    # 响应短信发送的结果
    return jsonify(errno=RET.OK,errmsg='存储短信验证码成功')

@api.route('/image_code')
def get_image_code():
    """提供图片的验证码"""
    # 获取uuid
    uuid = request.args.get('uuid')
    last_uuid =request.args.get('last_uuid')
    if not uuid:
        abort(403)
    # 生成验证码：text是验证码的文字信息
    name,text,image = captcha.generate_captcha()
    current_app.logger.debug('图片的验证文字的信息有误'+text)
    # 使用uuid存储图片验证码
    try:
        if last_uuid:
            # 上次的uuid还存在的话，则删除它
            redis_store.delete('ImageCode:'+last_uuid)
            # 保存本次需要记录的验证数据
            redis_store.set('ImageCode:'+uuid,text,constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(error=RET.DBERR,errmsg=u'保存验证码失败')
    # 4 返回图片验证
    response = make_response(image)
    response.headers['Content-Type'] = 'image/jpg'
    return response














