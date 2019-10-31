import numpy as np
import sys
sys.path.append('../')
from PublicLib.ACModule.simEnergy import energy
from PublicLib.ACModule.simCurrent import ACsampling
from PublicLib.Protocol import dl645resp as dl645
from MeterReadingSimulation.devMeter485 import meter485

relation = {'tly2315': [
    {'addr': '231500000123', 'meterPhaseA': [1, 2, 3], 'meterPhaseB': [4, 5, 6, 7], 'meterPhaseC': [8, 9, 0]},
    {'addr': '231500000001', 'meterPhaseA': [1], 'meterPhaseB': [4, 5], 'meterPhaseC': [8]},
    {'addr': '231500000002', 'meterPhaseA': [2], 'meterPhaseB': [6], 'meterPhaseC': [9]},
    {'addr': '231500000003', 'meterPhaseA': [3], 'meterPhaseB': [7], 'meterPhaseC': [0]}
]}

class dev2315():
    def __init__(self, rel):
        self.num = len(rel['tly2315'])
        # self.dev2315list = []
        self.rel = rel

    def readins(self, mtr, index):
        if index >= self.num:
            return mtr.readins(index)

        acTotal = np.zeros([5, 4], dtype=float)

        # A相
        acA = np.zeros([5,4], dtype=float)
        for i in self.rel['tly2315'][index]['meterPhaseA']:
            if i < mtr.num:
                acsmp = mtr.readins(i)
                acp = np.asarray(acsmp.ac)
                acA[1:2] += acp[1:2]  # I
                acA[3:5] += acp[3:5]  # P/Q
                acA[0:1] = acp[0:1]   # U
                acA[2:3] = acp[2:3]   # A

        # B相
        acB = np.zeros([5, 4], dtype=float)
        for i in self.rel['tly2315'][index]['meterPhaseB']:
            if i < mtr.num:
                acsmp = mtr.readins(i)
                acp = np.asarray(acsmp.ac)
                acB[1:2] += acp[1:2]  # I
                acB[3:5] += acp[3:5]  # P/Q
                acB[0:1] = acp[0:1]   # U
                acB[2:3] = acp[2:3]   # A

        # C相
        acC = np.zeros([5, 4], dtype=float)
        for i in self.rel['tly2315'][index]['meterPhaseC']:
            if i < mtr.num:
                acsmp = mtr.readins(i)
                acp = np.asarray(acsmp.ac)
                acC[1:2] += acp[1:2]  # I
                acC[3:5] += acp[3:5]  # P/Q
                acC[0:1] = acp[0:1]   # U
                acC[2:3] = acp[2:3]   # A

        # U
        acTotal[0:1] = (acA[0:1] + acA[0:1] + acA[0:1]) / 3
        # I
        acTotal[1][0] = acA[1][3]
        acTotal[1][1] = acB[1][3]
        acTotal[1][2] = acC[1][3]
        acTotal[1][3] = acTotal[1][0] + acTotal[1][1] + acTotal[1][2]
        # A
        acTotal[2:3] = (acA[2:3] + acA[2:3] + acA[2:3]) / 3
        # P/Q
        acTotal[3][0] = acA[3][3]
        acTotal[3][1] = acB[3][3]
        acTotal[3][2] = acC[3][3]
        acTotal[3][3] = acTotal[3][0] + acTotal[3][1] + acTotal[3][2]
        acTotal[4][0] = acA[4][3]
        acTotal[4][1] = acB[4][3]
        acTotal[4][2] = acC[4][3]
        acTotal[4][3] = acTotal[4][0] + acTotal[4][1] + acTotal[4][2]

        return acTotal

    def readenergy(self, mtr, index):
        dataTotal = np.zeros([4, 6, 9], dtype=float)

        if index >= self.num:
            return dataTotal

        # A相
        dataA = np.zeros([4, 6, 9], dtype=float)
        for i in self.rel['tly2315'][index]['meterPhaseA']:
            if i < mtr.num:
                eng = mtr.readenergy(i)
                dataA += np.asarray(eng)

        # B相
        dataB = np.zeros([4, 6, 9], dtype=float)
        for i in self.rel['tly2315'][index]['meterPhaseB']:
            if i < mtr.num:
                eng = mtr.readenergy(i)
                dataB += np.asarray(eng)

        # C相
        dataC = np.zeros([4, 6, 9], dtype=float)
        for i in self.rel['tly2315'][index]['meterPhaseC']:
            if i < mtr.num:
                eng = mtr.readenergy(i)
                dataC += np.asarray(eng)

        dataTotal[1:2] = dataA[0:1]
        dataTotal[2:3] = dataB[0:1]
        dataTotal[3:4] = dataC[0:1]
        dataTotal[0:1] = dataA[0:1] + dataB[0:1] + dataC[0:1]

        return dataTotal

    def readaddr(self,i):
        if i < self.num:
            return self.rel['tly2315'][i]['addr']
        else:
            return self.rel['tly2315'][0]['addr']

    def readindex(self, addr):
        for i in range(self.num):
            laddr = self.rel['tly2315'][i]['addr']
            for j in range (0, 12, 2):
                if addr[j:j+2] == laddr[j:j + 2] or addr[j:j+2] == 'AA':
                    continue
                else:
                    break
            if j >= 10:
                if addr[j:j + 2] == laddr[j:j + 2] or addr[j:j + 2] == 'AA':
                    return i
        return -1


if __name__ == '__main__':
    mtr = meter485()
    mtr.addmeter(10)

    mtr.run(3600)
    #ac1 = mtr.readins(1)
    #print(ac1.I)
    mtr.run(3600)
    #ac1 = mtr.readins(1)
    #print(ac1.I)

    mmtr = dev2315(relation)
    # a = mmtr.readenergy(mtr, 1)
    a = mmtr.readins(mtr, 1)
    print(a)


    '''
    frame = 'FE FE FE FE 68 02 00 00 00 50 48 68 11 04 33 32 35 33 4c 16'
    ret, dt = dl645.dl645_dealframe(frame)
    print(ret, dt)

    if ret:
        index = mtr.readindex(dt['addr'])
        dt['index'] = index

        eng = mtr.readenergy(index)
        print(eng)
        dl645.dl645_read(dt, eng)

        fe = dl645.dl645_makeframe(dt)
        print(fe)
'''


