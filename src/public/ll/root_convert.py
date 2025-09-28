#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
将 `ll_div.txt` 和 `ll_map.txt` 中的复杂字根（含别名）根据 `PUAtoalias.txt`
转换为对应的 PUA 简单字根字符。

输出：
- 生成同目录下的 `ll_div.real.txt` 与 `ll_map.real.txt`，不改动原始文件。

规则概述：
1) 从 `PUAtoalias.txt` 构建“别名（文本） -> PUA字符”的映射。

2) 转换 `ll_div.txt`：
   - 每行形如：字\t构形串
   - 构形串中：
       a. 花括号包裹的多字别名：如 `{在字框}` 作为整体处理
       b. 其他为单字逐字处理
   - 处理顺序：
       i. 若 token 命中 PUA 表（别名→PUA），替换为对应的 PUA 字符
       ii. 若无法映射，保持原样（含花括号）
   - 输出时：成功映射者不再保留花括号；未映射者保留原样。

3) 转换 `ll_map.txt`：
   - 将该行右侧所有别名用 PUA 表替换为对应 PUA 字符；未命中则保留原文。
   - 去重后按出现顺序保留。

用法：
  直接运行该脚本即可在同目录生成简化文件。
"""

from __future__ import annotations

import os
from typing import Dict, List, Tuple


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_PUA = os.path.join(THIS_DIR, "PUAtoalias.txt")
PATH_MAP = os.path.join(THIS_DIR, "ll_map.txt")
PATH_DIV = os.path.join(THIS_DIR, "ll_div.txt")

OUT_MAP = os.path.join(THIS_DIR, "ll_map.real.txt")
OUT_DIV = os.path.join(THIS_DIR, "ll_div.real.txt")


def read_lines(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]


def write_lines(path: str, lines: List[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def build_pua_to_alias(pua_lines: List[str]) -> Dict[str, str]:
    """根据用户说明：第一列为简单字根，第二列为复杂字根/别名。
    构建映射：复杂(别名) -> 简单。
    """
    mapping: Dict[str, str] = {}
    for line in pua_lines:
        if not line or "\t" not in line:
            continue
        real, complex_alias = line.split("\t", 1)
        real = real.strip()
        complex_alias = complex_alias.strip()
        if real and complex_alias:
            mapping[complex_alias] = real
    return mapping


# 取消从 ll_map.txt 推导“规范形”的逻辑，需求仅基于 PUA 映射


def tokenize_div_rhs(rhs: str) -> List[Tuple[str, bool]]:
    """将 ll_div 右侧构形串切分为 token。
    返回列表：[(token, is_braced)]，其中 is_braced 表示该 token 是否来自 `{...}`。
    """
    tokens: List[Tuple[str, bool]] = []
    i = 0
    n = len(rhs)
    while i < n:
        ch = rhs[i]
        if ch == "{":
            j = i + 1
            # 寻找匹配的 '}'
            while j < n and rhs[j] != "}":
                j += 1
            if j < n and rhs[j] == "}":
                inner = rhs[i + 1 : j]
                tokens.append((inner, True))
                i = j + 1
            else:
                # 没有闭合，按单字处理 '{'
                tokens.append((ch, False))
                i += 1
        else:
            tokens.append((ch, False))
            i += 1
    return tokens


def map_one_token(token: str, is_braced: bool, pua_to_alias: Dict[str, str]) -> str:
    original = token
    # 先用 PUA 别名表进行“别名 -> PUA”的替换（无论是否花括号）
    if token in pua_to_alias:
        token = pua_to_alias[token]
        # 命中映射：直接返回替换结果（不保留花括号）
        return token

    # 未命中映射：
    #    - 若是 braced，保留原样（含花括号），以免信息丢失；
    #    - 若不是 braced，返回原字。
    if is_braced:
        return "{" + original + "}"
    return original


def convert_ll_div(div_lines: List[str], pua_to_alias: Dict[str, str]) -> List[str]:
    out: List[str] = []
    for line in div_lines:
        if not line or "\t" not in line:
            out.append(line)
            continue
        left, rhs = line.split("\t", 1)
        tokens = tokenize_div_rhs(rhs)
        mapped_parts: List[str] = []
        for tok, is_braced in tokens:
            mapped_parts.append(map_one_token(tok, is_braced, pua_to_alias))
        out.append(f"{left}\t{''.join(mapped_parts)}")
    return out


def convert_ll_map(map_lines: List[str], pua_to_alias: Dict[str, str]) -> List[str]:
    out: List[str] = []
    for line in map_lines:
        if not line or "\t" not in line:
            out.append(line)
            continue
        code, rhs = line.split("\t", 1)
        aliases = [t for t in rhs.strip().split(" ") if t]
        simplified: List[str] = []
        for alias in aliases:
            a = pua_to_alias.get(alias, alias)
            simplified.append(a)

        # 去重但保持相对顺序，且尽量只保留一个规范形
        seen = set()
        uniq: List[str] = []
        for x in simplified:
            if x not in seen:
                seen.add(x)
                uniq.append(x)

        # 若存在多个，确保第一个是最终规范形（即 uniq[0]）
        out.append(f"{code}\t{' '.join(uniq)}")
    return out


def main() -> None:
    # 读取三份源文件
    pua_lines = read_lines(PATH_PUA)
    map_lines = read_lines(PATH_MAP)
    div_lines = read_lines(PATH_DIV)

    # 构建映射（别名 -> PUA）
    pua_to_alias = build_pua_to_alias(pua_lines)

    # 转换
    new_div = convert_ll_div(div_lines, pua_to_alias)
    new_map = convert_ll_map(map_lines, pua_to_alias)

    # 写入结果
    write_lines(OUT_DIV, new_div)
    write_lines(OUT_MAP, new_map)

    print("完成：已生成 ll_div.real.txt 与 ll_map.real.txt")


if __name__ == "__main__":
    main()


