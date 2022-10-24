# extract the required data
from .general import updateIndexes, __extractData
__extractData()

from .searcher.searcher import Searcher
from .tester.tester import Tester