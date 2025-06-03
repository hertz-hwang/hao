import json
import re
from collections import defaultdict

def read_hao_map(file_path):
    """读取hao_map.txt文件，返回字根到编码的映射"""
    hao_map = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            code, zigen = line.split('\t')
            # 将编码转换为小写
            code = code.lower()
            if zigen not in hao_map:
                hao_map[zigen] = {'key': code[0], 'secondary': code[1] if len(code) > 1 else None}
    return hao_map

def extract_components(line):
    """从一行中提取拆分部件"""
    if '[' not in line:
        return []
    
    # 提取方括号中的内容
    parts = line.split('[')[1].split(']')[0].split(',')[0]
    # 分离每个部件
    components = list(parts)
    return components

def read_hao_div(file_path):
    """读取hao_div.txt文件，返回字根到相关汉字的映射和字根使用频率"""
    zigen_to_chars = defaultdict(list)  # 改为list以保持顺序
    zigen_frequency = defaultdict(int)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # 获取汉字和它的部件
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

def generate_zigen_json(hao_map, zigen_to_chars, zigen_frequency):
    """生成zigen.json格式的数据，按字根使用频率排序"""
    result = []
    for zigen, code_info in hao_map.items():
        # 获取相关汉字
        related_chars = zigen_to_chars.get(zigen, '')
        
        item = {
            'name': zigen,
            'rel': related_chars,
            'key': code_info['key'],
            'secondary': code_info['secondary'],
            'frequency': zigen_frequency.get(zigen, 0)  # 添加频率信息
        }
        result.append(item)
    
    # 按频率降序排序
    result.sort(key=lambda x: x['frequency'], reverse=True)
    
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
    hao_map_path = 'src/public/hao/hao_map.txt'
    hao_div_path = 'src/public/hao/hao_div.txt'
    output_path = 'src/public/hao/zigen-xi.json'
    
    # 读取数据
    hao_map = read_hao_map(hao_map_path)
    zigen_to_chars, zigen_frequency = read_hao_div(hao_div_path)
    
    # 生成JSON数据
    zigen_data = generate_zigen_json(hao_map, zigen_to_chars, zigen_frequency)
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(zigen_data, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    main() 