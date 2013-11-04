#ifndef EVAL_H
#define EVAL_H

#include "sp.h"

struct EvalSP : SP
{
  EvalSP()
    { 
      isESRReference = true;
      makesESRs = true;
      canAbsorbRequest = false;

    }

  VentureValue * simulateRequest(Node * node, gsl_rng * rng) const override;

};




#endif
