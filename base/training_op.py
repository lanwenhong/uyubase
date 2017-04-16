#coding: utf-8
import os, sys
from zbase.utils import createid
from zbase.base.dbpool import with_database
from zbase.base import dbpool
import traceback
from uyubase.uyu.define import UYU_OP_OK, UYU_OP_ERR, UYU_ORDER_STATUS_NEED_CONFIRM, UYU_ORDER_STATUS_SUCC
from uyubase.uyu import define
from uyubase.base import response
from zbase.utils.createid import new_id64

import datetime
import logging
log = logging.getLogger()

class StoreToConsumerCancel:
    def __init__(self, order_no):
        self.order_no = order_no

    @with_database('uyu_core')
    def do_cancel(self):
        try:
            self.db.start()
            sql = "select * from training_operator_record where orderno='%s' for update" % self.order_no
            dbret = self.db.get(sql)
            if not dbret:
                self.db.rollback()
                return UYU_OP_ERR

            self.store_id = dbret.get("store_id", None)
            self.consumer_id = dbret.get("consumer_id", None)
            self.cancel_times = dbret.get("training_times")
            ctime = dbret["create_time"]

            db_day = ctime.strftime("%Y-%m-%d")
            n_day = datetime.datetime.now().strftime("%Y-%m-%d")
            if db_day != n_day:
                 self.db.rollback()
                 return UYU_OP_ERR

            uptime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sql = "update training_operator_record set status=%d, uptime_time='%s' where orderno='%s' and status=%d" % (define.UYU_ORDER_STATUS_CANCEL,
                    uptime,
                    dbret["orderno"],
                    define.UYU_ORDER_STATUS_SUCC
                    )
            ret = self.db.execute(sql)
            if ret == 0:
                self.db.rollback()
                log.warn("update order %s fail", self.dbret["orderno"])
                return UYU_OP_ERR
            sql = "update stores set remain_times=remain_times+%d where id=%d" % (self.cancel_times, self.store_id)
            ret = self.db.execute(sql)
            if ret == 0:
                self.db.rollback()
                log.warn("update sotres %d fail", self.store_id)
                return UYU_OP_ERR
            sql = "update consumer set remain_times=remain_times-%d where userid=%d and remain_times>=%d" % (self.cancel_times, self.consumer_id, self.cancel_times)
            ret = self.db.execute(sql)
            if ret == 0:
                log.warn("update consumer %d fail", self.consumer_id)
                self.db.rollback()
                return UYU_OP_ERR
            self.db.commit()
            return UYU_OP_OK
        except:
            self.db.rollback()
            log.warn(traceback.format_exc())
            return UYU_OP_ERR

class OrgAllotToChanCancel:
    def __init__(self, order_no):
        self.order_no = order_no

    @with_database('uyu_core')
    def do_cancel(self):
        try:
            self.db.start()

            sql = "select * from training_operator_record where orderno='%s' for update" % self.order_no
            dbret = self.db.get(sql)
            if not dbret:
                self.db.rollback()
                return UYU_OP_ERR
            self.channel_id = dbret.get("channel_id", None)
            self.cancel_times = dbret.get("training_times")
            ctime = dbret["create_time"]

            db_day = ctime.strftime("%Y-%m-%d")
            n_day = datetime.datetime.now().strftime("%Y-%m-%d")
            if db_day != n_day:
                 self.db.rollback()
                 return UYU_OP_ERR

            uptime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sql = "update training_operator_record set status=%d, uptime_time='%s'  where orderno='%s' and status=%d" % (define.UYU_ORDER_STATUS_CANCEL,
                uptime,
                dbret["orderno"],
                define.UYU_ORDER_STATUS_SUCC
                )
            ret = self.db.execute(sql)
            if ret == 0:
                self.db.rollback()
                return UYU_OP_ERR
            # sql = "update channel set remain_times=remain_times-%d where id=%d and remain_times>=%d" % (self.cancel_times, self.channel_id, self.cancel_times)
            sql = "update channel set remain_times=remain_times-%d where id=%d" % (self.cancel_times, self.channel_id)
            ret = self.db.execute(sql)
            if ret == 0:
                self.db.rollback()
                return UYU_OP_ERR
            self.db.commit()
            return UYU_OP_OK
        except:
            self.db.rollback()
            log.warn(traceback.format_exc())
            return UYU_OP_ERR

