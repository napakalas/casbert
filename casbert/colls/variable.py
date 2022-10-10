from .pmrcollection import PmrCollection
from ..general import MATH_FORMAT
import math


class Variables(PmrCollection):
    def __init__(self, sysMaths, *paths):
        super().__init__(*paths)
        self.sysMaths = sysMaths

    def getT2Id(self, ids=None, short=False):
        if ids != None:
            return {self.getName(id, short): id for id in ids if self.getType(id) != 'rate'}
        return {self.getName(id, short): id for id in self.data if self.getType(id) != 'rate'}

    def getName(self, id, short=False):
        if short:
            return(self.data[id]['shortName'])
        return self.data[id]['name']

    def getType(self, id):
        return self.data[id]['type']

    def getInit(self, id):
        if not math.isnan(self.data[id]['init']):
            return self.data[id]['init']
        return '-'

    def getRate(self, id):
        if self.getType(id) == 'state':
            if not math.isnan(self.data[id]['rate']):
                return self.data[id]['rate']
        return '-'

    def getMaths(self, id, format=MATH_FORMAT.WEB):
        varMaths = []
        if 'math' in self.data[id]:
            for mathId in self.data[id]['math']:
                varMaths += [self.sysMaths.getText(mathId, format)]
        return varMaths

    def getDependents(self, id, format=MATH_FORMAT.WEB, varDep={}):
        if 'dependent' in self.data[id]:
            if len(self.data[id]['dependent']) > 0:
                for varIdDep, varNameDep in self.data[id]['dependent'].items():
                    if varIdDep not in varDep:
                        varDep[varIdDep] = {'name': varNameDep, 'math': self.getMaths(
                            varIdDep, format), 'type': self.getType(varIdDep), 'init': self.getInit(varIdDep)}
                        if 'dependent' in self.data[varIdDep]:
                            if len(self.data[varIdDep]['dependent']) > 0:
                                self.getDependents(varIdDep, format, varDep)

    def getUnit(self, id):
        return self.data[id]['unit']

    def getPlots(self, id):
        if 'plot' in self.data[id]:
            return self.data[id]['plot']
        return []

    def getCompId(self, id):
        return self.data[id]['component']
