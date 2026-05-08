#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
找出琉璃的「必拆字」。

必拆字的定义：
从 ll_div.txt 拆分表前 6000 行中筛选：
  1. 二根字，且在码表 琉璃_三定.txt 中无简码。同时输出其末字根。
     按末字根去重，同一末字根只保留字频最高的代表字。
     二根字全码 = 首根大码 + 末根大码 + 末根小码，练到了末字根的「大码+小码」。
  2. 单根字（字根字），且在码表 琉璃_三定.txt 中无简码：
     - 若其根能在 (1) 的末字根集合中找到覆盖，说明已经有二根字把该根
       的「大码+小码」练到位了，这个单根字就从必拆字里删掉。
     - 找不到覆盖的单根字保留下来，继续单独练。
  3. 有简码但拆分里含「难拆根」的字：作为补充一并练习。

输出 bichai.json，供训练页面（TrainHanzi）加载，格式与 chaifen.json 一致：
  [{"name": 字, "comp": "根1 根2", "key": 全码, "endRoot": 末字根?}, ...]
拆分中的花括号别名（如 {在字框}）会依据 PUAtoalias.txt 替换成对应 PUA 字符。
"""

import json
import os
import re


TOKEN_RE = re.compile(r'\{[^{}]+\}|.')


def load_root_code(path: str, alias_to_pua: dict[str, str]) -> dict[str, str]:
    """读取 ll_map.txt：第一列是字根编码（大码+小码），第二列是空格分隔的字根列表。
    返回 {字根: 编码}，同时把别名形式（如「成三」）同时映射到 PUA 字符上。
    一个字根若出现在多行（极少见），只保留首次命中。
    """
    root_code: dict[str, str] = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line or '\t' not in line:
                continue
            code, roots_str = line.split('\t', 1)
            code = code.strip()
            if not code:
                continue
            for r in roots_str.split():
                if not r or r in root_code:
                    continue
                root_code[r] = code
                # 别名 → 对应 PUA 字符也登记一份，方便按 PUA 查表
                pua = alias_to_pua.get(r)
                if pua and pua not in root_code:
                    root_code[pua] = code
                # 花括号别名形式也登记（解析失败时 token 是 {xxx}）
                braced = '{' + r + '}'
                if braced not in root_code:
                    root_code[braced] = code
    return root_code



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


def alt_codes_of(char: str, codes: dict[str, list[str]], key: str) -> list[str]:
    """返回该字所有比全码短的编码（即各级简码），去重并按码长升序。"""
    entries = codes.get(char, [])
    alts = sorted({c for c in entries if c and c != key and len(c) < len(key)}, key=len)
    return alts


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    div_path = os.path.join(script_dir, 'll_div.txt')
    code_path = os.path.join(script_dir, '琉璃_三定.txt')
    pua_path = os.path.join(script_dir, 'PUAtoalias.txt')
    map_path = os.path.join(script_dir, 'll_map.txt')
    out_json = os.path.join(script_dir, 'bichai.json')
    out_tsv = os.path.join(script_dir, 'bichai.txt')

    print(f'加载 PUA 别名表：{pua_path}')
    alias_to_pua = load_pua_alias(pua_path)
    print(f'  共 {len(alias_to_pua)} 条别名映射。')

    print(f'加载字根编码表：{map_path}')
    root_code = load_root_code(map_path, alias_to_pua)
    print(f'  共 {len(root_code)} 条字根→编码映射。')

    print(f'加载码表：{code_path}')
    codes, min_code_len = load_code_table(code_path)
    print(f'  码表覆盖 {len(codes)} 个字。')

    print(f'加载拆分表（前 6000 行）：{div_path}')
    entries = load_div(div_path, 6000)
    print(f'  读取 {len(entries)} 行。')

    single_root_candidates = []  # 单根字候选：(char, roots, key)，先全收，等二根字跑完再过滤
    two_root = []    # 二根字（按末字根去重后）
    hard_root = []   # 难拆字（含生僻/别名根，不受简码过滤和末字根去重影响）
    seen_end_root: set[str] = set()
    covered_end_roots: set[str] = set()  # 被二根字练到的末字根，用来替代单根字
    collected: set[str] = set()  # 已经放进任一类别的字，避免难拆类重复收
    skipped_no_code = []  # 拆分有但码表没有的字
    dedup_skipped = 0

    def build_item(char: str, kind: str, roots: list[str], key: str) -> dict:
        """拼 bichai.json 单条记录。kind ∈ {'single', 'two'}。
        rootKeys[*].key 存字根的完整编码（通常 2 位：大码+小码），
        方便提示里直接显示字根自己的完整码，而不是它在当前字里被用到的那段。
        altKeys 存该字的所有简码（如'成'有简码'ag'），用户敲简码+空格也算对。"""
        comp_display = ' '.join(roots)
        root_keys = [{'zigen': r, 'key': root_code.get(r, '')} for r in roots]
        item = {
            'name': char,
            'comp': comp_display,
            'key': key,
            'rootKeys': root_keys,
        }
        alts = alt_codes_of(char, codes, key)
        if alts:
            item['altKeys'] = alts
        return item

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
            if kind == 'single':
                # 先收着，等二根字收集完再根据末字根覆盖情况过滤
                single_root_candidates.append((char, roots, key))
            else:
                end_root = roots[-1]
                # 二根字按末字根去重；但以下两种情况豁免去重：
                # - 末字根本身是难拆根（末根本就难练，不因代表字已存在而跳过）
                # - 首根是难拆根（这字练的是「难拆首根大码 + 末根编码」的组合，
                #   同末字根的普通代表字替代不了）
                has_hard_here = any(is_hard_root(r) for r in roots)
                if end_root in seen_end_root and not has_hard_here:
                    dedup_skipped += 1
                else:
                    seen_end_root.add(end_root)
                    item = build_item(char, kind, roots, key)
                    item['endRoot'] = end_root
                    if has_hard_here:
                        item['hard'] = True
                    two_root.append(item)
                    collected.add(char)
                    covered_end_roots.add(end_root)
            continue

        # 2) 有简码但拆分里含难拆根：也收，归入「难拆」类
        if has_hard and char not in collected:
            item = build_item(char, kind, roots, key)
            if kind == 'two':
                item['endRoot'] = roots[-1]
                # 难拆二根字的末字根也能替代同根的单根字
                covered_end_roots.add(roots[-1])
            item['hard'] = True
            hard_root.append(item)
            collected.add(char)

    # 二根字全都定了，再回头过滤单根字：根已被二根字末字根覆盖的就删
    single_root = []
    single_replaced = []  # 被替代的单根字，留作日志
    for char, roots, key in single_root_candidates:
        root = roots[0]
        if root in covered_end_roots:
            single_replaced.append(char)
            continue
        single_root.append(build_item(char, 'single', roots, key))
        collected.add(char)

    print(f'  单根字必拆：{len(single_root)}（另有 {len(single_replaced)} 个被二根字替代）')
    if single_replaced:
        print(f'    被替代示例（前 20）：{single_replaced[:20]}')
    if single_root:
        print(f'    保留的单根字：{[it["name"] for it in single_root]}')
    print(f'  二根字必拆（按末字根去重）：{len(two_root)}，去重跳过 {dedup_skipped} 条')
    print(f'  难拆字（含生僻/别名根，不受简码过滤）：{len(hard_root)}')
    if skipped_no_code:
        print(f'  跳过（码表无此字）：{len(skipped_no_code)}，前 10 个：{skipped_no_code[:10]}')

    # 混合聚类：
    # - 首根难拆（如 {温字框}、PUA 根）的字，聚焦点在首根 → 按首根聚
    # - 其余字（含普通二根字、单根字）选入目的是练末字根 → 按末字根聚
    # 这样 {温字框}+业/土/比/皿 会连成一片；木/亲、榇/棋/梁 会按末根聚在一起。
    def sort_key(item: dict) -> tuple:
        roots = item['comp'].split(' ')
        first = roots[0]
        last = roots[-1]
        if is_hard_root(first):
            return (0, first, last)           # tier 0：首根难拆，按首根聚
        return (1, last, first)               # tier 1：普通字，按末字根聚

    kinded: list[tuple[str, dict]] = (
        [('单根', it) for it in single_root]
        + [('二根', it) for it in two_root]
        + [('难拆', it) for it in hard_root]
    )
    kinded.sort(key=lambda x: sort_key(x[1]))
    result = [it for _, it in kinded]

    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'写入 {out_json}（{len(result)} 条）。')

    with open(out_tsv, 'w', encoding='utf-8') as f:
        f.write('字\t拆分\t全码\t类型\t末字根\n')
        for kind, it in kinded:
            end = it.get('endRoot', '')
            f.write(f"{it['name']}\t{it['comp']}\t{it['key']}\t{kind}\t{end}\n")
    print(f'写入 {out_tsv}。')


if __name__ == '__main__':
    main()