class ChanAllotStoreCancel:
    def __init__(self, order_no):
        self.order_no = order_no

    @with_database('uyu_core')
    def do_cancel(self):
        try:
            self.db.start()
            sql = "select * from training_operator_record where orderno='%s' for update" % self.order_no
            dbret = self.db.get(sql)
            if not dbret:
                self.db.rollback()
                return UYU_OP_ERR
            self.channel_id = dbret.get("channel_id", None)
            self.store_id = dbret.get("store_id", None)
            self.cancel_times = dbret.get("training_times")
            ctime = dbret["create_time"]

            db_day = ctime.strftime("%Y-%m-%d")
            n_day = datetime.datetime.now().strftime("%Y-%m-%d")
            if db_day != n_day:
                 self.db.rollback()
                 return UYU_OP_ERR

            uptime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sql = "update training_operator_record set status=%d, uptime_time='%s' where orderno='%s' and status=%d" % (define.UYU_ORDER_STATUS_CANCEL,
                uptime,
                dbret["orderno"],
                define.UYU_ORDER_STATUS_SUCC
                )

            ret = self.db.execute(sql)
            if ret == 0:
                self.db.rollback()
                return UYU_OP_ERR
            sql = "update channel set remain_times=remain_times+%d where id=%d" % (self.cancel_times, self.channel_id)
            ret = self.db.execute(sql)
            if ret == 0:
                self.db.rollback()
                return UYU_OP_ERR
            sql = "update stores set remain_times=remain_times-%d where id=%d and remain_times>=%d" % (self.cancel_times, self.store_id, self.cancel_times)
            ret = self.db.execute(sql)
            if ret == 0:
                self.db.rollback()
                return UYU_OP_ERR
            self.db.commit()
            return UYU_OP_OK
        except:
            self.db.rollback()
            log.warn(traceback.format_exc())
            return UYU_OP_ERR


