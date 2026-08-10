#!/usr/bin/env python3
"""
Generiert portolan-ch Sub-Kataloge aus sources.yaml.
Läuft lokal und via GitHub Actions.
Ausgabe: catalog/<publisher-id>/catalog.json
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

REPO_ROOT = Path(__file__).parent.parent
SOURCES_FILE = REPO_ROOT / "sources.yaml"
CATALOG_DIR = REPO_ROOT / "catalog"
ROOT_CATALOG_FILE = CATALOG_DIR / "catalog.json"

STAC_VERSION = "1.1.0"
TIMEOUT = 20


def get_json(url: str) -> dict:
    r = requests.get(url, timeout=TIMEOUT, headers={"Accept": "application/json"})
    r.raise_for_status()
    return r.json()


def child_link(href: str, title: str) -> dict:
    return {"rel": "child", "href": href, "type": "application/json", "title": title}


def base_links(publisher_id: str, title: str, endpoint: str, service_doc: str | None = None) -> list:
    links = [
        {"rel": "root",      "href": "../catalog.json", "type": "application/json", "title": "Portolan CH"},
        {"rel": "parent",    "href": "../catalog.json", "type": "application/json", "title": "Portolan CH"},
        {"rel": "self",      "href": "./catalog.json",  "type": "application/json"},
        {"rel": "alternate", "href": endpoint,          "type": "application/json",
         "title": f"{title} — vollständiger Katalog (autoritativ)"},
    ]
    if service_doc:
        links.append({"rel": "service-doc", "href": service_doc,
                       "type": "text/html", "title": "API-Dokumentation"})
    return links


def fetch_api_collections(pub: dict) -> list[dict]:
    """Paginiert durch STAC API, gibt alle Collections zurück."""
    base = pub["endpoint"].rstrip("/")
    url = f"{base}/{pub.get('collections_path', 'collections')}"
    pagination = pub.get("pagination", "next_link")
    exclude_auth = pub.get("filter", {}).get("exclude_auth", False)
    id_prefix = pub.get("filter", {}).get("id_prefix", "")
    all_collections = []

    if pagination == "next_link":
        while url:
            data = get_json(url)
            all_collections.extend(data.get("collections", []))
            url = next((l["href"] for l in data.get("links", []) if l.get("rel") == "next"), None)

    elif pagination == "offset":
        limit, offset = 100, 0
        while True:
            data = get_json(f"{url}?limit={limit}&offset={offset}")
            batch = data.get("collections", [])
            if not batch:
                break
            all_collections.extend(batch)
            if data.get("numberReturned", len(batch)) < limit:
                break
            offset += limit

    else:
        all_collections = get_json(url).get("collections", [])

    result = []
    for col in all_collections:
        col_id = col.get("id", "")
        if id_prefix and not col_id.startswith(id_prefix):
            continue
        if exclude_auth:
            items_links = [l for l in col.get("links", []) if l.get("rel") == "items"]
            if any("auth:refs" in l for l in items_links):
                print(f"  ↳ übersprungen (Auth): {col_id}")
                continue
        result.append(col)
    return result


def api_collection_to_child(col: dict, base_endpoint: str) -> dict:
    col_id = col["id"]
    title = col.get("title", col_id)
    self_link = next((l["href"] for l in col.get("links", []) if l.get("rel") == "self"), None)
    href = self_link or f"{base_endpoint.rstrip('/')}/collections/{col_id}"
    return child_link(href, title)


def fetch_static_children(pub: dict) -> list[dict]:
    """Liest child-Links aus statischem STAC-Katalog."""
    data = get_json(pub["endpoint"])
    return [
        child_link(l["href"], l.get("title", l["href"]))
        for l in data.get("links", [])
        if l.get("rel") == "child"
    ]


def generate_subcatalog(pub: dict) -> None:
    pub_id = pub["id"]
    print(f"\n→ {pub_id}")

    out_dir = CATALOG_DIR / pub_id
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        if pub["type"] == "stac_api":
            collections = fetch_api_collections(pub)
            children = [api_collection_to_child(c, pub["endpoint"]) for c in collections]
            print(f"  {len(children)} Collections gefunden")
        else:
            children = fetch_static_children(pub)
            print(f"  {len(children)} child-Links gefunden")
    except Exception as e:
        print(f"  ⚠️  Fehler: {e}", file=sys.stderr)
        children = []

    for extra in pub.get("extra_children", []):
        children.append(child_link(extra["href"], extra["title"]))

    base = pub["endpoint"].rstrip("/")
    service_doc = f"{base}/api.html" if pub["type"] == "stac_api" else None

    catalog = {
        "type": "Catalog",
        "id": pub_id,
        "stac_version": STAC_VERSION,
        "title": pub["title"],
        "description": pub["description"],
        "links": base_links(pub_id, pub["title"], pub["endpoint"], service_doc) + children,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    out_path = out_dir / "catalog.json"
    out_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ✓ {out_path.relative_to(REPO_ROOT)} ({len(children)} Links)")


def update_root_catalog(publishers: list[dict]) -> None:
    root = json.loads(ROOT_CATALOG_FILE.read_text(encoding="utf-8"))
    other_links = [l for l in root["links"] if l.get("rel") != "child"]
    new_children = [child_link(f"./{p['id']}/catalog.json", p["title"]) for p in publishers]
    root["links"] = other_links + new_children
    root["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ROOT_CATALOG_FILE.write_text(json.dumps(root, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✓ Root-Katalog: {len(new_children)} Publisher")


def main():
    sources = yaml.safe_load(SOURCES_FILE.read_text(encoding="utf-8"))
    for pub in sources["publishers"]:
        generate_subcatalog(pub)
    update_root_catalog(sources["publishers"])
    print("\nFertig.")


if __name__ == "__main__":
    main()
