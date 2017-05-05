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


class USession:
    def __init__(self, redis_pool, c_conf, sk=None):
        self.sk = sk
        self.redis_pool = redis_pool
        self.c_conf = c_conf

    def gen_skey(self):
        self.sk = str(uuid.uuid4())

    def set_session(self, value, sys_role):
        svalue = {}
        svalue["userid"] = value["userid"]
        svalue["user_type"] = sys_role
        if value.get("login_id", None):
            svalue["login_id"] = value.get("login_id")

        client = redis.StrictRedis(connection_pool=self.redis_pool)
        client.set(self.sk, json.dumps(svalue))
        client.expire(self.sk, self.c_conf["expires"])

        client.rpush(svalue["userid"], self.sk)
        if svalue.get("login_id", None):
            client.rpush(svalue["login_id"], self.sk)

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

class KickSession:
    def __init__(self, redis_pool, userid):
        self.redis_pool = redis_pool
        self.userid = userid

    def kick(self):
        client = redis.StrictRedis(connection_pool=self.redis_pool)
        while True:
            ret = client.lpop(userid)
            if not ret:
                break
            client.delete(ret)

class SUser:
    def __init__(self, userid, session, sys_role):
        #session 检查， SESSION中的USERID和传上来的USERID是否一致
        self.sauth = False
        #标记系统是渠道系统或者渠道运营系统或者门店系统后台
        self.sys_role = sys_role
        self.userid = int(userid)
        self.udata = None
        self.pdata = None
        self.sdata = None
        self.cdata = None
        self.se = session

    #检查SESSION对应的USERID是否有权限获取用户数据
    def check_permission(self):
        #是否能获取SESSION
        v = self.se.get_session()
        if not v:
            return False

        log.debug("get session: %s", v)
        log.debug("cuserid: %d", self.userid)
        log.debug("suserid: %d", v["userid"])

        #session中的用户角色和系统是否一致
        user_type = v.get("user_type")
        plist = define.PERMISSION_CHECK.get(self.sys_role, None)
        if not plist:
            return False

        log.debug("user_type: %d get plist: %s", user_type, plist)
        if user_type not in plist:
            return False

        log.debug("self.userd: %d s_userid: %d", self.userid, v.get("userid"))
        if self.userid != v.get("userid"):
            return False

        self.load_user()
        if self.udata["state"] != define.UYU_USER_STATE_OK:
            self.se.rm_session()
            return False

        log.debug("session check ok")
        self.sauth = True
        return True

    @dbpool.with_database('uyu_core')
    def load_user(self):
        sql = "select * from auth_user where id=%d" % self.userid
        ret = self.db.get(sql)
        self.udata = ret

    #load 渠道用户，门店用户，医院用户的档案数据
    @dbpool.with_database("uyu_core")
    def load_profile(self):
        if not self.udata:
            return
        user_type = self.udata.get("user_type", -1)
        #门店，医院和渠道才有profile信息
        # if user_type != define.UYU_USER_ROLE_CHAN and user_type != define.UYU_USER_ROLE_STORE:
        if user_type not in [define.UYU_USER_ROLE_CHAN, define.UYU_USER_ROLE_STORE, define.UYU_USER_ROLE_HOSPITAL]:
            return
        sql = "select * from profile where userid=%d" % self.userid
        self.pdata= self.db.get(sql)

    @dbpool.with_database("uyu_core")
    def load_store(self):
        if not self.udata or not self.pdata:
            return
        user_type = self.udata.get("user_type", -1)
        #if user_type != define.UYU_USER_ROLE_STORE:
        if user_type not in [define.UYU_USER_ROLE_STORE, define.UYU_USER_ROLE_HOSPITAL]:
            return
        sql = "select * from stores where userid=%d" % self.userid
        self.sdata = self.db.get(sql)

    @dbpool.with_database('uyu_core')
    def load_channel(self):
        if not self.udata or not self.pdata:
            return
        user_type = self.udata.get('user_type', -1)

        if user_type != define.UYU_USER_ROLE_CHAN:
            return

        ret = self.db.select_one(table='channel', where={'userid': self.userid})
        self.cdata = ret


def uyu_check_session(redis_pool, cookie_conf, sys_role):
    def f(func):
        def _(self, *args, **kwargs):
            try:
                sk = self.get_cookie("sessionid")
                log.debug("sk: %s", sk)
                self.session = USession(redis_pool, cookie_conf, sk)

                params = self.req.input()
                userid = params.get("se_userid", -1)
                self.user = SUser(userid, self.session, sys_role)
                self.user.check_permission()

                x = func(self, *args, **kwargs)
                #set cookie
                self.session.expire_session()
                return x
            except:
                log.warn(traceback.format_exc())
                return error(UAURET.SERVERERR)
        return _
    return f

def uyu_set_cookie(redis_pool, cookie_conf, user_role):
    def f(func):
        def _(self, *args, **kwargs):
            try:
                x = func(self, *args, **kwargs)
                #创建SESSION
                self.session = USession(redis_pool, cookie_conf)
                self.session.gen_skey()

                v = json.loads(x)
                if v["respcd"] == UAURET.OK:
                    self.session.set_session(v["data"], user_role)
                    self.set_cookie("sessionid", self.session.sk, **cookie_conf)
                return x
            except:
                log.warn(traceback.format_exc())
                return error(UAURET.SERVERERR)
                #raise
        return _
    return f


def uyu_check_session_for_page(redis_pool, cookie_conf, sys_role):
    def f(func):
        def _(self, *args, **kwargs):
            try:
                flag = True
                sk = self.get_cookie("sessionid")
                log.debug("sk: %s", sk)
                self.session = USession(redis_pool, cookie_conf, sk)
                v = self.session.get_session()
                if not v:
                    flag = False

                plist = define.PERMISSION_CHECK.get(sys_role, None)
                if not plist:
                    log.debug('tool permission error')
                    flag = False

                log.debug("tool get plist: %s", plist)
                if v:
                    user_type = v.get("user_type")
                    log.debug("user_type: %d", user_type)
                    if user_type not in plist:
                        log.debug('tool user type error')
                        flag = False

                if not flag:
                    if sys_role == define.UYU_SYS_ROLE_OP:
                        self.redirect('/channel_op/v1/page/login.html')
                    else:
                        self.redirect('/channel/v1/page/login.html')

                ret = func(self, *args, **kwargs)
                return ret
            #except Exception as e:
            except:
                #log.warn(e)
                log.warn(traceback.format_exc())
                log.debug('tool except redirect')
                if sys_role == define.UYU_SYS_ROLE_OP:
                    self.redirect('/channel_op/v1/page/login.html')
                else:
                    self.redirect('/channel/v1/page/login.html')
        return _
    return f


def check_login(func):
    """sessionid userid all"""
    def _(self, *args, **kwargs):
        try:
            if not self.user.sauth:
                # 带修改
                self.redirect('/channel_op/v1/page/login.html')
            ret = func(self, *args, **kwargs)
            return ret
        except Exception as e:
            log.warn(e)
            print 'except redirect'
            # 带修改
            self.redirect('/channel_op/v1/page/login.html')
    return _
