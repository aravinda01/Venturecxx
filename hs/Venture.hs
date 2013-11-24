
module Venture where

import Data.Maybe
import Control.Monad.Reader
import Control.Monad.Trans.State.Lazy
import Control.Monad.Trans.Writer.Strict
import Control.Monad.Trans.Class
import Control.Monad.Random hiding (randoms) -- From cabal install MonadRandom

import Language hiding (Exp, Value)
import Trace
import Regen
import Detach hiding (empty)
import SP

type Kernel m a = a -> WriterT LogDensity m a

mix_mh_kernels :: (Monad m) => (a -> m ind) -> (a -> ind -> LogDensity) ->
                  (ind -> Kernel m a) -> (Kernel m a)
mix_mh_kernels sampleIndex measureIndex paramK x = do
  ind <- lift $ sampleIndex x
  let ldRho = measureIndex x ind
  tell ldRho
  x' <- paramK ind x
  let ldXi = measureIndex x' ind
  tell $ log_density_negate ldXi
  return x'

metropolis_hastings :: (MonadRandom m) => Kernel m a -> a -> m a
metropolis_hastings propose x = do
  (x', (LogDensity alpha)) <- runWriterT $ propose x
  u <- getRandomR (0.0,1.0)
  if (log u < alpha) then
      return x'
  else
      return x



scaffold_mh_kernel :: (MonadRandom m) => Scaffold -> Kernel m (Trace m)
scaffold_mh_kernel scaffold trace = do
  torus <- censor log_density_negate $ stupid $ detach scaffold trace
  regen scaffold torus
        where stupid :: (Monad m) => Writer w a -> WriterT w m a
              stupid = WriterT . return . runWriter

principal_node_mh :: (MonadRandom m) => Kernel m (Trace m)
principal_node_mh = mix_mh_kernels sample log_density scaffold_mh_kernel where
    sample :: (MonadRandom m) => Trace m -> m Scaffold
    sample trace@Trace{ randoms = choices } = do
      index <- getRandomR (0, length choices - 1)
      return $ runReader (scaffold_from_principal_node (choices !! index)) trace

    log_density :: Trace m -> a -> LogDensity
    log_density Trace{ randoms = choices } _ = LogDensity $ -log(fromIntegral $ length choices)
    
simulate_soup :: (MonadRandom m) => Exp -> m Value
simulate_soup exp = evalStateT act empty
    where act = do
            env <- initializeBuiltins Toplevel
            address <- eval exp env
            gets $ fromJust . valueOf . fromJust . (lookupNode address)

-- simulate_soup $ Datum $ Number 1.0
-- simulate_soup $ App (Lam ["x"] (Variable "x")) [(Datum $ Number 1.0)]
-- (let (id ...) (id 1))
-- simulate_soup $ App (Lam ["id"] (App (Variable "id") [(Datum $ Number 1.0)])) [(Lam ["x"] (Variable "x"))]
-- K combinator
-- simulate_soup $ App (App (Lam ["x"] (Lam ["y"] (Variable "x"))) [(Datum $ Number 1.0)]) [(Datum $ Number 2.0)]
-- simulate_soup $ App (Variable "bernoulli") []
-- simulate_soup $ App (Variable "normal") [(Datum $ Number 0.0), (Datum $ Number 2.0)]

-- Next subgoal: Do MH inference (without observations) and see bernoulli change value

-- Next subgoal: Do MH inference (without observations) on an example that has a brush
-- - requires implementing IF

-- Next subgoal: Do MH inference with observations on some trivial
--   programs (e.g. normal with normally distributed mean?)
-- - replace fromJusts with things that signal error messages (forceLookup)

-- Eventual goals
-- - Built-in SPs with collapsed exchangeably coupled state
--   - This imposes the ordering requirement on regen and detach
--   - This is where incorporate and unincorporate (remove) come from

-- Non-goals
-- - Latent simulation kernels for SPs
--   - This seems to be the only source of nonzero weights in {regen,detach}Internal
--     (also eval and uneval (detachFamily?))
-- - Absorbing At Applications (I don't even understand the machinery this requires)
