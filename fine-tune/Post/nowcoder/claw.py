from playwright.sync_api import sync_playwright
import time
import json
from datetime import datetime

# 全局变量存储已处理的帖子ID
processed_post_ids = set()

def login_with_qq(page):
    """使用QQ登录"""
    try:
        print("  正在点击QQ登录按钮...")
        # 点击QQ登录，等待新窗口弹出
        with page.context.expect_page() as new_page_info:
            page.locator("span.bar:has-text('QQ')").click()
        
        qq_login_page = new_page_info.value
        print("  ✓ QQ登录窗口已弹出")
        
        # 等待页面加载完成
        qq_login_page.wait_for_load_state('networkidle')
        print(f"  QQ登录页面URL: {qq_login_page.url}")
        
        # 保存截图以便调试（可选）
        try:
            qq_login_page.screenshot(path="qq_login_page.png")
            print("  ✓ 已保存QQ登录页面截图到 qq_login_page.png")
        except:
            pass
        
        # 等待一下让页面完全渲染
        time.sleep(2)
        
        # 获取页面视口尺寸
        viewport_size = qq_login_page.viewport_size
        print(f"  QQ登录页面视口尺寸: {viewport_size}")
        
        # 计算中心点坐标
        center_x = viewport_size['width'] // 2
        center_y = viewport_size['height'] // 2
        print(f"  页面中心点坐标: ({center_x}, {center_y})")
        
        # 移动鼠标到中心点
        print(f"  正在移动鼠标到中心点...")
        qq_login_page.mouse.move(center_x, center_y)
        time.sleep(0.5)
        
        # 点击中心点
        print(f"  正在点击中心点...")
        qq_login_page.mouse.click(center_x, center_y)
        print("  ✓ 已点击页面中心点")
        
        # 等待登录完成
        print("  等待登录完成...")
        time.sleep(5)
        
        # 等待原始页面可能的跳转或更新
        try:
            page.wait_for_load_state('networkidle', timeout=10000)
        except:
            pass
        
        print("✓ QQ登录流程完成")
        return True

    except Exception as e:
        print(f"✗ QQ登录时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def save_post_content(post_data, status):
    """保存帖子内容到JSON文件
    
    Args:
        post_data: 从API解析的帖子数据字典
        status: 'not_voted', 'voted', 'ended'
    """
    try:
        # 构造保存数据
        save_data = {
            "timestamp": datetime.now().isoformat(),
            "post_id": post_data.get('id', 'unknown'),
            "status": status,
            "title": post_data.get('title', '未知标题'),
            "author": post_data.get('author', {}),
            "content": post_data.get('content', ''),
            "vote": post_data.get('vote', {})
        }
        
        # 写入文件（追加模式）
        file_path = "voted_posts.json"
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(save_data, ensure_ascii=False) + "\n")
            
        print(f"  ✓ 已保存帖子: {save_data['title'][:30]}... (状态: {status})")
        return True
        
    except Exception as e:
        print(f"  ⚠ 保存帖子内容失败: {e}")
        return False

def fetch_vote_details(page, vote_id):
    """获取投票的详细信息（选项和票数）
    
    Args:
        page: Playwright page对象
        vote_id: 投票ID
    Returns:
        dict: 投票详细信息，包含选项列表
    """
    try:
        import time
        timestamp = int(time.time() * 1000)
        result = page.evaluate("""
            async ({voteId, ts}) => {
                try {
                    const response = await fetch(`/vote/info?voteId=${voteId}&_=${ts}`);
                    const data = await response.json();
                    return {success: true, data: data};
                } catch (error) {
                    return {success: false, error: error.message};
                }
            }
        """, {"voteId": vote_id, "ts": timestamp})
        
        if result.get('success'):
            return result.get('data', {})
        else:
            return None
            
    except Exception as e:
        return None

def vote_first_option(page, vote_id, first_option_id):
    """对未投票的帖子投第一个选项
    
    Args:
        page: Playwright page对象
        vote_id: 投票ID
        first_option_id: 第一个选项的ID
    """
    try:
        print(f"  正在投票: 选择第一个选项 (ID: {first_option_id})...")
        
        # 使用页面上下文发送投票请求
        result = page.evaluate("""
            async ({voteId, optionId}) => {
                try {
                    const response = await fetch('/vote/do', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            voteId: voteId,
                            voteOptions: [optionId]
                        })
                    });
                    const data = await response.json();
                    return {success: response.ok, data: data};
                } catch (error) {
                    return {success: false, error: error.message};
                }
            }
        """, {"voteId": vote_id, "optionId": first_option_id})
        
        if result.get('success'):
            print(f"  ✓ 投票成功!")
            time.sleep(0.5)
            return True
        else:
            print(f"  ⚠ 投票失败: {result.get('data', result.get('error'))}")
            return False
            
    except Exception as e:
        print(f"  ⚠ 投票过程出错: {e}")
        return False

