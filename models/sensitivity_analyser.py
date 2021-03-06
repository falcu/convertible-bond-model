import matplotlib.pyplot as plt

class SensitivityAnalyser:
    def __init__(self, objectToChange, actionToExecute):
        self.objectToChange = objectToChange
        self.actionToExecute = actionToExecute

    def analyzeValues(self, dependentValues, attributeFormula):
        '''
        :param dependentValues: Values used to compute result
        :param attributeFormula: Supports '.' for attribute concatenation.
                                 Supports '&' for setting more than 1 attribute
                                 Example: 'obj1.att1&obj2.obj3.att3'
        :return: values calculated from dependent values by executing actionToExecute
        '''

        def mapFunc( aValue ):
            self._setValue( attributeFormula, aValue)
            return self.actionToExecute()

        return list(map(mapFunc, dependentValues))

    def _setValue(self, attributeFormula, aValue):
        def _setValueFunc(attributeFormula, aValue):
            attributes = attributeFormula.split('.')
            theObjectToChange = self.objectToChange
            i = 0
            while(i<len(attributes)-1):
                self._raiseExceptionIfHasNoAttr(theObjectToChange, attributes[i])
                theObjectToChange = getattr(theObjectToChange,attributes[i])
                i+=1

            self._raiseExceptionIfHasNoAttr(theObjectToChange, attributes[i])
            setattr(theObjectToChange, attributes[i], aValue)

        for attributeToSet in attributeFormula.split('&'):
            _setValueFunc( attributeToSet, aValue)

    def _raiseExceptionIfHasNoAttr(self, obj, attributeName):
        if not hasattr(obj, attributeName):
            raise Exception('{} has no attr {}'.format(obj, attributeName))



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

    def analyzeBondConversionValue(self, attributeToAnalyze, dependentValues):
        helper = SensitivityAnalyser(self.convertibleBondModel.modelInput, self.convertibleBondModel.conversionValue)
        return helper.analyzeValues(dependentValues, attributeToAnalyze)

class Plotter:
    def __init__(self, title='Convertible Bond'):
        self._lastFigure = None
        self._lastPlot = None
        self.title = title
        self.newGraph = 1
        self._availableColors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
        self._currentColor = 0

    def plot(self, dataToPlot, newGraph=True):
        '''dataToPlot is a list of dictionaries'''
        figure,thePlot = self._initializePlot( newGraph )
        for aData in dataToPlot:
            xValues = aData['x']
            yValues = aData['y']
            color   = '-{}'.format( self._nextColor() )
            label   = aData.get('label','')
            thePlot.plot( xValues, yValues, color, label=label)
            thePlot.legend(loc='upper left')

        figure.show()
        plt.pause(0.05)

    def _nextColor(self):
        color = self._availableColors[self._currentColor % len(self._availableColors)]
        self._currentColor += 1

        return color

    def _initializePlot(self, newGraph):
        if newGraph or not self._lastFigure:
            self._currentColor = 0
            self._lastFigure = plt.figure('{} New Graph {}'.format(self.title, self.newGraph))
            self._lastPlot = self._lastFigure.add_subplot(111)
            self.newGraph += 1
        return self._lastFigure, self._lastPlot





