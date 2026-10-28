import sys
import tempfile
from pathlib import Path

if __package__:
    from .short_packet import load_inputs
    from .short_render import draft, split_field
else:
    from short_packet import load_inputs
    from short_render import draft, split_field


def filled_packet(folder):
    plan, files, saved, hunks = load_inputs(folder)
    lines = (folder / 'packet.md').read_text(encoding='utf-8').split('\n')
    # Cases: absent, exactly 1 whole line, repeated, or padded placeholders.
    markers = ('@@split-field@@', '@@split-draft@@')
    if any(lines.count(marker) != 1 for marker in markers):
        raise ValueError('expected 1 whole line for each split placeholder')
    opening = (f"This PR is {saved['counted_total']} counted lines; the cap is 300. "
               'It was reviewed over the cap, on request.')
    replacements = dict(zip(markers, [split_field(plan, files, hunks), draft(plan, files, hunks, opening)]))
    packet = '\n'.join(replacements.get(line, line) for line in lines)
    if any(phrase in packet for phrase in ['not reviewed past size', 'safe to merge', 'not checked: PR over the cap']):
        raise ValueError('rendered packet contains forbidden text')
    return packet


def write_packet(path, text):
    # A failed write or replace must leave the original bytes intact.
    output = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                         dir=path.parent, delete=False)
    staged = Path(output.name)
    try:
        with output:
            output.write(text)
        staged.replace(path)
    finally:
        staged.unlink(missing_ok=True)


def main(args):
    try:
        if len(args) != 1 or not Path(args[0]).is_dir():
            raise ValueError('expected a packet folder')
        folder = Path(args[0])
        packet = filled_packet(folder)
        write_packet(folder / 'packet.md', packet)
        print('override_parts: filled')
        return 0
    except (ValueError, OSError, UnicodeError, KeyError, TypeError, AttributeError) as error:
        print('override_parts: ' + ' '.join(str(error).splitlines()), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1:]))
