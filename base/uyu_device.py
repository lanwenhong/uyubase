# -*- coding: utf-8 -*-
import os, sys
from zbase.base.dbpool import with_database
import logging, time, random
import traceback

import string
import hashlib
import base64

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


class UDevice:
    def __init__(self):
        self.device_addr = None
        self.data = {}
        self.login = False

    @with_database('uyu_core')
    def check_device_login(self, device_addr, password):
        record = self.db.select_one(table='device', where={'blooth_tag': device_addr})
        log.debug("get record:%s", record)
        if record:
            self.data['password'] = record.get('password')
            self.data['device_addr'] = record.get('blooth_tag')
            self.data['device_id'] = record.get('id')
            self.data['device_name'] = record.get('device_name')
            self.data['channel_id'] = record.get('channel_id')
            self.data['store_id'] = record.get('store_id')
            self.data['status'] = record.get('status')
            if check_password(password, self.data['password']):
                self.login = True

    def call(self, func_name, *args, **kwargs):
        try:
            func = getattr(self, func_name)
            func(*args, **kwargs)
            return UYU_OP_OK
        except:
            log.warn(traceback.format_exc())
            return UYU_OP_ERR
