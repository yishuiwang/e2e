from playwright.sync_api import sync_playwright
import time
import json
from datetime import datetime

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

def scroll_down(page, scroll_times=3):
    """向下滚动页面"""
    print(f"开始向下滚动 {scroll_times} 次...")
    for i in range(scroll_times):
        page.evaluate("window.scrollBy(0, 1000);")
        time.sleep(3)
        print(f"  滚动进度: {i+1}/{scroll_times}")
    print("✓ 滚动完成")

def find_posts_with_poll(page, start_index=0):
    """查找包含投票的帖子，优化版：只查找从start_index开始的新帖子"""
    posts_with_poll = []
    
    try:
        # 查找所有帖子容器
        post_containers = page.locator("div[data-v-7c0cfd84]").all()
        total_count = len(post_containers)
        
        # 只处理新增的帖子
        for idx in range(start_index, total_count):
            try:
                container = post_containers[idx]
                
                # 检查是否有投票特征（单选框 或 "投票成功"文本）
                has_poll = False
                if container.locator("input.el-radio__original[type='radio']").count() > 0:
                    has_poll = True
                elif container.locator("span:has-text('投票成功')").count() > 0:
                    has_poll = True
                
                if has_poll:
                    # 提取标题和作者作为唯一标识
                    title = "无标题"
                    # 尝试获取标题
                    for selector in [".feed-title", ".title", ".subject", "h1", "div.tw-font-bold"]:
                        if container.locator(selector).count() > 0:
                            title = container.locator(selector).first.inner_text().strip()
                            break
                    
                    # 尝试获取作者
                    author = "未知作者"
                    if container.locator(".user-nickname").count() > 0:
                        author = container.locator(".user-nickname").first.inner_text().strip()
                        
                    # 生成唯一签名
                    signature = f"{title}_{author}"
                    
                    posts_with_poll.append({
                        'index': idx,
                        'container': container,
                        'signature': signature,
                        'title': title
                    })
            except Exception as e:
                continue
        
        return posts_with_poll, total_count  # 返回结果和总数
        
    except Exception as e:
        print(f"查找投票帖子时出错: {e}")
        return [], start_index

def get_active_modal(page):
    """获取当前活动的详情页弹窗容器"""
    try:
        # 策略1: 优先查找标准的弹窗容器
        # 常见的弹窗类名或属性
        dialog_selectors = [
            "div[role='dialog']",
            ".el-dialog",
            ".el-drawer",
            ".nc-modal",
            ".van-popup"
        ]
        
        for selector in dialog_selectors:
            dialogs = page.locator(selector).all()
            for dialog in dialogs:
                if dialog.is_visible():
                    # 确认这个弹窗里有内容（比如标题或投票项）
                    # 避免选中空的遮罩层
                    if dialog.locator("h1, .vote-item, .el-radio").count() > 0:
                        # print(f"  ✓ 通过选择器 {selector} 找到弹窗")
                        return dialog

        # 策略2: 查找可见的关闭按钮，然后向上查找
        close_btns = page.locator(".close, .el-dialog__headerbtn, .el-drawer__close-btn").all()
        target_close_btn = None
        for btn in close_btns:
            if btn.is_visible():
                target_close_btn = btn
                break
        
        if target_close_btn:
            current = target_close_btn
            # 向上找，但不要找太多层，避免找到 body
            for _ in range(5): 
                parent = current.locator("..")
                # 检查是否是主要容器特征
                # 必须包含 h1 或者是 dialog/content 类的容器
                class_attr = parent.get_attribute("class") or ""
                if "dialog" in class_attr or "content" in class_attr or "wrapper" in class_attr:
                     return parent
                
                # 如果包含 h1 且不是 body
                if parent.locator("h1").count() > 0:
                    tag_name = parent.evaluate("el => el.tagName").lower()
                    if tag_name != "body" and tag_name != "html":
                        return parent
                        
                current = parent
                
    except Exception as e:
        print(f"  ⚠ 定位详情页容器出错: {e}")
    
    return None

