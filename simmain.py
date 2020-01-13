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
    colindex, indexlist = relation2list(uartcfg['port'], relation)
    if indexlist == None or colindex == None:
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
            fe = None
            dt['ctime'] = rtc.gettick()
            fe = meterread(mtr, dt, indexlist)
            if fe != None:
                print(datetime.datetime.now(), uartcfg['port'], 'Send:', fe.replace(' ',''))
                ss.onSendData(ser, fe, 'hex')
            else:  # 2315尝试解析
                fe = colread(mmtr, mtr, dt, colindex)
                if fe != None:
                    print(datetime.datetime.now(), uartcfg['port'], 'Send:', fe.replace(' ',''))
                    ss.onSendData(ser, fe, 'hex')


def relation2list(port, relation):
    for i in range(len(relation['tly2315'])):
        if port == relation['tly2315'][i]['port']:
            colindex = [i]
            for k in range(len(relation['tly2315'][i]['topologycol'])):
                for j in range(len(relation['tly2315'])):
                    if relation['tly2315'][j]['addr'] == relation['tly2315'][i]['topologycol'][k]:
                        colindex += [j]
                        break
            return colindex, relation['tly2315'][i]['topology']
    return None, None


if __name__ == '__main__':
    cfg2215 =   {'port': 'COM7', 'baud': '9600', "parity": "Even", "bytesize": 8, "stopbits": 1, "timeout": 1}
    
    cfg2315_1 = {'port': 'COM9', 'baud': '9600', "parity": "Even", "bytesize": 8, "stopbits": 1, "timeout": 1}
    cfg2315_2 = {'port': 'COM11', 'baud': '9600', "parity": "Even", "bytesize": 8, "stopbits": 1, "timeout": 1}
    cfg2315_3 = {'port': 'COM13', 'baud': '9600', "parity": "Even", "bytesize": 8, "stopbits": 1, "timeout": 1}
    
    cfg2937_1 = {'port': 'COM15', 'baud': '9600', "parity": "Even", "bytesize": 8, "stopbits": 1, "timeout": 1}
    cfg2937_2 = {'port': 'COM17', 'baud': '9600', "parity": "Even", "bytesize": 8, "stopbits": 1, "timeout": 1}
    cfg2937_3 = {'port': 'COM19', 'baud': '9600', "parity": "Even", "bytesize": 8, "stopbits": 1, "timeout": 1}

    mtrcfg = {'meterNum': 9, 'looptimes': 5, 'Magnification': 1} # looptimes: 刷新时间, Magnification: 刷新放大倍数

    relation = {'tly2315': [
        #{'port': 'COM7',  'addr': '221500000123', 'CT': 5, 'meterPhaseA': [0, 3, 6, 9, 12, 15], 'meterPhaseB': [1, 4, 7, 10, 13, 16], 'meterPhaseC': [2, 5, 8, 11, 14, 17]},
        {'port': 'COM7',  'addr': '221500000123', 'CT': 1, 'meterPhaseA': [0,3,6], 'meterPhaseB': [1,4,7], 'meterPhaseC': [2,5,8], 'topology': [0,1,2,3,4,5,6,7,8], 'topologycol':[]},
        
        {'port': 'COM9',  'addr': '231500000102', 'CT': 1, 'meterPhaseA': [3,6], 'meterPhaseB': [4,7], 'meterPhaseC': [5,8], 'topology': [3,4,5], 'topologycol': ['293700000202']},
        {'port': 'COM11',  'addr': '231500000101', 'CT': 1, 'meterPhaseA': [0], 'meterPhaseB': [1], 'meterPhaseC': [2], 'topology': [0,1,2], 'topologycol':[]},
        {'port': 'COM13',  'addr': '231500000103', 'CT': 1, 'meterPhaseA': [6], 'meterPhaseB': [7], 'meterPhaseC': [8], 'topology': [6,7,8], 'topologycol':[]},

        {'port': 'COM15', 'addr': '293700000205', 'CT': 1, 'meterPhaseA': [0,3,6], 'meterPhaseB': [1,4,7], 'meterPhaseC': [2,5,8], 'topology': [], 'topologycol':[]},
        {'port': 'COM17', 'addr': '293700000201', 'CT': 1, 'meterPhaseA': [0], 'meterPhaseB': [1], 'meterPhaseC': [2], 'topology': [], 'topologycol':[]},
        {'port': 'COM19', 'addr': '293700000202', 'CT': 1, 'meterPhaseA': [6], 'meterPhaseB': [7], 'meterPhaseC': [8], 'topology': [], 'topologycol':[]},
    ]}

    freezedatacfg = {'day': 62, 'month': 12, 'hour': 24}

    # 创建时钟
    rtc = simrtc(mtrcfg['Magnification'])

    # 创建485表
    mtr = dm.meter485()
    mtr.addmeter(mtrcfg['meterNum'], 1)

    # 创建485表 历史数据
    mtr.createFreezeHisData(freezedatacfg)

    # 创建2315
    mmtr = dc.dev2315(relation)

    # 485表 走字ins = mmtr.readins(index)
    threading.Thread(target=meterrun, args=(mtr, rtc, mtrcfg['looptimes'], mtrcfg['Magnification'])).start()

    # 创建 2215串口
    threading.Thread(target=simserialexc, args=(cfg2215, relation)).start()

    # 创建 2315_1串口
    threading.Thread(target=simserialexc, args=(cfg2315_1, relation)).start()

    # 创建 2315_2串口
    threading.Thread(target=simserialexc, args=(cfg2315_2, relation)).start()

    # 创建 2315_3串口
    threading.Thread(target=simserialexc, args=(cfg2315_3, relation)).start()

    # 创建 2937_1串口
    threading.Thread(target=simserialexc, args=(cfg2937_1, relation)).start()

    # 创建 2937_2
    threading.Thread(target=simserialexc, args=(cfg2937_2, relation)).start()

    # 创建 2937_3
    threading.Thread(target=simserialexc, args=(cfg2937_3, relation)).start()
