import sys
sys.path.append("../..")

from venture.cxx.libsp import SP

class SquareSP(SP):

  def __init__(self):
        super(SquareSP, self).__init__()

  def simulate(self,args):
    value = args[0] * args[0]
    return {'type': 'number', 'value': value}

def makeSP():
  return SquareSP()

def getSymbol(): return "square"