def save_post_content(page, post_index, post_type, is_voted, modal_container=None):
    """保存帖子内容到JSON文件"""
    try:
        print("  正在保存帖子内容...")
        
        # 如果未提供容器，尝试自动定位
        if not modal_container:
            modal_container = get_active_modal(page)
            
        if not modal_container:
            print("  ⚠ 未能定位详情页容器，将使用全局查找")
            modal_container = page
        
        # 等待内容加载 (在容器内等待)
        try:
            modal_container.locator("h1").first.wait_for(state="visible", timeout=3000)
        except:
            pass
        
        # 提取标题
        title = "未知标题"
        try:
            title_el = modal_container.locator("h1").first
            if title_el.is_visible():
                title = title_el.inner_text().strip()
        except:
            pass
            
        # 提取作者
        author_info = ""
        try:
            user_info = modal_container.locator(".user-info-container").first
            if user_info.is_visible():
                nickname = user_info.locator(".user-nickname").inner_text().strip()
                job = ""
                if user_info.locator(".user-job-name").count() > 0:
                    job = user_info.locator(".user-job-name").inner_text().strip()
                author_info = {"name": nickname, "job": job}
        except:
            pass
            
        # 提取正文
        content = ""
        try:
            content_el = modal_container.locator(".feed-content-text").first
            if content_el.is_visible():
                content = content_el.inner_text().strip()
        except:
            pass
            
        # 提取投票选项和票数
        vote_options = []
        try:
            # 策略1: 针对用户提供的已投票详情页结构
            # 查找所有投票项行 (flex container)
            # 结构特征: class包含 tw-flex tw-items-center ... tw-h-7.5
            # 注意：必须在 modal_container 内查找
            vote_rows = modal_container.locator("div.tw-flex.tw-items-center.tw-h-7\\.5").all()
            
            if vote_rows:
                for row in vote_rows:
                    try:
                        # 提取选项名称 (在第一个子元素内的绝对定位元素中)
                        # 结构: div(relative) > div(absolute text)
                        option_name_el = row.locator("div.tw-relative > div.tw-absolute").first
                        option_name = option_name_el.inner_text().strip() if option_name_el.count() > 0 else ""
                        
                        # 提取票数和百分比 (在第二个子元素中)
                        # 结构: div(whitespace-nowrap)
                        count_info_el = row.locator("div.tw-whitespace-nowrap").first
                        count_info = count_info_el.inner_text().strip() if count_info_el.count() > 0 else ""
                        
                        if option_name:
                            vote_options.append(f"{option_name} [{count_info}]")
                    except:
                        continue
            
            # 策略2: 如果策略1没找到，尝试之前的通用方法 (兼容未投票状态或旧结构)
            if not vote_options:
                # 尝试查找 .vote-item (未投票时的选项)
                option_elements = modal_container.locator(".vote-item").all()
                if not option_elements:
                     option_elements = modal_container.locator(".el-radio-group > *").all()

                for opt in option_elements:
                    text = opt.inner_text().strip()
                    vote_options.append(text)
                
                # 尝试补充票数信息 (如果已投票但上面只拿到了选项名)
                if is_voted and vote_options and not any("[" in opt for opt in vote_options):
                     progress_texts = modal_container.locator(".el-progress__text, .vote-count, .poll-count").all_inner_texts()
                     if progress_texts:
                         new_options = []
                         for i, opt in enumerate(vote_options):
                             count_text = progress_texts[i] if i < len(progress_texts) else ""
                             new_options.append(f"{opt} ({count_text})")
                         if new_options:
                             vote_options = new_options

        except Exception as e:
            print(f"  ⚠ 提取投票选项出错: {e}")
            pass
            
        # 构造数据
        post_data = {
            "timestamp": datetime.now().isoformat(),
            "post_index": post_index,
            "post_type": post_type,
            "is_voted": is_voted,
            "title": title,
            "author": author_info,
            "content": content,
            "vote_results": vote_options
        }
        
        # 写入文件
        file_path = "voted_posts.json"
        try:
            # 读取现有数据
            with open(file_path, 'r', encoding='utf-8') as f:
                # 检查文件是否为空
                content = f.read().strip()
                if content:
                    pass
        except FileNotFoundError:
            pass
            
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(post_data, ensure_ascii=False) + "\n")
            
        print("  ✓ 帖子内容已保存")
        return True
        
    except Exception as e:
        print(f"  ⚠ 保存帖子内容失败: {e}")
        return False

