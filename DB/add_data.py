import pandas as pd
import pymysql
import sys

# 配置
host = '127.0.0.1'
port = 3306
user = 'root'
password = 'sz2025'
database = 'low_altitude_db'

# 读取 Excel
df = pd.read_excel('低空经济毕业生.xlsx')
df = df.where(pd.notnull(df), None)  # 将 NaN 转为 None（MySQL 的 NULL）

# 连接数据库
conn = pymysql.connect(
    host=host,
    port=port,
    user=user,
    password=password,
    charset='utf8mb4'
)
cursor = conn.cursor()

# 创建数据库和表
cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
cursor.execute(f"USE `{database}`")

# 生成 CREATE TABLE 语句（简单版：所有字段用 TEXT）
columns = df.columns
col_defs = ', '.join([f"`{col}` TEXT" for col in columns])
create_table_sql = f"CREATE TABLE IF NOT EXISTS `graduates` ({col_defs}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
cursor.execute(create_table_sql)

# 批量插入
placeholders = ', '.join(['%s'] * len(columns))
insert_sql = f"INSERT INTO `graduates` (`{'`, `'.join(columns)}`) VALUES ({placeholders})"
data = [tuple(row) for row in df.values]

cursor.executemany(insert_sql, data)
conn.commit()

print(f"✅ 成功插入 {len(data)} 条记录到表 graduates")

cursor.close()
conn.close()