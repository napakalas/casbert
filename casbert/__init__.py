# extract the required data
from .general import updateIndexes, __extractData, __loadData
__extractData()
__loadData()

from .searcher.searcher import Searcher
from .tester.tester import Tester