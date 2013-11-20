/*
* Copyright (c) 2013, MIT Probabilistic Computing Project.
* 
* This file is part of Venture.
* 
* Venture is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
* 
* Venture is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
* 
* You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
*/
#include "sps/map.h"
#include "value.h"
#include "node.h"
#include "utils.h"
#include "env.h"

#include <iostream>

VentureValue * MakeMapSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  VentureList * keys = dynamic_cast<VentureList*>(node->operandNodes[0]->getValue());
  VentureList * values = dynamic_cast<VentureList*>(node->operandNodes[1]->getValue());
  assert(keys);
  assert(values);

  VentureMap * vmap = new VentureMap;

  while (!dynamic_cast<VentureNil*>(keys))
  {
    VenturePair * pkeys = dynamic_cast<VenturePair*>(keys);
    VenturePair * pvalues = dynamic_cast<VenturePair*>(values);
    assert(pkeys);
    assert(pvalues);
    vmap->map.insert({pkeys->first,pvalues->first});
    keys = pkeys->rest;
    values = pvalues->rest;
  }
  return vmap;
}

VentureValue * MapContainsSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  VentureMap * vmap = dynamic_cast<VentureMap*>(node->operandNodes[0]->getValue());
  assert(vmap);

  return new VentureBool(vmap->map.count(node->operandNodes[1]->getValue()));
}


VentureValue * MapLookupSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  VentureMap * vmap = dynamic_cast<VentureMap*>(node->operandNodes[0]->getValue());
  assert(vmap);

  assert(vmap->map.count(node->operandNodes[1]->getValue()));
  return vmap->map[node->operandNodes[1]->getValue()];
}


