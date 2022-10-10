from .pmrcollection import PmrCollection
from ..general import MATH_FORMAT


class Sedmls(PmrCollection):
    def __init__(self, *paths):
        super().__init__(*paths)
        self.id2Url = {v['id']: k for k, v in self.data.items()}
        self.statusC = {'deprecated': 0, 'current': 1,
                        'validating': 2, 'invalid': 3}

    def getUrl(self, id):
        return self.id2Url[id] if id in self.id2Url else None

    def getVariables(self, id, plot=None, collVariable=None, format=MATH_FORMAT.LATEX):
        url = self.getUrl(id)
        if plot == None:
            return self.data[url]['variables']
        else:
            series = self.data[url]['outputs'][plot]
            checkVars, variables = [], []
            for seri in series:
                vars = {}
                for axis in ['x', 'y']:
                    if seri[axis] not in checkVars:
                        vars['id'] = seri[axis]
                        vars['init'] = self.data[url]['variables'][seri[axis]]
                        vars['math'] = collVariable.getMaths(
                            seri[axis], format=format)
                    checkVars += [seri[axis]]
                if len(vars) > 0:
                    variables += [vars]
            return variables

    def getWorkspace(self, id=None, url=None):
        if url is None:
            url = self.getUrl(id)
        return self.data[url]['workspace']

    def getCellmlId(self, id=None, url=None):
        if url is None:
            url = self.getUrl(id)
        return self.data[url]['models']['model']

    def getPlots(self, id=None, url=None, collVariable=None, format=MATH_FORMAT.LATEX):
        if id is not None:
            url = self.getUrl(id)
        try:
            result = []
            for plotId, plot in self.data[url]['outputs'].items():
                rs = {'url': self.data[url]['id'] + '.' + plotId + '.png'}
                rs['variables'] = self.getVariables(
                    self.data[url]['id'], plot=plotId, collVariable=collVariable, format=format)
                result += [rs]
            return result
        except Exception:
            return []

    def getCellmlUrl(self, cellmlColl, id=None, url=None):
        if url is None:
            cellmlId = self.getCellmlId(id=id)
        else:
            cellmlId = self.getCellmlId(url=url)
        return cellmlColl.getUrl(id=cellmlId)
