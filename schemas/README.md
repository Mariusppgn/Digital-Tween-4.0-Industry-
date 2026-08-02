# SylvaPapers contract schemas

The canonical schemas are generated from the Pydantic models, which prevents
documentation drift:

```python
from sylvapapers_contracts import export_json_schemas

export_json_schemas("schemas/generated")
```

The exporter writes one deterministic Draft 2020-12-compatible JSON Schema per
public top-level contract.
