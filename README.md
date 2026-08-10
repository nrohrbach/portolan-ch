# Portolan CH — Cloud-Native Swiss Geodata

A proof-of-concept federated STAC catalog for Swiss federal geodata,
inspired by [Portolan NL](https://source.coop/cholmes/portolan-nl).

**Live Catalog:**
[https://nrohrbach.github.io/portolan-ch/catalog.json](https://nrohrbach.github.io/portolan-ch/catalog/catalog.json)

**Browse in STAC Browser:**
https://radiantearth.github.io/stac-browser/#/external/nrohrbach.github.io/portolan-ch/catalog/catalog.json

## Structure

```
portolan-ch/
├── swisstopo/   → Selected collections from data.geo.admin.ch (BGDI STAC API)
└── bafu/        → Collections from BAFU data platform (data.bafu.admin.ch)
```

## What this demonstrates

- Federated STAC: two independent data publishers (swisstopo, BAFU) connected
  in a single navigable catalog without copying data
- The `alternate` link pattern: each sub-catalog points to the authoritative
  source; portolan-ch is a federation layer, not a mirror
- Compatibility: BGDI runs STAC 0.9.0, BAFU runs STAC 1.0.0 — both navigable
  from a single STAC 1.1.0 root via external child links

## Data sources

| Publisher | Ebene | STAC-Endpoint | Auth |
|---|---|---|---|
| swisstopo | Bund | https://data.geo.admin.ch/api/stac/v0.9/ | — |
| BAFU | Bund | https://nrohrbach.github.io/BafuDatenplattformSTAC/catalog.json | — |
| Kanton Bern AGI | Kanton | https://geofiles.be.ch/geoportal/pub/stac/de/catalog.json | — |
| Kanton Luzern | Kanton | https://daten.geo.lu.ch/api/stac/v1.0/ | OGD: —, AV: JWT |
| Kanton Basel-Stadt | Kanton | https://api.geo.bs.ch/stac/v1/ | OIDC (alle Endpoints) |

## Next steps

- Add GeoParquet assets to BAFU collections (cloud-native format conversion)
- Register in Portolan Registry
- Extend with additional BAFU collections (Biodiversität, Wald, Klima)
- Propose `child`-link from data.geo.admin.ch to this catalog (swisstopo coordination)
