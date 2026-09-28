#!/usr/bin/env python3
"""Executes a scripted sequence of pool operations against the submitted
ResourcePool, injecting caller exceptions and factory failures at exact,
pre-determined points, and checking invariants after every step.
"""
import argparse
import json
import sys


class CallerProbeError(Exception):
    pass


class FactoryError(Exception):
    pass


def make_factory(fail_at_calls):
    state = {"calls": 0, "next_id": 1}

    def factory():
        state["calls"] += 1
        if state["calls"] in fail_at_calls:
            raise FactoryError("factory failure #%d" % state["calls"])
        rid = state["next_id"]
        state["next_id"] += 1
        return {"id": rid}

    return factory


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkgdir", required=True)
    ap.add_argument("--ops", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    result = {"ok": False}
    try:
        sys.path.insert(0, args.pkgdir)
        from pool import ResourcePool, PoolExhausted  # noqa: E402

        with open(args.ops, "r", encoding="utf-8") as f:
            fixture = json.load(f)
        max_size = fixture["max_size"]
        fail_at_calls = set(fixture.get("fail_factory_at_calls", []))

        destroyed_ids = []

        def destroy(resource):
            destroyed_ids.append(resource["id"])

        pool = ResourcePool(factory=make_factory(fail_at_calls), max_size=max_size, destroy=destroy)
        live = {}
        outstanding_resource_ids = set()

        def check_generic(step):
            if pool.outstanding < 0:
                raise AssertionError("negative outstanding at step %d" % step)
            if pool.outstanding + pool.available != max_size:
                raise AssertionError(
                    "outstanding(%d) + available(%d) != max_size(%d) at step %d"
                    % (pool.outstanding, pool.available, max_size, step)
                )

        for step, op in enumerate(fixture["ops"]):
            kind = op["op"]

            if kind == "acquire":
                h = pool.acquire()
                rid = h.resource["id"]
                if rid in outstanding_resource_ids:
                    raise AssertionError(
                        "resource %r handed out to two live handles at once, step %d" % (rid, step)
                    )
                outstanding_resource_ids.add(rid)
                live[op["id"]] = h

            elif kind == "acquire_exhausted":
                try:
                    pool.acquire()
                except PoolExhausted:
                    pass
                else:
                    raise AssertionError("expected PoolExhausted at step %d" % step)

            elif kind == "acquire_factory_fails":
                try:
                    pool.acquire()
                except FactoryError:
                    pass
                else:
                    raise AssertionError("expected FactoryError at step %d" % step)

            elif kind == "release":
                h = live.pop(op["id"])
                outstanding_resource_ids.discard(h.resource["id"])
                pool.release(h)

            elif kind == "mark_broken_release":
                h = live.pop(op["id"])
                outstanding_resource_ids.discard(h.resource["id"])
                before = len(destroyed_ids)
                h.mark_broken()
                pool.release(h)
                if len(destroyed_ids) != before + 1:
                    raise AssertionError(
                        "destroy() not called exactly once for mark_broken_release at step %d" % step
                    )

            elif kind == "with_ok":
                before_outstanding = pool.outstanding
                with pool.acquire() as h:
                    pass
                if pool.outstanding != before_outstanding:
                    raise AssertionError("capacity not restored after with_ok at step %d" % step)

            elif kind == "with_raise":
                before_outstanding = pool.outstanding
                raised = False
                try:
                    with pool.acquire() as h:
                        raise CallerProbeError("injected")
                except CallerProbeError:
                    raised = True
                if not raised:
                    raise AssertionError("exception was swallowed by __exit__ at step %d" % step)
                if pool.outstanding != before_outstanding:
                    raise AssertionError("capacity leaked after with_raise at step %d" % step)

            elif kind == "with_mark_broken_raise":
                before_outstanding = pool.outstanding
                before_destroyed = len(destroyed_ids)
                raised = False
                try:
                    with pool.acquire() as h:
                        h.mark_broken()
                        raise CallerProbeError("injected")
                except CallerProbeError:
                    raised = True
                if not raised:
                    raise AssertionError("exception was swallowed by __exit__ at step %d" % step)
                if pool.outstanding != before_outstanding:
                    raise AssertionError(
                        "capacity leaked after with_mark_broken_raise at step %d" % step
                    )
                if len(destroyed_ids) != before_destroyed + 1:
                    raise AssertionError(
                        "destroy() not called exactly once for with_mark_broken_raise at step %d" % step
                    )

            else:
                raise ValueError("unknown op: " + kind)

            check_generic(step)

        result = {
            "ok": True,
            "final_outstanding": pool.outstanding,
            "final_available": pool.available,
            "created_total": pool.created_total,
            "destroyed_total": pool.destroyed_total,
            "live_remaining": sorted(live.keys()),
        }
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
