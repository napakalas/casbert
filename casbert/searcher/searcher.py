from ..general import *
from ..colls.unit import Units
from ..colls.equation import Maths
from ..colls.variable import Variables
from ..colls.cellml import Cellmls
from ..colls.sedml import Sedmls
from ..colls.workspace import Workspaces
from ..colls.component import Components
from ..colls.image import Images
import os
import torch
from sentence_transformers import SentenceTransformer, util


class PmrIndex:
    def __init__(self, index):
        self._entityIds = index['id']
        self._entityClasses = index['class']
        self._entityEmbedding = index['embedding']

        BERTModel = 'multi-qa-MiniLM-L6-cos-v1'
        self._model = SentenceTransformer(BERTModel)

    def searchEntities(self, query, topK, minSim, indexType):
        return self._entitySearch(query, topK, minSim, indexType)

    def _entitySearch(self, query, topK, minSim, indexType):
        """
        In this approach:
        1. Get vector of query
        2. Get similar entities using cosine similarity
        3. Return topK result in descending
        """
        textEmbedding = self._model.encode(query, convert_to_tensor=True)
        # We use cosine-similarity and torch.topk to find the highest top_k scores
        cosScores = util.pytorch_cos_sim(
            textEmbedding, self._entityEmbedding[indexType])[0]
        topResults = torch.topk(cosScores, k=topK)
        results = []
        for rank, (score, idx) in enumerate(zip(topResults[0], topResults[1])):
            if score < minSim:
                break
            results += [self._entityIds[idx]]
        return results


