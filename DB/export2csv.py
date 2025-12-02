import pandas as pd
import pymysql

# 配置
host = '127.0.0.1'
port = 3306
user = 'root'
password = 'sz2025'
database = 'low_altitude_db'

# 连接数据库
conn = pymysql.connect(
    host=host,
    port=port,
    user=user,
    password=password,
    database=database,
    charset='utf8mb4'
)

# 查询南京航空航天大学的数据
query = "SELECT * FROM graduates WHERE `院校名称` = '南京航空航天大学'"
df = pd.read_sql(query, conn)

# 导出到 CSV
output_file = '南京航空航天大学_毕业生.csv'
df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"✅ 成功导出 {len(df)} 条记录到 {output_file}")

conn.close()
