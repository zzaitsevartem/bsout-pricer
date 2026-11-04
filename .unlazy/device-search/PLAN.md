# Plan: Device-first search
Scope: device-search
Depth: tree 3
Mode: orchestrated, sequential implementation after Luna research

## Contract
Reader: native Luna subagent; all project exploration and Liberty inspection delegated. Sol 6.1 implements from reader evidence; driver orchestrates and reviews. Preserve dirty changes, filters/exports and device variants; no commit, no real .env access. Python 3.11 disposable Docker runtime, frontend existing npm toolchain. Exact implementation ownership and executable test commands will be refined from research before implementation. This is an execution ledger; MASTERPLAN remains the live project plan.

## Current contract inventory
Contract revision: 3
| ID | Required outcome or constraint | Owner | Observing gate | Disposition | Revision |
|---|---|---|---|---|---|
| C1 | Complexity assessed before implementation | 1.1.1 | leaf-1.1.1:G1 | ACTIVE | 1 |
| C2 | Luna alone explores repository and Liberty with evidence | 1.1.1 | leaf-1.1.1:G2 | ACTIVE | 1 |
| C3 | Device query retrieves varied spare parts with correct variants | 1.2.1 | leaf-1.2.1:G1 | ACTIVE | 1 |
| C4 | Category necessity evaluated and coherent narrowing implemented | 1.2.2 | leaf-1.2.2:G1 | ACTIVE | 1 |
| C5 | Filters, exports, legacy query compatibility | 1.2 | node-1.2:N2 | ACTIVE | 1 |
| C6 | Tests and live user journey verified | 1.2 | node-1.2:N3 | ACTIVE | 1 |
| C7 | Unrelated edits preserved; audit and live plan maintained | 1 | G2 | ACTIVE | 1 |

## Tree
- 1 Device-first search: GATES.md
  - 1.1 Research: gates/node-1.1.md
    - 1.1.1 Repository and Liberty evidence: gates/leaf-1.1.1.md
  - 1.2 Implementation: gates/node-1.2.md
    - 1.2.1 Search semantics and regression tests: gates/leaf-1.2.1.md
    - 1.2.2 Device-first UI and categories: gates/leaf-1.2.2.md

## Leaf dispatch table
| Leaf | Owns | Needs | Tier | Planned wave | State |
|---|---|---|---|---|---|
| 1.1.1 | .unlazy/device-search/research.md | - | judgment | 1 | VERIFIED |
| 1.2.1 | backend/src/modules/products/**, backend/tests/integration/test_device_search.py, backend/tests/unit/test_product_search.py | 1.1.1 | judgment | 2 | VERIFIED |
| 1.2.2 | frontend/src/app/search/**, frontend/src/models/catalog/**, frontend/src/widgets/ProductSearch/**, frontend/src/widgets/Header/**, frontend/src/widgets/authorizedHome/**, frontend/src/models/product/** | 1.2.1 | judgment | 3 | VERIFIED |

Revision 2 interfaces: GET /catalog/devices?q=&limit= returns id,label,count for devices with catalog products, matching Device.name or DeviceAlias. GET /catalog/facets adds existing device/type/tier/offer filters and count per option, excluding own dimension while counting. Explicit model selection sends device_id and clears q/part_type/page; free text retains legacy semantics. Frontend ownership refined once source support arrives.

Revision 3: expanded raw offers must obey canonical device/type/tier constraints too. ProductService and raw /products optional IDs extended; selected zero-result facet labels retained with count0. Runtime tests use disposable backend container and separate Redis hostname because REDIS_DB is unsupported.