class TrainingOP:
    def __init__(self, cdata=None, suser=None, order_no=None):
        self.data_key = (
            "busicd",  "channel_id", "store_id", "consumer_id",
            "category", "op_type", "pay_type", "training_times",
            "training_amt", "status", "op_name", "orderno",
            "create_time", "update_time", "ch_training_amt_per",
            "store_training_amt_per", "remark",
        )
        self.db_data = {}
        self.cdata = cdata
        self.suser = suser
        self.respcd = None

        self.order_no = order_no

        self.cancel_handler = {
            define.BUSICD_ORG_ALLOT_TO_CHAN: OrgAllotToChanCancel,
            define.BUSICD_CHAN_ALLOT_TO_STORE: ChanAllotStoreCancel,
            define.BUSICD_CHAN_ALLOT_TO_COSUMER: StoreToConsumerCancel,
            define.BUSICD_CHAN_BUY_TRAING_TIMES: OrgAllotToChanCancel,
        }

    def create_orderno(self):
        with dbpool.get_connection('uyu_core') as conn:
            sql = "replace into counter set name=%d" % 1
            ret = conn.execute(sql)

            if ret != 2:
                log.warn("create order_no error")
                raise ValueError, "order_no counter error"
            c_id = "%08d" % (conn.last_insert_id() % 100000000)
            order_no = datetime.datetime.now().strftime("%Y%m%d") + c_id

            return order_no

    #@with_database('uyu_core')
    #def __check_cancel_permission(self):
    #    dbret = self.db.select_one("training_operator_record", {"orderno": self.order_no})
    #    ctime = dbret["create_time"]
    #    db_day = ctime.strftime("%Y-%m-%d")
    #    n_day = datetime.datetime.now().strftime("%Y-%m-%d")
    #    if db_day != n_day:
    #        return False, None
    #    return True, dbret

    @with_database('uyu_core')
    def __get_busicd(self):
        dbret = self.db.select_one('training_operator_record', {"orderno": self.order_no})
        if not dbret:
            return False, None
        return True, dbret["busicd"]


    def order_cancel(self):
        flag, busicd = self.__get_busicd()
        if not flag:
            return UYU_OP_ERR
        log.debug("busicd: %s", busicd)
        handler_class = self.cancel_handler.get(busicd)
        if not handler_class:
            return UYU_OP_ERR
        log.debug("order_no: %s", self.order_no)
        obj_handler = handler_class(self.order_no)
        ret = obj_handler.do_cancel()
        return ret


    def order_confirm(self):
        flag, busicd = self.__get_busicd()
        if not flag:
            return UYU_OP_ERR
        log.debug("busicd: %s", busicd)
        obj_handler = OrgConfirmChannel(self.order_no)
        ret = obj_handler.do_confirm()
        return ret


    def __gen_vsql(self, order_status):
        sql_value = {}
        order_no = self.create_orderno()
        log.debug("order_no: %s", order_no)

        for key in self.data_key:
            if self.cdata.get(key, None):
                sql_value[key] = self.cdata[key]

        sql_value["orderno"] = order_no
        sql_value["status"] = order_status
        create_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql_value["create_time"] = create_time

        return sql_value


    def __gen_buyer_seller(self, busicd, sql_value, channel_id=None, store_id=None, consumer_id=None):
        if busicd == define.BUSICD_ORG_ALLOT_TO_CHAN:
            ch_ret = self.db.select_one(table='channel', fields='channel_name, userid, is_prepayment', where={'id': channel_id})
            sql_value['buyer'] = ch_ret.get('channel_name')
            sql_value['buyer_id'] = ch_ret.get('userid')
            sql_value['seller'] = '公司'
            sql_value['seller_id'] = 0 
            sql_value['chan_is_prepay'] = ch_ret.get('is_prepayment')
        elif busicd == define.BUSICD_CHAN_BUY_TRAING_TIMES:
            ch_ret = self.db.select_one(table='channel', fields='channel_name, userid, is_prepayment', where={'id': channel_id})
            sql_value['buyer'] = ch_ret.get('channel_name')
            sql_value['buyer_id'] = ch_ret.get('userid')
            sql_value['seller'] = '公司'
            sql_value['seller_id'] = 0 
            sql_value['chan_is_prepay'] = ch_ret.get('is_prepayment')
        elif busicd == define.BUSICD_CHAN_ALLOT_TO_STORE:
            ch_ret = self.db.select_one(table='channel', fields='channel_name, userid, is_prepayment', where={'id': channel_id})
            st_ret = self.db.select_one(table='stores', fields='store_name, userid, is_prepayment', where={'id': store_id})
            sql_value['buyer'] =  st_ret.get('store_name')
            sql_value['buyer_id'] = st_ret.get('userid')
            sql_value['seller'] =  ch_ret.get('channel_name')
            sql_value['seller_id'] = ch_ret.get('userid')
            sql_value['chan_is_prepay'] = ch_ret.get('is_prepayment')
            sql_value['store_is_prepay'] = st_ret.get('is_prepayment')
        elif busicd == define.BUSICD_CHAN_ALLOT_TO_COSUMER:
            st_ret = self.db.select_one(table='stores', fields='store_name, userid, is_prepayment', where={'id': store_id})
            at_ret = self.db.select_one(table='auth_user', fields='username', where={'id': consumer_id})
            sql_value['buyer'] = at_ret.get('username')
            sql_value['buyer_id'] = consumer_id
            sql_value['seller'] = st_ret.get('store_name')
            sql_value['seller_id'] = st_ret.get('userid')
            sql_value['store_is_prepay'] = st_ret.get('is_prepayment')
        else:
            pass  

    #公司分配给渠道训练次数的订单
    @with_database('uyu_core')
    def create_org_allot_to_chan_order(self):
        chan_id = self.cdata["channel_id"]
        log.debug("chan_id: %d", chan_id)
        try:
            sql_value = self.__gen_vsql(UYU_ORDER_STATUS_SUCC)
            sql_value["op_type"] = define.UYU_ORDER_TYPE_ALLOT
            sql_value["op_name"] = self.suser.get("username", "")
            sql_value["op_id"] = self.suser.get("id", "")
            self.__gen_buyer_seller(define.BUSICD_ORG_ALLOT_TO_CHAN, sql_value, chan_id)

            self.db.start()
            self.db.insert("training_operator_record", sql_value)
            training_times = self.cdata["training_times"]
            sql = "update channel set remain_times=remain_times+%d where id=%d" % (training_times, chan_id)
            ret = self.db.execute(sql)
            if ret == 0:
                self.db.rollback()
                return UYU_OP_ERR
            else:
                self.db.commit()
                return UYU_OP_OK
        except:
            log.warn(traceback.format_exc())
            self.db.rollback()
            return UYU_OP_ERR

    #渠道分配门店训练次数订单
    @with_database('uyu_core')
    def create_org_allot_to_store_order(self):
        chan_id = self.cdata["channel_id"]
        store_id = self.cdata["store_id"]
        try:
            sql_value = self.__gen_vsql(UYU_ORDER_STATUS_SUCC)

            sql_value["op_type"] = define.UYU_ORDER_TYPE_ALLOT
            sql_value["op_name"] = self.suser.get("username", "")
            sql_value["op_id"] = self.suser.get("id", "")
            self.__gen_buyer_seller(define.BUSICD_CHAN_ALLOT_TO_STORE, sql_value, chan_id, store_id)
            self.db.start()
            self.db.insert("training_operator_record", sql_value)
            training_times = self.cdata["training_times"]
            sql = "update stores set remain_times=remain_times+%d where id=%d and channel_id=%d" % (training_times, store_id, chan_id)
            ret = self.db.execute(sql)
            if ret == 0:
                self.db.rollback()
                return UYU_OP_ERR
            else:
                self.db.commit()
                return UYU_OP_OK
        except:
            log.warn(traceback.foramt_exc())
            sef.db.rollback()
            return UYU_OP_ERR

    #门店分配训练点数给消费者
    @with_database('uyu_core')
    def create_store_allot_to_consumer_order(self):
        store_id = self.cdata["store_id"]
        userid = self.cdata["consumer_id"]
        channel_id = self.cdata["channel_id"]
        ret = self.db.select_one(table='stores', fields='is_prepayment', where={'id': store_id})
        is_prepayment = ret.get('is_prepayment')
        now = datetime.datetime.now()
        try:
            sql_value = self.__gen_vsql(UYU_ORDER_STATUS_SUCC)
            sql_value["op_type"] = define.UYU_ORDER_TYPE_ALLOT
            sql_value["op_name"] = self.suser.get("username", "")
            sql_value["op_id"] = self.suser.get("id", "")
            self.__gen_buyer_seller(define.BUSICD_CHAN_ALLOT_TO_COSUMER, sql_value, store_id=store_id, consumer_id=userid)

            log.debug("=====sql_value: %s", sql_value)
            self.db.start()
            self.db.insert("training_operator_record", sql_value)
            training_times = self.cdata["training_times"]
            if is_prepayment == define.UYU_STORE_PREPAY_TYPE:
                sql = "update stores set remain_times=remain_times-%d, utime='%s' where id=%d and remain_times>%d" % (training_times, now, store_id, training_times)
            else:
                sql = "update stores set remain_times=remain_times-%d, utime='%s' where id=%d" % (training_times, now, store_id)

            ret = self.db.execute(sql)
            if ret == 0:
                self.db.rollback()
                self.respcd = response.UAURET.BALANCEERR
                return UYU_OP_ERR

            record = self.db.select_one(table='consumer', fields='*', where={'userid': userid, 'store_id': store_id})
            if record:
                sql = "update consumer set remain_times=remain_times+%d, uptime_time='%s' where userid=%d and store_id=%d" % (training_times, now, userid, store_id)
                ret = self.db.execute(sql)
                if ret == 0:
                    self.db.rollback()
                    return UYU_OP_ERR
            else:
                now = datetime.datetime.now()
                value = {
                    'userid': userid,
                    'remain_times': training_times,
                    'store_id': store_id,
                    'create_time': now,
                }
                ret = self.db.insert(table='consumer', values=value);
                if ret != 1:
                    self.db.rollback()
                    return UYU_OP_ERR

            use_value = {
                'channel_id': channel_id,
                'store_id': store_id,
                'consumer_id': userid,
                'comsumer_nums': training_times,
                'status': 0,
                'ctime': now,
                'utime': now,
            }

            ret = self.db.insert(table='training_use_record', values=use_value)
            if ret != 1:
                self.db.rollback()
                return UYU_OP_ERR


            self.db.commit()
            return UYU_OP_OK
        except:
            log.warn(traceback.format_exc())
            return UYU_OP_ERR

    #渠道购买训练次数订单
    @with_database('uyu_core')
    def create_chan_buy_trainings_order(self):
        chan_id = self.cdata["channel_id"]
        try:
            sql_value = self.__gen_vsql(UYU_ORDER_STATUS_NEED_CONFIRM)

            sql_value["op_type"] = define.UYU_ORDER_TYPE_BUY
            sql_value["op_name"] = self.suser.get("username", "")
            sql_value["op_id"] = self.suser.get("id", "")
            self.__gen_buyer_seller(define.BUSICD_CHAN_BUY_TRAING_TIMES, sql_value, chan_id)

            self.db.insert("training_operator_record", sql_value)
            return UYU_OP_OK
        except:
            log.warn(traceback.format_exc())
            return UYU_OP_ERR

    #渠道分配训练点数给门店
    @with_database('uyu_core')
    def create_chan_allot_to_store_order(self):
        chan_id = self.cdata["channel_id"]
        ret = self.db.select_one(table='channel', fields='is_prepayment', where={'id': chan_id})
        is_prepayment = ret.get('is_prepayment')
        store_id = self.cdata["store_id"]
        try:
            sql_value = self.__gen_vsql(UYU_ORDER_STATUS_SUCC)

            sql_value["op_type"] = define.UYU_ORDER_TYPE_ALLOT
            sql_value["op_name"] = self.suser.get("username", "")
            sql_value["op_id"] = self.suser.get("id", "")
            self.__gen_buyer_seller(define.BUSICD_CHAN_ALLOT_TO_STORE, sql_value, chan_id, store_id)
            log.debug("=====sql_value: %s", sql_value)
            self.db.start()
            self.db.insert("training_operator_record", sql_value)
            training_times = self.cdata["training_times"]
            if is_prepayment == define.UYU_CHAN_DIV_TYPE:
                self.db.rollback()
                return UYU_OP_ERR
            sql = "update channel set remain_times=remain_times-%d where id=%d and remain_times>=%d" % (training_times, chan_id, training_times)
            ret = self.db.execute(sql)
            if ret == 0:
                self.db.rollback()
                self.respcd = response.UAURET.BALANCEERR
                return UYU_OP_ERR
            sql = "update stores set remain_times=remain_times+%d where id=%d and channel_id=%d" % (training_times, store_id, chan_id)
            ret = self.db.execute(sql)
            if ret == 0:
                self.db.rollback()
                return UYU_OP_ERR
            self.db.commit()
            return UYU_OP_OK
        except:
            log.warn(traceback.format_exc())
            self.db.rollback()
            return UYU_OP_ERR

    def get_order_by_no(self, order_no):
        pass

    def set_order_status(self, status):
        pass


