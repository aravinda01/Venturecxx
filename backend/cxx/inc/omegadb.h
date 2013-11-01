#ifndef OMEGA_DB_H
#define OMEGA_DB_H

#include <map>
#include <unordered_map>
#include <vector>
#include <queue>

using namespace std;

struct SP;
struct VentureValue;
enum class NodeType;
struct Node;
struct LatentDB;

struct FlushEntry
{
  FlushEntry(SP * owner, VentureValue * value, NodeType nodeType):
    owner(owner), value(value), nodeType(nodeType) { }
  SP * owner;
  VentureValue * value;
  NodeType nodeType;
};


struct LatentDB 
{
  virtual ~LatentDB() {};
};


/*
(1-2)<latents>
------(3) self-evaluating/lambdas to flush [don't need]
(4) drgDB { Node * => VentureValue * }  [all get flushed]
(5) csrTopDB { (Node * (of SP-value), string name) => Node * } [some are constrained]

spFlushQueue (SP *, Value *) some SP's are NULL, values from DRG and Brush
THEN destroy nodes recursively from csrTopDB

-------
(launch a thread for destroying the nodes, but maybe not the (sp->flush) commands)
-------
outdated:
(6) spFlushQueue --{ (Node *, SP *, Value*,DRG?) 

Node * from brush, (SP *, Value *) from DRG }
(all (unowned) nodes in order, SP * is nullptr for Venture-created values)
*/

struct OmegaDB
{
  /* Node * is always the makerNode for the SP, which coincides with the AAA node. */
  unordered_map<Node *,LatentDB *> latentDBs;

  unordered_map<Node *, VentureValue *> drgDB;  

  /* (Node *, size_t): Node * represents the SP's maker node, size_t the family name. */
  map<pair<Node *,size_t>, Node *> spFamilyDBs;

  /* This will contain all values that need to be flushed (not owned by nodes visited during detach),
     in the detach order. Some of these SP's will be null, indicating that Venture created the value
     and should just delete it. */
  queue<FlushEntry> flushQueue;
};


#endif
