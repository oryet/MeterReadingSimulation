import sys
sys.path.append('../')
from PublicLib.ACModule.simEnergy import energy
from PublicLib.ACModule.simCurrent import ACsampling
from PublicLib.ACModule.simMeterFreeze import freeze
from PublicLib.Protocol import dl645resp as dl645


def creataddr(i):
    addr = '0000' + str(i + 1)
    addr = '48500000' + addr[-4:]
    return addr


class meter485():
    def __init__(self):
        self.num = 0
        self.meter485list = []

    def run(self, t):
        for i in range(self.num):
            ins = self.meter485list[i]['ac']
            eng = self.meter485list[i]['energy']
            ins.run()
            eng.run(ins.ac, t)

    def num(self):
        return self.num

    def addmeter(self, addnum, phaseNum=1, cfg=None):  # 485表默认单相表
        for i in range(addnum):
            eng = energy(phaseNum)
            ac = ACsampling()
            fz = freeze(cfg)
            addr = creataddr(self.num + i)
            if phaseNum != 1 and phaseNum != 3:
                phaseNum = 1
            self.meter485list += [{'energy': eng, 'ac': ac, 'addr': addr, 'phaseNum': phaseNum,
                                   'freeze': fz}]
        self.num += addnum

    def readins(self, i):
        ac = self.meter485list[i]['ac'].ac
        return ac

    def readenergy(self, i):
        eng = self.meter485list[i]['energy'].energy
        return eng

    def readaddr(self, i):
        return self.meter485list[i]['addr']

    def readindex(self, addr):
        for i in range(self.num):
            laddr = self.meter485list[i]['addr']
            for j in range(0, 12, 2):
                if addr[j:j + 2] == laddr[j:j + 2] or addr[j:j + 2] == 'AA':
                    continue
                else:
                    break
            if j >= 10:
                if addr[j:j + 2] == laddr[j:j + 2] or addr[j:j + 2] == 'AA':
                    return i
        return -1

    def getphaseNum(self, i):
        return self.meter485list[i]['phaseNum']

    def freezeformat(self, cfg):
        mon = cfg['month']
        day = cfg['day']
        hour = cfg['hour']

        daym = int(day / 30)
        hourd = int(hour / 24)

        if mon >= daym:
            mon = mon - daym
        else:
            mon = 0

        if day >= hourd:
            day = day - hourd
        else:
            day = 0
        return mon, day, hour

    def createFreezeHisData(self, cfg):
        mon, day, hour = self.freezeformat(cfg)
        # for n in range(self.num):
        for i in range(mon):
            self.run(3600 * 24 * 30)
            for n in range(self.num):
                fz = self.meter485list[n]['freeze']
                eng = self.meter485list[n]['energy'].energy
                fz.FreezeData('month', eng)

        for i in range(day):
            self.run(3600 * 24)
            for n in range(self.num):
                fz = self.meter485list[n]['freeze']
                eng = self.meter485list[n]['energy'].energy
                fz.FreezeData('day', eng)
                if i % 30 == 29:
                    fz.FreezeData('month', eng)

        for i in range(hour):
            self.run(3600)
            for n in range(self.num):
                fz = self.meter485list[n]['freeze']
                eng = self.meter485list[n]['energy'].energy
                fz.FreezeData('hour', eng)
                if i % 24 == 23:
                    fz.FreezeData('day', eng)

    def freezeHisData(self, type):
        for n in range(self.num):
            fz = self.meter485list[n]['freeze']
            eng = self.meter485list[n]['energy'].energy
            fz.FreezeData(type, eng)

    def readhismon(self, i, n):
        return self.meter485list[i]['freeze'].mon[-n-1]

    def readhisday(self, i, n):
        return self.meter485list[i]['freeze'].day[-n-1]

    def readhishour(self, i, n):
        return self.meter485list[i]['freeze'].hour[-n-1]


if __name__ == '__main__':
    mtr = meter485()
    mtr.addmeter(3, 3)
    addr = mtr.readaddr(1)
    index = mtr.readindex(addr)
    print(addr, index)
    mtr.run(3600)
    ins = mtr.readins(1)
    print(ins[0])
    mtr.run(3600)
    ins = mtr.readins(1)
    print(ins[0])

    defultcfg = {'day': 15, 'month': 12, 'hour': 6}
    mtr.createFreezeHisData(defultcfg)
    mondata = mtr.readhismon(1, 3)

    frame = 'FE FE FE FE 68 02 00 00 00 50 48 68 11 04 33 32 35 33 4c 16'
    ret, dt = dl645.dl645_dealframe(frame)
    print(ret, dt)

    if ret:
        index = mtr.readindex(dt['addr'])
        dt['index'] = index

        eng = mtr.readenergy(index)
        print(eng)
        dl645.dl645_read(dt, mtr, index)

        fe = dl645.dl645_makeframe(dt)
        print(fe)
