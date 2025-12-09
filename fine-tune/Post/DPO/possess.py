import json

def clean_data(input_file, output_file):
    keywords = ["路过", "看结果", "围观", "瓜", "酱油"]
    
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
        
        for line in f_in:
            try:
                data = json.loads(line)
                
                content = data.get('content', '')
                vote_data = data.get('vote', {})
                options = vote_data.get('options', [])
                
                cleaned_options = []
                for opt in options:
                    text = opt.get('text', '')
                    # Check if text contains any meaningless keywords
                    if not any(keyword in text for keyword in keywords):
                        cleaned_options.append({
                            'text': text,
                            'votes': opt.get('votes', 0)
                        })
                
                # Only save if there are valid options remaining
                if cleaned_options:
                    new_record = {
                        'content': content,
                        'options': cleaned_options
                    }
                    f_out.write(json.dumps(new_record, ensure_ascii=False) + '\n')
                else:
                    print(f"Skipping record: {data.get('post_id', 'unknown')} - No valid options")

            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                continue
            except Exception as e:
                print(f"Error processing line: {e}")
                continue

if __name__ == "__main__":
    input_path = "/root/e2e/fine-tune/Post/DPO/voted_posts.jsonl"
    output_path = "/root/e2e/fine-tune/Post/DPO/cleaned_voted_posts.jsonl"
    clean_data(input_path, output_path)
    print(f"Data cleaned and saved to {output_path}")
