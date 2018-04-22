from collections import deque
from abc import ABC, abstractmethod

class Node(ABC):
    def solve(self, **kwargs):
        if not self.isSolved():
            self._solveImplementation(**kwargs)

    def _solveImplementation(self, **kwargs):
        pass

    @abstractmethod
    def hasChilds(self):
        pass

    @abstractmethod
    def value(self):
        pass

    @abstractmethod
    def isSolved(self):
        pass

class TerminateNode(Node):
    def __init__(self, terminateValue=1):
        super().__init__()
        self.terminateValue = terminateValue

    def hasChilds(self):
        return False

    def value(self):
        return self.terminateValue

    def isSolved(self):
        return True


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

class NodeRoleFactory:

    def __init__(self,node):
        self.node = node

    def buildRole(self):
        if not self.node.hasChilds():
            return TerminateNodeRole(self.node._valueImplementation())
        elif not self.node.parent:
            return IntermediateNodeRole(self.node)
        elif self.node.parent and not self.node.parent.isSolved():
            return TerminateNodeRole( self.node.terminateValue )
        else:
            return IntermediateNodeRole(self.node)


class BaseTree(ABC):
    def __init__(self):
        self.root = None
        self._isSolved = False

    def solve(self):
        if not self.isSolved():
            self.buildTree()
            return self._solveTree( self.targetValues() )

    def isSolved(self):
        return self._isSolved

    def _preBuildTree(self):
        pass

    def _postBuildTree(self):
        pass

    def buildTree(self):
        self._preBuildTree()
        currentNodes = []
        for currentLevel in reversed(range(1,self.treeSize()+1)):
            lastNodes = currentNodes
            currentNodes = self._buildLevelNodes(currentLevel, self.treeSize(), lastNodes)

        self.root = currentNodes[0] #First node of the tree

        self._postBuildTree()

    @abstractmethod
    def _solveTree(self, targetValues ):
        pass

    @abstractmethod
    def targetValues(self):
            pass

class DiscreteModelInput:
    def __init__(self, deltaTime, time):
        self._deltaTime = deltaTime
        self._time = time

    @property
    def deltaTime(self):
        return self._deltaTime

    @deltaTime.setter
    def deltaTime(self, value):
        self._deltaTime = value

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, value):
        self._time = value

    @property
    def periods(self):
        return int(self.time / self.deltaTime )

class BaseBinomialTree(BaseTree):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def treeSize(self):
        pass

    def nodesOfLevel(self, level):
        totalNodes    = int(((level+1)/2.0)*level)
        toIgnoreNodes = totalNodes - level
        stack = deque()
        stack.append( self.root )
        for i in range(toIgnoreNodes):
            currentNode = stack.popleft()
            if not currentNode.low in stack:
                stack.append(currentNode.low)
            if not currentNode.up in stack:
                stack.append(currentNode.up)

        return stack

    def nodesByLevels(self, nodeToStart=None ):
        nodeToStart = nodeToStart or self.root
        stack = deque()
        stack.append(nodeToStart)
        nodesByLevel=[]
        while (len(stack) > 0):
            currentNode = stack.popleft()
            nodesByLevel.append(currentNode)
            if currentNode.hasChilds():
                if not currentNode.low in stack:
                    stack.append(currentNode.low)
                if not currentNode.up in stack:
                    stack.append(currentNode.up)

        return nodesByLevel


