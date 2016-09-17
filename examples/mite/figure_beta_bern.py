import pickle
import sys
import time
from collections import OrderedDict

import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn

import venture.shortcuts as vs

vnts_file = __file__.rsplit('.', 1)[0] + '.vnts'

def compute_results(num_reps, stub=False):
  if stub:
    dataset = [1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1]
    alpha = 0.5
    def stub_collapsed():
      counts = [0, 0]
      weight = 0
      for x in dataset:
        weight += np.log(alpha + counts[x]) - np.log(alpha + alpha + sum(counts))
        counts[x] += 1
      return {'time': np.random.normal(2, 0.2),
              'measurement': weight}
    def stub_uncollapsed():
      counts = [0, 0]
      weight = 0
      for x in dataset:
        theta = np.random.dirichlet(alpha + np.array(counts))
        weight += np.log(theta[x])
        counts[x] += 1
      return {'time': np.random.normal(2, 0.2),
              'measurement': weight}
    def stub_proc(steps):
      counts = [0, 0]
      weight = 0
      theta = None
      for x in dataset:
        thetas = np.random.beta(alpha, alpha, size=1+steps)
        weights = np.exp(np.dot(counts, np.log([thetas, 1-thetas])))
        theta = np.random.choice(thetas, p=weights/weights.sum())
        weight += np.log([theta, 1-theta][x])
        counts[x] += 1
      return {'time': np.random.normal(1 + steps, 0.1),
              'measurement': weight}

    ret = OrderedDict()
    infer_programs = {
      'collapsed': [(stub_collapsed, 'pass')],
      'uncollapsed': [(stub_uncollapsed, 'conjugate_gibbs_infer()')],
      'proc': [((lambda steps=steps: stub_proc(steps)),
                'repeat({}, resimulation_infer())'.format(steps))
               for steps in [0, 1, 2, 4, 8]]
    }
    for variant in ['proc', 'collapsed', 'uncollapsed']:
      for package in infer_programs[variant]:
        (f, infer) = package
        ret[variant, infer] = [f() for _ in range(num_reps)]
    return ret
  else:
    ripl = vs.Mite().make_ripl()
    ripl.execute_program_from_file(vnts_file)
    def time_and_result(beta_bern, infer):
      string = '''\
example_beta_bern(make_beta_bern_{}, () -> {})
'''.format(beta_bern, infer)
      then = time.time()
      result = ripl.evaluate(string)
      now = time.time()
      return {'time': now - then, 'measurement': result}
    ret = OrderedDict()
    infer_programs = {
      'collapsed': ['pass'],
      'coll_foreign': ['pass'],
      'uncollapsed': ['conjugate_gibbs_infer()'],
      'uncoll_foreign': ['conjugate_gibbs_infer()'],
      'proc': ['repeat({}, resimulation_infer())'.format(steps)
               for steps in [0, 1, 2, 4, 8]]
    }
    for variant in ['proc', 'collapsed', 'coll_foreign', 'uncollapsed', 'uncoll_foreign']:
      for infer in infer_programs[variant]:
        ret[variant, infer] = [
          time_and_result(variant, infer)
          for _ in range(num_reps)]
    return ret

def save(stub=False):
  results = compute_results(50, stub=stub)
  with open("beta_bern.sav", "w") as f:
    pickle.dump(results, f)

def timeplot(fname, results):
  fig = plt.figure()
  colors = {
    'collapsed': lambda _: 'blue',
    'coll_foreign': lambda _: 'blue',
    'uncollapsed': lambda _: 'orange',
    'uncoll_foreign': lambda _: 'orange',
    'proc': lambda infer: (float(infer[7])*0.1, 0, 0)
  }
  markers = {
    'collapsed': '.',
    'uncollapsed': '.',
    'coll_foreign': 'x',
    'uncoll_foreign': 'x',
    'proc': '.'
  }
  labels = {
    'collapsed': lambda _: "collapsed, Venture counts",
    'coll_foreign': lambda _: "collapsed, foreign counts",
    'uncollapsed': lambda _: "exact Gibbs, Venture counts",
    'uncoll_foreign': lambda _: "exact Gibbs, foreign counts",
    'proc': lambda infer: "unoptimized, {} steps resim MH".format(infer[7])
  }
  # plot each kind
  for (variant, infer), measurements in results.items():
    times = [m['time'] for m in measurements]
    weights = [m['measurement'] for m in measurements]
    plt.scatter(times, weights,
                color=colors[variant](infer),
                label=labels[variant](infer),
                alpha=0.7, marker=markers[variant])
  plt.legend(loc='lower right')
  plt.xlabel('Runtime')
  plt.ylabel('Observation log weight (higher is better)')
  plt.title('Speed-accuracy comparison of beta-Bernoulli representations')
  fig.savefig("figures/{}.pdf".format(fname))

def plot():
  with open("beta_bern.sav", "r") as f:
    results = pickle.load(f)
  timeplot("beta_bern", results)

if __name__ == '__main__':
  if len(sys.argv) == 1:
    save()
    plot()
  elif sys.argv[1] == "save":
    save()
  elif sys.argv[1] == "plot":
    plot()
  elif sys.argv[1] == "stub":
    save(stub=True)
    plot()