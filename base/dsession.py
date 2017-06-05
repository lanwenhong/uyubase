#coding:utf-8

import os, sys
import uuid, redis, json

from zbase.base import dbpool
from uyubase.base import response
from uyubase.base.response import UAURET
from uyubase.uyu import define

from uyubase.base.response import success, error, UAURET

import logging, datetime, time, traceback
log = logging.getLogger()


class DSession:
    def __init__(self, redis_pool, c_conf, sk=None):
        self.sk = sk
        self.redis_pool = redis_pool
        self.c_conf = c_conf

    def gen_skey(self):
        self.sk = str(uuid.uuid4())

    def set_session(self, value):
        svalue = {}
        svalue["device_addr"] = value["device_addr"]
        client = redis.StrictRedis(connection_pool=self.redis_pool)
        client.set(self.sk, json.dumps(svalue))
        client.expire(self.sk, self.c_conf["expires"])
        client.rpush(svalue["device_addr"], self.sk)

    def get_session(self):
        client = redis.StrictRedis(connection_pool=self.redis_pool)
        v = client.get(self.sk)
        if not v:
            return None
        return json.loads(v)

    def expire_session(self):
        client = redis.StrictRedis(connection_pool=self.redis_pool)
        client.expire(self.sk, self.c_conf["expires"])

    def rm_session(self):
        client = redis.StrictRedis(connection_pool=self.redis_pool)
        client.delete(self.sk)


class SDevice:
    def __init__(self, device_addr, session):
        #session 检查， SESSION中的device_addr和传上来的device_addr是否一致
        self.sauth = False
        self.device_addr = device_addr
        self.data = None
        self.se = session

    #检查SESSION对应的USERID是否有权限获取用户数据
    def check_permission(self):
        #是否能获取SESSION
        v = self.se.get_session()
        if not v:
            return False

        log.debug("get session: %s", v)
        log.debug("input device_addr: %s", self.device_addr)
        log.debug("session device_addr: %s", v["device_addr"])

        log.debug("self.device_addr: %s sssion device_addr: %s", self.device_addr, v.get("device_addr"))
        if self.device_addr != v.get("device_addr"):
            return False

        self.load_device()
        if self.data["status"] != define.UYU_DEVICE_ENABLE:
            self.se.rm_session()
            return False

        log.debug("session check ok")
        self.sauth = True
        return True

    @dbpool.with_database('uyu_core')
    def load_device(self):
        sql = "select * from device where blooth_tag=%s" % self.device_addr
        ret = self.db.get(sql)
        self.data = ret


def uyu_check_device_session(redis_pool, cookie_conf):
    def f(func):
        def _(self, *args, **kwargs):
            try:
                sk = self.get_cookie("sessionid")
                log.debug("sk: %s", sk)
                self.session = DSession(redis_pool, cookie_conf, sk)

                params = self.req.input()
                device_addr = params.get("se_device_addr", -1)
                self.device = SDevice(device_addr, self.session)
                self.device.check_permission()

                x = func(self, *args, **kwargs)
                self.session.expire_session()
                return x
            except:
                log.warn(traceback.format_exc())
                return error(UAURET.SERVERERR)
        return _
    return f

def uyu_set_device_cookie(redis_pool, cookie_conf):
    def f(func):
        def _(self, *args, **kwargs):
            try:
                x = func(self, *args, **kwargs)
                #创建SESSION
                self.session = DSession(redis_pool, cookie_conf)
                self.session.gen_skey()

                v = json.loads(x)
                if v["respcd"] == UAURET.OK:
                    self.session.set_session(v["data"])
                    self.set_cookie("sessionid", self.session.sk, **cookie_conf)
                return x
            except:
                log.warn(traceback.format_exc())
                return error(UAURET.SERVERERR)
                #raise
        return _
    return f
