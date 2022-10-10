from .pmrcollection import PmrCollection
from ..general import MATH_FORMAT, m_c2p, mml2tex


class Maths(PmrCollection):
    def __init__(self, *paths):
        super().__init__(*paths)

    def getText(self, id, format=MATH_FORMAT.CODE):
        if format == MATH_FORMAT.CODE:
            return self.data[id]
        if format in [MATH_FORMAT.WEB, MATH_FORMAT.JUPYTER]:
            return m_c2p(self.data[id], format)
        if format == MATH_FORMAT.LATEX:
            mathP = m_c2p(self.data[id], MATH_FORMAT.JUPYTER)
            return mml2tex(mathP)[1:-1]
        return ''