def process_poll_data(data, page):
    """处理API响应中的投票贴数据
    
    Args:
        data: API响应的JSON数据
        page: Playwright page对象（用于获取投票详情和投票）
    """
    global processed_post_ids
    
    try:
        # 根据实际API结构解析
        posts = []
        
        # 实际结构: {success: true, data: {records: [...]}}
        if isinstance(data, dict) and 'data' in data:
            data_obj = data['data']
            if isinstance(data_obj, dict) and 'records' in data_obj:
                posts = data_obj['records']
            elif isinstance(data_obj, list):
                posts = data_obj
        
        if not posts:
            return
        
        new_count = 0
        for post in posts:
            try:
                # 检查是否包含投票信息
                vote_data = post.get('voteData')
                if not vote_data or not vote_data.get('withVote'):
                    continue
                
                # 获取内容ID
                content_id = post.get('contentId')
                if not content_id:
                    continue
                
                # 检查是否已处理
                if content_id in processed_post_ids:
                    continue
                
                processed_post_ids.add(content_id)
                new_count += 1
                
                # 提取基本信息
                moment_data = post.get('momentData', {})
                user_brief = post.get('userBrief', {})
                
                vote_id = vote_data.get('voteId')
                title = moment_data.get('title') or '无标题'
                content = moment_data.get('content', '')
                
                print(f"\n发现投票贴: {title[:40]}... (投票ID: {vote_id})")
                
                # 获取投票详情
                vote_details = fetch_vote_details(page, vote_id)
                
                if not vote_details or vote_details.get('code') != 0:
                    print("  ⚠ 无法获取投票详情，跳过")
                    continue
                
                vote_data_detail = vote_details.get('data', {})
                vote_options = vote_data_detail.get('voteOptions', [])
                has_voted = vote_data_detail.get('hasVote', False)
                is_expired = vote_data_detail.get('isExpired', False)
                total_vote_count = vote_data_detail.get('totalVoteUserCount', 0)
                count_info = vote_data_detail.get('countInfo', {})
                percent_info = vote_data_detail.get('percentInfo', {})
                
                # 构造选项信息（包含票数）
                options = []
                for opt in vote_options:
                    opt_id = str(opt.get('optionId'))
                    options.append({
                        'id': opt_id,
                        'text': opt.get('optionTitle', ''),
                        'votes': count_info.get(opt_id, 0),
                        'percentage': f"{percent_info.get(opt_id, '0')}%"
                    })
                
                # 构造帖子信息
                post_info = {
                    'id': content_id,
                    'vote_id': vote_id,
                    'title': title,
                    'content': content,
                    'author': {
                        'name': user_brief.get('nickname', '未知'),
                        'id': user_brief.get('userId', '')
                    },
                    'vote': {
                        'vote_id': vote_id,
                        'title': vote_data.get('voteTitle', ''),
                        'type': vote_data.get('voteType'),
                        'total_votes': total_vote_count,
                        'voted': has_voted,
                        'ended': is_expired,
                        'options': options
                    }
                }
                
                # 判断状态并处理
                if is_expired:
                    print("  状态: 已结束")
                    save_post_content(post_info, 'ended')
                elif has_voted:
                    print("  状态: 已投票")
                    save_post_content(post_info, 'voted')
                else:
                    print("  状态: 未投票 - 准备自动投票")
                    # 自动投第一个选项
                    if vote_options:
                        first_option_id = vote_options[0].get('optionId')
                        if vote_first_option(page, vote_id, first_option_id):
                            # 投票成功后重新获取详情（获取票数）
                            time.sleep(1)
                            updated_details = fetch_vote_details(page, vote_id)
                            if updated_details and updated_details.get('code') == 0:
                                updated_data = updated_details.get('data', {})
                                updated_count = updated_data.get('countInfo', {})
                                updated_percent = updated_data.get('percentInfo', {})
                                # 更新选项的票数信息
                                for opt in post_info['vote']['options']:
                                    opt_id = str(opt['id'])
                                    opt['votes'] = updated_count.get(opt_id, 0)
                                    opt['percentage'] = f"{updated_percent.get(opt_id, '0')}%"
                                post_info['vote']['voted'] = True
                            save_post_content(post_info, 'voted_by_bot')
                        else:
                            save_post_content(post_info, 'not_voted')
                    else:
                        print("  ⚠ 没有可投票的选项")
                        save_post_content(post_info, 'not_voted')
                
            except Exception as e:
                print(f"  ⚠ 处理单个帖子时出错: {e}")
                continue
        
        if new_count > 0:
            print(f"\n✓ 本次处理了 {new_count} 个新投票贴")
            
    except Exception as e:
        print(f"处理投票数据时出错: {e}")
        import traceback
        traceback.print_exc()

