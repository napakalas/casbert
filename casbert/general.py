import json
import os
import requests
import pickle
import gzip
import io
from lxml import etree
from enum import Enum
import regex as re


"""init global variable"""
CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
PMR_SERVER = 'https://models.physiomeproject.org/'
WORKSPACE_DIR = 'workspaces'
INDEX_DIR = 'index'
RESOURCE_DIR = 'resources'
ONTOLOGY_DIR = 'ontologies'
SEDML_IMG_DIR = 'sedmlImages'
SEDML_RSL_DIR = 'sedmlResults'

# RESOURCE FILE COLLECTION
RS_CATEGORY = 'listOfCategory.json'
RS_CELLML = 'listOfCellml.json'
RS_COMPONENT = 'listOfComponent.json'
RS_EXPOSURE = 'listOfExposure.json'
RS_IMAGE = 'listOfImage.json'
RS_MATH = 'listOfMath.json'
RS_SEDML = 'listOfSedml.json'
RS_UNIT = 'listOfUnit.json'
RS_VARIABLE = 'listOfVariable.json'
RS_VIEW = 'listOfView.json'
RS_WORKSPACE = 'listOfWorkspace.json'
RS_C2P_XSL = 'ctopff.xsl'
RS_M2L_XSL = 'mmltex.xsl'
RS_CLUSTERER = 'cellmlClusterer.json'
RS_ONTOLOGY = 'ontoDf.gz'

IMG_EXT = '.png'

# INDEXING SETTING
STEM_PORTER = 0
STEM_LANCASTER = 1
IS_LOWER = True
IS_LEMMA = True

URL_CASBERT_INDEX = 'https://auckland.figshare.com/ndownloader/files/37932492'


class MATH_FORMAT(Enum):
    """MATH DESTINATION"""
    CODE = 0
    WEB = 1
    JUPYTER = 2
    LATEX = 3


def loadJson(*paths):
    file = os.path.join(CURRENT_PATH, *paths)
    isExist = os.path.exists(file)
    if isExist:
        with open(file, 'r') as fp:
            data = json.load(fp)
        fp.close()
        return data
    else:
        return {}


def dumpJson(data, *paths):
    file = os.path.join(CURRENT_PATH, *paths)
    with open(file, 'w') as fp:
        json.dump(data, fp)
    fp.close()


def saveToFlatFile(data, *paths):
    file = os.path.join(CURRENT_PATH, *paths)
    f = open(file, 'w+')
    for datum in data:
        f.write(str(datum).replace('\n', ' ').replace('\r', ' ') + '\n')
    f.close()


def loadFromFlatFile(*paths):
    file = os.path.join(CURRENT_PATH, *paths)
    try:
        f = open(file, 'r')
        lines = f.readlines()
        f.close()
        return lines
    except:
        return []


def saveBinaryInteger(data, *paths):
    import struct
    file = os.path.join(CURRENT_PATH, *paths)
    with open(file, "wb") as f:
        for x in data:
            f.write(struct.pack('i', x))  # 4bytes
    f.close()


def loadBinaryInteger(*paths):
    import struct
    file = os.path.join(CURRENT_PATH, *paths)
    with open(file, 'rb') as f:
        bdata = []
        while True:
            bytes = f.read(4)
            if bytes == b'':
                break
            else:
                bdata.append(struct.unpack('i', bytes)[0])  # 4bytes
    f.close()
    return bdata


def dumpPickle(data, *paths):
    filename = os.path.join(CURRENT_PATH, *paths)
    file = gzip.GzipFile(filename, 'wb')
    pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)
    file.close()


def loadPickle(*paths):
    filename = os.path.join(CURRENT_PATH, *paths)
    file = gzip.GzipFile(filename, 'rb')
    data = pickle.load(file)
    file.close()
    return data


def getAllFilesInDir(*paths):
    drc = os.path.join(CURRENT_PATH, *paths)
    lst = []
    for path, subdirs, files in os.walk(drc):
        for name in files:
            lst += [os.path.join(path, name)]
    return lst

# get list of URLs inside a particulat URL in the PMR


def getUrlFromPmr(url):
    r = requests.get(
        url, headers={"Accept": "application/vnd.physiome.pmr2.json.1"})
    urls = [link['href'] for link in r.json()['collection']['links']]
    return urls

# get json from PMR based on URL address


def getJsonFromPmr(url):
    r = requests.get(
        url, headers={"Accept": "application/vnd.physiome.pmr2.json.1"})
    try:
        return r.json()['collection']
    except:
        return {}


greek_code2name = {
    u'\u0391': 'Alpha',
    u'\u0392': 'Beta',
    u'\u0393': 'Gamma',
    u'\u0394': 'Delta',
    u'\u0395': 'Epsilon',
    u'\u0396': 'Zeta',
    u'\u0397': 'Eta',
    u'\u0398': 'Theta',
    u'\u0399': 'Iota',
    u'\u039A': 'Kappa',
    u'\u039B': 'Lamda',
    u'\u039C': 'Mu',
    u'\u039D': 'Nu',
    u'\u039E': 'Xi',
    u'\u039F': 'Omicron',
    u'\u03A0': 'Pi',
    u'\u03A1': 'Rho',
    u'\u03A3': 'Sigma',
    u'\u03A4': 'Tau',
    u'\u03A5': 'Upsilon',
    u'\u03A6': 'Phi',
    u'\u03A7': 'Chi',
    u'\u03A8': 'Psi',
    u'\u03A9': 'Omega',
    u'\u03B1': 'alpha',
    u'\u03B2': 'beta',
    u'\u03B3': 'gamma',
    u'\u03B4': 'delta',
    u'\u03B5': 'epsilon',
    u'\u03B6': 'zeta',
    u'\u03B7': 'eta',
    u'\u03B8': 'theta',
    u'\u03B9': 'iota',
    u'\u03BA': 'kappa',
    u'\u03BB': 'lamda',
    u'\u03BC': 'mu',
    u'\u03BD': 'nu',
    u'\u03BE': 'xi',
    u'\u03BF': 'omicron',
    u'\u03C0': 'pi',
    u'\u03C1': 'rho',
    u'\u03C3': 'sigma',
    u'\u03C4': 'tau',
    u'\u03C5': 'upsilon',
    u'\u03C6': 'phi',
    u'\u03C7': 'chi',
    u'\u03C8': 'psi',
    u'\u03C9': 'omega',
}

