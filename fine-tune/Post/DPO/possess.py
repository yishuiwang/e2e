import json

def split_concatenated_json(text):
    """
    从连续拼接的 JSON 对象字符串（如 {}{}{}）中，分割出每个合法的 JSON 对象字符串。
    使用括号计数法，确保嵌套对象也能正确分割。
    """
    objects = []
    i = 0
    n = len(text)
    while i < n:
        if text[i].strip() == '{':
            # 开始一个对象
            brace_count = 0
            start = i
            while i < n:
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # 找到匹配的结束
                        obj_str = text[start:i+1]
                        objects.append(obj_str)
                        break
                i += 1
            else:
                raise ValueError(f"未闭合的 JSON 对象从位置 {start} 开始")
        else:
            i += 1
    return objects

def extract_content_and_options(json_str_list):
    extracted = []
    for s in json_str_list:
        try:
            obj = json.loads(s)
            content = obj.get("content", "")
            options = obj.get("vote", {}).get("options", [])
            extracted.append({
                "content": content,
                "options": options
            })
        except json.JSONDecodeError as e:
            print(f"解析失败，跳过一段数据: {e}")
            continue
    return extracted

def main():
    # 读取原始文件（假定文件名为 data.txt）
    input_file = "input.txt"
    output_file = "output.json"

    with open(input_file, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # 分割出每个 JSON 对象字符串
    json_strings = split_concatenated_json(raw_text)

    # 提取所需字段
    extracted_data = extract_content_and_options(json_strings)

    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=2)

    print(f"成功提取 {len(extracted_data)} 条记录，已保存至 {output_file}")

if __name__ == "__main__":
    main()