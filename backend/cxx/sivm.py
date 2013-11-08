from libtrace import Trace
from venture.exception import VentureException

# Thin wrapper around cxx Trace
# TODO: merge with CoreSivmCxx?

class SIVM:

    def __init__(self):
        self.directiveCounter = 0
        self.directives = {}
        self.trace = Trace()

    def nextBaseAddr(self):
        self.directiveCounter += 1
        return self.directiveCounter

    def assume(self,id,datum):
        baseAddr = self.nextBaseAddr()

        self.trace.eval(baseAddr,datum);
        self.trace.bindInGlobalEnv(id,baseAddr)

        self.directives[self.directiveCounter] = ["assume",id,datum]

        return (self.directiveCounter,self.trace.extractValue(baseAddr))
        
    def predict(self,datum):
        baseAddr = self.nextBaseAddr()
        self.trace.eval(baseAddr,datum)

        self.directives[self.directiveCounter] = ["predict",datum]

        return (self.directiveCounter,self.trace.extractValue(baseAddr))

    def observe(self,datum,val):
        baseAddr = self.nextBaseAddr()
        self.trace.eval(baseAddr,datum)
        logDensity = self.trace.observe(baseAddr,val)

        # TODO check for -infinity? Throw an exception?
        if logDensity == float("-inf"):
            raise VentureException("invalid_constraint", "Observe failed to constrain", expression=datum, value=val)
        self.directives[self.directiveCounter] = ["observe",datum,val]

        return self.directiveCounter

    def forget(self,directiveId):
        if directiveId not in self.directives:
            raise VentureException("invalid_argument", "Cannot forget a non-existent directive id", argument="directive_id", directive_id=directiveId)
        directive = self.directives[directiveId]
        if directive[0] == "assume":
            raise VentureException("invalid_argument", "Cannot forget an ASSUME directive", argument="directive_id", directive_id=directiveId)
        if directive[0] == "observe": self.trace.unobserve(directiveId)
        self.trace.uneval(directiveId)
        del self.directives[directiveId]
    
    def report_value(self,directiveId):
        if directiveId not in self.directives:
            raise VentureException("invalid_argument", "Cannot report a non-existent directive id", argument=directiveId)
        return self.trace.extractValue(directiveId)

    def clear(self):
        del self.trace
        self.directiveCounter = 0
        self.directives = {}
        self.trace = Trace()

    # This could be parameterized to call different inference programs.
    def infer(self,params=None):
        if params is None:
            params = {}

        if 'transitions' not in params:
            params['transitions'] = 1
        else:
            # FIXME: Kludge. If removed, test_infer (in python/test/ripl_test.py) fails, and if params are printed, you'll see a float for the number of transitions
            params['transitions'] = int(params['transitions'])

        if 'kernel' not in params:
            params['kernel'] = 'mh'
        if 'use_global_scaffold' not in params:
            params['use_global_scaffold'] = False

        if len(params.keys()) > 3:
            raise Exception("Invalid parameter dictionary passed to infer: " + str(params))

        #print "params: " + str(params)

        self.trace.infer(params)

    def logscore(self): return self.trace.getGlobalLogScore()

    def get_entropy_info(self):
      return { 'unconstrained_random_choices' : self.trace.numRandomChoices() }


    def get_seed(self):
        return self.trace.get_seed()

    def set_seed(self, seed):
        self.trace.set_seed(seed)
    
    # TODO: Add methods to inspect/manipulate the trace for debugging and profiling
    
