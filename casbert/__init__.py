# extract the required data
def __extractData():
    import os
    path = os.path.dirname(os.path.realpath(__file__))
    drive = os.path.join(path, 'resources')
    checkedFile = os.path.join(drive, 'listOfMath.json')
    isExist = os.path.exists(checkedFile)

    if not isExist:
        import zipfile
        file = os.path.join(drive, 'casbert_data.zip')
        with zipfile.ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(drive)


__extractData()

# import main classes
from .searcher.searcher import Searcher
from .tester.tester import Tester