{-# LANGUAGE ScopedTypeVariables #-}

module Distributions where

import Control.Monad.Random

---- Bernoulli trials

weighted_flip :: (MonadRandom m, Real num) => num -> m Bool
weighted_flip weight = do
  (toss :: Double) <- getRandomR (0.0,1.0)
  return $ toss < realToFrac weight

log_d_weight :: (Floating num) => num -> Bool -> num
log_d_weight weight True = log weight
log_d_weight weight False = log (1 - weight)

---- Normal

box_muller_cos :: Double -> Double -> Double
box_muller_cos u1 u2 = r * cos theta where
    r = sqrt (-2 * log u1)
    theta = 2 * pi * u2

normal_flip :: (MonadRandom m, Fractional num) => num -> num -> m num
normal_flip mu sigma = do
  u1 <- getRandomR (0.0, 1.0)
  u2 <- getRandomR (0.0, 1.0)
  let normal = box_muller_cos u1 u2
  return $ sigma * realToFrac normal + mu

log_d_normal :: (Floating num) => num -> num -> num -> num
log_d_normal mean sigma x = - (x - mean)^^(2::Int) / (2 * sigma^^(2::Int)) - scale where
    scale = log sigma + (log pi)/2

