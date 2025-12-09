import requests
import re
import json
import sys
from bs4 import BeautifulSoup

class MoocCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.csrf = None
        self.headers = None

    def init_session(self):
        """初始化会话并获取 CSRF Token"""
        try:
            self.session.get("https://www.icourse163.org")
            self.csrf = self.session.cookies.get("NTESSTUDYSI")
            
            if not self.csrf:
                raise Exception("未能获取 csrf token (NTESSTUDYSI)")
            
            self.headers = {
                "edu-script-token": self.csrf,
                "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            print(f"[+] 会话初始化成功")
        except Exception as e:
            print(f"[-] 初始化失败: {e}")
            sys.exit(1)

    def search_course(self, keyword="人工智能"):
        """搜索课程并返回结果列表"""
        url = f"https://www.icourse163.org/web/j/mocSearchBean.searchCourse.rpc?csrfKey={self.csrf}"
        
        payload_dict = {
            "keyword": keyword,
            "pageIndex": 1,
            "highlight": True,
            "orderBy": 0,
            "stats": 30,
            "pageSize": 20
        }
        
        try:
            resp = self.session.post(url, headers=self.headers, data={"mocCourseQueryVo": json.dumps(payload_dict)})
            result = resp.json()
            courses = result.get('result', {}).get('list', [])
            if not courses:
                print("[-] 未找到相关课程")
                return []
            
            print(f"[+] 搜索成功，找到 {len(courses)} 门课程")
            
            # 排序：将 type=306 的课程排在前面，优先尝试
            # key logic: False (0) comes before True (1), so we check if type != 306
            courses.sort(key=lambda x: x.get('type') != 306)
            
            return courses
            
        except Exception as e:
            print(f"[-] 搜索出错: {e}")
            return []

    def _extract_school_panel(self, course_data):
        """提取学校信息的辅助逻辑"""
        moc_card = course_data.get('mocCourseCard', {})
        
        if sp := moc_card.get('schoolPanel'): return sp
        
        moc_dto = moc_card.get('mocCourseCardDto', {})
        if sp := moc_dto.get('schoolPanel'): return sp

        term_panel = moc_dto.get('termPanel', {})
        for lector in term_panel.get('lectorPanels', []):
            if sp := lector.get('schoolPanel'): return sp
            
        return None

    def extract_course_identifiers(self, course):
        """从单条课程数据中提取 (school_short, course_id)"""
        try:
            school_panel = self._extract_school_panel(course)
            school_short = school_panel.get('shortName', '').lower() if school_panel else "unknown"
            
            course_id = course['mocCourseCard']['mocCourseCardDto']['id']
            return school_short, course_id
        except (KeyError, TypeError):
            return None, None

    def fetch_and_parse_outline(self, school_short, course_id):
        """获取详情页并解析大纲"""
        url = f"https://www.icourse163.org/course/{school_short}-{course_id}?from=searchPage&outVendor=zw_mooc_pcssjg_"
        
        try:
            print(f"[*] 正在尝试获取: {school_short}-{course_id}")
            resp = self.session.get(url, headers=self.headers, timeout=10)
            
            pattern = r'outLine\s*:\s*"((?:\\.|[^"\\])*)"'
            match = re.search(pattern, resp.text)
            
            if not match:
                print("   [-] 页面中未找到 outLine 数据")
                return []

            raw_js_string = match.group(1)
            outline_html = json.loads(f'"{raw_js_string}"')
            
            soup = BeautifulSoup(outline_html, 'html.parser')
            titles = []
            
            # 提取 font-size: 16px 的内容
            for span in soup.find_all('span'):
                style = span.get('style', '')
                if 'font-size: 16px' in style:
                    titles.append(span.get_text(strip=True))
            
            # 如果没提取到 16px 的，尝试提取所有 <p> 标签作为备选（防止某些课程样式不同）
            if not titles:
                print("   [!] 未找到标准标题格式(16px)，尝试提取普通段落...")
                for p in soup.find_all('p'):
                    text = p.get_text(strip=True)
                    # 简单过滤太短的或者看起来像小节的
                    if text and len(text) > 2: 
                        titles.append(text)
            
            return titles

        except Exception as e:
            print(f"   [-] 解析过程出错: {e}")
            return []

    def save_to_file(self, data, filename):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"[+] 成功保存文件: {filename}")
        except Exception as e:
            print(f"[-] 保存文件失败: {e}")

def main():
    crawler = MoocCrawler()
    crawler.init_session()
    
    courses = crawler.search_course("电工电子实践B")
    
    max_attempts = 5
    attempts = 0
    
    for course in courses:
        if attempts >= max_attempts:
            print(f"[-] 已达到最大尝试次数 ({max_attempts})，停止运行。")
            break

        # 1. 提取当前课程ID
        school_short, course_id = crawler.extract_course_identifiers(course)
        if not course_id:
            continue
            
        attempts += 1
        print(f"\n--- 第 {attempts} 次尝试 ---")
        
        # 2. 尝试获取大纲
        titles = crawler.fetch_and_parse_outline(school_short, course_id)
        
        # 3. 验证结果
        if titles and len(titles) > 0:
            print(f"[+] 成功！共提取到 {len(titles)} 条大纲内容")
            filename = f"{school_short}-{course_id}.json"
            crawler.save_to_file(titles, filename)
            # 成功后直接退出程序
            return
        else:
            print(f"[-] 该课程提取内容为空，准备尝试下一个...")
    
    print("\n[-] 所有尝试均未获取到有效大纲数据。")

if __name__ == "__main__":
    main()