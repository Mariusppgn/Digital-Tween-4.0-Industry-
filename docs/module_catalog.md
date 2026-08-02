# SylvaPapers — Module catalog

## 1. `sylvapapers-contracts`

| Field | Value |
|---|---|
| Objective | Validate factory, product, reliability and operational exchanges. |
| Inputs | YAML/JSON documents. |
| Outputs | Typed models and JSON Schemas. |
| Status | Implemented and tested. |

## 2. `sylvapapers-digital-twin`

| Field | Value |
|---|---|
| Objective | Simulate the paper mill and produce auditable operational evidence. |
| Inputs | Factory graph, products, orders, seed and parameters. |
| Outputs | Events, jobs, eleven KPI, figures and reports. |
| Status | Factory increment implemented and tested. |

## 3. Factory editor

| Field | Value |
|---|---|
| Objective | Edit steps, materials, machines, relations and Weibull coefficients visually. |
| Interface | Local French web application with keyboard support. |
| Persistence | Validated JSON import/export and explicit atomic YAML/JSON write. |
| Status | Implemented and browser-validated. |

## 4. Future business modules

Predictive maintenance, resource optimization, marketing and R&D portfolio modules remain roadmap
items. They must consume public contracts rather than importing simulator internals.