def vote_and_submit(page, post_data):
    """处理投票帖子（投票或查看已投票内容）"""
    try:
        container = post_data['container']
        post_title = post_data.get('title', '未知标题')
        
        print(f"\n处理帖子: {post_title} ...")

        # 滚动到该帖子
        container.scroll_into_view_if_needed()
        time.sleep(0.3)
        
        # 步骤1: 点击标题打开详情页
        print("  正在点击标题打开详情...")
        title_clicked = False
        selectors = [
            "div.tw-font-bold.tw-text-lg",
            ".feed-title", 
            ".title", 
            ".subject", 
            "h1", "h2", "h3", "h4"
        ]
        
        for selector in selectors:
            elements = container.locator(selector).all()
            for el in elements:
                if el.is_visible():
                    try:
                        try:
                            el.click(timeout=2000)
                        except Exception as click_err:
                            if "intercepts pointer events" in str(click_err):
                                print(f"  ⚠ 点击被遮挡，尝试强制点击...")
                                el.click(timeout=2000, force=True)
                            else:
                                raise click_err
                        title_clicked = True
                        break
                    except Exception as e:
                        continue
            if title_clicked:
                break
        
        if not title_clicked:
            print("  ⚠ 未找到明确的标题元素，尝试点击容器空白处...")
            try:
                container.click(position={"x": 50, "y": 30}, timeout=3000)
                title_clicked = True
            except Exception as e:
                print(f"  ⚠ 点击容器失败: {e}")
        
        # 等待详情页弹出
        try:
            page.wait_for_selector(".close", timeout=5000)
        except:
            print("  ⚠ 未检测到详情页弹出，可能点击失败")
            return False

        time.sleep(1) # 等待动画
      
        # 获取详情页容器
        modal_container = get_active_modal(page)
        if not modal_container:
            print("  ⚠ 警告: 未能精确定位详情页容器，操作可能不稳定")
            modal_container = page

        # 步骤2: 在详情页内部检查是否已投票
        is_voted = False
        # 检查 "投票成功" 按钮或文本
        # 用户提供的按钮特征: <button ...><span ...>投票成功 发表观点</span></button>
        if modal_container.locator("button:has-text('投票成功')").count() > 0:
            is_voted = True
            print("  ✓ 检测到已投票状态 (找到'投票成功'按钮)")
        elif modal_container.locator("span:has-text('投票成功')").count() > 0:
            is_voted = True
            print("  ✓ 检测到已投票状态 (找到'投票成功'文本)")

        post_type = "已投票" if is_voted else "新投票"

        # 如果未投票，执行投票流程
        if not is_voted:
            print("  状态: 未投票，准备进行投票...")
            try:
                # 查找投票选项
                vote_options = modal_container.locator(".vote-item")
                if vote_options.count() == 0:
                     vote_options = modal_container.locator(".el-radio")

                if vote_options.count() > 0:
                    # 点击第一个选项
                    print(f"  找到 {vote_options.count()} 个选项，选择第一个...")
                    vote_options.first.click()
                    time.sleep(0.5)
                    
                    # 点击投票按钮
                    vote_btns = modal_container.locator("button:has-text('投票')").all()
                    clicked_vote = False
                    for btn in vote_btns:
                        if btn.is_visible():
                            btn.click()
                            print("  ✓ 已点击投票按钮")
                            time.sleep(2) # 等待提交和状态更新
                            is_voted = True
                            clicked_vote = True
                            break
                    
                    if not clicked_vote:
                        print("  ⚠ 未找到可见的投票按钮")
                else:
                    print("  ⚠ 详情页中未找到投票选项")
            except Exception as e:
                print(f"  ⚠ 投票过程出错: {e}")
            
        # 保存帖子内容
        save_post_content(page, post_data['index'], post_type, is_voted, modal_container)

        # 步骤4: 点击关闭按钮
        print("  正在关闭详情页...")
        try:
            close_btn = page.locator(".close").first
            if close_btn.is_visible():
                close_btn.click()
                try:
                    page.locator(".close").wait_for(state="hidden", timeout=3000)
                except:
                    pass
            else:
                page.keyboard.press("Escape")
        except Exception as e:
            print(f"  ⚠ 关闭详情页时出错: {e}")
            
        return True

    except Exception as e:
        print(f"处理帖子时发生未知错误: {e}")
        return False
     


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        # 创建一个浏览器上下文（context），用于共享cookie等状态
        context = browser.new_context()
        # 在这个context中创建第一个页面
        page = context.new_page()

        try:
            # 步骤 1: 打开网站
            url = "https://www.nowcoder.com/creation/subject/913bd8c7bf26412fac5465aa6704493d?entranceType_var=%E5%86%85%E5%AE%B9%E6%9D%A1%E7%9B%AE"
            print(f"步骤 1: 正在打开网站...")
            print(f"URL: {url}")
            page.goto(url)
            page.wait_for_load_state('networkidle')
            print("✓ 网站已打开\n")

            # 步骤 2: 尝试使用QQ登录...
            print("步骤 2: 尝试使用QQ登录...")
            if not login_with_qq(page):
                print("登录失败，退出脚本")
                return
            print("✓ 登录成功\n")

            # 步骤 3: 在新标签页中打开目标页面
            print("步骤 3: 在新标签页中打开目标页面...")
            try:
                # 在同一个浏览器上下文中创建新标签页（共享cookie）
                new_page = context.new_page()
                
                # 在新标签页中访问目标URL
                target_url = "https://www.nowcoder.com/creation/subject/913bd8c7bf26412fac5465aa6704493d?entranceType_var=%E5%86%85%E5%AE%B9%E6%9D%A1%E7%9B%AE"
                print(f"  访问URL: {target_url}")
                new_page.goto(target_url)
                new_page.wait_for_load_state('networkidle')
                time.sleep(2)
                print("  ✓ 新标签页已打开（共享登录状态）")
                
                # 使用新页面继续操作（保留旧页面不关闭）
                page = new_page
                print("✓ 已切换到新标签页")
            except Exception as e:
                print(f"⚠ 打开新标签页时出错: {e}")
            print()

            # 步骤 4: 持续滚动并处理投票帖子（直到 Ctrl+C）
            print("步骤 4: 开始持续处理投票帖子...")
            print("提示: 按 Ctrl+C 可随时停止")
            print("=" * 50)
            
            processed_signatures = set()  # 记录已处理的帖子签名，避免重复
            total_processed = 0  # 处理总数
            scroll_count = 0  # 滚动次数
            last_checked_index = 0  # 记录上次检查到的帖子索引
            
            try:
                while True:  # 无限循环直到Ctrl+C
                    # 每次滚动一小段距离
                    scroll_count += 1
                    print(f"\n[滚动 #{scroll_count}] 向下滚动页面...")
                    page.evaluate("window.scrollBy(0, 800);")
                    time.sleep(2)  # 等待内容加载
                    
                    # 查找当前可见的投票帖子（只查找新增的）
                    posts_with_poll, current_total = find_posts_with_poll(page, last_checked_index)
                    last_checked_index = current_total  # 更新已检查的索引
                    
                    # 找出未处理的新帖子
                    new_posts = []
                    for post in posts_with_poll:
                        # 使用 Title+Author 签名作为唯一ID
                        post_id = post['signature']
                        if post_id not in processed_signatures:
                            new_posts.append(post)
                            processed_signatures.add(post_id)
                    
                    if new_posts:
                        print(f"✓ 发现 {len(new_posts)} 个新的投票帖子")
                        
                        # 处理这些新帖子
                        for post_data in new_posts:
                            # 处理帖子（投票或查看）
                            if vote_and_submit(page, post_data):
                                total_processed += 1
                            
                            print("-" * 50)
                            time.sleep(0.5)  # 每个帖子之间等待0.5秒
                    else:  
                        print("  没有新的投票帖子")
                    
                    # 显示统计信息
                    print(f"\n[统计] 已处理: {total_processed} 个帖子 | 滚动次数: {scroll_count} | 页面帖子总数: {current_total}")
                    
            except KeyboardInterrupt:
                print("\n\n✓ 用户中断，停止处理")
                print(f"✓ 本次共处理 {total_processed} 个投票帖子")
                print(f"✓ 帖子内容已保存到 voted_posts.json")

        except Exception as e:
            print(f"\n✗ 发生错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()

if __name__ == "__main__":
    main()
