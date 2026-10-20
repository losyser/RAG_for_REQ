"""Title + independent id/text EA XMI view; preserves the input model properties.

Uses the supplied ea_native_sel1.xml serialization (ClassifierRole, content-level
tagged values, SysML stereotype/xref, Tag=1). Geometry is conservative static
layout, not a claim of verified EA font metrics or automatic sizing.
"""
import math
import re
import xml.etree.ElementTree as ET
from .ea_compact import q, merge_style, LEGEND_ID


def requirement_title(name, business_id, fallback=''):
    """Remove a legacy ID/status label without truncating meaningful words."""
    title = re.sub(r'^' + re.escape(business_id) + r'(?=\s|$)\s*', '', name.strip())
    title = re.sub(r'\s*\[(?:SOURCE|[ABCX]\s*\|[^\]]*)\]\s*$', '', title)
    title = ' '.join(title.split())
    for bad, good in [('Requiremen', 'Requirement'), ('Complianc', 'Compliance'),
                      ('Settin', 'Setting'), ('Sett', 'Setting')]:
        title = re.sub(r'\b' + bad + r'$', good, title)
    if not title or title in ('Requirement', 'Engineering Requirement'):
        title = ' '.join(fallback.split())
    if not title or title == business_id:
        raise ValueError('Missing meaningful title: ' + business_id)
    return title


def properties(root):
    result = {}
    for tv in root.iter(q('TaggedValue')):
        rid = tv.get('modelElement')
        if rid:
            bucket = result.setdefault(rid, {})
            if tv.get('tag') in bucket:
                raise ValueError('Duplicate property: ' + str((rid, tv.get('tag'))))
            bucket[tv.get('tag')] = tv.get('value', '')
    return result


