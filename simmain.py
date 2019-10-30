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
from PublicLib.SerialModule.simSerial import simSerial
from MeterReadingSimulation import devMeter485 as dm
import PublicLib.Protocol.dl645resp as resp
from MeterReadingSimulation import dev2315 as dc


def meterrun(mtr, timeouts, magnification=1):
    while 1:
        time.sleep(timeouts)
        if magnification > 0:
            mtr.run(timeouts * magnification)
        else:
            mtr.run(timeouts)

def meterread(mtr, dt):
    index = mtr.readindex(dt['addr'])
    if index >= 0:  # 485表地址存在
        dt['index'] = index
        dt['addr'] = mtr.readaddr(index)

        eng = mtr.readenergy(index)
        ins = mtr.readins(index)
        phaseNum = mtr.getphaseNum(index)
        resp.dl645_read(dt, eng.energy, ins.ac, phaseNum)

        fe = resp.dl645_makeframe(dt)
        return fe
    return None

def colread(mmtr, mtr, dt):
    index = mmtr.readindex(dt['addr'])
    if index >= 0:  # 485表地址存在
        dt['index'] = index
        dt['addr'] = mmtr.readaddr(index)

        energy = mmtr.readenergy(mtr, index)
        resp.dl645_read(dt, energy)

        fe = resp.dl645_makeframe(dt)
        return fe


if __name__ == '__main__':

    cfg = {'port': 'COM15', 'baud': '9600', "parity": "Even", "bytesize": 8, "stopbits": 1, "timeout": 1,
           'meterNum': 10, 'looptimes': 10, 'Magnification': 100}

    relation = {'tly2315': [
        {'addr': '231500000123', 'meterPhaseA': [1,2,3], 'meterPhaseB': [4,5,6,7], 'meterPhaseC': [8,9,0]},
        {'addr': '231500000001', 'meterPhaseA': [1], 'meterPhaseB': [4,5], 'meterPhaseC': [8]},
        {'addr': '231500000002', 'meterPhaseA': [2], 'meterPhaseB': [6], 'meterPhaseC': [9]},
        {'addr': '231500000003', 'meterPhaseA': [3], 'meterPhaseB': [7], 'meterPhaseC': [0]}
    ]}

    # 创建485表
    mtr = dm.meter485()
    mtr.addmeter(cfg['meterNum'])

    # 创建2315
    mmtr = dc.dev2315(relation)

    # 485表 走字
    threading.Thread(target=meterrun, args=(mtr, cfg['looptimes'], cfg['Magnification'])).start()

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
                else: # 2315尝试解析
                    fe = colread(mmtr, mtr, dt)
                    if fe != None:
                        ss.onSendData(ser, fe, 'hex')