greek_name2code = {v: k for k, v in greek_code2name.items()}
tran_c2p = None
tran_m2l = None


def m_c2p(math_c, format=MATH_FORMAT.WEB):
    preff = '{http://www.w3.org/1998/Math/MathML}'
    if '<math ' not in math_c:
        math_c = '<math xmlns="http://www.w3.org/1998/Math/MathML">' + math_c + '</math>'
    mml_dom = etree.fromstring(math_c)
    mmldom = tran_c2p(mml_dom)
    root = mmldom.getroot()
    for name in root.iter(preff + 'mi'):
        comps = name.text.split('_')
        if len(comps) > 1:
            if format == MATH_FORMAT.WEB:
                comps = [
                    '&' + x + ';' if x in greek_name2code else x for x in comps]
            elif format == MATH_FORMAT.JUPYTER:
                comps = [greek_name2code[x]
                         if x in greek_name2code else x for x in comps]
            name.tag = preff + 'msub'
            name.text = ''
            name.attrib.pop('mathvariant')
            rightEl = etree.Element(
                preff + 'mn' if comps[len(comps) - 1].isnumeric() else 'mi', mathvariant='italic')
            rightEl.text = comps[len(comps) - 1]
            leftEl = etree.Element(
                preff + 'mn' if comps[len(comps) - 2].isnumeric() else 'mi', mathvariant='italic')
            leftEl.text = comps[len(comps) - 2]
            if len(comps) > 2:
                subEl = etree.Element(preff + 'msub')
                subEl.append(leftEl)
                subEl.append(rightEl)
                for i in range(len(comps) - 3, -1, -1):
                    rightEl = subEl
                    leftEl = etree.Element(
                        preff + 'mn' if comps[i].isnumeric() else 'mi', mathvariant='italic')
                    leftEl.text = comps[i]
                    subEl = etree.Element(preff + 'msub')
                    subEl.append(leftEl)
                    subEl.append(rightEl)
            name.append(leftEl)
            name.append(rightEl)
    for elem in root.iter('*'):
        if elem.text != None:
            elem.text = elem.text.strip()
    return str(mmldom).replace('·', '&#xB7;').replace('−', '-').replace('<?xml version="1.0"?>', '<?xml version="1.0" encoding="UTF-8"?>')


def mml2tex(text):
    """ Remove TeX codes in text"""
    text = re.sub(r"(\$\$.*?\$\$)", " ", text)

    """ Find MathML codes and replace it with its LaTeX representations."""
    mml_codes = re.findall(r"(<math.*?<\/math>)", text)
    for mml_code in mml_codes:
        # Required.
        mml_ns = mml_code.replace(
            '<math>', '<math xmlns="http://www.w3.org/1998/Math/MathML">')
        mml_dom = etree.fromstring(mml_ns)
        mmldom = tran_m2l(mml_dom)
        latex_code = str(mmldom)
        latex_code = latex_code.replace('·', '.').replace('\\hfill', ' ')
        if '=\\left\\{' in latex_code and not latex_code.endswith('\\right\\}'):
            latex_code = latex_code[0:-1] + '\\right\\}' + latex_code[-1]
        if '\\multicolumn{2}{c}' in latex_code:
            latex_code = latex_code.replace('\\multicolumn{2}{c}', ' & ')
    return latex_code


def updateIndexes(filePath=''):
    import zipfile
    path = os.path.dirname(os.path.realpath(__file__))
    if not os.path.exists(filePath):
        print("... downloading from server")
        fileUrl = URL_CASBERT_INDEX
        r = requests.get(fileUrl)
        print("... extracting data")
        packz = zipfile.ZipFile(io.BytesIO(r.content))
        for name in packz.namelist():
            packz.extract(name, path)
        print("... done")
    else:
        pz = open(filePath, 'rb')
        packz = zipfile.ZipFile(pz)
        for name in packz.namelist():
            packz.extract(name, path)
        pz.close()


def __extractData():
    path = os.path.dirname(os.path.realpath(__file__))
    drive = os.path.join(path, RESOURCE_DIR)
    checkedFile = os.path.join(drive, RS_MATH)

    if not os.path.exists(checkedFile):
        updateIndexes(os.path.join(drive, 'casbert_data.zip'))


def __loadData():
    xsl_c2p = etree.parse(os.path.join(CURRENT_PATH, RESOURCE_DIR, RS_C2P_XSL))
    global tran_c2p
    tran_c2p = etree.XSLT(xsl_c2p)
    xsl_m2l = etree.parse(os.path.join(CURRENT_PATH, RESOURCE_DIR, RS_M2L_XSL))
    global tran_m2l
    tran_m2l = etree.XSLT(xsl_m2l)
