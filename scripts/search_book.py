#!/usr/bin/env python3
"""Read-only, offline search over the bundled book. Python 3.9+, stdlib only."""
import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / 'references'
HEADING = re.compile(r'^###\s+(\d+)[.．、]\s*(.+)$')


def manifest():
    data = json.loads((REF / 'snapshot.json').read_text(encoding='utf-8'))
    if not re.fullmatch(r'[0-9a-f]{40}', data['commit']):
        raise ValueError('快照版本号无效。')
    return data


def verified_text(path, data):
    relative = path.relative_to(REF).as_posix()
    expected = data['files'].get(relative)
    if expected is None:
        raise ValueError(f'快照清单未记录：{relative}')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f'原文校验失败：{relative}；请恢复快照或完成版本更新。')
    return raw.decode('utf-8-sig')


def parse_chapter(path, data):
    text = verified_text(path, data)
    chapter = int(path.name.split('-')[0])
    lines = text.splitlines(keepends=True)
    heads = []
    fence = None
    for number, line in enumerate(lines):
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            kind = marker.group(1)[0]
            if fence is None:
                fence = kind
            elif fence == kind:
                fence = None
            continue
        if fence:
            continue
        if line.startswith('## ') or line.startswith('### '):
            heads.append((number, HEADING.match(line.strip())))
    numbered = [(n, m) for n, m in heads if m]
    preamble = ''.join(lines[:numbered[0][0]]) if numbered else text
    entries = []
    for i, (start, match) in enumerate(heads):
        if not match:
            continue
        end = heads[i + 1][0] if i + 1 < len(heads) else len(lines)
        entry = int(match.group(1))
        relative = path.relative_to(REF).as_posix()
        entries.append({
            'id': f'{chapter:02d}:{entry}', 'chapter': chapter,
            'title': match.group(2), 'path': relative,
            'line_start': start + 1, 'line_end': end,
            'url': f"{data['repository']}/blob/{data['commit']}/{quote(relative, safe='/')}#L{start + 1}-L{end}",
            'text': ''.join(lines[start:end]).rstrip(),
            'preamble': preamble.rstrip(),
        })
    return entries


def all_entries(data, chapter=None):
    paths = sorted((REF / 'book').glob('*.md'))
    if not paths:
        raise ValueError('正文快照缺失。')
    if chapter is not None:
        paths = [p for p in paths if int(p.name.split('-')[0]) == chapter]
        if not paths:
            raise ValueError(f'没有第 {chapter} 节。')
    result = [entry for path in paths for entry in parse_chapter(path, data)]
    ids = [e['id'] for e in result]
    if len(ids) != len(set(ids)):
        raise ValueError('存在重复节号/条号，请修复索引后再引用。')
    return result


def normalize(text):
    return unicodedata.normalize('NFKC', text).casefold()


def search(entries, terms, require_all=False):
    terms = list(dict.fromkeys(normalize(t.strip()) for t in terms if t.strip()))
    if not terms:
        raise ValueError('请输入至少一个非空关键词。')
    scored = []
    for entry in entries:
        body, title = normalize(entry['text']), normalize(entry['title'])
        count = sum(term in body for term in terms)
        if count == 0 or (require_all and count != len(terms)):
            continue
        score = (count, sum(term in title for term in terms))
        scored.append((score, entry))
    scored.sort(key=lambda pair: (-pair[0][0], -pair[0][1], pair[1]['chapter'], pair[1]['line_start']))
    return [entry for _, entry in scored]


def public_entry(entry):
    return {key: value for key, value in entry.items() if key not in ('text', 'preamble')}


def check(data):
    errors = []
    for name, expected in data['files'].items():
        path = (REF / name).resolve()
        if not path.is_relative_to(REF.resolve()):
            errors.append(f'清单路径越界：{name}')
            continue
        if not path.is_file():
            errors.append(f'文件缺失：{name}')
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f'内容变化：{name}')
    if errors:
        return {'ok': False, 'errors': errors}
    entries = all_entries(data)
    return {'ok': True, 'commit': data['commit'], 'snapshot_date': data['snapshot_date'],
            'source_files': len(data['files']), 'chapters': len({e['chapter'] for e in entries}),
            'entries': len(entries)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    query = commands.add_parser('search', help='查条目位置，不替代阅读全文')
    query.add_argument('terms', nargs='+', help='用空格分开同义词；默认任一词命中')
    query.add_argument('--chapter', type=int)
    query.add_argument('--limit', type=int, default=8)
    query.add_argument('--all', action='store_true', help='要求全部关键词命中')
    read = commands.add_parser('read', help='读条目全文和章节说明')
    read.add_argument('ids', nargs='+', help='例如 08:16 23:8')
    commands.add_parser('check', help='验证全部原文哈希和条目唯一性')
    args = parser.parse_args(argv)
    try:
        data = manifest()
        if args.command == 'check':
            result = check(data)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result['ok'] else 1
        if args.command == 'search':
            if not 1 <= args.limit <= 50:
                raise ValueError('--limit 必须为 1 到 50。')
            matches = search(all_entries(data, args.chapter), args.terms, args.all)
            print(json.dumps({'snapshot_date': data['snapshot_date'], 'total_matches': len(matches),
                              'note': '检索顺序是文字相关性，不是建议优先级。引用前用 read 读完整条目。',
                              'results': [public_entry(e) for e in matches[:args.limit]]},
                             ensure_ascii=False, indent=2))
            return 0
        wanted = []
        for value in args.ids:
            if not re.fullmatch(r'\d{1,2}:\d+', value):
                raise ValueError(f'条目标识格式错误：{value}；应为 08:16。')
            chapter, number = map(int, value.split(':'))
            wanted.append(f'{chapter:02d}:{number}')
        entries = {e['id']: e for e in all_entries(data)}
        missing = [value for value in wanted if value not in entries]
        if missing:
            raise ValueError('未找到条目：' + ', '.join(missing))
        print(f"快照：{data['snapshot_date']}；版本：{data['commit']}\n")
        seen = set()
        for value in wanted:
            entry = entries[value]
            if entry['chapter'] not in seen:
                print('【章节说明】\n' + entry['preamble'] + '\n')
                seen.add(entry['chapter'])
            print(f"【{value}】{entry['url']}\n{entry['text']}\n")
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f'错误：{exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
