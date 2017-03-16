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

class OrgAllotToChanCancel:
    def __init__(self, *args, **kwargs):
        self.dbret = kwargs["dbret"]
        self.store_id = self.dbret.get("store_id", None)
        self.channel_id = self.dbret.get("channel_id", None)
        self.cancel_times = self.dbret.get("training_times")
    
    @with_database('uyu_core')
    def do_cancel(self):
        try:
            self.db.start()
            uptime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sql = "update training_operator_record set status=%d, uptime_time='%s'  where orderno='%s' and status=%d" % (define.UYU_ORDER_STATUS_CANCEL, 
                uptime, 
                self.dbret["orderno"],
                define.UYU_ORDER_STATUS_SUCC
                )
            ret = self.db.execute(sql)
            if ret == 0:
                self.db.rollback()
                return UYU_OP_ERR               
            sql = "update channel set remain_times=remain_times-%d where id=%d" % (self.cancel_times, self.channel_id)
            ret = self.db.execute(sql)
            if ret == 0:
                self.db.rollback()
                return UYU_OP_ERR      
            self.db.commit()
            return UYU_OP_OK
        except:
            log.warn(traceback.format_exc())
            return UYU_OP_ERR

class ChanAllotStoreCancel:
    def __init__(self, *args, **kwargs):
        self.dbret = kwargs["dbret"]
        self.store_id = self.dbret.get("store_id", None)
        self.channel_id = self.dbret.get("channel_id", None)
        self.cancel_times = self.dbret.get("training_times")
    
    @with_database('uyu_core')
    def do_cancel(self):
        try:
            self.db.start()
            uptime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sql = "update training_operator_record set status=%d, uptime_time='%s' where orderno='%s' and status=%d" % (define.UYU_ORDER_STATUS_CANCEL, 
                uptime, 
                self.dbret["orderno"],
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
            sql = "update stores set remain_times=remain_times-%d where id=%d" % (self.cancel_times, self.store_id)
            ret = self.db.execute(sql)
            if ret == 0:
                self.db.rollback()
                return UYU_OP_ERR      
            self.db.commit()
            return UYU_OP_OK
        except:
            log.warn(traceback.format_exc())
            return UYU_OP_ERR


class TrainingOP:
    def __init__(self, cdata=None, suser=None, order_no=None):
        self.data_key = (
            "busicd",  "channel_id", "store_id", "consumer_id",
            "category", "op_type", "pay_type", "training_times",
            "training_amt", "status", "op_name", "orderno",
            "create_time", "update_time", "ch_training_amt_per",
            "store_training_amt_per",
        )
        self.db_data = {}
        self.cdata = cdata
        self.suser = suser 
        self.respcd = None

        self.order_no = order_no

        self.cancel_handler = {
            define.BUSICD_ORG_ALLOT_TO_CHAN: OrgAllotToChanCancel,
            define.BUSICD_CHAN_ALLOT_TO_STORE: ChanAllotStoreCancel,
        }
        

    def create_orderno(self):
        with dbpool.get_connection('uyu_core') as conn:
            myid = new_id64(conn=conn)
            return datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(myid)

    @with_database('uyu_core')  
    def __check_cancel_permission(self):
        dbret = self.db.select_one("training_operator_record", {"orderno": self.order_no})
        ctime = dbret["create_time"]
        db_day = ctime.strftime("%Y-%m-%d")
        n_day = datetime.datetime.now().strftime("%Y-%m-%d")
        if db_day != n_day:
            return False, None
        return True, dbret
        
    def order_cancel(self):
        can_cancel, dbret = self.__check_cancel_permission()
        if can_cancel and handler_class:
            busicd = dbret.get("busicd", "")
            log.debug("dbret: %s busicd: %s", dbret, busicd)
            handler_class = self.cancel_handler.get(busicd)
            obj_handler = handler_class(dbret=dbret)
            ret = obj_handler.do_cancel()
            return ret
        return UYU_OP_ERR

    def __gen_vsql(self, order_status):
        sql_value = {}
        order_no = self.create_orderno()
        log.debug("order_no: %s", order_no)

        for key in self.cdata:
            if self.cdata.get(key, None):
                sql_value[key] = self.cdata[key]

        sql_value["orderno"] = order_no
        sql_value["status"] = order_status
        create_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql_value["create_time"] = create_time

        return sql_value

    #公司分配给渠道训练次数的订单
    @with_database('uyu_core')
    def create_org_allot_to_chan_order(self):
        chan_id = self.cdata["channel_id"]
        log.debug("chan_id: %d", chan_id)
        sql_value = self.__gen_vsql(UYU_ORDER_STATUS_SUCC)
        sql_value["op_type"] = define.UYU_ORDER_TYPE_ALLOT
        sql_value["op_name"] = self.suser.get("login_name", "")

        try:
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

    #公司分配门店训练次数订单
    @with_database('uyu_core')
    def create_org_allot_to_store_order(self):
        chan_id = self.cdata["channel_id"]
        store_id = self.cdata["store_id"]
        sql_value = self.__gen_vsql(UYU_ORDER_STATUS_SUCC)
        
        sql_value["op_type"] = define.UYU_ORDER_TYPE_ALLOT
        sql_value["op_name"] = self.suser.get("login_name", "")

        try:
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

    #渠道购买训练次数订单
    @with_database('uyu_core')
    def create_chan_buy_trainings_order(self):
        chan_id = self.cdata["channel_id"]
        sql_value = self.__gen_vsql(UYU_ORDER_STATUS_NEED_CONFIRM)

        sql_value["op_type"] = define.UYU_ORDER_TYPE_BUY
        sql_value["op_name"] = self.suser.get("login_name", "")

        try:
            self.db.insert("training_operator_record", sql_value) 
            return UYU_OP_OK
        except:
            log.warn(traceback.format_exc())
            return UYU_OP_ERR

    #渠道分配训练点数给门店
    @with_database('uyu_core') 
    def create_chan_allot_to_store_order(self):
        chan_id = self.cdata["channel_id"]
        store_id = self.cdata["store_id"]
        sql_value = self.__gen_vsql(UYU_ORDER_STATUS_SUCC)

        sql_value["op_type"] = define.UYU_ORDER_TYPE_ALLOT
        sql_value["op_name"] = self.suser.get("login_name", "")

        try:
            log.debug("=====sql_value: %s", sql_value)
            self.db.start()
            self.db.insert("training_operator_record", sql_value)
            training_times = self.cdata["training_times"]
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
