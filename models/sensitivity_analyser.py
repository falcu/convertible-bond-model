import matplotlib.pyplot as plt

class SensitivityAnalyser:
    def __init__(self, objectToChange, actionToExecute):
        self.objectToChange = objectToChange
        self.actionToExecute = actionToExecute

    def analyzeValues(self, dependentValues, attributeName):
        if not hasattr( self.objectToChange, attributeName):
            raise Exception('Object {} has no attribute {}'.format( self.objectToChange, attributeName))

        def mapFunc( aValue ):
                setattr( self.objectToChange, attributeName, aValue)
                return self.actionToExecute()

        return list(map(mapFunc, dependentValues))

class ThreadData:
    def __init__(self, id, data, result=None):
        self.id = id
        self.data = data
        self.result = result

class ConvertibleBondSensitivityAnalyzer:
    def __init__(self, convertibleBondModel):
        self.convertibleBondModel = convertibleBondModel

    def analyzeBondPrice(self, attributeToAnalyze, dependentValues):
        helper = SensitivityAnalyser(self.convertibleBondModel.modelInput,self.convertibleBondModel.priceBond)
        return helper.analyzeValues( dependentValues, attributeToAnalyze)

    def analyzeBondPriceNoConversion(self, attributeToAnalyze, dependentValues):
        helper = SensitivityAnalyser(self.convertibleBondModel.modelInput, self.convertibleBondModel.priceBondWithNoConversion)
        return helper.analyzeValues(dependentValues, attributeToAnalyze)

class Plotter:
    def __init__(self, title='Convertible Bond'):
        self.figure = None
        self._plot = None
        self.title = title
        self.newGraph = 1

    def plot(self, dataToPlot, newGraph=True):
        '''dataToPlot is a list of dictionaries'''
        figure,thePlot = self._initializePlot( newGraph )
        for aData in dataToPlot:
            xValues = aData['x']
            yValues = aData['y']
            color   = '-{}'.format( aData.get('color','r') )
            label   = aData.get('label','')
            thePlot.plot( xValues, yValues, color, label=label)
            thePlot.legend(loc='upper left')

        figure.show()

    def _initializePlot(self, newGraph):
        if newGraph:
            fig = plt.figure('{} New Graph {}'.format(self.title, self.newGraph))
            thePlot = fig.add_subplot(111)
            self.newGraph += 1
            return fig, thePlot
        else:
            if self.figure:
                plt.close( self.figure )
            self.figure = plt.figure(self.title)
            self._plot = self.figure.add_subplot(111)

            return self.figure, self._plot





