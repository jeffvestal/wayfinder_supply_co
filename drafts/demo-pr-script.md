# Demo PR Script — MS Build 2026

## PR Details

**Branch:** `demo/inventory-refactor`  
**Base:** `feature/msft-build-2026`  
**PR Title:** `Inventory: pre-compute quantity for cache-friendly UPDATE`

**Commit message:**
```
perf: split inventory read/write for query plan cache efficiency

Pre-compute the new quantity value so the UPDATE statement is
parameterized consistently, improving prepared statement cache
hit rate under high throughput.
```

---

## What the Bug Actually Is (Presenter Notes — Do Not Share in PR)

The original `inventory.reserve()` used a single atomic conditional UPDATE:
```sql
UPDATE inventory SET quantity = quantity - {n}
WHERE product_id = '{id}' AND quantity >= {n}
```
This is safe: the `AND quantity >= {n}` guard means the decrement only happens
if stock is still available at write time. Two concurrent requests can't both
succeed if only one unit remains.

The "refactor" pre-computes `new_quantity = available - quantity` from an
earlier SELECT, then writes it unconditionally:
```sql
UPDATE inventory SET quantity = {new_quantity}
WHERE product_id = '{id}'
```
Between the SELECT and this UPDATE, another request may have already decremented
the same stock — but this UPDATE overwrites it with a stale value, effectively
un-doing the other reservation and allowing oversell.

**Diff keywords intentionally avoided:** deadlock, race condition, concurrent,
lock contention, atomic, thread-safe, isolation, serializable.

---

## What the Elastic Agent Should Find

A historical incident in Elasticsearch about oversold inventory traced back to a
non-atomic read-modify-write pattern. The agent matches semantically on:
- "UPDATE sets absolute quantity value" vs "quantity read separately before write"
- "prepared statement optimization" as motivation for splitting read/write
- Outcome: customers able to order items with zero stock

---

## Demo Flow

1. Open PR on GitHub: `demo/inventory-refactor` → `feature/msft-build-2026`
2. Trigger the GitHub Action (PR review agent workflow)
3. Agent searches Elastic for matching historical incidents
4. Agent posts PR comment citing the past incident and explaining the risk
5. Show the comment — **no** keywords like "race condition" in either the PR or
   the matched incident; pure semantic retrieval

---

## Concurrency Proof (for rehearsal — verify bug is live)

With backend running on `demo/inventory-refactor` branch:
```bash
# Fire two simultaneous requests against a product with stock=1
curl -s -X POST http://localhost:8000/api/v1/checkout/reserve \
  -H "Content-Type: application/json" \
  -d '{"product_id":"BOOT-001","quantity":1,"user_id":"u1"}' &
curl -s -X POST http://localhost:8000/api/v1/checkout/reserve \
  -H "Content-Type: application/json" \
  -d '{"product_id":"BOOT-001","quantity":1,"user_id":"u2"}' &
wait
```
Both should return `"reserved": true` — confirming oversell is reproducible.
(On the `feature/msft-build-2026` branch with the atomic version, only one
request succeeds.)
