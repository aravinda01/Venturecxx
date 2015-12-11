# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import copy

import pystan

from venture.lite.psp import DeterministicPSP
from venture.lite.psp import RandomPSP
from venture.lite.psp import TypedPSP
from venture.lite.request import Request
from venture.lite.sp import SP
from venture.lite.sp import SPAux
from venture.lite.sp import SPType
from venture.lite.sp import VentureSPRecord

import venture.lite.types as t
import venture.lite.value as vv

# - Inputs are a list of pairs: name and type.
# - Output are a list of triples: name, type, and constrainable name which may be Nil.
# - An output that is not constrainable corresponds to a generated quantity
#   in Stan.
# - An output that is constrainable corresponds to a generated quantity
#   and an input datum, the latter named by the "constrainable name".
# - It is up to the user to make sure that the use as a constraint is
#   compatible with the generating process they define.
# - This all produces an SP with the given inputs and outputs, which
#   is likelihood-free on unconstrainable outputs, and has the Stan
#   parameters as (uncollapsed) latent state.

# Operating invariants:
# - Simulation has the inputs and simulates the parameters and the outputs
# - Log density has the inputs, outputs, and parameters, and evaluates
#   the posterior (?) (likelihood only?)
# - There is an LKernel that has the inputs, outputs, and parameters, and
#   updates the parameters by taking a step
#   - Can I have an interface for taking multiple steps in batch?
#   - Can I have an interface for running to convergence?
#   - What do I do with the unconstrainable outputs?  They need to be
#     resampled, without resampling the constrainable ones.
# - Ergo, simulate needs to be able to synthesize bogus values for the
#   constrainable outputs

# Plan:
# - A model is represented as a made SP from inputs to outputs
# - made simulation makes an LSR (which need not carry any information)
# - simulating this lsr consists of sampling the parameters
#   conditioned on bogus data
# - given the result, (communicated via the aux, presumably),
#   simulating the output is straightforward (but needs bogus data)
# - fiddling with the parameters now looks like a AEKernel, which
#   means I really need to be able to control when that gets run,
#   b/c it stands to be expensive
# - Nuts: The AEKernel is global to all applications, but I want
#   them to be independent :(

# Thought: Is it reasonable to use primitive multivalue returns to
# separate constrainable from unconstrainable outputs?

# Problem: There is no way to incorporate downstream uses of the
# generated quantities and/or parameters into the behavior of the Stan
# simulator.

# Oddly, simulateLatents doesn't get the Args struct.  Perhaps the
# intention is that the requester can pass all pertinent information
# along.

# Note: The mapping from inputs to parameters is not independently
# assessable in Stan; only the aggregate including the data is.

# The request PSP can't both extract values into the lsr and assess at
# the same time.  Could do nodes, or could do an ESR for a custom SP.
# - Problem: The SP can't properly extract values from the nodes when
#   simulating the latent, because it doesn't have a pointer to the
#   trace (which is necessary to respect the particles hack).

# Possible solution: give simulateLatents the Args corresponding to
# the application in question.
# - May have the side effect of simplifying other uses of
#   simulateLatents, but maybe not.
# - HMM seems to be the only other SP that uses latent simulation
#   requests?

# Alternate plan:
# - A made model is represented as a made SP from inputs to outputs,
#   that uses an ESR to cause the parameters to be simulated (by
#   another SP customized for the purpose)
# - Problem: The param SP can't properly absorb because it doesn't see
#   the data.  Could hack it by having it absorb with likelihood 1
#   every time, and leave the second SP responsible for absorbing
#   changes to the input at both the parameters and the data.
# - Problem: The param SP can't properly resimulate, even with a
#   kernel, because it doesn't see the data.

def interpret_type_spec(_tp):
  return t.NumberType() # TODO: Actually interpret types

def io_spec_to_type_spec(inputs, outputs):
  assert len(outputs) == 1
  (_, tp, _) = outputs[0]
  return ([interpret_type_spec(tp) for _,tp in inputs],
          interpret_type_spec(tp))

def io_spec_to_api_spec(inputs, outputs):
  assert len(outputs) == 1
  (name, _, observable_name) = outputs[0]
  output_names = [name]
  input_names = [name for name,_ in inputs]
  if observable_name is not None:
    input_names.append(observable_name)
  return (input_names, output_names)

def bogus_valid_value(_tp):
  return vv.VentureNumber(0) # TODO: Actually synthesize type-correct bogosity

class MakerVenStanOutputPSP(DeterministicPSP):
  def simulate(self, args):
    (stan_prog, inputs, outputs) = args.operandValues()
    built_result = pystan.stanc(model_code=stan_prog)
    sp = VenStanSP(built_result, inputs, outputs)
    return VentureSPRecord(sp)

class VenStanSP(SP):
  def __init__(self, built_result, inputs, outputs):
    (args_types, output_type) = io_spec_to_type_spec(inputs, outputs)
    req = TypedPSP(VenStanRequestPSP(), SPType(args_types, t.RequestType()))
    output = TypedPSP(VenStanOutputPSP(built_result, inputs, outputs),
                      SPType(args_types, output_type))
    super(VenStanSP, self).__init__(req, output)

  def constructSPAux(self): return VenStanSPAux()

  def constructLatentDB(self):
    # { app_id => parameters }
    return {}

  def simulateLatents(self, aux, lsr, shouldRestore, latentDB):
    if lsr not in aux.parameters:
      if shouldRestore:
        aux[lsr] = latentDB[lsr]
      else:
        aux[lsr] = self.synthesize_parameters_with_bogus_data()
    return 0

  def detachLatents(self, aux, lsr, latentDB):
    latentDB[lsr] = aux[lsr]
    del aux[lsr]
    return 0

  def hasAEKernel(self): return True

  def AEInfer(self, aux):
    pass

# The Aux is shared across all applications, so I use a dictionary
# with unique keys to implement independence.
class VenStanSPAux(SPAux):
  def __init__(self):
    super(VenStanSPAux,self).__init__()
    self.parameters_map = {}

  def copy(self):
    ans = VenStanSPAux()
    ans.parameters_map = copy.copy(self.parameters_map)
    return ans

class VenStanRequestPSP(DeterministicPSP):
  def simulate(self, args):
    # The args node uniquely identifies the application
    return Request([], [args.node])
  def gradientOfSimulate(self, args, _value, _direction):
    return [0 for _ in args.operandNodes]
  def canAbsorb(self, _trace, _appNode, _parentNode):
    return True

class VenStanOutputPSP(RandomPSP):
  def __init__(self, stan_model, inputs, outputs):
    self.stan_model = stan_model
    (self.input_names, self.output_names) = io_spec_to_api_spec(inputs, outputs)

  def simulate(self, args):
    pass
