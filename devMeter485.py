import sys
sys.path.append('../')
from PublicLib.ACModule.simEnergy import energy
from PublicLib.ACModule.simCurrent import ACsampling


def creataddr(i):
    addr = '0000' + str(i+1)
    addr = '48500000' + addr[-4:]
    return addr

class meter485():
    def __init__(self):
        self.num = 0
        self.meter485list = []

    def run(self, t):
        for i in range(self.num):
            ac = self.meter485list[i]['ac']
            eng = self.meter485list[i]['energy']
            ac.run()
            eng.run(ac, t)

    def addmeter(self, addnum):
        for i in range(addnum):
            eng = energy()
            ac = ACsampling()
            addr = creataddr(self.num+i)
            self.meter485list += [{'energy':eng, 'ac':ac, 'addr':addr}]
        self.num += addnum

    def readins(self,i):
        ac = self.meter485list[i]['ac']
        return ac

    def readenergy(self,i):
        eng = self.meter485list[i]['energy']
        return eng

    def readaddr(self,i):
        return self.meter485list[i]['addr']

    def readindex(self, addr):
        for i in range(self.num):
            if addr == self.meter485list[i]['addr']:
                return i
        return -1


if __name__ == '__main__':
    mtr = meter485()
    mtr.addmeter(3)
    addr = mtr.readaddr(1)
    index = mtr.readindex(addr)
    print(addr, index)
    mtr.run(3600)
    ac1 = mtr.readins(1)
    print(ac1.I)
    mtr.run(3600)
    ac1 = mtr.readins(1)
    print(ac1.I)



