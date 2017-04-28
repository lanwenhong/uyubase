# -*- coding: utf-8 -*-
import logging
import traceback
from CCPRestSDK import REST
from uyubase.uyu import define

log = logging.getLogger()

class UYUSendSMS(REST):

    def __init__(self):
        self.account_sid = define.RONG_YUN_SMS_ACCOUNT_SID
        self.account_token = define.RONG_YUN_SMS_ACCOUNT_TOKEN
        self.app_id = define.RONG_YUN_SMS_APPID
        self.server_ip = define.RONG_YUN_SMS_SERVER_IP
        self.server_port = define.RONG_YUN_SMS_SERVER_PORT
        self.soft_version = define.RONG_YUN_SMS_SOFT_VERSION
        super(UYUSendSMS, self).__init__(self.server_ip, self.server_port, self.soft_version)
        self.init()

    def init(self):
        self.setAccount(self.account_sid, self.account_token)
        self.setAppId(self.app_id)
        self.BodyType = 'json'

    def send_sms(self, to, datas, temp_id):
        try:
            result = self.sendTemplateSMS(to, datas, temp_id)
            log.debug('send_sms result: %s', result)
            return result
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            log.debug('send_sms except')
            return None
