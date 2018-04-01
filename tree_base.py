class Node:

    def __init__(self ):
        self.solved = False

    def solve(self, **kwargs):
        if not self.isSolved():
            self._solveImplementation(**kwargs)
        self.solved = True

    def _solveImplementation(self, **kwargs):
        pass

    def hasChilds(self):
        pass

    def value(self):
        pass

    def isSolved(self):
        return self.solved

class TerminateNode(Node):
    def __init__(self, terminateValue=1):
        super().__init__()
        self.terminateValue = terminateValue

    def hasChilds(self):
        return False

    def value(self):
        return self.terminateValue


class AbsractNodeRole:

    def __init__(self, node):
        self.node = node

    def value(self):
        pass

class TerminateNodeRole(AbsractNodeRole):
    def __init__(self, val):
        self.val = val

    def value(self):
        return self.val

class IntermediateNodeRole(AbsractNodeRole):
    def __init__(self, node):
        super().__init__(node)

    def value(self):
        return self.node._valueImplementation()
