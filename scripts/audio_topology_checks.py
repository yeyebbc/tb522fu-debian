# SPDX-License-Identifier: GPL-2.0-only
# Imported from yzddmr6/onepluspad-2pro-mainline@25325453637b1f9f4c128d969269a5a132111f78
# tools/build-debs.py, audio validation subset. Original source license retained.
import re
import struct

def die(message):
    raise SystemExit(message)

Q6APM_DAI_STREAMS = {'Playback': ({'S16_LE', 'S24_LE'}, 2, 4),
                    'Capture': ({'S16_LE', 'S24_LE'}, 2, 4)}

def topology_sections(text, kind):
    """(name, body) of each Section<kind>."name" { ... } in a topology conf."""
    for match in re.finditer(r'Section' + kind + r'\."([^"]+)"\s*\{', text):
        depth, end = 1, match.end()
        while depth:
            if end == len(text):
                die(f'unterminated Section{kind}."{match[1]}" in the topology')
            depth += {'{': 1, '}': -1}.get(text[end], 0)
            end += 1
        yield match[1], text[match.end():end - 1]


def check_topology(text, kernel_widgets):
    """Refuse a topology whose PCMs cannot open or reach no back end.

    alsatplg accepts both: it only warns about route ends it does not define
    (the back-end DAI widgets the kernel creates) and knows nothing of the
    platform driver.  kernel_widgets names the back-end DAI widgets the graph
    may end at; each must be used, so a renamed or unused back end fails too.
    """
    widgets, streams = {}, {}
    for name, body in topology_sections(text, 'Widget'):
        mixer = re.search(r'\bmixer\s*\[(.*?)\]', body, re.S)
        widgets[name] = {m[0] or m[1] for m in re.findall(r'"([^"]+)"|(\S+)', mixer[1])} if mixer else set()
        stream = re.search(r'\bstream_name\s+"([^"]+)"', body)
        if stream:
            streams.setdefault(stream[1], set()).add(name)
    edges, used = [], set()
    for graph, body in topology_sections(text, 'Graph'):
        lines = re.search(r'\blines\s*\[(.*?)\]', body, re.S)
        for line in re.findall(r'"([^"]*)"', lines[1] if lines else ''):
            parts = [part.strip() for part in line.split(',')]
            if len(parts) != 3:
                die(f'topology graph {graph!r}: malformed route {line!r}')
            sink, control, source = parts
            for end in (sink, source):
                if end in kernel_widgets:
                    used.add(end)
                elif end not in widgets:
                    die(f'topology graph {graph!r}: route end {end!r} is neither a '
                        'topology widget nor a declared back-end DAI widget')
            if control and control not in widgets.get(sink, ()):
                die(f'topology graph {graph!r}: {sink!r} has no mixer control {control!r}')
            edges.append((source, sink))
    unused = sorted(set(kernel_widgets) - used)
    if unused:
        die(f'declared back-end DAI widgets no route reaches: {", ".join(unused)}')
    for name, body in topology_sections(text, 'PCMCapabilities'):
        direction = name.rsplit(' ', 1)[-1]
        if direction not in Q6APM_DAI_STREAMS:
            die(f'topology PCM {name!r} is neither Playback nor Capture')
        formats, low, high = Q6APM_DAI_STREAMS[direction]
        found = re.search(r'\bformats\s+"([^"]+)"', body)
        advertised = {f.strip() for f in found[1].split(',')} if found else set()
        if not advertised or not advertised <= formats:
            die(f'topology PCM {name!r} offers {sorted(advertised)}; q6apm-dai serves '
                f'{direction.lower()} only as {sorted(formats)}, so open() would fail')
        channels = [re.search(r'\bchannels_' + key + r'\s+"(\d+)"', body) for key in ('min', 'max')]
        if not all(channels) or max(int(channels[0][1]), low) > min(int(channels[1][1]), high):
            die(f'topology PCM {name!r}: channel range outside q6apm-dai {low}..{high}')
        # A playback front end must reach a back end downstream, a capture one upstream.
        forward = direction == 'Playback'
        reached, todo = set(), list(streams.get(name, ()))
        if not todo:
            die(f'topology PCM {name!r}: no widget carries its stream')
        while todo:
            node = todo.pop()
            if node in reached:
                continue
            reached.add(node)
            todo += [b if forward else a for a, b in edges if (a if forward else b) == node]
        if not reached & set(kernel_widgets):
            die(f'topology PCM {name!r} reaches no back-end DAI widget')


