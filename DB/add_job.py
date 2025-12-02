import pymysql
import numpy as np

# 岗位列表，常见的在前面
positions = [
    "无人机系统工程师",
    "自主飞行控制系统工程师",
    "低空导航算法工程师",
    "无人机传感器开发工程师",
    "航空电池技术研究员",
    "电动垂直起降飞行器（eVTOL）设计师",
    "轻量化材料研发",
    "航空通信协议工程师",
    "无人机空气动力学",
    "低空雷达技术研究员",
    "人工智能飞行规划师",
    "航空电子设备测试工程师",
    "氢能源航空动力工程师",
    "无人机3D打印工程师",
    "低空遥感技术研究员"
]

# 连接数据库
conn = pymysql.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    password='sz2025',
    database='low_altitude_db',
    charset='utf8mb4'
)
cursor = conn.cursor()

# 查询南京航空航天大学的所有记录
cursor.execute("SELECT id FROM graduates WHERE `院校名称` LIKE '南京航空航天大学'")
ids = [row[0] for row in cursor.fetchall()]
n = len(ids)

# 按指数分布分配岗位
prob = np.exp(-np.arange(len(positions)))  # 指数分布权重
prob = prob / prob.sum()
assigned = np.random.choice(positions, size=n, p=prob)

# 批量更新
for i, job in zip(ids, assigned):
    cursor.execute("UPDATE graduates SET `岗位名称`=%s WHERE id=%s", (job, i))

conn.commit()
cursor.close()
conn.close()
print(f"已为南京航空航天大学的 {n} 条记录分配岗位名称")