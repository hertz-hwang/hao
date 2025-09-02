import json
import re
from collections import defaultdict

def read_ll_map(file_path):
    """读取ll_map.txt文件，返回字根到编码的映射"""
    ll_map = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            code, zigen = line.split('\t')
            # 将编码转换为小写
            code = code.lower()
            if zigen not in ll_map:
                ll_map[zigen] = {'key': code[0], 'secondary': code[1:] if len(code) > 1 else None}
    return ll_map

def extract_components(line):
    """从一行中提取拆分部件，兼容两种格式：
    1) "字<TAB>部件(以空格分隔)"
    2) "... [部件列表] ..."（若无空格，则逐字符拆分）
    """
    # 新格式：汉字与部件以制表符分隔，部件以空格分隔
    if '\t' in line:
        try:
            _char, components_str = line.split('\t', 1)
        except ValueError:
            return []
        components = [c for c in components_str.strip().split() if c]
        return components

    # 兼容旧格式：方括号包裹
    if '[' in line and ']' in line:
        parts = line.split('[', 1)[1].split(']', 1)[0]
        tokens = [t for t in parts.strip().split() if t]
        if tokens:
            return tokens
        return list(parts.strip())

    return []

def read_ll_div(file_path):
    """读取ll_div.txt文件，返回字根到相关汉字的映射和字根使用频率"""
    zigen_to_chars = defaultdict(list)  # 改为list以保持顺序
    zigen_frequency = defaultdict(int)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # 获取汉字和它的部件
            if '\t' in line:
                char = line.split('\t', 1)[0]
            else:
                char = line.split()[0]
            components = extract_components(line)
            
            # 将汉字添加到每个部件的相关字列表中，最多10个
            for component in components:
                if component:  # 忽略空部件
                    if len(zigen_to_chars[component]) < 10:  # 只保留前10个
                        zigen_to_chars[component].append(char)
                    zigen_frequency[component] += 1
    
    # 将列表转换为字符串
    zigen_to_chars = {k: ''.join(v) for k, v in zigen_to_chars.items()}
    
    # 打印调试信息
    print(f"读取到的字根数量: {len(zigen_to_chars)}")
    print("前10个字根及其相关字示例:")
    for i, (zigen, chars) in enumerate(list(zigen_to_chars.items())[:10]):
        print(f"{zigen}: {chars}")
            
    return zigen_to_chars, zigen_frequency

def generate_zigen_json(ll_map, zigen_to_chars, zigen_frequency):
    """生成zigen.json格式的数据，按字根使用频率排序"""
    result = []
    for zigen, code_info in ll_map.items():
        # 获取相关汉字
        related_chars = zigen_to_chars.get(zigen, '')
        # 分组字根增强：当 name 含多个子字根（以空格分隔）时，
        # 优先从每个子字根各取若干例字，按分组内顺序拼接，保证每个子字根都出现示例。
        if ' ' in zigen:
            sub_components = [t for t in zigen.split(' ') if t]
            collected = []
            seen = set()
            # 每个子字根取前 N 个例字
            examples_per_comp = 3
            for comp in sub_components:
                chars = zigen_to_chars.get(comp, '')
                if not chars:
                    continue
                take = chars[:examples_per_comp]
                for ch in take:
                    if ch not in seen:
                        collected.append(ch)
                        seen.add(ch)
            if collected:
                # 控制总长度，避免过长
                related_chars = ''.join(collected[:15])
        
        item = {
            'name': zigen,
            'rel': related_chars,
            'key': code_info['key'],
            'secondary': code_info['secondary'],
            'frequency': zigen_frequency.get(zigen, 0)  # 添加频率信息
        }
        result.append(item)
    
    # 移除频率字段，因为最终JSON不需要
    for item in result:
        del item['frequency']
    
    # 打印调试信息
    print("\n生成的JSON数据示例:")
    for i, item in enumerate(result[:5]):
        print(f"{item['name']}: {item['rel'][:20]}...")
    
    return result

def main():
    # 文件路径
    ll_map_path = 'src/public/ll/ll_map.txt'
    ll_div_path = 'src/public/ll/ll_div.txt'
    output_path = 'src/public/ll/zigen.json'
    
    # 读取数据
    ll_map = read_ll_map(ll_map_path)
    zigen_to_chars, zigen_frequency = read_ll_div(ll_div_path)
    
    # 生成JSON数据
    zigen_data = generate_zigen_json(ll_map, zigen_to_chars, zigen_frequency)
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(zigen_data, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    main() 