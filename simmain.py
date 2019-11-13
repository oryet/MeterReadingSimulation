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
from PublicLib.SerialModule.simSerial import simSerial
from MeterReadingSimulation import devMeter485 as dm
import PublicLib.Protocol.dl645resp as resp
from MeterReadingSimulation import dev2315 as dc
from PublicLib.ACModule.simRTC import simrtc


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
            t = rtc.gettime(timeouts * magnification)
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


def meterread(mtr, dt):
    index = mtr.readindex(dt['addr'])
    if index >= 0:  # 485表地址存在
        dt['index'] = index
        dt['addr'] = mtr.readaddr(index)

        eng = mtr.readenergy(index)
        ins = mtr.readins(index)
        phaseNum = mtr.getphaseNum(index)
        resp.dl645_read(dt, eng, ins, phaseNum)

        fe = resp.dl645_makeframe(dt)
        return fe
    return None


def colread(mmtr, mtr, dt):
    index = mmtr.readindex(dt['addr'])
    if index >= 0:  # col地址存在
        dt['index'] = index
        dt['addr'] = mmtr.readaddr(index)

        eng = mmtr.readenergy(mtr, index)
        ins = mmtr.readins(mtr, index)
        resp.dl645_read(dt, eng, ins, 3)  # col直接取数据结构

        fe = resp.dl645_makeframe(dt)
        return fe


if __name__ == '__main__':
    cfg = {'port': 'COM7', 'baud': '9600', "parity": "Even", "bytesize": 8, "stopbits": 1, "timeout": 1,
           'meterNum': 10, 'looptimes': 10, 'Magnification': 100}  # looptimes: 刷新时间, Magnification: 刷新放大倍数

    relation = {'tly2315': [
        {'addr': '231500000123', 'meterPhaseA': [1, 2, 3], 'meterPhaseB': [4, 5, 6, 7], 'meterPhaseC': [8, 9, 0]},
        {'addr': '231500000001', 'meterPhaseA': [1], 'meterPhaseB': [4, 5], 'meterPhaseC': [8]},
        {'addr': '231500000002', 'meterPhaseA': [2], 'meterPhaseB': [6], 'meterPhaseC': [9]},
        {'addr': '231500000003', 'meterPhaseA': [3], 'meterPhaseB': [7], 'meterPhaseC': [0]}
    ]}

    freezedatacfg = {'day': 62, 'month': 12, 'hour': 24}

    # 创建时钟
    rtc = simrtc()

    # 创建485表
    mtr = dm.meter485()
    mtr.addmeter(cfg['meterNum'])

    # 创建485表 历史数据
    mtr.createFreezeHisData(freezedatacfg)

    # 创建2315
    mmtr = dc.dev2315(relation)

    # 485表 走字
    threading.Thread(target=meterrun, args=(mtr, rtc, cfg['looptimes'], cfg['Magnification'])).start()

    # 创建 模拟表串口
    ss = simSerial()
    openret, ser = ss.DOpenPort(cfg['port'], cfg['baud'])
    while openret:
        dt = {}
        str = ss.DReadPort()  # 读串口数据
        ret, dt = resp.dl645_dealframe(str)
        if ret:
            # 485表尝试解析
            fe = None
            fe = meterread(mtr, dt)
            if fe != None:
                ss.onSendData(ser, fe, 'hex')
            else:  # 2315尝试解析
                fe = colread(mmtr, mtr, dt)
                if fe != None:
                    ss.onSendData(ser, fe, 'hex')
