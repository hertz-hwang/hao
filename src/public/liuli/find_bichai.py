#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
找出琉璃的「必拆字」。

必拆字的定义：
从 ll_div.txt 拆分表前 6000 行中筛选：
  1. 单根字（字根字），且在码表 琉璃_三定.txt 中无简码（没有码长小于 3 的条目）。
  2. 二根字，且在码表 琉璃_三定.txt 中无简码。同时输出其末字根。
二根字按末字根去重，同一末字根只保留字频最高的代表字。

输出 bichai.json，供训练页面（TrainHanzi）加载，格式与 chaifen.json 一致：
  [{"name": 字, "comp": "根1 根2", "key": 全码, "endRoot": 末字根?}, ...]
拆分中的花括号别名（如 {在字框}）会依据 PUAtoalias.txt 替换成对应 PUA 字符。
"""

import json
import os
import re


TOKEN_RE = re.compile(r'\{[^{}]+\}|.')


def load_pua_alias(path: str) -> dict[str, str]:
    """读取 PUAtoalias.txt：第一列是 PUA 字符，第二列是别名。
    返回 {别名: PUA 字符}。"""
    mapping: dict[str, str] = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line or '\t' not in line:
                continue
            pua, alias = line.split('\t', 1)
            pua = pua.strip()
            alias = alias.strip()
            if pua and alias:
                mapping[alias] = pua
    return mapping


def parse_roots(comp: str, alias_to_pua: dict[str, str]):
    """把 拆分串 解析成字根 token 列表，并把 {别名} 换成 PUA 字符。
    - "白勹丶"     -> ["白", "勹", "丶"]
    - "{在字框}土" -> ["", "土"]
    未命中的 {别名} 保留原样（带花括号）。
    """
    roots: list[str] = []
    for tok in TOKEN_RE.findall(comp):
        if tok.startswith('{') and tok.endswith('}'):
            inner = tok[1:-1]
            roots.append(alias_to_pua.get(inner, tok))
        else:
            roots.append(tok)
    return roots


def is_hard_root(root: str) -> bool:
    """判断一个字根是否「难拆」——用户很少直接见到的字形：
    - 仍保留花括号（别名未解析）
    - PUA 区字符 U+E000+
    - CJK Ext-A 区 U+3400–U+4DBF
    - SIP/Ext-B 及以上 U+20000+
    """
    if not root:
        return False
    if root.startswith('{') and root.endswith('}'):
        return True
    if len(root) == 1:
        cp = ord(root)
        if cp >= 0xE000:
            return True
        if 0x3400 <= cp <= 0x4DBF:
            return True
        return False
    # 多码位（代理对或组合）保守当作难拆
    return True


def load_code_table(path: str):
    """读取码表：返回 {字: [所有编码]} 和 {字: 最短码长}。"""
    codes: dict[str, list[str]] = {}
    for line in open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line or '\t' not in line:
            continue
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        char, code = parts[0], parts[1]
        if not char or not code:
            continue
        codes.setdefault(char, []).append(code)
    min_len = {c: min(len(k) for k in ks) for c, ks in codes.items()}
    return codes, min_len


def load_div(path: str, limit: int):
    """读取拆分表前 limit 行，返回 [(char, comp), ...]。"""
    result = []
    with open(path, encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            line = line.rstrip('\n')
            if not line or '\t' not in line:
                continue
            parts = line.split('\t', 1)
            if len(parts) != 2:
                continue
            result.append((parts[0], parts[1]))
    return result


def full_code_of(char: str, codes: dict[str, list[str]]) -> str:
    """返回该字最长的编码（通常就是全码，三位）。找不到返回空串。"""
    entries = codes.get(char)
    if not entries:
        return ''
    return max(entries, key=len)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    div_path = os.path.join(script_dir, 'll_div.txt')
    code_path = os.path.join(script_dir, '琉璃_三定.txt')
    pua_path = os.path.join(script_dir, 'PUAtoalias.txt')
    out_json = os.path.join(script_dir, 'bichai.json')
    out_tsv = os.path.join(script_dir, 'bichai.txt')

    print(f'加载 PUA 别名表：{pua_path}')
    alias_to_pua = load_pua_alias(pua_path)
    print(f'  共 {len(alias_to_pua)} 条别名映射。')

    print(f'加载码表：{code_path}')
    codes, min_code_len = load_code_table(code_path)
    print(f'  码表覆盖 {len(codes)} 个字。')

    print(f'加载拆分表（前 6000 行）：{div_path}')
    entries = load_div(div_path, 6000)
    print(f'  读取 {len(entries)} 行。')

    single_root = []  # 单根字
    two_root = []    # 二根字（按末字根去重后）
    hard_root = []   # 难拆字（含生僻/别名根，不受简码过滤和末字根去重影响）
    seen_end_root: set[str] = set()
    collected: set[str] = set()  # 已经放进任一类别的字，避免难拆类重复收
    skipped_no_code = []  # 拆分有但码表没有的字
    dedup_skipped = 0

    def build_item(char: str, kind: str, roots: list[str], key: str) -> dict:
        """拼 bichai.json 单条记录。kind ∈ {'single', 'two'}。"""
        comp_display = ' '.join(roots)
        if kind == 'single':
            root_keys = [{'zigen': roots[0], 'key': key}]
        else:
            root_keys = [
                {'zigen': roots[0], 'key': key[0] if len(key) >= 1 else ''},
                {'zigen': roots[1], 'key': key[1:] if len(key) >= 2 else ''},
            ]
        return {
            'name': char,
            'comp': comp_display,
            'key': key,
            'rootKeys': root_keys,
        }

    for char, comp in entries:
        roots = parse_roots(comp, alias_to_pua)
        if len(roots) == 1:
            kind = 'single'
        elif len(roots) == 2:
            kind = 'two'
        else:
            continue

        if char not in min_code_len:
            skipped_no_code.append(char)
            continue

        key = full_code_of(char, codes)
        has_hard = any(is_hard_root(r) for r in roots)

        # 1) 正常路径：无简码才纳入
        if min_code_len[char] >= 3:
            item = build_item(char, kind, roots, key)
            if kind == 'single':
                single_root.append(item)
                collected.add(char)
            else:
                end_root = roots[-1]
                # 二根字按末字根去重；末字根是难拆根的不去重，它的首根难度在别处
                if end_root in seen_end_root and not is_hard_root(end_root):
                    dedup_skipped += 1
                else:
                    seen_end_root.add(end_root)
                    item['endRoot'] = end_root
                    two_root.append(item)
                    collected.add(char)
            continue

        # 2) 有简码但拆分里含难拆根：也收，归入「难拆」类
        if has_hard and char not in collected:
            item = build_item(char, kind, roots, key)
            if kind == 'two':
                item['endRoot'] = roots[-1]
            item['hard'] = True
            hard_root.append(item)
            collected.add(char)

    print(f'  单根字必拆：{len(single_root)}')
    print(f'  二根字必拆（按末字根去重）：{len(two_root)}，去重跳过 {dedup_skipped} 条')
    print(f'  难拆字（含生僻/别名根，不受简码过滤）：{len(hard_root)}')
    if skipped_no_code:
        print(f'  跳过（码表无此字）：{len(skipped_no_code)}，前 10 个：{skipped_no_code[:10]}')

    result = single_root + two_root + hard_root

    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'写入 {out_json}（{len(result)} 条）。')

    with open(out_tsv, 'w', encoding='utf-8') as f:
        f.write('字\t拆分\t全码\t类型\t末字根\n')
        for it in single_root:
            f.write(f"{it['name']}\t{it['comp']}\t{it['key']}\t单根\t\n")
        for it in two_root:
            f.write(f"{it['name']}\t{it['comp']}\t{it['key']}\t二根\t{it['endRoot']}\n")
        for it in hard_root:
            end = it.get('endRoot', '')
            f.write(f"{it['name']}\t{it['comp']}\t{it['key']}\t难拆\t{end}\n")
    print(f'写入 {out_tsv}。')


if __name__ == '__main__':
    main()
