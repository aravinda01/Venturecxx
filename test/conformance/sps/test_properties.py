from nose import SkipTest
from nose.tools import eq_
from testconfig import config
import math

from venture.test.config import get_ripl
from venture.lite.builtin import builtInSPsList
from venture.test.randomized import * # Importing many things, which are closely related to what this is trying to do pylint: disable=wildcard-import, unused-wildcard-import
from venture.lite.psp import NullRequestPSP
from venture.lite.sp import VentureSP
from venture.lite.value import AnyType

def testEquality():
  checkTypedProperty(propEquality, AnyType())

def propEquality(value):
  assert value.equal(value)

def relevantSPs():
  for (name,sp) in builtInSPsList:
    if isinstance(sp.requestPSP, NullRequestPSP):
      if name not in []: # Placeholder for selecting SPs to do or not do
        yield name, sp

def testTypes():
  for (name,sp) in relevantSPs():
    yield checkTypeCorrect, name, sp

def checkTypeCorrect(_name, sp):
  type_ = sp.venture_type()
  checkTypedProperty(propTypeCorrect, fully_uncurried_sp_type(type_), sp, type_)

def propTypeCorrect(args_lists, sp, type_):
  """Check that the successive return values of the given SP (when
applied fully uncurried) match the expected types."""
  if len(args_lists) == 0:
    pass # OK
  else:
    args = BogusArgs(args_lists[0], sp.constructSPAux())
    answer = carefully(sp.outputPSP.simulate, args)
    assert answer in type_.return_type
    propTypeCorrect(args_lists[1:], answer, type_.return_type)

def testDeterministic():
  for (name,sp) in relevantSPs():
    if not sp.outputPSP.isRandom():
      yield checkDeterministic, name, sp

def checkDeterministic(name, sp):
  checkTypedProperty(propDeterministic, fully_uncurried_sp_type(sp.venture_type()), name, sp)

def propDeterministic(args_lists, name, sp):
  """Check that the given SP returns the same answer every time (applied
fully uncurried)."""
  args = BogusArgs(args_lists[0], sp.constructSPAux())
  answer = carefully(sp.outputPSP.simulate, args)
  if isinstance(answer, VentureSP):
    if isinstance(answer.requestPSP, NullRequestPSP):
      if not answer.outputPSP.isRandom():
        args2 = BogusArgs(args_lists[1], answer.constructSPAux())
        ans2 = carefully(answer.outputPSP.simulate, args2)
        for _ in range(5):
          new_ans = carefully(sp.outputPSP.simulate, args)
          new_ans2 = carefully(new_ans.outputPSP.simulate, args2)
          eq_(ans2, new_ans2)
      else:
        raise SkipTest("Putatively deterministic sp %s returned a random SP" % name)
    else:
      raise SkipTest("Putatively deterministic sp %s returned a requesting SP" % name)
  else:
    for _ in range(5):
      eq_(answer, carefully(sp.outputPSP.simulate, args))

def testRandom():
  for (name,sp) in relevantSPs():
    if sp.outputPSP.isRandom():
      if not name in ["make_uc_dir_mult", "categorical", "make_uc_sym_dir_mult"]:
        yield checkRandom, name, sp

def checkRandom(_name, sp):
  # I take the name because I want it to appear in the nose arg list
  args_type = fully_uncurried_sp_type(sp.venture_type())
  checkTypedProperty(propRandom, [args_type for _ in range(5)] , sp)

def evaluate_fully_uncurried(sp, args_lists):
  args = BogusArgs(args_lists[0], sp.constructSPAux())
  answer = carefully(sp.outputPSP.simulate, args)
  if len(args_lists) == 1:
    return answer
  else:
    return evaluate_fully_uncurried(answer, args_lists[1:])

def propRandom(args_listss, sp):
  """Check that the given SP is random on at least one set of arguments."""
  answers = []
  for args_lists in args_listss:
    try:
      answer = evaluate_fully_uncurried(sp, args_lists)
      answers.append(answer)
      for _ in range(10):
        ans2 = evaluate_fully_uncurried(sp, args_lists)
        if not ans2 == answer:
          return True
    except ArgumentsNotAppropriate:
      # This complication serves the purpose of not decreasing the
      # acceptance rate of the search of appropriate arguments to the
      # SP, while allowing the SP to redeem its claims of randomness
      # on additional arguments if they are available.
      if answers == []:
        raise
      else:
        answers.append("Inappropriate arguments")
        continue
  assert False, "SP deterministically returned %s (parallel to arguments)" % answers

