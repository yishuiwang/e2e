"""
Configuration for DPO data pipeline
"""

# Doubao API Configuration
DOUBAO_API_KEY = "7212460f-77f8-472b-b44f-aefae420dfc5"
DOUBAO_API_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/responses"
DOUBAO_MODEL = "doubao-seed-1-6-251015"

# Meaningless option keywords (case-insensitive)
MEANINGLESS_KEYWORDS = [
    "路过",
    "看结果",
    "大佬路过",
    "我就逛逛",
    "大佬评论",
    "看看",
    "路过看",
    "大佬",
    "评论区",
]

# DPO Pair Generation Parameters
MIN_VOTE_DIFFERENCE = 2  # Minimum vote count difference between chosen and rejected
MIN_VOTE_COUNT = 1  # Minimum votes for an option to be considered
MIN_VOTE_PERCENTAGE_DIFF = 0.0  # Minimum percentage difference (0-100)

# Text Augmentation Prompt Template
CHOSEN_PROMPT = """你是一个专业的职场顾问。我会给你一个求职者的背景和两个选项。胜出的选项是"{chosen_text}"。请根据求职者的描述，为这个胜出选项写一段详细的分析理由，作为最终的 Chosen Response。

求职者背景和问题：
{context}

两个选项：
1. {chosen_text} (获得 {chosen_votes} 票，{chosen_percentage})
2. {rejected_text} (获得 {rejected_votes} 票，{rejected_percentage})

请分析为什么"{chosen_text}"更适合这位求职者，写一段详细的推荐理由（100-150字）："""

REJECTED_PROMPT = """你是一个专业的职场顾问。我会给你一个求职者的背景和两个选项。这个选项"{rejected_text}"获得的票数较少。请根据求职者的描述，分析这个选项为什么不如另一个选项合适，作为最终的 Rejected Response。

求职者背景和问题：
{context}

两个选项：
1. {chosen_text} (获得 {chosen_votes} 票，{chosen_percentage})
2. {rejected_text} (获得 {rejected_votes} 票，{rejected_percentage})

请分析为什么"{rejected_text}"相对不太适合这位求职者，写一段客观的分析（100-150字）："""

# Output Configuration
OUTPUT_FILE = "dpo_dataset.jsonl"
INCLUDE_METADATA = True

# API Rate Limiting
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
REQUEST_TIMEOUT = 30  # seconds

# Multi-threading Configuration
MAX_WORKERS = 10  # Number of concurrent API requests
WRITE_IMMEDIATELY = True  # Write results to file immediately instead of batching
