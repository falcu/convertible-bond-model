class SensibilityAnalyser:
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


