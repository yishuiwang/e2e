# LangGraph Agent 新增工具说明

## 🎉 新增功能概览

本次更新为LangGraph Agent添加了8个强大的新工具，大大扩展了Agent的能力范围，且这些工具都**不需要额外的API KEY**！

## 🔧 新增工具详细说明

### 1. 🔍 谷歌搜索工具 (google_search)
- **功能**: 免费的谷歌搜索，无需API KEY
- **用途**: 搜索最新信息、新闻、技术文档等
- **示例**: "搜索Python数据分析教程"
- **参数**: 
  - `query`: 搜索关键词
  - `num_results`: 返回结果数量（默认5个）

### 2. 🌐 网页内容抓取工具 (web_scraping)
- **功能**: 抓取指定网页的内容
- **用途**: 获取网页文本内容或HTML源码
- **示例**: "抓取https://www.python.org的内容"
- **参数**:
  - `url`: 要抓取的网页URL
  - `extract_text`: 是否只提取文本内容（默认True）

### 3. 📁 文件操作工具 (file_operations)
- **功能**: 全面的文件系统操作
- **支持操作**: read, write, append, list, delete, exists
- **示例**: 
  - "读取requirements.txt文件"
  - "列出当前目录的文件"
  - "检查config.json文件是否存在"
- **参数**:
  - `operation`: 操作类型
  - `file_path`: 文件路径
  - `content`: 写入内容（可选）

### 4. 💻 系统信息工具 (get_system_info)
- **功能**: 获取系统详细信息
- **包含信息**: 操作系统、CPU、内存、磁盘使用情况等
- **示例**: "获取当前系统信息"
- **无需参数**

### 5. ⚡ 命令执行工具 (execute_command)
- **功能**: 安全地执行系统命令
- **安全特性**: 自动阻止危险命令（如rm -rf, format等）
- **示例**: 
  - "执行ls命令"
  - "查看Python版本"
- **参数**:
  - `command`: 要执行的命令
  - `timeout`: 超时时间（默认30秒）

### 6. ⏰ 时间日期工具 (datetime_operations)
- **功能**: 全面的时间日期处理
- **支持操作**: now, format, calculate, timezone
- **示例**: 
  - "获取当前时间"
  - "计算3天后的日期"
  - "格式化日期"
- **参数**:
  - `operation`: 操作类型
  - `date_string`: 日期字符串（可选）
  - `format_string`: 日期格式（可选）
  - `days_offset`: 天数偏移（可选）

### 7. 📊 CSV数据处理工具 (csv_operations)
- **功能**: CSV文件的读取、写入和分析
- **支持操作**: read, write, analyze
- **示例**: 
  - "分析telco_data.csv文件"
  - "读取sales_data.csv的前10行"
- **参数**:
  - `operation`: 操作类型
  - `file_path`: CSV文件路径
  - `data`: CSV数据（JSON格式，用于写入）

### 8. 🔍 增强的Tavily搜索 (search_tool)
- **功能**: 高质量的网络搜索（原有工具）
- **用途**: 获取最新新闻和实时信息
- **优势**: 搜索质量更高，结果更准确

## 🚀 使用示例

### 基本测试
```bash
# 运行基本功能测试
python test_new_tools.py

# 进入交互模式测试
python test_new_tools.py --interactive
```

### 实际使用场景

1. **信息搜索**:
   - "搜索最新的AI技术发展"
   - "查找Python机器学习库的使用教程"

2. **文件管理**:
   - "读取项目配置文件"
   - "列出数据目录下的所有CSV文件"
   - "创建一个新的日志文件"

3. **系统监控**:
   - "检查系统资源使用情况"
   - "获取当前服务器状态"

4. **数据处理**:
   - "分析销售数据的基本统计信息"
   - "读取用户行为数据并进行预处理"

5. **网页数据获取**:
   - "抓取新闻网站的最新文章"
   - "获取API文档的内容"

## 🔧 安装新依赖

新工具需要以下额外依赖包：
```bash
pip install requests beautifulsoup4 psutil
```

这些依赖已经添加到`requirements.txt`文件中。

## ⚠️ 注意事项

1. **安全性**: 命令执行工具有安全限制，会阻止潜在危险命令
2. **网络访问**: 搜索和网页抓取工具需要网络连接
3. **文件权限**: 文件操作需要相应的读写权限
4. **系统兼容性**: 系统信息工具在不同操作系统上显示的信息可能略有差异

## 🎯 工具选择建议

- **搜索信息**: 优先使用`search_tool`（高质量），备选`google_search`（免费）
- **网页内容**: 使用`web_scraping`获取特定网页内容
- **文件操作**: 使用专门的`file_operations`而不是通用Python代码
- **数据分析**: CSV文件优先使用`csv_operations`，复杂分析再用Python工具
- **系统管理**: 使用`get_system_info`和`execute_command`进行系统操作

## 🔄 更新内容总结

- ✅ 添加了8个新的实用工具
- ✅ 更新了工具列表和提示词模板
- ✅ 增加了必要的依赖包
- ✅ 创建了测试文件和文档
- ✅ 保持了原有功能的完整性

现在你的LangGraph Agent具备了更强大的功能，可以处理更多样化的任务！