# Binary topology layout: include/uapi/sound/asoc.h and snd_ar_tokens.h.
TPLG_MAGIC = 0x41536F43
TPLG_TYPE_DAPM_WIDGET = 5
TPLG_VALUE_TUPLES = {2, 3, 4, 5}        # bool, byte, word, short: token/value pairs
AR_TKN_U32_MODULE_ID = 200
AR_TKN_U32_MODULE_INSTANCE_ID = 201
AR_TPLG_MODULE_CFG_TYPE = 0x01001006    # SND_SOC_AR_TPLG_MODULE_CFG_TYPE
AR_MODULE_ID_MFC = 0x07001015
AR_PARAM_ID_CHMIXER_COEFF = 0x0800101F  # AudioReach chmixer_common_api.h
Q14_UNITY = 0x4000
# The channel maps the kernel sends with every PCM and MFC media format:
# audioreach_set_default_channel_mapping(), i.e. q6dsp_map_channels() in
# q6dsp-common.c with mono as FL.  The MFC applies a mixing table only when
# its maps equal the stream's; any other table is silently ignored and the
# built-in ITU-R BS.775 coefficients are used instead.
KERNEL_CHANNEL_MAPS = {1: (1,), 2: (1, 2), 3: (1, 2, 3), 4: (1, 2, 4, 5),
                       5: (1, 2, 3, 4, 5), 6: (1, 2, 6, 3, 4, 5),
                       8: (1, 2, 6, 3, 4, 5, 8, 9)}


def topology_widgets(blob):
    """(name, private data) of each DAPM widget in a binary topology."""
    pos = 0
    while pos < len(blob):
        magic, _, _, kind, size, _, payload, _, count = struct.unpack_from('<9I', blob, pos)
        if magic != TPLG_MAGIC:
            die(f'topology binary: bad block magic at {pos}')
        at = pos + size
        pos = at + payload
        if kind != TPLG_TYPE_DAPM_WIDGET:
            continue
        for _ in range(count):
            wsize = struct.unpack_from('<I', blob, at)[0]
            name = blob[at + 8:at + 52].split(b'\0')[0].decode()
            controls, private = struct.unpack_from('<2I', blob, at + wsize - 8)
            yield name, blob[at + wsize:at + wsize + private]
            at += wsize + private
            for _ in range(controls):
                # Each control struct starts with a header whose first word is
                # its size; the struct's own size follows it, and the struct
                # ends with its private data's size.
                hsize = struct.unpack_from('<I', blob, at)[0]
                csize = struct.unpack_from('<I', blob, at + hsize)[0]
                at += csize + struct.unpack_from('<I', blob, at + csize - 4)[0]
        if at != pos:
            die('topology binary: widget block does not add up')


def module_config(name, private):
    """The module tokens and the configuration blob of one widget's private data.

    Mirrors audioreach_get_module_priv_data(): the private data is a run of
    vendor arrays, each sized including its header, and a module
    configuration is the array of type SND_SOC_AR_TPLG_MODULE_CFG_TYPE.
    """
    tokens, blob, at = {}, None, 0
    while at < len(private):
        if len(private) - at < 12:
            die(f'topology widget {name!r}: {len(private) - at} stray private bytes')
        size, kind, count = struct.unpack_from('<3I', private, at)
        if size < 12 or size > len(private) - at:
            die(f'topology widget {name!r}: vendor array of {size} bytes at {at}')
        if kind == AR_TPLG_MODULE_CFG_TYPE:
            if blob is not None or size <= 16:
                die(f'topology widget {name!r}: module configuration is repeated or empty')
            blob = private[at + 16:at + size]
        elif kind in TPLG_VALUE_TUPLES and size == 12 + 8 * count:
            for i in range(count):
                token, value = struct.unpack_from('<2I', private, at + 12 + 8 * i)
                tokens[token] = value
        at += size
    return tokens, blob


