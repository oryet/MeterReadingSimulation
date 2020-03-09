#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2019-10-24 11:13:14

@author: jiagnzy
"""

import sys

sys.path.append('../')
import threading
import time
import datetime
import logging
from PublicLib.SerialModule.simSerial import simSerial
from MeterReadingSimulation import devMeter485 as dm
import PublicLib.Protocol.dl645resp as resp
from MeterReadingSimulation import dev2315 as dc
from PublicLib.ACModule.simRTC import simrtc
from PublicLib import public as pub


def formatdatetime(dt, mon, day, hour):
    dflag = {'M': 0, 'D': 0, 'H': 0}

    if hour != dt['hour']:
        dflag['H'] = 1
        dt['hour'] = hour
    if day != dt['day']:
        dflag['D'] = 1
        dt['day'] = day
    if mon != dt['month']:
        dflag['M'] = 1
        dt['month'] = mon
    return dflag


def meterrun(mtr, rtc, timeouts, magnification=1):
    dt = {'month': 0, 'day': 0, 'hour': 0}

    while 1:
        time.sleep(timeouts)
        if magnification > 1:  # 虚拟倍数走字
            mtr.run(timeouts * magnification)
        else:  # 根据当前时间自然走字
            mtr.run(timeouts)

        t = rtc.gettime()
        dflag = formatdatetime(dt, t.month, t.day, t.hour)

        if dflag['M']:
            mtr.freezeHisData('month')
        if dflag['D']:
            mtr.freezeHisData('day')
        if dflag['H']:
            mtr.freezeHisData('hour')


def meterread(mtr, dt, indexlist):
    index = mtr.readindex(dt['addr'])
    if index in indexlist:  # 485表地址存在
        dt['index'] = index
        dt['addr'] = mtr.readaddr(index)
        resp.dl645_read(dt, mtr, index)

        fe = resp.dl645_makeframe(dt)
        return fe
    return None


def colread(mmtr, mtr, dt, colindex):
    index = mmtr.readindex(dt['addr'], colindex)
    if index >= 0:  # col地址存在
        dt['index'] = index
        dt['addr'] = mmtr.readaddr(index)

        resp.dl645_read(dt, mtr, index, mmtr)  # col直接取数据结构

        fe = resp.dl645_makeframe(dt)
        return fe


def simserialexc(uartcfg, relation):
    logger = logging.getLogger('simserialexc')
    colindex, indexlist = relation2list(uartcfg['port'], relation)
    if indexlist == None or colindex == None:
        logger.warning('indexlist or colindex is None')
        return

    # 创建 模拟表串口
    ss = simSerial()
    openret, ser = ss.DOpenPort(uartcfg['port'], uartcfg['baud'])
    while openret:
        dt = {}
        str = ss.DReadPort()  # 读串口数据
        ret, dt = resp.dl645_dealframe(str)
        if ret:
            # 485表尝试解析
            print(datetime.datetime.now(), uartcfg['port'], 'Recv:', str)
            logger.info(uartcfg['port'] + ' Recv: ' + str)
            fe = None
            dt['ctime'] = rtc.gettick()
            fe = meterread(mtr, dt, indexlist)
            if fe != None:
                print(datetime.datetime.now(), uartcfg['port'], 'Send:', fe.replace(' ', ''))
                logger.info(uartcfg['port'] + ' Send: ' + fe.replace(' ', ''))
                ss.onSendData(ser, fe, 'hex')
            else:  # 2315尝试解析
                fe = colread(mmtr, mtr, dt, colindex)
                if fe != None:
                    print(datetime.datetime.now(), uartcfg['port'], 'Send:', fe.replace(' ', ''))
                    logger.info(uartcfg['port'] + ' Send: ' + fe.replace(' ', ''))


def relation2list(port, relation):
    for i in range(len(relation)):
        if port == relation[i]['port']:
            colindex = [i]
            for k in range(len(relation[i]['topologycol'])):
                for j in range(len(relation)):
                    if relation[j]['addr'] == relation[i]['topologycol'][k]:
                        colindex += [j]
                        break
            return colindex, relation[i]['topology']
    return None, None


# 配置文件有效性判断
def iscfg(cfg):
    if 'devNum' in cfg and 'uartcfg' in cfg and 'devcfg' in cfg:
        pass
    else:
        return False

    if len(cfg['uartcfg']) == len(cfg['devcfg']) >= cfg['devNum'] > 0:
        for i in range(cfg['devNum']):
            uartcfg = cfg['uartcfg'][i]
            if 'port' in uartcfg and 'baud' in uartcfg and 'parity' in uartcfg and \
                    'bytesize' in uartcfg and 'stopbits' in uartcfg and 'timeout' in uartcfg:
                continue
            else:
                return False

        for i in range(cfg['devNum']):
            devcfg = cfg['devcfg'][i]
            if 'port' in devcfg and 'addr' in devcfg and 'CT' in devcfg and \
                    'meterPhaseA' in devcfg and 'meterPhaseB' in devcfg and 'meterPhaseC' in devcfg and \
                    'topology' in devcfg and 'topologycol' in devcfg:
                continue
            else:
                return False
    else:
        return False

    if 'mtrcfg' in cfg:
        mtrcfg = cfg['mtrcfg']
        if 'meterNum' in mtrcfg and 'looptimes' in mtrcfg and 'Magnification' in mtrcfg:
            pass
        else:
            return False

    if 'freezedatacfg' in cfg:
        freezedatacfg = cfg['freezedatacfg']
        if 'day' in freezedatacfg and 'month' in freezedatacfg and 'hour' in freezedatacfg:
            pass
        else:
            return False

    return True


if __name__ == '__main__':
    pub.loggingConfig('logging.conf')
    logger = logging.getLogger('simmain')

    simConfig = pub.loadDefaultSettings("cfgsim.json")
    while not iscfg(simConfig):
        print('simConfig error')
        time.sleep(10)

    # 串口配置参数
    uartcfg = simConfig['uartcfg']

    # 模拟表 表数量及参数配置
    mtrcfg = simConfig['mtrcfg']

    # A/B/C 索引号为各个相位下通过的电流
    # topology：端口下支撑的485表
    # topologycol： 端口下支撑的采集器
    devcfg = simConfig['devcfg']

    # 冻结参数配置
    freezedatacfg = simConfig['freezedatacfg']

    # 创建时钟
    rtc = simrtc(mtrcfg['Magnification'])

    # 创建485表
    mtr = dm.meter485()
    mtr.addmeter(mtrcfg['meterNum'], 1)

    # 创建485表 历史数据
    mtr.createFreezeHisData(freezedatacfg)

    # 创建2315
    mmtr = dc.dev2315(devcfg)

    # 485表 走字ins = mmtr.readins(index)
    threading.Thread(target=meterrun, args=(mtr, rtc, mtrcfg['looptimes'], mtrcfg['Magnification'])).start()

    # 创建 2215串口
    for i in range(simConfig['devNum']):
        threading.Thread(target=simserialexc, args=(uartcfg[i], devcfg)).start()
        time.sleep(1)