class OrgConfirmChannel:
    def __init__(self, order_no):
        self.order_no = order_no


    @with_database('uyu_core')
    def do_confirm(self):
        try:
            self.db.start()
            sql = "select * from training_operator_record where orderno='%s' for update" % self.order_no
            dbret = self.db.get(sql)
            if not dbret:
                self.db.rollback()
                return UYU_OP_ERR

            status = dbret['status']
            busicd = dbret['busicd']
            self.channel_id = dbret['channel_id']
            self.training_times = dbret['training_times']
            self.record_id = dbret['id']

            if busicd == define.BUSICD_CHAN_BUY_TRAING_TIMES and status == define.UYU_ORDER_STATUS_NEED_CONFIRM:
                uptime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sql = "update channel set remain_times=remain_times+%d, utime='%s' where id=%d" % (self.training_times, uptime, self.channel_id)
                ret = self.db.execute(sql)
                if ret == 0:
                    self.db.rollback()
                    return UYU_OP_ERR

                sql = "update training_operator_record set status=%d, uptime_time='%s' where id=%d" % (define.UYU_ORDER_STATUS_SUCC, uptime, self.record_id)
                ret = self.db.execute(sql)
                if ret == 0:
                    self.db.rollback()
                    return UYU_OP_ERR
            else:
                return UYU_OP_ERR

            self.db.commit()
            return UYU_OP_OK
        except:
            self.db.rollback()
            log.warn(traceback.format_exc())
            return UYU_OP_ERR



