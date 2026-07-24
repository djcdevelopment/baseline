# cre-e02-gateway-pressure-route / gateway-pressure-route-v1

- Run: `gateway_udp-20260724T141258Z`
- Driver: `gateway_udp`
- Seed: `411`
- Classification: `supported`
- Stop: `completed`

## Invariants

- PASS `gateway_only_routes_selected_presentation` — selected=9; observed=9; suppressed=23
- PASS `gateway_udp_delivery` — received=10; relayed=9; expected_relayed=9
- PASS `gateway_route_sequence_monotonic` — sequences=1,2,3,4,5,6,7,8,9
- PASS `critical_carriage_not_overclaimed` — CRE-E02 exercises presentation motion transport only; critical state requires its own reliable-carriage experiment

## Prediction observations

- `pressure_to_transport`: 9 selected presentation decisions reached the real bound UDP seam; 23 deferred/dropped decisions did not
- `critical_transport_boundary`: critical mutations remain gate decisions only in CRE-E02; this result makes no death, hit, build, or inventory durability claim
