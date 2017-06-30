#coding:utf-8
import datetime
import logging
try:
    import simplejson as json
except ImportError:
    import json


class UAURET:
    OK                    = "0000"
    DBERR                 = "2000"
    THIRDERR              = "2001"
    SESSIONERR            = "2002"
    DATAERR               = "2003"
    IOERR                 = "2004"
    LOGINERR              = "2100"
    PARAMERR              = "2101"
    USERERR               = "2102"
    ROLEERR               = "2103"
    PWDERR                = "2104"
    USERNOTEXISTS         = "2105"
    REQERR                = "2200"
    IPERR                 = "2201"
    NODATA                = "2300"
    DATAEXIST             = "2301"
    PHONENUMEXIST         = "2302"
    UNKOWNERR             = "2400"
    SERVERERR             = "2600"
    METHODERR             = "2601"
    VCODEERR              = "1000"
    REGISTERERR           = "1001"
    CHANGECHANERR         = "1002"
    CHANGESTOREERR        = "1003"
    USERROLEERR           = "1004"
    ORDERERR              = "1005"
    BUSICEERR             = "1006"
    BALANCEERR            = "1007"
    STOREERR1             = "1008"
    UNBINDEYEERR          = "1009"
    STOREDEVICEERR        = "1010"
    USERTIMESERR          = "1011"
    ORGALLOCATEROLEERR    = "1012"
    LOGINNAMEEXISTS       = "1013"
    MODIFYUSERINFOERR     = "1014"
    DEVICEUNBINDERR       = "1015"
    SUBTIMESERR           = "1016"
    CREATEITEMERR         = "2700"
    UPDATEITEMERR         = "2701"
    CREATEPRESCRIPTIONERR = "2702"
    UPDATEPRESCRIPTIONERR = "2703"
    USERNOPRESCERR        = "2704"
    PRESCADDITEMERR       = "2705"



error_map = {
    UAURET.OK                    : u"成功",
    UAURET.DBERR                 : u"数据库查询错误",
    UAURET.THIRDERR              : u"第三方系统错误",
    UAURET.SESSIONERR            : u"用户未登录",
    UAURET.DATAERR               : u"数据错误",
    UAURET.IOERR                 : u"文件读写错误",
    UAURET.LOGINERR              : u"用户登录失败",
    UAURET.PARAMERR              : u"参数错误",
    UAURET.USERERR               : u"用户不存在或未激活",
    UAURET.ROLEERR               : u"用户身份错误",
    UAURET.PWDERR                : u"密码错误",
    UAURET.REQERR                : u"非法请求或请求次数受限",
    UAURET.IPERR                 : u"IP受限",
    UAURET.NODATA                : u"无数据",
    UAURET.DATAEXIST             : u"数据已存在",
    UAURET.UNKOWNERR             : u"未知错误",
    UAURET.SERVERERR             : u"内部错误",
    UAURET.METHODERR             : u"函数未实现",
    UAURET.VCODEERR              : u"验证码错误",
    UAURET.REGISTERERR           : u"用户注册失败",
    UAURET.CHANGECHANERR         : u"更新渠道信息失败",
    UAURET.CHANGESTOREERR        : u"更新门店信息失败",
    UAURET.USERROLEERR           : u"用户身份出错",
    UAURET.ORDERERR              : u"订单操作失败",
    UAURET.BUSICEERR             : u"订单类型错误",
    UAURET.BALANCEERR            : u"训练次数余额不足",
    UAURET.STOREERR1             : u"渠道和门店模式不一致",
    UAURET.USERNOTEXISTS         : u"用户不存在",
    UAURET.PHONENUMEXIST         : u"手机号已经存在",
    UAURET.UNBINDEYEERR          : u"解绑视光师失败",
    UAURET.STOREDEVICEERR        : u"门店设备不匹配",
    UAURET.USERTIMESERR          : u"用户训练点数不足",
    UAURET.ORGALLOCATEROLEERR    : u"平台只能分配给消费者或视光师",
    UAURET.LOGINNAMEEXISTS       : u"登录名已存在",
    UAURET.MODIFYUSERINFOERR     : u"修改用户信息失败",
    UAURET.DEVICEUNBINDERR       : u"设备未绑定",
    UAURET.SUBTIMESERR           : u"减扣次数失败",
    UAURET.CREATEITEMERR         : u"创建项目失败",
    UAURET.UPDATEITEMERR         : u"修改项目失败",
    UAURET.CREATEPRESCRIPTIONERR : u"创建处方失败",
    UAURET.UPDATEPRESCRIPTIONERR : u"修改处方失败",
    UAURET.USERNOPRESCERR        : u"用户没有处方",
    UAURET.PRESCADDITEMERR       : u"处方添加项目失败",
}

def json_default_trans(obj):
    '''json对处理不了的格式的处理方法'''
    if isinstance(obj, datetime.datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(obj, datetime.date):
        return obj.strftime('%Y-%m-%d')
    raise TypeError('%r is not JSON serializable' % obj)


def error(errcode, resperr='', respmsg='', data=None, debug=False, escape=True, encoder=None):
    global error_map
    if not resperr:
        resperr = respmsg if respmsg else error_map[errcode]
    if not data:
        data = {}
    ret = {"respcd": errcode, "respmsg": respmsg, "resperr": resperr, "data": data}
    if debug:
        log.debug('error:%s', ret)
    return json.dumps(ret, ensure_ascii=escape, cls=encoder, separators=(',', ':'), default = json_default_trans)

def success(data, resperr='', debug=False, escape=True, encoder=None):
    ret = {"respcd": "0000", "resperr": resperr, "respmsg": "", "data": data}
    if debug:
        log.debug('success:%s', ret)
    return json.dumps(ret, ensure_ascii=escape, cls=encoder, separators=(',', ':'), default = json_default_trans)
