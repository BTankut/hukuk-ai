# FAZ10 V3 Topology Ladder

Tarih: 2026-03-24

## L0

- tek kayit replay
- fresh process
- fresh session namespace
- single worker
- cache `off`
- release-controls `off`
- retry `0`
- fallback `disabled`
- streaming `off`
- fixed seed
- canonical generation contract

## L1

- `v3-32` frontier pack
- fresh process per request
- fresh session namespace
- single worker
- cache `off`
- release-controls `off`
- retry `0`
- fallback `disabled`
- streaming `off`
- serial execution

## L2

- `v3-32` frontier pack
- shared process
- hard reset after each request
- fresh session namespace per request
- single worker
- cache `off`
- release-controls `off`
- retry `0`
- fallback `disabled`
- streaming `off`
- serial execution

## L3

- `v3-32` frontier pack
- shared process
- no hard reset between requests
- fresh session namespace per request
- single worker
- cache `off`
- release-controls `off`
- retry `0`
- fallback `disabled`
- streaming `off`
- serial execution

## L4

- `v3-32` frontier pack
- shared process
- no hard reset between requests
- fresh session namespace per request
- single worker
- cache `off`
- release-controls `on`
- retry `0`
- fallback `disabled`
- streaming `off`
- serial execution

## L5

- `v3-170` tam aile
- shared process
- no hard reset between requests
- fresh session namespace per request
- single worker
- cache `off`
- release-controls `on`
- retry `0`
- fallback `disabled`
- streaming `off`
- serial execution

## L6

- `v3-170` tam aile
- canonical worker topology
- cache `off`
- release-controls `on`
- retry `0`
- fallback `disabled`
- streaming `off`
- canonical request ordering

## L7

- `v3-170` tam aile
- canonical worker topology
- canonical cache policy
- release-controls `on`
- canonical retry / timeout policy
- canonical streaming policy
- canonical request ordering
