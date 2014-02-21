#ifndef PERSISTENT_SET_H
#define PERSISTENT_SET_H

#include "wttree.h"

namespace persistent
{
/*
Persistent set backed by a weight-balanced tree.
At present, happens to be implemented just like a PMap, but with the
values always being True. In principle could be impemented more
efficiently by specializing the nodes not to store values at all.
*/
template <typename Key>
class PSet
{
  typedef typename Node<Key, bool>::NodePtr NodePtr;
  
  NodePtr root;
  
  PSet(NodePtr root) : root(root) {} 

public:
  PSet() : root(new Node<Key, bool>()) {}
  
  bool contains(const Key& key)
    { return Node<Key, bool>::node_contains(root, key); }
  
  PSet insert(const Key& key)
    { return PSet(Node<Key, bool>::node_insert(root, key, true)); }
  
  /*
  adjust :: (PSet k v) -> k -> (v -> v) -> PSet k v

  Returns a new PSet obtained from this one by applying the given
  function to the bool at the given key. Returns the original PSet
  unchanged if the key is not present. The name is chosen by
  analogy to Data.PSet.adjust from the Haskell standard library.
  */
  template <class Function>
  PSet adjust(const Key& key, const Function& f)
    { return PSet(Node<Key, bool>::node_adjust(root, key, f)); }
  
  PSet remove(const Key& key)
    { return PSet(Node<Key, bool>::node_remove(root, key)); }

  size_t size() { return root->size; }
  
  vector<Key> keys()
    { return Node<Key, bool>::node_traverse_keys_in_order(root); }
};
};
/*
TODO test balance, either as asymptotics with the timings framework
or through an explicit check that a tree built by some mechanism is
balanced->  Issue https://app->asana->com/0/9277419963067/9924589720809
*/

#endif
