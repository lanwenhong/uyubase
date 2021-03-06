#coding: utf-8

import os, sys
from zbase.base.dbpool import with_database
import logging, time, random
import traceback

from uyubase.base.response import success, error, UAURET
from uyubase.uyu import define
from uyubase.uyu.define import UYU_OP_OK, UYU_OP_ERR

import logging, datetime
log = logging.getLogger()

class VCode:
    def __init__(self):
        pass

    @with_database('uyu_core')
    def gen_vcode(self, mobile):
        try:
            now = int(time.time())
            sql = "select * from verify_code where mobile='%s' and stime<%d and etime>%d" % (mobile, now, now)
            dbret = self.db.get(sql)

            if not dbret:
                vcode = ''
                for i in xrange(0, 4):
                    vcode += str(random.randint(0,9))
                sql = "insert into verify_code set mobile='%s', code='%s', stime=%d, etime=%d" % (mobile, vcode, int(time.time()), int(time.time()) + 60)
                self.db.execute(sql)
                return vcode
            else:
                return dbret["code"]
        except:
            log.warn(traceback.format_exc())
            return None

    def sms_vcode(self, vcode):
        pass

class UUser:
    def __init__(self):
        self.userid = None
        self.udata = {}
        self.pdata = {}
        self.cdata = {}
        self.sdata = {}

        self.login = False

        self.ukey = [
            "login_name", "nick_name", "phone_num", "password",
            "ctime", "utime", "user_type", "email",
            "sex", "state", "id", "username",
        ]

        self.pkey = [
            "userid", "org_code", "license_id", "legal_person",
            "business", "front_business", "account_name", "bank_name",
            "bank_account", "contact_name", "contact_phone", "contact_email",
            "address", "org_pic", "license_pic", "idcard_no",
            "idcard_front", "idcard_back", "state", "ctime",
        ]

        self.chan_key = [
            "userid", "remain_times", "training_amt_per", "divide_percent",
            "status", "is_valid", "is_prepayment", "ctime",
            "channel_name",
        ]

        self.skey = [
            "userid", "channel_id", "store_type", "store_contacter",
            "store_mobile", "store_addr", "training_amt_per", "divide_percent",
            "remain_times", "is_valid", "ctime", "utime",
            "store_name",
        ]

    def __gen_vsql(self, klist, cdata):
        sql_value = {}
        for key in cdata:
            if cdata.get(key, None) != None:
                sql_value[key] = cdata[key]
        return sql_value

    #用户注册
    @with_database('uyu_core')
    def user_register(self, udata):
        sql_value = self.__gen_vsql(self.ukey, udata)
        sql_value["ctime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mobile = udata["login_name"]
        #默认密码手机号后六位
        sql_value["password"] = mobile[-6:]
        sql_value["state"] = define.UYU_USER_STATE_OK
        self.db.insert("auth_user", sql_value)
        self.userid = self.db.last_insert_id()
    

    @with_database('uyu_core')
    def load_user_by_mobile(self, mobile):
        record = self.db.select_one("auth_user", {"phone_num": mobile})
        log.debug('#record: %s', record)
        if record:
            for key in self.ukey:
                if record.get(key, None):
                    self.udata[key] = record[key]
            self.udata["userid"] = record["id"]

    def __gen_base_user_sql(self, role, udata):
            sql_value = self.__gen_vsql(self.ukey, udata)
            sql_value["ctime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            mobile = udata["login_name"]
            sql_value["password"] = mobile[-6:]
            sql_value["state"] = define.UYU_USER_STATE_OK
            #sql_value["user_type"] = define.UYU_USER_ROLE_CHAN
            sql_value["user_type"] = role
            return sql_value

    def __gen_profile_sql(self, userid, pdata):
            sql_value = self.__gen_vsql(self.pkey, pdata)
            sql_value["userid"] = userid
            sql_value["state"] = define.UYU_USER_PROFILE_STATE_UNAUDITED
            sql_value["ctime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sql_value["userid"] = userid
            return sql_value


    def __gen_chan_sql(self, userid, cdata):
            sql_value = self.__gen_vsql(self.chan_key, cdata)
            sql_value["userid"] = userid
            sql_value["is_valid"] = define.UYU_CHAN_STATUS_OPEN
            sql_value["ctime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return sql_value

    def __gen_store_sql(self, userid, sdata):
            sql_value = self.__gen_vsql(self.skey, sdata)
            sql_value["userid"] = userid
            sql_value["is_valid"] = define.UYU_STORE_STATUS_OPEN
            sql_value["ctime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return sql_value

    #创建渠道事务
    @with_database('uyu_core')
    def create_chan_transaction(self, udata, pdata, cdata):
        try:
            self.db.start()
            #创建用户基本信息
            sql_value = self.__gen_base_user_sql(define.UYU_USER_ROLE_CHAN, udata)
            log.debug("auth_user sql: %s", sql_value)
            self.db.insert("auth_user", sql_value)
            userid = self.db.last_insert_id()

            #创建渠道档案
            sql_value = self.__gen_profile_sql(userid, pdata)
            log.debug("profile sql: %s", sql_value)
            self.db.insert("profile", sql_value)

            #创建渠道相关信息
            sql_value = self.__gen_chan_sql(userid, cdata)
            self.db.insert("channel", sql_value)
            chnid = self.db.last_insert_id()

            self.db.commit()
            self.userid = userid
            self.chnid = chnid
        except:
            self.db.rollback()
            raise

    #创建门店信息
    @with_database('uyu_core')
    def create_store_transaction(self, udata, pdata, sdata):
        try:
            self.db.start()
            #创建用户基本信息
            sql_value = self.__gen_base_user_sql(define.UYU_USER_ROLE_STORE, udata)
            self.db.insert("auth_user", sql_value)
            userid = self.db.last_insert_id()

            #创建渠道档案
            sql_value = self.__gen_profile_sql(userid, pdata)
            self.db.insert("profile", sql_value)

            #创门店相关信息
            sql_value = self.__gen_store_sql(userid, sdata)
            self.db.insert("stores", sql_value)
            store_id = self.db.last_insert_id()

            self.db.commit()
            self.userid = userid
            self.store_id = store_id
            self.chnid = sdata["channel_id"]

        except:
            self.db.rollback()
            raise

    #设置渠道状态， 打开/关闭
    @with_database('uyu_core')
    def set_chan_state(self, userid, state):
        self.db.update("channel", {"is_valid": state}, {"userid": userid})
        self.db.update("auth_user", {"state": define.UYU_USER_STATE_FORBIDDEN}, {"id": userid})

    #设置门店状态，打开/关闭
    @with_database('uyu_core')
    def set_store_state(self, userid, state):
        self.db.update("stores", {"is_valid": state}, {"userid": userid})
        self.db.update("auth_user", {"state": define.UYU_USER_STATE_FORBIDDEN}, {"id": userid})

    @with_database('uyu_core')
    def __update_user(self, userid, udata):
        sql_value = self.__gen_vsql(self.ukey, udata)
        sql_value["utime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.update("auth_user", sql_value, {"id": userid})
        log.debug("update auth_user succ!!!")

    @with_database('uyu_core')
    def __update_profile(self, userid, pdata):
        sql_value = self.__gen_vsql(self.pkey, pdata)
        sql_value["utime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.update("profile", sql_value, {"userid": userid})
        log.debug("update profile succ!!!")

    @with_database('uyu_core')
    def __update_chan(self, userid, cdata):
        sql_value = self.__gen_vsql(self.chan_key, cdata)
        sql_value["utime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.update("channel", sql_value, {"userid": userid})
        log.debug("update channel succ!!!")


    @with_database('uyu_core')
    def __update_store(self, userid, sdata):
        sql_value = self.__gen_vsql(self.skey, sdata)
        sql_value["utime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.update("stores", sql_value, {"userid": userid})
        log.debug("update store succ!!!")

    #更新渠道信息
    def chan_info_change(self, userid, udata, pdata, cdata):
        self.__update_user(userid, udata)
        self.__update_profile(userid, pdata)
        self.__update_chan(userid, cdata)

    #更新门店信息
    def store_info_change(self, userid, udata, pdata, sdata):
        self.__update_user(userid, udata)
        self.__update_profile(userid, pdata)
        self.__update_store(userid, sdata)

    #门店绑定视光师
    @with_database("uyu_core")
    def store_bind_eyesight(self, userid, store_id, chan_id):
        try:
            sql_value = {"eyesight_id": userid, "store_id": store_id, "channel_id": chan_id, 'is_valid': define.UYU_STORE_EYESIGHT_BIND}
            sql_value['ctime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.insert("store_eyesight_bind", sql_value)
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            if 'Duplicate entry' in e[1]:
                self.db.update(table='store_eyesight_bind',
                               values={'is_valid': define.UYU_STORE_EYESIGHT_BIND},
                               where={'eyesight_id': userid, 'store_id': store_id, 'channel_id': chan_id}
                )
            else:
                raise


    #门店解绑视光师
    @with_database("uyu_core")
    def unbind_eyesight(self, userid, store_id, chan_id):
        where = {}
        sql_value = {}
        sql_value['utime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql_value['is_valid'] = define.UYU_STORE_EYESIGHT_UNBIND
        where['eyesight_id'] = userid
        where['store_id'] = store_id
        where['channel_id'] = chan_id
        self.db.update(table='store_eyesight_bind', values=sql_value, where=where)

    #load用户信息
    @with_database('uyu_core')
    def load_info_by_userid(self, userid):
        record = self.db.select_one("auth_user", {"id": userid})
        if record:
            for key in self.ukey:
                # if record.get(key, None):
                self.udata[key] = record[key]
            self.udata["userid"] = userid
        else:
            log.warn("not found: %d", userid)
            return
        role = self.udata["user_type"]

        if role == define.UYU_USER_ROLE_CHAN or role == define.UYU_USER_ROLE_STORE:
            record = self.db.select_one("profile", {"userid": userid})
            if record:
                for key in self.pkey:
                    # if record.get(key, None):
                    self.pdata[key] = record[key]
                self.udata["userid"] = userid

        if role == define.UYU_USER_ROLE_CHAN:
            record = self.db.select_one("channel", {"userid": userid})
            if record:
                for key in self.chan_key:
                    # if record.get(key, None):
                    self.cdata[key] = record[key]
                self.cdata["chnid"] = record["id"]

        if role == define.UYU_USER_ROLE_STORE:
            record = self.db.select_one("stores", {"userid": userid})
            if record:
                for key in self.skey:
                    # if record.get(key, None):
                    self.sdata[key] = record[key]
                self.sdata["store_id"] = record["id"]

    def _check_permission(self, user_type, sys_role):
        log.debug(define.PERMISSION_CHECK)
        plist = define.PERMISSION_CHECK.get(sys_role, None)
        if not plist:
            return False

        log.debug("plist: %s", plist)
        if user_type not in plist:
            log.debug("user login forbidden")
            return False
        return True

    @with_database('uyu_core')
    def check_userlogin(self, mobile, password, sys_role):
        record = self.db.select_one("auth_user", {"phone_num": mobile, "password": password, "state": define.UYU_USER_STATE_OK})
        log.debug("get record: %s", record)
        if record:
            for key in self.ukey:
                log.debug(key)
                if record.get(key, None):
                    self.udata[key] = record[key]
            if self._check_permission(self.udata['user_type'], sys_role) and password == self.udata["password"]:
                self.login = True

    @with_database('uyu_core')
    def change_password(self, mobile, vcode, password):
        try:
            now = int(time.time())
            sql = "select * from verify_code where mobile='%s' and stime<%d and etime>%d" % (mobile, now, now)
            dbret = self.db.get(sql)
            log.debug("dbret: %s", dbret)

            if dbret and vcode == dbret['code']:
                sql = "update auth_user set password='%s' where phone_num='%s'" % (password, mobile)
                self.db.execute(sql)
                return UAURET.OK
            return UAURET.VCODEERR
        except:
            log.warn(traceback.format_exc())
            return UAURET.VCODEERR

    def call(self, func_name, *args, **kwargs):
        try:
            func = getattr(self, func_name)
            func(*args, **kwargs)
            return UYU_OP_OK
        except:
            log.warn(traceback.format_exc())
            return UYU_OP_ERR
