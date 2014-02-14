#include "sps/discrete.h"
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_sf.h>

#include "utils.h"

VentureValuePtr BernoulliOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{
  double p = 0.5;
  if (!args->operandValues.empty()) { p = args->operandValues[0]->getDouble(); }
  int n = gsl_ran_bernoulli(rng,p);
  assert(n == 0 || n == 1);
  return shared_ptr<VentureBool>(new VentureBool(n));
}

double BernoulliOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  double p = 0.5;
  if (!args->operandValues.empty()) { p = args->operandValues[0]->getDouble(); }

  if (value->getBool()) { return log(p); }
  else { return log(1 - p); }
}


VentureValuePtr CategoricalOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const 
{
  assert(args->operandValues.size() == 1 || args->operandValues.size() == 2);
  if (args->operandValues.size() == 1) { return simulateCategorical(args->operandValues[0]->getSimplex(),rng); }
  else { return simulateCategorical(args->operandValues[0]->getSimplex(),args->operandValues[1]->getArray(),rng); }
}
double CategoricalOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const 
{ 
  assert(args->operandValues.size() == 1 || args->operandValues.size() == 2);
  if (args->operandValues.size() == 1) { return logDensityCategorical(value,args->operandValues[0]->getSimplex()); }
  else { return logDensityCategorical(value,args->operandValues[0]->getSimplex(),args->operandValues[1]->getArray()); }
}