def chmixer_tables(name, payload):
    """Decode PARAM_ID_CHMIXER_COEFF: [(out map, in map, rows)]."""
    tables, at = [], 4
    for _ in range(struct.unpack_from('<I', payload)[0]):
        outs, ins = struct.unpack_from('<2H', payload, at)
        count = outs + ins + outs * ins
        if not outs or not ins or at + 4 + 2 * count > len(payload):
            die(f'topology widget {name!r}: chmixer table overruns its parameter')
        words = struct.unpack_from(f'<{count}H', payload, at + 4)
        rows = [words[outs + ins + r * ins:outs + ins + (r + 1) * ins] for r in range(outs)]
        if any(c > Q14_UNITY for row in rows for c in row):
            die(f'topology widget {name!r}: chmixer coefficient above Q14 unity')
        tables.append((words[:outs], words[outs:outs + ins], rows))
        at += (4 + 2 * count + 3) & ~3
    if payload[at:].strip(b'\0'):
        die(f'topology widget {name!r}: bytes after the chmixer tables')
    return tables


def check_module_configs(blob):
    """Refuse module configurations the kernel or the DSP would misapply.

    Returns {widget: {param id: payload or decoded tables}} for the widgets
    that carry one.  The kernel sends a blob verbatim as APM parameters, so
    each must address its own module; a channel mixing table must use the
    maps the kernel sends or the MFC falls back to its default upmix.
    """
    found = {}
    for name, private in topology_widgets(blob):
        tokens, config = module_config(name, private)
        if config is None:
            continue
        module = tokens.get(AR_TKN_U32_MODULE_ID)
        if module != AR_MODULE_ID_MFC:
            die(f'topology widget {name!r}: the kernel sends a module configuration '
                f'only to MFC modules, not to {module:#x}' if module is not None else
                f'topology widget {name!r}: module configuration without a module')
        params, at = {}, 0
        while len(config) - at >= 16:
            iid, pid, psize, error = struct.unpack_from('<4I', config, at)
            if iid != tokens.get(AR_TKN_U32_MODULE_INSTANCE_ID) or error:
                die(f'topology widget {name!r}: parameter {pid:#x} addresses instance '
                    f'{iid:#x}, not its own')
            payload = config[at + 16:at + 16 + psize]
            if len(payload) != psize or psize % 4:
                die(f'topology widget {name!r}: parameter {pid:#x} size {psize}')
            params[pid] = (chmixer_tables(name, payload) if pid == AR_PARAM_ID_CHMIXER_COEFF
                           else payload)
            at += 16 + ((psize + 7) & ~7)
        if config[at:].strip(b'\0') or not params:
            die(f'topology widget {name!r}: module configuration does not parse')
        for out_map, in_map, _ in params.get(AR_PARAM_ID_CHMIXER_COEFF, ()):
            if (tuple(out_map) != KERNEL_CHANNEL_MAPS.get(len(out_map)) or
                    tuple(in_map) != KERNEL_CHANNEL_MAPS.get(len(in_map))):
                die(f'topology widget {name!r}: chmixer maps {list(in_map)} -> '
                    f'{list(out_map)} are not the ones the kernel sends; the MFC '
                    'would ignore the table')
        found[name] = params
    return found


def describe_chmixer(params):
    """'L R L R ...' per output of each mixing table, for the build log."""
    names = {}
    for _, in_map, rows in params.get(AR_PARAM_ID_CHMIXER_COEFF, ()):
        labels = {1: 'L', 2: 'R'}
        cells = ['+'.join(labels.get(in_map[i], str(in_map[i])) +
                          ('' if c == Q14_UNITY else f'*{c / Q14_UNITY:.3g}')
                          for i, c in enumerate(row) if c) or '-' for row in rows]
        names[f'{len(in_map)}->{len(rows)}'] = ' '.join(cells)
    return names

