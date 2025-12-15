import json
import re
from pathlib import Path
from datetime import datetime

# Input files (existing in workspace)
PRD_EXTRACT = Path('Interop Project PRD Document_extracted.json')
FIGMA_RAW = Path('figma_z8KzX9eaO53rDOb887HYWv.json')
OUT = Path('equivalents_detailed.json')

# Simple tokenizer
WORD_RE = re.compile(r"[A-Za-z0-9]{3,}")


def tokenize(text):
    if not text:
        return []
    return [w.lower() for w in WORD_RE.findall(text)]


def collect_prd_items(prd_json):
    # prd_json contains xml_method
    xml = prd_json.get('xml_method', {})
    sections = prd_json.get('xml_method', {}).get('text_blocks', [])
    # We also had parsed sections in normalized; but we use text_blocks
    items = []
    # heuristic: treat headings and lines starting with digits/sections as section names
    for i, block in enumerate(sections):
        text = block.strip()
        if not text:
            continue
        items.append({'index': i, 'text': text, 'tokens': tokenize(text)})
    return items


def traverse_figma_node(node, collected, parent_id=None):
    # node is a dict representing a figma node (document subtree)
    nid = node.get('id') or node.get('document') and node.get('document').get('id')
    # Some nodes are wrapped; if no id, try name-based key generation
    if not nid:
        nid = node.get('id') or node.get('name') or f"node_{len(collected)}"
    entry = {}
    entry['id'] = nid
    entry['name'] = node.get('name', '')
    entry['type'] = node.get('type', '')
    # collect text content
    chars = node.get('characters') or ''
    # some text content may be in description or documentation
    desc = node.get('description') or node.get('hint') or ''
    # images
    image_ref = None
    if 'imageRef' in node:
        image_ref = node.get('imageRef')
    # styles
    styles = node.get('styles', {})
    # bounding box
    bbox = node.get('absoluteBoundingBox')
    entry.update({
        'characters': chars,
        'description': desc,
        'imageRef': image_ref,
        'styles': styles,
        'absoluteBoundingBox': bbox,
        'children_count': len(node.get('children', [])) if isinstance(node.get('children'), list) else 0,
        'tokens': tokenize(' '.join(filter(None, [entry.get('name',''), chars, desc])))
    })
    collected[nid] = entry
    # Recurse children
    for child in node.get('children', []):
        traverse_figma_node(child, collected, nid)


def collect_figma_nodes(figma_json):
    collected = {}
    # figma_json likely has structure similar to the API response: keys like 'nodes' or 'document'
    # Try several entry points
    if isinstance(figma_json, dict):
        # direct nodes map (from /nodes response)
        if 'nodes' in figma_json and isinstance(figma_json['nodes'], dict):
            for key, block in figma_json['nodes'].items():
                # block may have 'document' or similar
                node = block.get('document') or block
                traverse_figma_node(node, collected)
        # if top-level document
        elif 'document' in figma_json:
            traverse_figma_node(figma_json['document'], collected)
        else:
            # try any dict values that appear node-like
            for v in figma_json.values():
                if isinstance(v, dict) and 'children' in v:
                    traverse_figma_node(v, collected)
    return collected


def score_match(tokens_a, tokens_b):
    if not tokens_a or not tokens_b:
        return 0.0
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    common = set_a.intersection(set_b)
    # score = |common| / sqrt(|A|*|B|) to normalize
    import math
    score = len(common) / math.sqrt(max(1,len(set_a)) * max(1,len(set_b)))
    return float(score)


def build_mappings(prd_items, figma_nodes):
    # For each PRD item find top matching nodes
    mappings = []
    node_list = list(figma_nodes.values())
    for item in prd_items:
        scores = []
        for n in node_list:
            s = score_match(item['tokens'], n['tokens'])
            if s > 0:
                scores.append((s, n))
        # sort desc
        scores.sort(key=lambda x: x[0], reverse=True)
        matched = []
        for s, n in scores[:10]:
            matched.append({'node_id': n['id'], 'name': n['name'], 'type': n['type'], 'score': round(s,4), 'matched_tokens': list(set(item['tokens']).intersection(set(n['tokens'])) )})
        mappings.append({'prd_index': item['index'], 'prd_text': item['text'], 'matched_nodes': matched})
    return mappings


def invert_mappings(mappings):
    # produce node -> prd matches
    node_map = {}
    for m in mappings:
        for match in m['matched_nodes']:
            nid = match['node_id']
            node_map.setdefault(nid, []).append({'prd_index': m['prd_index'], 'prd_text': m['prd_text'], 'score': match['score']})
    return node_map


def main():
    if not PRD_EXTRACT.exists():
        print(f"Missing PRD extract: {PRD_EXTRACT}")
        return
    if not FIGMA_RAW.exists():
        print(f"Missing Figma raw: {FIGMA_RAW}")
        return

    prd = json.loads(PRD_EXTRACT.read_text(encoding='utf-8'))
    figma = json.loads(FIGMA_RAW.read_text(encoding='utf-8'))

    prd_items = collect_prd_items(prd)
    figma_nodes = collect_figma_nodes(figma)

    mappings = build_mappings(prd_items, figma_nodes)
    node_mappings = invert_mappings(mappings)

    out = {
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'prd_source': str(PRD_EXTRACT),
            'figma_source': str(FIGMA_RAW),
            'prd_items_count': len(prd_items),
            'figma_nodes_count': len(figma_nodes)
        },
        'prd_items': prd_items,
        'figma_nodes': figma_nodes,
        'mappings': mappings,
        'node_mappings': node_mappings
    }

    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Wrote detailed equivalents to {OUT} (PRD items: {len(prd_items)}, figma nodes: {len(figma_nodes)})")


if __name__ == '__main__':
    main()
