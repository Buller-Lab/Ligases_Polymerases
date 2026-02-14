import json
import copy
from pathlib import Path
import argparse
from collections import defaultdict

def load_cytoscape_json(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def get_elements(data: dict):
    if "elements" in data:
        elems = data["elements"]
        return elems.get("nodes", []), elems.get("edges", [])
    return data.get("nodes", []), data.get("edges", [])

def set_elements(data: dict, nodes, edges):
    if "elements" in data:
        data["elements"]["nodes"] = nodes
        data["elements"]["edges"] = edges
    else:
        data["nodes"] = nodes
        data["edges"] = edges

def split_network(input_path: str):
    data = load_cytoscape_json(input_path)
    orig_nodes, orig_edges = get_elements(data)

    if not orig_edges:
        print("No edges → nothing to split")
        return

    # Build adjacency
    node_to_edges = defaultdict(list)
    edge_to_nodes = {}
    for e in orig_edges:
        d = e.get("data", {})
        src = d.get("source")
        tgt = d.get("target")
        eid = d.get("id")
        if src and tgt:
            node_to_edges[src].append(e)
            node_to_edges[tgt].append(e)
            if eid:
                edge_to_nodes[eid] = (src, tgt)

    # Sort edges deterministically
    orig_edges_sorted = sorted(
        orig_edges,
        key=lambda e: (
            e.get("data", {}).get("id") or "",
            e.get("data", {}).get("source") or "",
            e.get("data", {}).get("target") or ""
        )
    )

    half = len(orig_edges_sorted) // 2
    edges_a = orig_edges_sorted[:half]
    edges_b = orig_edges_sorted[half:]

    # Nodes used in each part
    nodes_a = set()
    nodes_b = set()
    for e in edges_a:
        d = e.get("data", {})
        if "source" in d: nodes_a.add(d["source"])
        if "target" in d: nodes_a.add(d["target"])
    for e in edges_b:
        d = e.get("data", {})
        if "source" in d: nodes_b.add(d["source"])
        if "target" in d: nodes_b.add(d["target"])

    # Bridge nodes = appear in both parts
    bridge = nodes_a & nodes_b

    # Exclusive nodes
    only_a = nodes_a - bridge
    only_b = nodes_b - bridge

    # Prepare node objects (by id)
    node_by_id = {n["data"]["id"]: n for n in orig_nodes if "data" in n and "id" in n["data"]}

    # Build part A nodes = only_a + bridge
    nodes_part_a = [copy.deepcopy(node_by_id[nid]) for nid in (only_a | bridge) if nid in node_by_id]
    # Part B nodes = only_b + bridge
    nodes_part_b = [copy.deepcopy(node_by_id[nid]) for nid in (only_b | bridge) if nid in node_by_id]

    # Create two almost-independent network objects
    part_a = copy.deepcopy(data)
    set_elements(part_a, nodes_part_a, [copy.deepcopy(e) for e in edges_a])

    part_b = copy.deepcopy(data)
    set_elements(part_b, nodes_part_b, [copy.deepcopy(e) for e in edges_b])

    # Save
    base = Path(input_path).stem
    p1 = f"{base}_part1.cyjs"
    p2 = f"{base}_part2.cyjs"

    with open(p1, "w", encoding="utf-8") as f:
        json.dump(part_a, f, indent=2, sort_keys=False)
    with open(p2, "w", encoding="utf-8") as f:
        json.dump(part_b, f, indent=2, sort_keys=False)

    orig_size = Path(input_path).stat().st_size
    s1 = Path(p1).stat().st_size
    s2 = Path(p2).stat().st_size

    print(f"Original:     {orig_size:>8,} bytes")
    print(f"Part 1:       {s1:>8,} bytes  ({s1/orig_size*100:5.1f}%)")
    print(f"Part 2:       {s2:>8,} bytes  ({s2/orig_size*100:5.1f}%)")
    print(f"Total parts:  {s1+s2:>8,} bytes  ({(s1+s2)/orig_size*100:5.1f}%)")
    print(f"Saved:        {orig_size - (s1+s2):>8,} bytes")
    print(f"→ {p1}")
    print(f"→ {p2}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Cytoscape JSON file to split")
    args = parser.parse_args()
    split_network(args.input)

if __name__ == "__main__":
    main()