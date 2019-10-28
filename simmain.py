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


def meterrun(mtr, timeouts, magnification=1):
    while 1:
        time.sleep(timeouts)
        if magnification > 0:
            mtr.run(timeouts*magnification)
        else:
            mtr.run(timeouts)




if __name__ == '__main__':


    cfg = {'port':'COM15', 'baud':'9600',"parity": "Even", "bytesize":8, "stopbits":1,"timeout": 1,
           'meterNum':10, 'looptimes':10, 'Magnification':100}

    # 创建485表
    mtr = dm.meter485()
    mtr.addmeter(cfg['meterNum'])

    # 485表 走字
    threading.Thread(target=meterrun, args=(mtr, cfg['looptimes'], cfg['Magnification'])).start()

    # 创建 模拟表串口
    ss = simSerial()
    ret, ser = ss.DOpenPort(cfg['port'], cfg['baud'])
    while ret:
        str = ss.DReadPort()  # 读串口数据
        ret, dt = resp.dl645_dealframe(str)
        if ret:
            index = mtr.readindex(dt['addr'])
            dt['index'] = index

            eng = mtr.readenergy(index)
            resp.dl645_read(dt, eng)

            fe = resp.dl645_makeframe(dt)
            ss.onSendData(ser, fe, 'hex')
