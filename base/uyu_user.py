#coding: utf-8

import os, sys
from zbase.base.dbpool import with_database
import logging, time, random
import traceback

import string
import hashlib

from uyubase.base.response import success, error, UAURET
from uyubase.uyu import define
from uyubase.uyu.define import UYU_OP_OK, UYU_OP_ERR

import logging, datetime
log = logging.getLogger()


def gen_passwd(password):
    pre = ''
    data_str = string.lowercase + string.digits
    data_list = list(data_str)
    # len = random.randint(5,15)
    len = 5
    for i in range(0, len):
        pre += random.choice(data_list)

    deal_passwd=hashlib.sha1(pre+password).hexdigest()
    finish_passwd='sha1$'+pre+'$'+deal_passwd
    return finish_passwd


def constant_time_compare(val1, val2):
    if len(val1) != len(val2):
        return False
    result = 0
    for x, y in zip(val1, val2):
        result |= ord(x) ^ ord(y)
    return result == 0


def get_hexdigest(algorithm, salt, raw_password):
    if algorithm == 'crypt':
        try:
            import crypt
        except ImportError:
            raise ValueError('"crypt" password algorithm not supported in this environment')
        return crypt.crypt(raw_password, salt)

    if algorithm == 'md5':
        return hashlib.md5(salt + raw_password).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(salt + raw_password).hexdigest()
    raise ValueError("Got unknown password algorithm type in password.")


def check_password(raw_password, enc_password):
    algo, salt, hsh = enc_password.split('$')
    return constant_time_compare(hsh, get_hexdigest(algo, salt, raw_password))


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
        md5_password = hashlib.md5(mobile[-6:]).hexdigest()
        sql_value["password"] = gen_passwd(md5_password)
        sql_value["state"] = define.UYU_USER_STATE_OK
        self.db.insert("auth_user", sql_value)
        self.userid = self.db.last_insert_id()


    #内部用户注册
    @with_database('uyu_core')
    def internal_user_register(self, udata):
        mobile = udata.pop('mobile')
        sql_value = self.__gen_vsql(self.ukey, udata)
        ret = self.db.select_one(table='auth_user', fields='*', where={'phone_num': mobile})
        if ret:
            return False, None
        password = udata['password']
        sql_value['login_name'] = mobile
        sql_value['phone_num'] = mobile
        md5_password = hashlib.md5(password).hexdigest()
        sql_value["password"] = gen_passwd(md5_password)
        sql_value["state"] = define.UYU_USER_STATE_OK
        sql_value["ctime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.insert("auth_user", sql_value)
        return True, self.db.last_insert_id()


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
            md5_password = hashlib.md5(mobile[-6:]).hexdigest()
            sql_value["password"] = gen_passwd(md5_password)
            sql_value["state"] = define.UYU_USER_STATE_OK
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
        if state == define.UYU_CHAN_STATUS_OPEN:
            user_state = define.UYU_USER_STATE_OK
        else:
            user_state = define.UYU_USER_STATE_FORBIDDEN
        self.db.update("auth_user", {"state": user_state}, {"id": userid})

    #设置门店状态，打开/关闭
    @with_database('uyu_core')
    def set_store_state(self, userid, state):
        self.db.update("stores", {"is_valid": state}, {"userid": userid})
        if state == define.UYU_STORE_STATUS_OPEN:
            user_state = define.UYU_USER_STATE_OK
        else:
            user_state = define.UYU_USER_STATE_FORBIDDEN
        self.db.update("auth_user", {"state": user_state}, {"id": userid})

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

            where = {"eyesight_id": userid, "store_id": store_id, "channel_id": chan_id}
            ret = self.db.select_one(table='store_eyesight_bind', fields='*', where=where)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if not ret:
                sql_value = {"eyesight_id": userid, "store_id": store_id, "channel_id": chan_id, 'is_valid': define.UYU_STORE_EYESIGHT_BIND}
                sql_value['ctime'] = now
                sql_value['utime'] = now
                self.db.insert("store_eyesight_bind", sql_value)
                return True, UAURET.OK
            else:
                is_valid = ret.get('is_valid')
                if is_valid == define.UYU_STORE_EYESIGHT_BIND:
                    return False, UAURET.DATAEXIST
                else:
                    self.db.update(
                        table='store_eyesight_bind',
                        values={'is_valid': define.UYU_STORE_EYESIGHT_BIND, 'utime': now},
                        where={'eyesight_id': userid, 'store_id': store_id, 'channel_id': chan_id}
                    )
                    return True, UAURET.OK

        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
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
        record = self.db.select_one("auth_user", {"phone_num": mobile, "state": define.UYU_USER_STATE_OK})
        log.debug("get record: %s", record)
        if record:
            for key in self.ukey:
                log.debug(key)
                if record.get(key, None):
                    self.udata[key] = record[key]
            if self._check_permission(self.udata['user_type'], sys_role) and check_password(password, self.udata["password"]):
                self.login = True

    @with_database('uyu_core')
    def change_password(self, mobile, vcode, password):
        try:
            now = int(time.time())
            sql = "select * from verify_code where mobile='%s' and stime<%d and etime>%d" % (mobile, now, now)
            dbret = self.db.get(sql)
            log.debug("dbret: %s", dbret)
            # 修改密码的password是js已经md5后的hash
            enc_password = gen_passwd(password)
            if dbret and vcode == dbret['code']:
                sql = "update auth_user set password='%s' where phone_num='%s'" % (enc_password, mobile)
                self.db.execute(sql)
                return UAURET.OK
            return UAURET.VCODEERR
        except:
            log.warn(traceback.format_exc())
            return UAURET.VCODEERR

    @with_database('uyu_core')
    def create_device(self, device_name, hd_version, blooth_tag, scm_tag, status, channel_id, store_id=None, training_nums=None, op=None):
        try:
            values = {}
            values['device_name'] = device_name;
            values['hd_version'] = hd_version;
            values['blooth_tag'] = blooth_tag;
            values['scm_tag'] = scm_tag;
            values['status'] = status;
            values['channel_id'] = channel_id;
            values['store_id'] = store_id;
            values['training_nums'] = training_nums;
            values['op'] = op;
            now = datetime.datetime.now()
            values['ctime'] = now
            values['utime'] = now
            ret = self.db.insert(table='device', values=values)
            log.debug('create device value:%s, ret:%s', values, ret)
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            raise

    @with_database('uyu_core')
    def allocate_device(self, channel_id, store_id, serial_number):
        try:
            where = {'id': serial_number}
            values = {'channel_id': channel_id}
            # if store_id:
            values.update({'store_id': store_id})
            ret = self.db.update(table='device', values=values, where=where)
            log.debug('allocate_device values:%s, where: %s, ret: %s', values, where, ret)
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            raise

    def call(self, func_name, *args, **kwargs):
        try:
            func = getattr(self, func_name)
            func(*args, **kwargs)
            return UYU_OP_OK
        except:
            log.warn(traceback.format_exc())
            return UYU_OP_ERR