class Searcher:
    # RETRIVAL ALGORITHMS
    ALG_BOOL = 0
    ALG_BM25 = 1
    ALG_CASBERT = 2

    IDX_CLASS = 'class'
    IDX_CLASS_PREDICATE = 'class_predicate'

    def __init__(self, algorithm=ALG_CASBERT, indexType=IDX_CLASS):
        """Initialise ...

        Parameters
        ----------
        algorithm ==> [Searcher.ALG_BOOL, Searcher.ALG_BM25, Searcher.ALG_CASBERT]
        indexType ==> [Searcher.IDX_CLASS, Searcher.IDX_CLASS_PREDICATE]
        ....

        Returns
        -------
        list
            a list of strings used that are the header columns
        """
        self.algorithm = algorithm
        indexPath = os.path.join(CURRENT_PATH, RESOURCE_DIR, 'casbert_pmr.pt')
        indexes = torch.load(indexPath, map_location=torch.device('cpu'))

        self.idxVar = PmrIndex(indexes['variable'])
        self.idxCellml = PmrIndex(indexes['cellml'])
        self.idxSedml = PmrIndex(indexes['sedml'])
        self.idxImage = PmrIndex(indexes['image'])
        self.idxComp = PmrIndex(indexes['component'])
        
        self.clusterer = loadJson(RESOURCE_DIR, RS_CLUSTERER)
        self.sysUnits = Units(RESOURCE_DIR, RS_UNIT)
        self.sysMaths = Maths(RESOURCE_DIR, RS_MATH)
        self.sysSedmls = Sedmls(RESOURCE_DIR, RS_SEDML)
        self.sysVars = Variables(self.sysMaths, RESOURCE_DIR, RS_VARIABLE)
        self.sysComps = Components(RESOURCE_DIR, RS_COMPONENT)
        self.sysWks = Workspaces(RESOURCE_DIR, RS_WORKSPACE)
        self.sysCellmls = Cellmls(RESOURCE_DIR, RS_CELLML)
        self.sysImages = Images(RESOURCE_DIR, RS_IMAGE)

    def search(self, query, top=20, minSim=0.5, indexType='class_predicate'):
        # classify the query vertically
        # queryTypes = self.__classify(query)

        # get result based on the classification results
        # temporarily just variable search :)
        # the sedml search temporarily is modified variable search

        # return self.__searchPlots(query, top, minSim)

        return self.__getVariables(query, top, minSim)

    def __getVariables(self, query, top, minSim, indexType):
        resultVars = self.idxVar.searchEntities(
            query, topK=top, minSim=minSim, indexType=indexType)
        result = {}
        for varId in resultVars:
            varData = {}
            # get main information
            varData['name'] = self.sysVars.getName(varId)
            varData['init'] = self.sysVars.getInit(varId)
            varData['type'] = self.sysVars.getType(varId)
            if varData['type'] == 'state':
                varData['rate'] = self.sysVars.getRate(varId)
            # get units
            varUnit = self.sysVars.getUnit(varId)
            varData['unit'] = {'name': self.sysUnits.getNames(
                varUnit)[0], 'text': self.sysUnits.getText(varUnit)}
            # get math
            varData['math'] = self.sysVars.getMaths(varId)
            # get maths' dependents
            varData['dependent'] = self.getEntityDependencyMaths(varId)
            # self.sysVars.getDependents(varId, varDep=varData['dependent'])
            # get leaves
            varData['rdfLeaves'] = self.sysVars.getObjLeaves(varId)
            # get sedmls and plot
            varData['plot'] = [os.path.join(
                CURRENT_PATH, RESOURCE_DIR, SEDML_IMG_DIR, plot+IMG_EXT) for plot in self.sysVars.getPlots(varId)]
            varData['sedml'] = [os.path.join(PMR_SERVER, self.sysSedmls.getUrl(
                plot.split('.')[0])) for plot in self.sysVars.getPlots(varId)]
            #get components
            varData['component'] = self.sysComps.getName(
                self.sysVars.getCompId(varId))
            varData['compLeaves'] = self.sysComps.getObjLeaves(
                self.sysVars.getCompId(varId))
            # get cellml, workspace, images
            cellmlId = self.sysComps.getCellml(self.sysVars.getCompId(varId))
            varData['cellmlUrl'] = PMR_SERVER + \
                self.sysCellmls.getUrl(id=cellmlId)
            varData['cellmlTitle'] = self.sysCellmls.getTitle(id=cellmlId)
            # varData['cellmlImages'] = [varData['cellmlUrl'][:varData['cellmlUrl'].rfind('/')+1]+self.sysImages.getPath(id) for id in self.sysCellmls.getImages(id=cellmlId)]
            varData['workspaceUrl'] = PMR_SERVER + \
                self.sysCellmls.getWorkspace(id=cellmlId)
            # get exposures
            exposures = self.sysWks.getExposures(
                url=self.sysCellmls.getWorkspace(id=cellmlId))
            varData['exposures'] = [PMR_SERVER +
                                    exposure for exposure in exposures.keys()]
            # get similar cellml using cluster
            varData['similarCellmls'] = self.getSimilarCellmls(varId)

            # get cellml images
            cellmlImages = []
            for imageId in self.sysCellmls.getImages(id=cellmlId):
                imagePath = os.path.join(CURRENT_PATH, WORKSPACE_DIR, os.path.dirname(
                    self.sysCellmls.getPath(id=cellmlId)), self.sysImages.getPath(imageId))
                if os.path.exists(imagePath):
                    cellmlImages += [os.path.join(os.path.dirname(
                        varData['cellmlUrl']), self.sysImages.getPath(imageId))]
            # get cellml images from other cellml / workspaces if not found
            if len(cellmlImages) == 0:
                for similarCellml in varData['similarCellmls']:
                    for imageId in self.sysCellmls.getImages(url=similarCellml):
                        imagePath = os.path.join(CURRENT_PATH, WORKSPACE_DIR, os.path.dirname(
                            self.sysCellmls.getPath(url=similarCellml)), self.sysImages.getPath(imageId))
                        if os.path.exists(imagePath):
                            cellmlImages += [os.path.join(os.path.dirname(
                                PMR_SERVER + similarCellml), self.sysImages.getPath(imageId))]
            varData['cellmlImages'] = cellmlImages

            result[varId] = varData

        return result

    def __searchPlots(self, query, top, minSim, indexType):
        def getVarDataForPlot(varId):
            varData = {}
            varData['name'] = self.sysVars.getName(varId)
            varData['init'] = self.sysVars.getInit(varId)
            varData['type'] = self.sysVars.getType(varId)
            if varData['type'] == 'state':
                varData['rate'] = self.sysVars.getRate(varId)
            varUnit = self.sysVars.getUnit(varId)
            varData['unit'] = {'name': self.sysUnits.getNames(
                varUnit)[0], 'text': self.sysUnits.getText(varUnit)}
            varData['math'] = self.sysVars.getMaths(varId)
            varData['dependent'] = {}
            self.sysVars.getDependents(varId, varDep=varData['dependent'])
            varData['rdfLeaves'] = self.sysVars.getObjLeaves(varId)
            return varData

        resultVars = self.idxVar.searchEntities(
            query, topK=top, minSim=minSim, indexType=indexType)
        resultPlots = {}
        # for each variable, identify the plot and store in a resultPlots
        for varId in resultVars:
            plots = self.sysVars.getPlots(varId)
            if len(plots) > 0:
                for plot in plots:
                    if plot not in resultPlots:
                        plotData = {}
                        plotData['variable'] = {}
                        sedmlId, plotId = plot.split('.')
                        varIdsPlot = self.sysSedmls.getVariables(
                            sedmlId, plot=plotId, collVariable=self.sysVars)
                        for varIdPlot in varIdsPlot:
                            if varIdPlot['id'] not in plotData['variable']:
                                plotData['variable'] += [
                                    getVarDataForPlot(varIdPlot['id'])]
                        resultPlots[plot] = plotData
                        resultPlots[plot]['path'] = os.path.join(
                            CURRENT_PATH, RESOURCE_DIR, SEDML_IMG_DIR, plot+IMG_EXT)
                        resultPlots[plot]['url'] = PMR_SERVER + \
                            self.sysSedmls.getUrl(sedmlId)
                        resultPlots[plot]['workspaceUrl'] = PMR_SERVER + \
                            self.sysSedmls.getWorkspace(sedmlId)
                        cellmlId = self.sysSedmls.getCellmlId(sedmlId)
                        resultPlots[plot]['cellmlUrl'] = PMR_SERVER + \
                            self.sysCellmls.getUrl(id=cellmlId)
                        # get exposures
                        exposures = self.sysWks.getExposures(
                            url=self.sysCellmls.getWorkspace(id=cellmlId))
                        resultPlots[plot]['exposures'] = [
                            PMR_SERVER + exposure for exposure in exposures.keys()]
                        # get similar cellml using cluster
                        similarCellmls = self.__getOtherCellms(cellmlId)
                        resultPlots[plot]['similarCellmls'] = [
                            PMR_SERVER + url for url in similarCellmls]

                        # get cellml images
                        cellmlImages = []
                        for imageId in self.sysCellmls.getImages(id=cellmlId):
                            imagePath = os.path.join(CURRENT_PATH, WORKSPACE_DIR, os.path.dirname(
                                self.sysCellmls.getPath(id=cellmlId)), self.sysImages.getPath(imageId))
                            if os.path.exists(imagePath):
                                cellmlImages += [os.path.join(os.path.dirname(
                                    resultPlots[plot]['cellmlUrl']), self.sysImages.getPath(imageId))]
                        # get cellml images from other cellml / workspaces if not found
                        if len(cellmlImages) == 0:
                            for similarCellml in similarCellmls:
                                for imageId in self.sysCellmls.getImages(url=similarCellml):
                                    imagePath = os.path.join(CURRENT_PATH, WORKSPACE_DIR, os.path.dirname(
                                        self.sysCellmls.getPath(url=similarCellml)), self.sysImages.getPath(imageId))
                                    if os.path.exists(imagePath):
                                        cellmlImages += [os.path.join(os.path.dirname(
                                            PMR_SERVER + similarCellml), self.sysImages.getPath(imageId))]
                        resultPlots[plot]['cellmlImages'] = cellmlImages

        return resultPlots

    def searchPlots(self, query, top=20, minSim=0.5, indexType='class_predicate'):
        def getVarDataForPlot(varId):
            varData = {}
            varData['id'] = varId
            varData['name'] = self.sysVars.getName(varId)
            varData['init'] = self.sysVars.getInit(varId)
            varData['type'] = self.sysVars.getType(varId)
            if varData['type'] == 'state':
                varData['rate'] = self.sysVars.getRate(varId)
            varUnit = self.sysVars.getUnit(varId)
            varData['unit'] = {'name': self.sysUnits.getNames(
                varUnit)[0], 'text': self.sysUnits.getText(varUnit)}
            varData['math'] = self.sysVars.getMaths(varId, MATH_FORMAT.LATEX)
            # get classes
            varData['classes'] = self.getEntityClasses(varId)
            return varData

        resultVars = self.idxVar.searchEntities(
            query, topK=2000, minSim=minSim)
        result = {}

        validPlots = []
        for varId in resultVars:
            if len(validPlots) >= top:
                break
            plots = self.sysVars.getPlots(varId)
            validPlots += [
                p for p in plots if p not in validPlots and len(validPlots) <= top]

        # for each variable, identify the plot and store in a resultPlots
        for plot in validPlots:
            plotData = {}
            plotData['variable'] = []
            sedmlId, plotId = plot.split('.')
            varIdsPlot = self.sysSedmls.getVariables(
                sedmlId, plot=plotId, collVariable=self.sysVars)
            for varIdPlot in varIdsPlot:
                if varIdPlot['id'] not in plotData['variable']:
                    plotData['variable'] += [
                        getVarDataForPlot(varIdPlot['id'])]
            plotData['path'] = os.path.join(
                CURRENT_PATH, RESOURCE_DIR, SEDML_IMG_DIR, plot+IMG_EXT)
            plotData['url'] = PMR_SERVER + self.sysSedmls.getUrl(sedmlId)
            plotData['workspaceUrl'] = PMR_SERVER + \
                self.sysSedmls.getWorkspace(sedmlId)
            cellmlId = self.sysSedmls.getCellmlId(sedmlId)
            plotData['cellmlUrl'] = PMR_SERVER + \
                self.sysCellmls.getUrl(id=cellmlId)
            # get exposures
            exposures = self.sysWks.getExposures(
                url=self.sysCellmls.getWorkspace(id=cellmlId))
            plotData['exposures'] = [PMR_SERVER +
                                     exposure for exposure in exposures.keys()]
            result[plot] = plotData
        return {'result': result, 'filter': self.__getFilter(result, 'sedml')}

    def searchVariables(self, query, top=20, minSim=0.5, indexType='class_predicate'):
        results = self.idxVar.searchEntities(
            query, topK=top, minSim=minSim, indexType=indexType)
        result = [self.getEntityMetadata(varId) for varId in results]
        return {'result': result, 'filter': self.__getFilter(result, 'variable')}

    def searchCellmls(self, query, top=20, minSim=0.5, indexType='class_predicate'):
        results = self.idxCellml.searchEntities(
            query, topK=top, minSim=minSim, indexType=indexType)
        cellmls = []
        for cellmlUrl in results:
            cellml = {'url': PMR_SERVER + cellmlUrl}
            cellml['title'] = self.sysCellmls.getTitle(url=cellmlUrl)
            workspace = self.sysCellmls.getWorkspace(url=cellmlUrl)
            cellml['workspace'] = PMR_SERVER + workspace
            exposures = self.sysWks.getExposures(url=workspace)
            cellml['exposure'] = [PMR_SERVER + e for e in exposures.keys()]
            cellml['abstract'] = self.sysCellmls.getAbstract(url=cellmlUrl)
            cellml['image'] = self.__getEntityImages(cellmlUrl=cellmlUrl)
            cellml['sedmls'] = []
            for sedmlId in self.sysCellmls.getSedmls(url=cellmlUrl):
                sedmlUrl = self.sysSedmls.getUrl(sedmlId)
                cellml['sedmls'] += [{'id': sedmlUrl, 'plots': self.sysSedmls.getPlots(
                    id=sedmlId, collVariable=self.sysVars)}]
            cellmls += [cellml]
        return cellmls

    def searchSedmls(self, query, top=20, minSim=0.5, indexType='class_predicate'):
        results = self.idxSedml.searchEntities(
            query, topK=top, minSim=minSim, indexType=indexType)
        sedmls = []
        for id in results:
            sedml = {'url': PMR_SERVER + self.sysSedmls.getUrl(id)}
            cellmlUrl = self.sysSedmls.getCellmlUrl(self.sysCellmls, id=id)
            sedml['cellmlUrl'] = PMR_SERVER + cellmlUrl
            sedml['cellmlTitle'] = self.sysCellmls.getTitle(url=cellmlUrl)
            sedml['plots'] = self.sysSedmls.getPlots(
                id=id, collVariable=self.sysVars)
            workspace = self.sysSedmls.getWorkspace(id=id)
            sedml['workspace'] = PMR_SERVER + workspace
            exposures = self.sysWks.getExposures(url=workspace)
            sedml['exposure'] = [PMR_SERVER + e for e in exposures.keys()]
            sedmls += [sedml]
        return sedmls

    def searchImages(self, query, top=20, minSim=0.5, indexType='class_predicate'):
        results = self.idxImage.searchEntities(
            query, topK=top, minSim=minSim, indexType=indexType)
        images = []
        for id in results:
            image = self.sysImages.getData(id)
            if len(image) == 0:
                continue
            workspace = self.sysCellmls.getWorkspace(id=image['cellml'])
            image['url'] = os.path.join(
                PMR_SERVER, workspace, 'rawfile/HEAD', self.sysImages.getPath(id))
            image['cellmlUrl'] = PMR_SERVER + \
                self.sysCellmls.getUrl(id=image['cellml'])
            image['workspaceUrl'] = PMR_SERVER + workspace

            exposures = self.sysWks.getExposures(url=workspace)
            image['exposures'] = [PMR_SERVER + e for e in exposures.keys()]

            images += [image]
        return images

    def searchComponents(self, query, top=20, minSim=0.5, indexType='class_predicate'):
        results = self.idxComp.searchEntities(
            query, topK=top, minSim=minSim, indexType=indexType)
        components = []
        for id in results:
            metadata = {'id': id, 'math': [], 'classes': {}}
            metadata['name'] = self.sysComps.getName(id)
            # get math and classes
            for varId in self.sysComps.getVariables(id):
                clss = {**metadata['classes'], **self.getEntityClasses(varId)}
                metadata['classes'] = clss
                if len(metadata['math']) > 0:
                    continue
                else:
                    metadata['math'] = self.getEntityMaths(varIds=varId)
            # get cellml, workspace
            cellmlId = self.sysComps.getCellml(id)
            cellmlUrl = self.sysCellmls.getUrl(id=cellmlId)
            metadata['cellmlUrl'] = PMR_SERVER + cellmlUrl
            metadata['cellmlTitle'] = self.sysCellmls.getTitle(id=cellmlId)
            workspaceUrl = self.sysCellmls.getWorkspace(id=cellmlId)
            metadata['workspaceUrl'] = PMR_SERVER + workspaceUrl
            # get exposures
            workspaceUrl = self.sysCellmls.getWorkspace(id=cellmlId)
            exposures = self.sysWks.getExposures(url=workspaceUrl)
            metadata['exposures'] = [PMR_SERVER + e for e in exposures.keys()]
            components += [metadata]
        return {'result': components, 'filter': self.__getFilter(components, 'component')}

    """
    BLOCK METHODS TO GET DETAIL OF A PARTICULAR VARIABLE
    """

    def getEntityMetadata(self, varId):
        metadata = {}
        # get main information
        metadata['id'] = varId
        metadata['name'] = self.sysVars.getName(varId)
        metadata['init'] = self.sysVars.getInit(varId)
        metadata['type'] = self.sysVars.getType(varId)
        if metadata['type'] == 'state':
            metadata['rate'] = self.sysVars.getRate(varId)
        # get units
        varUnit = self.sysVars.getUnit(varId)
        metadata['unit'] = {'name': self.sysUnits.getNames(
            varUnit)[0], 'text': self.sysUnits.getText(varUnit)}
        # get math
        metadata['math'] = self.getEntityMaths(varIds=varId)
        # get classes
        metadata['classes'] = self.getEntityClasses(varId)
        # get components
        metadata['component'] = self.sysComps.getName(
            self.sysVars.getCompId(varId))
        metadata['compLeaves'] = self.sysComps.getObjLeaves(
            self.sysVars.getCompId(varId))
        # get cellml, workspace
        cellmlId = self.sysComps.getCellml(self.sysVars.getCompId(varId))
        metadata['cellmlUrl'] = PMR_SERVER + \
            self.sysCellmls.getUrl(id=cellmlId)
        metadata['cellmlTitle'] = self.sysCellmls.getTitle(id=cellmlId)
        metadata['workspaceUrl'] = PMR_SERVER + \
            self.sysCellmls.getWorkspace(id=cellmlId)
        # get exposures
        exposures = self.sysWks.getExposures(
            url=self.sysCellmls.getWorkspace(id=cellmlId))
        metadata['exposures'] = [PMR_SERVER +
                                 exposure for exposure in exposures.keys()]
        # get additional data
        # metadata['plots'] = self.getEntityPlots(varId)
        metadata['sedmls'] = self.getEntitySedmls(varId)
        metadata['cellmlImages'] = self.getEntityImages(varId)
        metadata['similarCellmls'] = self.getSimilarCellmls(varId)
        return metadata

    def getEntityClasses(self, varId):
        if varId in self.idxVar._entityClasses:
            return self.idxVar._entityClasses[varId]['classes']
        return {}

    def getComponentCode(self, compId=None, varId=None, format=MATH_FORMAT.CODE):
        if compId is None:
            compId = self.sysVars.getCompId(varId)
        return self.sysComps.getComponentCode(compId, format)

    def getEntityMaths(self, compId=None, varIds=None, format=MATH_FORMAT.LATEX):
        if varIds is None:
            varIds = self.sysComps.getVariables(compId)
        if isinstance(varIds, str):
            varIds = [varIds]
        rs = []
        for varId in varIds:
            rs += self.sysVars.getMaths(varId, format)
        return list(set(rs))

    # be careful with getEntityDependencyMaths since it may take a long time
    # to be executed due to the recursive nature
    def getEntityDependencyMaths(self, varId, format=MATH_FORMAT.LATEX):
        varData = {}
        self.sysVars.getDependents(varId, format, varDep=varData)
        for varId, var in varData.items():
            names = var['name'].split('_')
            name = '{'+names[-1]+'}'
            for i in range(len(names)-2, -1, -1):
                if names[i] in greek_name2code:
                    names[i] = '\\' + names[i]
                name = '{' + names[i] + "_" + name + '}'
                names[i] = '\\mathit{' + names[i] + '}'
                var['name'] = name
        return varData

    def getEntityPlots(self, varId):
        return [os.path.join('images', plot+IMG_EXT) for plot in self.sysVars.getPlots(varId)]

    def getEntitySedmls(self, varId):
        sedmls = {}
        for plotId in self.sysVars.getPlots(varId):
            sedmlId = plotId.split('.')[0]
            sedmlUrl = PMR_SERVER + self.sysSedmls.getUrl(sedmlId)
            if sedmlUrl not in sedmls:
                sedmls[sedmlUrl] = []
            sedmls[sedmlUrl] += [
                {'url': os.path.join(plotId + IMG_EXT)}]
        return [{'id': k, 'plots': v} for (k, v) in sedmls.items()]

    def getEntityImages(self, varId):
        cellmlId = self.sysComps.getCellml(self.sysVars.getCompId(varId))
        cellmlImages = self.__getEntityImages(cellmlId=cellmlId)
        if len(cellmlImages) == 0:
            tmpImgs = {}
            similarCellmls = self.__getOtherCellms(cellmlId)
            for similarCellml in similarCellmls:
                cellmlImages += self.__getEntityImages(cellmlUrl=similarCellml)
                for image in cellmlImages:
                    if image['url'] not in tmpImgs:
                        tmpImgs[image['url']] = image
                    else:
                        tmpImgs[image['url']
                                ]['meta']['cellml'] += image['meta']['cellml']
                        tmpImgs[image['url']
                                ]['meta']['workspace'] += image['meta']['workspace']
                        tmpImgs[image['url']
                                ]['meta']['exposure'] += image['meta']['exposure']
            return list(tmpImgs.values())
        else:
            return cellmlImages

    def __getEntityImages(self, cellmlId=None, cellmlUrl=None):
        cellmlImages = []
        if cellmlId != None:
            cellmlUrl = self.sysCellmls.getUrl(id=cellmlId)
        workspace = self.sysCellmls.getWorkspace(url=cellmlUrl)
        exposure = list(self.sysWks.getExposures(url=workspace).keys())
        for imageId in self.sysCellmls.getImages(url=cellmlUrl):
            if self.sysImages.isAvailable(imageId):
                imageUrl = os.path.join(PMR_SERVER, self.sysCellmls.getWorkspace(
                    url=cellmlUrl), 'rawfile/HEAD', self.sysImages.getPath(imageId))
                imageTitle = self.sysImages.getTitle(imageId)
                meta = {'cellml': [PMR_SERVER + cellmlUrl],
                        'workspace': [PMR_SERVER + workspace]}
                if len(exposure) > 0:
                    meta['exposure'] = [PMR_SERVER + exposure[0]]
                else:
                    meta['exposure'] = []
                cellmlImages += [{'url': imageUrl,
                                  'title': imageTitle,
                                  'meta': meta}]
        return cellmlImages

    def getSimilarCellmls(self, varId):
        cellmlId = self.sysComps.getCellml(self.sysVars.getCompId(varId))
        similarCellmls = self.__getOtherCellms(cellmlId)
        return [PMR_SERVER + url for url in similarCellmls]

    def __getOtherCellms(self, cellmlId):
        url = self.sysCellmls.getUrl(id=cellmlId)
        clusterId = self.clusterer['url2Cluster'][url]
        if clusterId == '-1':
            return []
        others = self.clusterer['cluster'][clusterId] + []
        others.remove(url)
        return others

    """
    END OF BLOCK METHODS TO GET DETAIL OF A PARTICULAR VARIABLE
    """

    """ METHOD FOR GENERATING FILTER TO SHOW RESULTS (ENTITY or SEDML) """

    def __getFilter(self, result, rsType):
        filter = {}

        def extractVar(objectId, rs):
            classes = rs['classes']
            for classId, attr in classes.items():
                if classId not in filter:
                    filter[classId] = {'classes': [], 'entities': []}
                    filter[classId]['name'] = attr['name']
                filter[classId]['classes'] += list(classes.keys())
                filter[classId]['entities'] += [objectId]

        if rsType in ['variable', 'component']:
            for rs in result:
                extractVar(rs['id'], rs)
        elif rsType == 'sedml':
            for plotId, v in result.items():
                for variable in v['variable']:
                    extractVar(plotId, variable)
        for v in filter.values():
            v['classes'] = list(set(v['classes']))

        return filter
