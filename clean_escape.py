import re
import argparse
from pathlib import Path

ansi_pattern = re.compile(r'\x1b\[([0-9;]*)m')

def parse_sgr(params):
    state = {
        'bold': False,
        'underline': False,
        'fg_mode': None,  # 'standard' or '256'
        'fg': None,
        'bg_mode': None,
        'bg': None,
    }
    i = 0
    while i < len(params):
        p = params[i]
        if p == 0:
            state = {k: False if k in ('bold', 'underline') else None for k in state}
        elif p == 1:
            state['bold'] = True
        elif p == 22:
            state['bold'] = False
        elif p == 4:
            state['underline'] = True
        elif p == 24:
            state['underline'] = False
        elif (30 <= p <= 37) or (90 <= p <= 97):
            state['fg_mode'] = 'standard'
            state['fg'] = p
        elif p == 39:
            state['fg_mode'] = None
            state['fg'] = None
        elif p == 38 and i + 2 < len(params) and params[i + 1] == 5:
            state['fg_mode'] = '256'
            state['fg'] = params[i + 2]
            i += 2
        elif (40 <= p <= 47) or (100 <= p <= 107):
            state['bg_mode'] = 'standard'
            state['bg'] = p
        elif p == 49:
            state['bg_mode'] = None
            state['bg'] = None
        elif p == 48 and i + 2 < len(params) and params[i + 1] == 5:
            state['bg_mode'] = '256'
            state['bg'] = params[i + 2]
            i += 2
        i += 1
    return state

def diff_sgr(new_state, old_state):
    diff = []
    if new_state['bold'] != old_state['bold']:
        diff.append(1 if new_state['bold'] else 22)
    if new_state['underline'] != old_state['underline']:
        diff.append(4 if new_state['underline'] else 24)

    # Foreground
    if (new_state['fg_mode'], new_state['fg']) != (old_state['fg_mode'], old_state['fg']):
        if new_state['fg_mode'] == 'standard':
            diff.append(new_state['fg'])
        elif new_state['fg_mode'] == '256':
            diff.extend([38, 5, new_state['fg']])
        elif new_state['fg'] is None:
            diff.append(39)

    # Background
    if (new_state['bg_mode'], new_state['bg']) != (old_state['bg_mode'], old_state['bg']):
        if new_state['bg_mode'] == 'standard':
            diff.append(new_state['bg'])
        elif new_state['bg_mode'] == '256':
            diff.extend([48, 5, new_state['bg']])
        elif new_state['bg'] is None:
            diff.append(49)

    return diff

def simplify_ansi(text):
    matches = list(ansi_pattern.finditer(text))
    output = []
    current_pos = 0
    current_state = {
        'bold': False,
        'underline': False,
        'fg_mode': None,
        'fg': None,
        'bg_mode': None,
        'bg': None,
    }

    i = 0
    while i < len(matches):
        match = matches[i]
        start, end = match.span()
        raw_params = match.group(1)
        params = [int(p) if p else 0 for p in raw_params.split(';')]

        output.append(text[current_pos:start])

        if params == [0]:
            old_state = current_state.copy()
            if i + 1 < len(matches):
                next_match = matches[i + 1]
                next_params = [int(p) if p else 0 for p in next_match.group(1).split(';')]
                next_state = parse_sgr(next_params)
                if all(
                    next_state[k] == old_state[k]
                    for k in next_state if next_state[k] is not None
                ):
                    diff = diff_sgr(next_state, current_state)
                    if diff:
                        output.append(f'\x1b[{";".join(map(str, diff))}m')
                        current_state = next_state
                    i += 2
                    current_pos = matches[i - 1].end()
                    continue

        new_state = parse_sgr(params)
        diff = diff_sgr(new_state, current_state)
        if diff:
            output.append(f'\x1b[{";".join(map(str, diff))}m')
        elif params == [0]:
            output.append('\x1b[0m')
        current_state = new_state
        current_pos = end
        i += 1

    output.append(text[current_pos:])
    return insert_final_reset(''.join(output))

def insert_final_reset(text):
    # Remove any trailing resets
    text = re.sub(r'(\x1b\[0m)+$', '', text)

    # Append one reset before final newline(s)
    newline_match = re.search(r'(\n+)$', text)
    if newline_match:
        pos = newline_match.start()
        return text[:pos] + '\x1b[0m' + text[pos:]
    else:
        return text + '\x1b[0m'

def simplify_to_copy(filepath, suffix=".simplified"):
    path = Path(filepath)
    with path.open('r', encoding='utf-8', errors='replace') as f:
        original = f.read()

    simplified = simplify_ansi(original)

    outpath = path.with_name(path.stem + suffix + path.suffix)
    with outpath.open('w', encoding='utf-8') as f:
        f.write(simplified)

    print(f"✓ Wrote: {outpath}")

def main():
    parser = argparse.ArgumentParser(description="Simplify ANSI escape codes and write to copies.")
    parser.add_argument('files', metavar='FILE', nargs='+', help='Input file(s)')
    parser.add_argument('--suffix', default='.simplified', help='Suffix for output filenames')
    args = parser.parse_args()

    for filename in args.files:
        simplify_to_copy(filename, suffix=args.suffix)

if __name__ == '__main__':
    main()