def handle_response(response, page):
    """处理网络响应
    
    Args:
        response: Playwright Response对象
        page: Playwright page对象 (用于投票操作)
    """
    global processed_post_ids
    
    try:
        url = response.url
        
        # 调试: 显示所有API请求
        if '/api/' in url:
            print(f"[API] {response.request.method} {url}")
        
        # 识别可能包含投票贴的API响应
        # 需要根据实际情况调整这些关键词
        keywords = [
            '/feed',
            '/list',
            '/subject',
            '/creation',
            '/community',
            '/discuss'
        ]
        
        if any(keyword in url.lower() for keyword in keywords):
            try:
                # 只处理成功的JSON响应
                if response.status != 200:
                    return
                
                content_type = response.headers.get('content-type', '')
                if 'application/json' not in content_type:
                    return
                
                data = response.json()
                print(f"\n[投票API] 捕获到响应: {url}")
                
                # 调试: 保存原始响应以便分析
                # debug_file = f"api_response_debug_{datetime.now().strftime('%H%M%S')}.json"
                # with open(debug_file, 'w', encoding='utf-8') as f:
                #     json.dump(data, f, ensure_ascii=False, indent=2)
                # print(f"  ✓ 已保存原始响应到 {debug_file}")
                
                # 处理数据 (传入page对象)
                process_poll_data(data, page)
                
            except Exception as e:
                # JSON解析失败或其他错误，忽略
                pass
                
    except Exception as e:
        # 忽略所有错误，避免影响正常浏览
        pass

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 步骤 1: 打开网站
            url = "https://www.nowcoder.com/creation/subject/913bd8c7bf26412fac5465aa6704493d?entranceType_var=%E5%86%85%E5%AE%B9%E6%9D%A1%E7%9B%AE"
            print(f"步骤 1: 正在打开网站...")
            print(f"URL: {url}")
            page.goto(url)
            page.wait_for_load_state('networkidle')
            print("✓ 网站已打开\n")

            # 步骤 2: 尝试使用QQ登录
            print("步骤 2: 尝试使用QQ登录...")
            if not login_with_qq(page):
                print("登录失败，退出脚本")
                return
            print("✓ 登录成功\n")

            # 步骤 3: 在新标签页中打开目标页面
            print("步骤 3: 在新标签页中打开目标页面...")
            try:
                new_page = context.new_page()
                target_url = "https://www.nowcoder.com/creation/subject/913bd8c7bf26412fac5465aa6704493d?entranceType_var=%E5%86%85%E5%AE%B9%E6%9D%A1%E7%9B%AE"
                print(f"  访问URL: {target_url}")
                new_page.goto(target_url)
                new_page.wait_for_load_state('networkidle')
                time.sleep(2)
                print("  ✓ 新标签页已打开（共享登录状态）")
                
                page = new_page
                print("✓ 已切换到新标签页")
            except Exception as e:
                print(f"⚠ 打开新标签页时出错: {e}")
            print()

            # 步骤 4: 启动网络监听
            print("步骤 4: 启动API监听...")
            
            # 注册响应监听器
            def response_handler(response):
                handle_response(response, page)
            
            page.on("response", response_handler)
            print("✓ 已注册网络响应监听器")
            print("=" * 50)

            # 步骤 5: 持续滚动触发API请求
            print("\n步骤 5: 开始滚动页面加载投票贴...")
            print("提示: 按 Ctrl+C 可随时停止")
            print("=" * 50)
            
            scroll_count = 0
            
            try:
                while True:
                    scroll_count += 1
                    print(f"\n[滚动 #{scroll_count}] 向下滚动...")
                    page.evaluate("window.scrollBy(0, 800);")
                    time.sleep(3)  # 等待API请求和响应
                    
                    print(f"  已处理帖子总数: {len(processed_post_ids)}")
                    
            except KeyboardInterrupt:
                print("\n\n✓ 用户中断，停止处理")
                print(f"✓ 本次共处理 {len(processed_post_ids)} 个投票贴")
                print(f"✓ 帖子内容已保存到 voted_posts.json")

        except Exception as e:
            print(f"\n✗ 发生错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 等待一下再关闭，确保最后的请求处理完成
            time.sleep(2)
            browser.close()

if __name__ == "__main__":
    main()
