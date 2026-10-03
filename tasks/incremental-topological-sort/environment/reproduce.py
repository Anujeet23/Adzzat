"""Demonstrates the longer-cycle blind spot and the stale-order bug."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo"))
from toposort import DAG  # noqa: E402


def main():
    dag = DAG()
    dag.add_edge("a", "b")
    dag.add_edge("b", "c")
    closed = dag.add_edge("c", "a")  # closes a 3-cycle: a -> b -> c -> a
    if closed:
        print("BUG REPRODUCED: add_edge('c', 'a') returned True, closing a "
              "3-node cycle a->b->c->a -- only a direct reverse edge is checked.")
    else:
        print("longer cycle correctly rejected")

    print()
    dag2 = DAG()
    dag2.add_node("z")  # inserted first
    dag2.add_node("a")  # inserted second
    dag2.add_edge("a", "z")  # but a must now come before z
    order = dag2.order()
    if order.index("a") > order.index("z"):
        print("BUG REPRODUCED: order()=%r has 'z' before 'a', even though "
              "the edge a->z requires 'a' first -- order() just returns "
              "stale insertion order." % order)
    else:
        print("order() correctly reflects the edge:", order)


if __name__ == "__main__":
    main()
