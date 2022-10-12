# from ..searcher.searcher import Searcher
from .. import Searcher
from ..general import m_c2p, MATH_FORMAT
from IPython.display import HTML, Markdown, display
import logging
import string
import os
from shutil import copyfile


class Tester:
    def __init__(self):
        self.searcher = Searcher(algorithm=Searcher.ALG_CASBERT)
        self.viewTemplate = string.Template("""
            <hr style="height:2px;border:none;color:#333;background-color:#333;" />
            <details>
            <summary>${header}</summary>
            <p>
            ${content}
            </p>
            </details>
            """)
        self.cacheDir = os.path.join(os.path.abspath(''), 'cache')
        if not os.path.exists(self.cacheDir):
            os.makedirs(self.cacheDir)

    def __printMath(self, varData):
        def getVarMd(varData):
            logger = logging.getLogger()
            varMd = '<li>' + '; '.join(['<b>name:</b> %s' % varData['name'], '<b>type:</b> %s' %
                                        varData['type'], '<b>init:</b> %s' % varData['init']])
            if 'rate' in varData:
                varMd += '; <b>rate:</b> %s' % str(varData['rate'])
            varMd += '; <b>unit:</b> ' + \
                varData['unit']['text'] + \
                '<br>' if 'unit' in varData else '<br>'
            for mth in varData['math']:
                logger.disabled = True
                lttex = m_c2p(mth, format=MATH_FORMAT.JUPYTER)
                varMd += lttex + "<br>"

                if 'dependent' in varData:
                    if len(varData['dependent']) > 0:
                        varMd += '<ul><li><ul> dependents: '
                        for varIdDept, varDataDept in varData['dependent'].items():
                            varMd += getVarMd(varDataDept)
                        varMd += '</ul></li></ul>'
                logger.disabled = False

            return varMd + '</li>'

        varMd = getVarMd(varData)
        return varMd

    def searchVariables(self, query, top=100, verbose=False, minSim=0.5):
        result = self.searcher.searchVariables(query, top=top, minSim=minSim)
        html = ''
        for val in result['result']:
            header = '; '.join(['<b>name:</b> %s' % val['name'], '<b>type:</b> %s' %
                                val['type'], '<b>init:</b> %s' % val['init']])
            if 'rate' in val:
                header += '; <b>rate:</b> %s' % str(val['rate'])
            header += '; <b>unit:</b> ' + \
                val['unit']['text'] if 'unit' in val else ''
            content = 'CellML: <a href="%s">%s</a> <br>' % (
                val['cellmlUrl'], val['cellmlUrl'])
            content += 'Workspace: <a href="%s">%s</a> <br>' % (
                val['workspaceUrl'], val['workspaceUrl'])
            # print exposures
            if len(val['exposures']) > 0:
                content += 'Exposures: <ul>'
                for cellmlUrl in val['exposures']:
                    content += '<li><a href="%s">%s</a> </li>' % (
                        cellmlUrl, cellmlUrl)
                content += '</ul>'

            # print similar cellmls
            if len(val['similarCellmls']) > 0:
                content += 'Similar CellMLs: <ul>'
                for cellmlUrl in val['similarCellmls']:
                    content += '<li><a href="%s">%s</a> </li>' % (
                        cellmlUrl, cellmlUrl)
                content += '</ul>'

            # print images
            if 'cellmlImages' in val:
                for imgUrl in val['cellmlImages']:
                    content += '<img src="' + \
                        imgUrl['url'] + \
                        '" alt="drawing" style="width:400px;"/><br>'
            content += self.__printMath(val)
            content += '<hr style="height:1px;border:none;color:#333;background-color:#333;" />'

            replacer = {'header': header, 'content': content}
            html += self.viewTemplate.substitute(replacer)
        if verbose:
            display(HTML(html))
        else:
            return html
