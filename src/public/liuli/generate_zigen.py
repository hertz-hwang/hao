import json
import re
from collections import defaultdict

def read_ll_map(file_path):
    """读取ll_map.real.txt文件，返回字根到编码的映射和字根顺序列表"""
    ll_map = {}
    zigen_order = []  # 保持字根出现的顺序
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # 分离编码和字根序列
            parts = line.split('\t')
            if len(parts) < 2:
                continue
                
            code, zigen_sequence = parts[0], parts[1]
            
            # ll_map.real.txt中使用空格分隔字根
            components = [c for c in zigen_sequence.split() if c]
            
            # 为每个字根分配编码
            for component in components:
                if component not in ll_map:
                    # 将编码转换为小写
                    code_lower = code.lower()
                    ll_map[component] = {
                        'key': code_lower[0], 
                        'secondary': code_lower[1:] if len(code_lower) > 1 else None
                    }
                    # 记录字根出现的顺序
                    zigen_order.append(component)
    
    return ll_map, zigen_order

def parse_zigen_sequence(sequence):
    """解析字根序列，处理花括号组合（用于ll_div.real.txt）"""
    components = []
    i = 0
    while i < len(sequence):
        if sequence[i] == '{':
            # 找到匹配的右花括号
            j = i + 1
            while j < len(sequence) and sequence[j] != '}':
                j += 1
            if j < len(sequence):
                # 提取花括号内的内容
                component = sequence[i+1:j]
                components.append(component)
                i = j + 1
            else:
                # 没有找到右花括号，按普通字符处理
                components.append(sequence[i])
                i += 1
        else:
            # 普通字符，直接作为字根
            components.append(sequence[i])
            i += 1
    
    return components

def extract_components(line):
    """从一行中提取拆分部件，兼容两种格式：
    1) "字<TAB>部件(以空格分隔)"
    2) "字<TAB>连续部件字符串"（新格式）
    """
    # 新格式：汉字与部件以制表符分隔，部件可能是连续字符串
    if '\t' in line:
        try:
            _char, components_str = line.split('\t', 1)
        except ValueError:
            return []
        
        # 检查是否有空格分隔
        if ' ' in components_str:
            # 有空格，按空格分隔
            components = [c for c in components_str.strip().split() if c]
        else:
            # 没有空格，解析连续的字根序列（使用花括号解析）
            components = parse_zigen_sequence(components_str.strip())
        
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
    """读取ll_div.real.txt文件，返回字根到相关汉字的映射和字根使用频率"""
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

def generate_zigen_json(ll_map, zigen_order, zigen_to_chars, zigen_frequency):
    """生成zigen.json格式的数据，按照ll_map.real.txt中的字根顺序"""
    result = []
    
    # 按照ll_map.real.txt中的字根顺序
    for zigen in zigen_order:
        if zigen not in ll_map:
            continue
            
        code_info = ll_map[zigen]
        
        # 获取相关汉字
        related_chars = zigen_to_chars.get(zigen, '')
        
        # 对于组合字根，尝试从子字根中获取相关汉字
        if not related_chars:
            # 检查是否是组合字根（包含空格）
            if ' ' in zigen:
                sub_components = [t for t in zigen.split() if t]
                collected = []
                seen = set()
                # 每个子字根取前几个例字
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
            'secondary': code_info['secondary']
        }
        result.append(item)
    
    # 打印调试信息
    print(f"\n生成的JSON数据数量: {len(result)}")
    print("前5个字根数据示例:")
    for i, item in enumerate(result[:5]):
        print(f"{item['name']}: key='{item['key']}', secondary='{item['secondary']}', rel='{item['rel'][:20]}...'")
    
    return result

def main():
    # 文件路径
    ll_map_path = 'src/public/liuli/ll_map.real.txt'
    ll_div_path = 'src/public/liuli/ll_div.real.txt'
    output_path = 'src/public/liuli/zigen1.json'
    
    # 读取数据
    ll_map, zigen_order = read_ll_map(ll_map_path)
    zigen_to_chars, zigen_frequency = read_ll_div(ll_div_path)
    
    # 生成JSON数据
    zigen_data = generate_zigen_json(ll_map, zigen_order, zigen_to_chars, zigen_frequency)
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(zigen_data, f, ensure_ascii=False, indent=4)
    
    print(f"\n已成功生成 {output_path}")

if __name__ == '__main__':
    main()