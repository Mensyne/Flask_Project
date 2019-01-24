#-*- coding:utf-8 -*-
import logging
import redis

class Config(object):

    DEBUG = True

    SECRET_KEY ='9PWghV7TGwRObziZY/uEkItQBdZxHGseoWM7Ms2glYgavDRYp0xD3FasGFsaoEoCD6zY6ZA/yuUv6aYp2jpWSQ=='

    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/iHome'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # redis的配置
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # 设置session数据保存到的位置
    SESSION_TYPE = 'redis'
    # 指定存储session的数据的redis的位置
    SESSION_REDIS  = redis.StrictRedis(host= REDIS_HOST,port=REDIS_PORT)
    # 让cookie中的session_id 被加密处理
    SESSION_USE_SIGNER = True
    # 设置session的有效期
    PERMANENT_SESSION_LIFETIME = 7*24*3600 #设置session过期时间，单位是秒

class DevelopmentConfig(Config):
    """创建调试环境下的调试"""
    # 在本次项目中，我们调试环境配置和Config配置一样，所以直接pass
    LOGGING_LEVEL = logging.DEBUG


class ProductionConfig(Config):
    """创建线上生产环境下的配置类"""
    # 重写差异性的的环境
    SQLALCHEMY_DATABASE_URI = 'mysql://root:root@192.168.142.132/iHome_product_test'

    LOGGING_LEVEL = logging.WARN


class UnittestConfig(Config):
    """创建单元测试的环境"""
    SQLALCHEMY_DATABASE_URI = 'myql://root:mysql@192.168.142.132/iHome_unittest_test'


# 准备工厂设计模式的原材料
configs = {
    'default_config':Config,
    'development':DevelopmentConfig,
    'production':ProductionConfig,
    'unittest':UnittestConfig

}



