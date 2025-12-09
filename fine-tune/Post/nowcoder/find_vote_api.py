"""
简单的网络监听脚本，用于查找投票详情API
运行这个脚本，然后手动点击一个投票贴，查看控制台输出
"""
from playwright.sync_api import sync_playwright
import json

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # 监听所有网络响应
        def handle_response(response):
            url = response.url
            
            # 只关注vote相关的API
            if 'vote' in url.lower() or 'poll' in url.lower():
                try:
                    if response.status == 200 and 'application/json' in response.headers.get('content-type', ''):
                        data = response.json()
                        print(f"\n{'='*80}")
                        print(f"URL: {url}")
                        print(f"Method: {response.request.method}")
                        print(f"\n响应数据:")
                        print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])  # 只显示前2000字符
                        print(f"{'='*80}\n")
                except:
                    pass
        
        page.on("response", handle_response)
        
        # 打开页面
        url = "https://www.nowcoder.com/creation/subject/913bd8c7bf26412fac5465aa6704493d?entranceType_var=%E5%86%85%E5%AE%B9%E6%9D%A1%E7%9B%AE"
        print("正在打开页面...")
        page.goto(url)
        
        print("\n\n" + "="*80)
        print("页面已加载！")
        print("请手动完成以下操作：")
        print("1. 如需登录，请先登录")
        print("2. 点击任意一个投票贴查看详情")
        print("3. 观察控制台输出的API信息")
        print("4. 按 Ctrl+C 结束")
        print("="*80 + "\n\n")
        
        input("按回车键结束...")
        
        browser.close()

if __name__ == "__main__":
    main()
