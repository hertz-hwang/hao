#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 chaifen.json 文件
通过 ll_div.real.txt 和 ll_fullcode.txt 来生成 chaifen.json
"""

import json
import os

def load_ll_div_data(file_path):
    """加载 ll_div.real.txt 数据"""
    data = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '\t' in line:
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    char, comp = parts
                    data[char] = comp
    return data

def load_code_table_data(file_path):
    """加载 ll_fullcode.txt 数据"""
    data = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    char, key = parts[0], parts[1]
                    data[char] = key
    return data

def generate_chaifen_json():
    """生成 chaifen.json 文件"""
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 文件路径
    ll_div_file = os.path.join(script_dir, 'll_div.real.txt')
    code_table_file = os.path.join(script_dir, 'll_fullcode.txt')
    output_file = os.path.join(script_dir, 'chaifen.json')
    
    print(f"正在加载 {ll_div_file}...")
    ll_div_data = load_ll_div_data(ll_div_file)
    print(f"加载了 {len(ll_div_data)} 个汉字的部件数据")
    
    print(f"正在加载 {code_table_file}...")
    code_table_data = load_code_table_data(code_table_file)
    print(f"加载了 {len(code_table_data)} 个汉字的键码数据")
    
    # 合并数据
    result = []
    processed_chars = set()
    
    # 遍历 ll_div.real.txt 中的字符
    for char, comp in ll_div_data.items():
        if char in code_table_data and char not in processed_chars:
            key = code_table_data[char]
            result.append({
                "name": char,
                "comp": comp,
                "key": key
            })
            processed_chars.add(char)
    
    # 按字符排序（可选）
    result.sort(key=lambda x: x['name'])
    
    print(f"生成了 {len(result)} 个字符的数据")
    
    # 写入 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    
    print(f"已生成 {output_file}")
    return len(result)

if __name__ == "__main__":
    try:
        count = generate_chaifen_json()
        print(f"成功生成 chaifen.json，包含 {count} 个字符")
    except Exception as e:
        print(f"生成失败: {e}")
        import traceback
        traceback.print_exc()