def structure_xml(xml, colors, per_row=12):
    if per_row < 1:
        raise ValueError('per_row must be positive')
    root = ET.fromstring(xml)
    props = properties(root)
    roles = {e.get('xmi.id'): e for e in root.iter(q('ClassifierRole'))}
    content = root.find('XMI.content')
    names = {}
    for rid, role in roles.items():
        p = props[rid]
        if not p.get('id') or not p.get('text', '').startswith('<memo>#NOTES#'):
            raise ValueError('Missing independent id/text: ' + rid)
        old_name = role.get('name', '')
        names[rid] = requirement_title(p.get('display_full_name', old_name), p['id'],
                                      p['text'].removeprefix('<memo>#NOTES#'))
        role.set('name', names[rid])
        # Preserve original notes and all existing properties exactly. These are
        # model data, not the display label or a replacement for SysML text.
    for edge in root.iter(q('Association')):
        ends = list(edge.iter(q('AssociationEnd')))
        for tag, endpoint in zip(('ea_sourceName', 'ea_targetName'), ends):
            for tv in edge.findall('./' + q('ModelElement.taggedValue') + '/' + q('TaggedValue')):
                if tv.get('tag') == tag:
                    tv.set('value', names[endpoint.get('type')])
    for diagram in root.iter(q('Diagram')):
        dtv = diagram.find(q('ModelElement.taggedValue'))
        # EA build 1628 native import/render verified: SUPTAG suppresses named
        # tags on this diagram only. The complete model properties stay intact.
        hidden_tags = sorted({key for p in props.values() for key in p if key not in {'id', 'text'}})
        for key in ('styleex', 'EAStyle'):
            found = next((t for t in dtv if t.get('tag') == key), None)
            if found is None:
                found = ET.SubElement(dtv, q('TaggedValue'), {'tag': key})
            found.set('value', merge_style(found.get('value', ''), {'ShowNotes': 0, 'ShowTags': 1}))
            if key == 'styleex':
                found.set('value', merge_style(found.get('value', ''), {'SUPTAG': ','.join(hidden_tags)}))
        elements = diagram.find(q('Diagram.element'))
        association_ids = {e.get('xmi.id') for e in root.iter(q('Association'))}
        for e in elements:
            if e.get('subject') in association_ids:
                # Native DiagramLink.LineStyle=4 (Tree Vertical) serializes as
                # Mode=3;TREE=V; in EA build 1628. Prevent side-entry diagonals
                # from crossing sibling boxes even in a single row.
                e.set('style', merge_style(e.get('style',''), {'Mode': 3, 'TREE': 'V'}))
        nodes = {e.get('subject'): e for e in elements if e.get('subject') in roles}
        # Remove the obsolete compact-view legend; it advertises absent A/X
        # grades and hides id/text. It is not a requirement or engineering data.
        for e in list(elements):
            if e.get('subject') == LEGEND_ID:
                elements.remove(e)
        heights = {}
        width, gap, cursor = 300, 60, 40
        for rid in nodes:
            p = props[rid]
            # EA's SysML shape expands memo text. Reserve space for the FULL
            # normative text, while SUPTAG hides only non-core metadata.
            text = p['text'].removeprefix('<memo>#NOTES#')
            lines = sum(max(1, math.ceil(len(line) / 54)) for line in text.splitlines())
            heights[rid] = max(110, 48 + 13 * (lines + math.ceil(len(names[rid]) / 42)))
            grade = p.get('grade', '_src')
            bg, border = colors.get(grade, colors['_unknown'])
            nodes[rid].set('style', merge_style(nodes[rid].get('style', ''),
                {'Tag': 1, 'RzO': 1, 'BCol': bg, 'LCol': border, 'LWth': 2}))
        placed = set()
        def place(rid, x, y):
            nodes[rid].set('geometry', f'Left={x};Top={y};Right={x+width};Bottom={y+heights[rid]};')
            placed.add(rid)
        # Group by actual connector endpoints, not assumptions about dotted IDs.
        children = {}
        for edge in root.iter(q('Association')):
            ends = list(edge.iter(q('AssociationEnd')))
            if len(ends) == 2:
                a, b = [e.get('type') for e in ends]
                if a in nodes and b in nodes:
                    children.setdefault(a, []).append(b)
        all_children = {c for cs in children.values() for c in cs}
        for pid in [r for r in nodes if r not in all_children]:
            cs = children.get(pid, [])
            if len(cs) > per_row:
                raise ValueError('Straight-line connectors require all siblings in one row; increase per_row')
            cols = min(per_row, max(1, len(cs)))
            place(pid, 40 + (cols - 1) * (width + gap) // 2, cursor)
            cursor += heights[pid] + gap
            for start in range(0, len(cs), per_row):
                row = cs[start:start+per_row]
                for i, cid in enumerate(row):
                    place(cid, 40 + i*(width+gap), cursor)
                cursor += max(heights[c] for c in row) + gap
        if placed != set(nodes):
            raise ValueError('Unsupported cyclic or nested layout; no nodes silently omitted')
        # EA's XMI 1.1 reader expects Hidden last and a concrete orthogonal
        # Path. A TREE flag after Hidden or an empty Path is discarded.
        edge_map = {e.get('xmi.id'): list(e.iter(q('AssociationEnd'))) for e in root.iter(q('Association'))}
        for element in elements:
            ends = edge_map.get(element.get('subject'))
            if not ends or len(ends) != 2:
                continue
            source, target = [nodes[e.get('type')] for e in ends]
            def rect(node):
                return {k: int(v) for k, v in re.findall(r'(Left|Top|Right|Bottom)=(-?\d+)', node.get('geometry'))}
            a, b = rect(source), rect(target)
            sx, tx = (a['Left'] + a['Right']) // 2, (b['Left'] + b['Right']) // 2
            y = -(a['Bottom'] + b['Top']) // 2
            element.set('geometry', f'SX=0;SY=0;EX=0;EY=0;EDGE=3;$LLB=;LLT=;LMT=;LMB=;LRT=;LRB=;IRHS=;ILHS=;Path={sx}:{y}${tx}:{y}$;')
            style = re.sub(r'Hidden=[^;]*;', '', element.get('style', ''))
            element.set('style', style + 'Hidden=0;')
        maxright = max(int(re.search(r'Right=(\d+)', n.get('geometry')).group(1)) for n in nodes.values())
        for e in elements:
            if 'NSL=1;' in e.get('style', ''):
                e.set('geometry', f'Left=10;Top=10;Right={maxright+30};Bottom={cursor};')
        diagram.set('name', diagram.get('name', '').removesuffix('_Compact') + '_Structure')
    for e in list(content):
        if e.get('xmi.id') == LEGEND_ID:
            content.remove(e)
    result = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode').replace(' />', '/>')
    errors = validate_structure(xml, result)
    if errors:
        raise ValueError('; '.join(errors))
    return result


def validate_structure(original, revised):
    a, b = ET.fromstring(original), ET.fromstring(revised)
    errors = []
    ap, bp = properties(a), properties(b)
    if ap != bp:
        errors.append('model properties changed')
    def roles(t): return {e.get('xmi.id'): e for e in t.iter(q('ClassifierRole'))}
    ar, br = roles(a), roles(b)
    if ar.keys() != br.keys(): errors.append('element IDs changed')
    def edges(t): return [(e.get('xmi.id'), [n.get('type') for n in e.iter(q('AssociationEnd'))]) for e in t.iter(q('Association'))]
    if edges(a) != edges(b): errors.append('relationship IDs/endpoints changed')
    ids = [p.get('id') for r,p in bp.items() if r in br]
    if len(ids) != len(set(ids)): errors.append('duplicate business IDs')
    for rid, role in br.items():
        p = bp[rid]
        if rid in ar:
            old = ar[rid]
            if {k:v for k,v in old.attrib.items() if k != 'name'} != {k:v for k,v in role.attrib.items() if k != 'name'}:
                errors.append('requirement identity/type changed: ' + rid)
            if [ET.tostring(c) for c in old] != [ET.tostring(c) for c in role]:
                errors.append('requirement stereotype/notes/style changed: ' + rid)
        name = role.get('name', '')
        if name == p.get('id') or re.match(re.escape(p.get('id', '')) + r'\s', name) or re.search(r'\[(SOURCE|[ABCX]\s*\|)', name):
            errors.append('ID/status in name: ' + rid)
        if not p.get('text', '').startswith('<memo>#NOTES#') or p.get('text') == '<memo>#NOTES#':
            errors.append('missing full text: ' + rid)
    old_nodes = {n.get('subject'): n for n in a.iter(q('DiagramElement'))}
    for node in b.iter(q('DiagramElement')):
        old = old_nodes.get(node.get('subject'))
        if old is not None:
            keys = ('DUID',) if node.get('subject') in br else ('SOID', 'EOID')
            for key in keys:
                pattern = key + r'=([^;]+);'
                if re.findall(pattern, old.get('style','')) != re.findall(pattern, node.get('style','')):
                    errors.append('diagram identity/endpoints changed')
        if node.get('subject') in br and 'Tag=1;' not in node.get('style', ''):
            errors.append('hidden id/text compartment')
    if any('ShowTags=0;' in t.get('value','') for t in b.iter(q('TaggedValue'))):
        errors.append('diagram hides tags')
    for diagram in b.iter(q('Diagram')):
        for tv in diagram.find(q('ModelElement.taggedValue')):
            if tv.get('tag') == 'styleex':
                suppressed = re.findall(r'(?:^|;)SUPTAG=([^;]*);', tv.get('value',''))
                if suppressed and {'id','text'} & set(suppressed[0].split(',')):
                    errors.append('core id/text suppressed')
    return errors