class ConsumerTimesChange:

    def __init__(self):
        pass

    @with_database('uyu_core')
    def do_sub_times(self, data):
        try:
            consumer_id = data.get('userid')
            store_id = data.get('store_id')

            training_times = data.get('training_times')
            eyesight_id = data.get('eyesight_id', None)
            device_id = data.get('device_id', None)

            self.db.start()
            sql = "select channel_id from stores where id=%d" % store_id
            dbret = self.db.get(sql)
            if not dbret:
                self.db.rollback()
                return UYU_OP_ERR

            channel_id = dbret.get('channel_id')

            # sql = "select * from consumer where userid=%d and store_id=%d" % (consumer_id, store_id)
            # dbret = self.db.get(sql)
            # if not dbret:
            #     self.db.rollback()
            #     return UYU_OP_ERR

            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            value = {
                'channel_id': channel_id,
                # 'store_id': store_id,
                'consumer_id': consumer_id,
                'comsumer_nums': training_times * -1,
                'ctime': now
            }
            if eyesight_id:
                value['eyesight_id'] = eyesight_id
            if device_id:
                value['device_id'] = device_id
            # ret = self.db.insert(table='training_use_record', values=value)

            sql = "update consumer set remain_times=remain_times-%d, uptime_time='%s' where userid=%d and store_id=%s and remain_times>=%d" % (training_times, now, consumer_id, 0, training_times)
            default_ret = self.db.execute(sql)
            if  default_ret == 0:
                sql = "update consumer set remain_times=remain_times-%d, uptime_time='%s' where userid=%d and store_id=%s and remain_times>=%d" % (training_times, now, consumer_id, store_id, training_times)
                ret = self.db.execute(sql)
                if ret == 0:
                    self.db.rollback()
                    return UYU_OP_ERR
                else:
                    value.update({'store_id': store_id})
                    ret = self.db.insert(table='training_use_record', values=value)
                    if ret == 1:
                        self.db.commit()
                        return UYU_OP_OK
                    else:
                        self.db.rollback()
                        return UYU_OP_ERR

            else:
                value.update({'store_id': 0})
                ret = self.db.insert(table='training_use_record', values=value)
                if ret == 1:
                    self.db.commit()
                    return UYU_OP_OK
                else:
                    self.db.rollback()
                    return UYU_OP_ERR
        except:
            self.db.rollback()
            log.warn(traceback.format_exc())
            return UYU_OP_ERR
