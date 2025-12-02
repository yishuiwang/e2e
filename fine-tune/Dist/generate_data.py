import json
import random
import requests
import time
import os

# Configuration
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-hpghpzramrqsxlkrvlepvjjbgerfhiafohkkjpqjpyluzspu"
MODEL = "Qwen/QwQ-32B"
INPUT_FILE = "/root/e2e/fine-tune/Dist/instructions.json"
OUTPUT_FILE = "/root/e2e/fine-tune/Dist/alpaca_data.json"
NUM_SAMPLES = 50  # Number of samples to generate

def load_instructions(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def construct_prompt(pref, intention, task):
    templates = [
        f"作为一名{pref['major']}专业的学生，我的就业偏好是：{pref['content']}。我的职业意图是：{intention}。请{task}",
        f"请根据以下信息完成任务：\n专业背景：{pref['major']}\n偏好描述：{pref['content']}\n求职意图：{intention}\n\n具体任务：{task}",
        f"任务要求：{task}\n\n候选人信息：\n- 专业：{pref['major']}\n- 偏好：{pref['content']}\n- 意图：{intention}",
        f"背景：{pref['content']}（{pref['major']}）\n目标：{intention}\n请执行：{task}"
    ]
    return random.choice(templates)

def generate_data():
    data = load_instructions(INPUT_FILE)
    
    preferences = data['preferences']['explicit_preferences'] + data['preferences']['implicit_preferences']
    intentions = data['intentions']
    task_forms = data['task_forms']
    
    output_data = []
    
    print(f"Starting generation of {NUM_SAMPLES} samples...")
    
    for i in range(NUM_SAMPLES):
        pref = random.choice(preferences)
        intention = random.choice(intentions)
        task = random.choice(task_forms)
        
        prompt = construct_prompt(pref, intention, task)
        
        payload = {
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            print(f"Sending request {i+1}/{NUM_SAMPLES}...")
            response = requests.post(API_URL, json=payload, headers=headers)
            response.raise_for_status()
            res_json = response.json()
            
            # Handle potential API errors or unexpected formats
            if 'choices' in res_json and len(res_json['choices']) > 0:
                content = res_json['choices'][0]['message']['content']
                
                output_data.append({
                    "instruction": prompt,
                    "input": "",
                    "output": content
                })
                print(f"Request {i+1} successful.")
            else:
                print(f"Request {i+1} failed: No choices in response. Response: {res_json}")
                
        except Exception as e:
            print(f"Error on sample {i+1}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
        
        time.sleep(1)  # Rate limiting
        
    # Save to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    
    print(f"Data generation complete. Saved {len(output_data)} samples to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_data()