def testExpressionFor():
  if config["get_ripl"] != "lite": raise SkipTest("Round-trip to the ripl only works in Lite")
  checkTypedProperty(propExpressionWorks, AnyType())

def propExpressionWorks(value):
  expr = value.expressionFor()
  result = carefully(eval_in_ripl, expr)
  assert value.equal(result)

def eval_in_ripl(expr):
  ripl = get_ripl()
  # hack so that report_raw grabs the first directive after the prefix
  len_prefix = len(ripl.sivm.core_sivm.engine.getDistinguishedTrace().families)
  ripl.predict(expr)
  return ripl.sivm.core_sivm.engine.report_raw(len_prefix + 1)

def testRiplSimulate():
  if config["get_ripl"] != "lite": raise SkipTest("Round-trip to the ripl only works in Lite")
  for (name,sp) in relevantSPs():
    if name not in ["scope_include", # Because scope_include is
                                     # misannotated as to the true
                                     # permissible types of scopes and
                                     # blocks
                    "get_current_environment", # Because BogusArgs gives a bogus environment
                    "extend_environment", # Because BogusArgs gives a bogus environment
                  ]:
      if not sp.outputPSP.isRandom():
        yield checkRiplAgreesWithDeterministicSimulate, name, sp

def checkRiplAgreesWithDeterministicSimulate(name, sp):
  checkTypedProperty(propRiplAgreesWithDeterministicSimulate, fully_uncurried_sp_type(sp.venture_type()), name, sp)

def propRiplAgreesWithDeterministicSimulate(args_lists, name, sp):
  """Check that the given SP produces the same answer directly and
through a ripl (applied fully uncurried)."""
  args = BogusArgs(args_lists[0], sp.constructSPAux())
  answer = carefully(sp.outputPSP.simulate, args)
  if isinstance(answer, VentureSP):
    if isinstance(answer.requestPSP, NullRequestPSP):
      if not answer.outputPSP.isRandom():
        args2 = BogusArgs(args_lists[1], answer.constructSPAux())
        ans2 = carefully(answer.outputPSP.simulate, args2)
        inner = [{"type":"symbol", "value":name}] + [v.expressionFor() for v in args_lists[0]]
        expr = [inner] + [v.expressionFor() for v in args_lists[1]]
        assert ans2.equal(carefully(eval_in_ripl, expr))
      else:
        raise SkipTest("Putatively deterministic sp %s returned a random SP" % name)
    else:
      raise SkipTest("Putatively deterministic sp %s returned a requesting SP" % name)
  else:
    expr = [{"type":"symbol", "value":name}] + [v.expressionFor() for v in args_lists[0]]
    assert answer.equal(carefully(eval_in_ripl, expr))

def testLogDensityDeterministic():
  for (name,sp) in relevantSPs():
    if name not in ["dict", "multivariate_normal", "wishart", "inv_wishart", "categorical"]: # TODO
      yield checkLogDensityDeterministic, name, sp

def checkLogDensityDeterministic(_name, sp):
  checkTypedProperty(propLogDensityDeterministic, (fully_uncurried_sp_type(sp.venture_type()), final_return_type(sp.venture_type())), sp)

def propLogDensityDeterministic(rnd, sp):
  (args_lists, value) = rnd
  if not len(args_lists) == 1:
    raise SkipTest("TODO: Write the code for measuring log density of curried SPs")
  answer = carefully(sp.outputPSP.logDensity, value, BogusArgs(args_lists[0], sp.constructSPAux()))
  if math.isnan(answer):
    raise ArgumentsNotAppropriate("Log density turned out to be NaN")
  for _ in range(5):
    eq_(answer, carefully(sp.outputPSP.logDensity, value, BogusArgs(args_lists[0], sp.constructSPAux())))
