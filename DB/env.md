### USER
docker 启动一个mysql，可以root远程登陆，密码是sz2025

### ASSISTANT
你可以使用以下 Docker 命令来启动一个 MySQL 容器，并允许 `root` 用户从远程登录，密码设置为 `sz2025`：

```bash
docker run -d \
  --name mysql-remote \
  -e MYSQL_ROOT_PASSWORD=sz2025 \
  -e MYSQL_ROOT_HOST=% \
  -p 3306:3306 \
  mysql:8.0 \
  --default-authentication-plugin=mysql_native_password
```

### 参数说明：

- `-d`：后台运行容器（detached 模式）。
- `--name mysql-remote`：给容器起个名字（可自定义）。
- `-e MYSQL_ROOT_PASSWORD=sz2025`：设置 root 用户密码为 `sz2025`。
- `-e MYSQL_ROOT_HOST=%`：允许 root 从任意主机（`%` 表示所有主机）登录。  
  > 注意：在 MySQL 8+ 中，仅设置 `MYSQL_ROOT_HOST=%` 可能还不够，因为默认 root 用户只允许本地登录。但结合下面的 `--default-authentication-plugin` 和初始化行为，Docker 镜像通常会根据这个环境变量创建对应的远程 root 用户。
- `-p 3306:3306`：将容器的 3306 端口映射到宿主机，以便远程访问。
- `--default-authentication-plugin=mysql_native_password`：兼容旧版客户端（可选，但推荐，避免某些客户端连接报错）。

---

### 验证是否可远程登录（可选）：

1. **进入容器**：
   ```bash
   docker exec -it mysql-remote mysql -uroot -psz2025
   ```

2. **查看用户权限**：
   ```sql
   SELECT host, user FROM mysql.user;
   ```
   应该能看到类似：
   ```
   +-----------+------------------+
   | host      | user             |
   +-----------+------------------+
   | %         | root             |
   | localhost | root             |
   +-----------+------------------+
   ```

---

### 安全提醒：

- 允许 `root` 远程登录存在安全风险，建议仅在开发/测试环境使用。
- 生产环境应创建专用用户并限制 IP，同时关闭 root 远程访问。

---

如果你使用的是 **MySQL 5.7**，可以将 `mysql:8.0` 替换为 `mysql:5.7`，并去掉 `--default-authentication-plugin` 参数（因为 5.7 默认就是 `mysql_native_password`）：

```bash
docker run -d \
  --name mysql-remote \
  -e MYSQL_ROOT_PASSWORD=sz2025 \
  -e MYSQL_ROOT_HOST=% \
  -p 3306:3306 \
  mysql:5.7
```

这样就能实现你的需求了 ✅

### USER
写个python脚本登陆，验证一下

### ASSISTANT
下面是一个使用 Python 脚本连接并验证远程登录 MySQL 的示例。我们将使用 `pymysql` 库来实现连接测试。

---

### ✅ 前提条件
1. 已通过上一条命令成功启动 MySQL Docker 容器（允许 root 远程登录，密码 `sz2025`，端口 3306 映射到宿主机）。
2. 安装 `pymysql`：
   ```bash
   pip install pymysql
   ```

---

### 🐍 Python 验证脚本：`test_mysql_remote.py`

```python
import pymysql
import sys

def test_mysql_connection():
    try:
        # 尝试连接 MySQL（假设 MySQL 运行在本机 3306 端口）
        connection = pymysql.connect(
            host='127.0.0.1',        # 如果从其他机器连接，改为宿主机 IP
            port=3306,
            user='root',
            password='sz2025',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        with connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION() AS version;")
                result = cursor.fetchone()
                print("✅ 成功连接 MySQL！")
                print(f"MySQL 版本: {result['version']}")

                # 可选：验证是否允许远程 root 登录（查看当前用户）
                cursor.execute("SELECT USER(), CURRENT_USER();")
                user_info = cursor.fetchone()
                print(f"当前连接用户: {user_info['USER()']}")
                print(f"实际认证用户: {user_info['CURRENT_USER()']}")

    except pymysql.MySQLError as e:
        print(f"❌ 连接失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_mysql_connection()
```

---

### ▶️ 运行脚本

```bash
python test_mysql_remote.py
```

### ✅ 预期输出（成功时）：
```
✅ 成功连接 MySQL！
MySQL 版本: 8.0.39
当前连接用户: root@localhost
实际认证用户: root@%
```

> 注意：`USER()` 显示的是你连接时使用的用户和主机（通常为 `root@localhost` 如果从本机连），而 `CURRENT_USER()` 显示 MySQL 实际匹配的账户（应为 `root@%` 表示使用了远程权限账户）。

---

### 🔒 如果连接失败，常见原因：

1. **Docker 容器没运行**：运行 `docker ps` 确认 `mysql-remote` 在运行。
2. **防火墙/安全组**：确保 3306 端口开放（本地测试通常没问题）。
3. **MySQL 用户权限问题**：确认容器启动时设置了 `-e MYSQL_ROOT_HOST=%`。
4. **MySQL 8 默认认证插件问题**：脚本中 `pymysql` 支持 `caching_sha2_password`，但如果遇到问题，可改用 `--default-authentication-plugin=mysql_native_password` 启动容器（如之前建议）。

---

这个脚本能有效验证你的 MySQL 是否支持远程 root 登录。如需从其他机器测试，把 `host='127.0.0.1'` 改为运行 Docker 的服务器 IP 即可。

### USER

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/root/e2e/DB/pymysql.py", line 34, in <module>
    test_mysql_connection()
  File "/root/e2e/DB/pymysql.py", line 29, in test_mysql_connection
    except pymysql.MySQLError as e:
           ^^^^^^^^^^^^^^^^^^
AttributeError: module 'pymysql' has no attribute 'MySQLError'
(test) root@23-94-247-158-host:~/e2e/DB#

### ASSISTANT
你遇到的错误：

```
AttributeError: module 'pymysql' has no attribute 'MySQLError'
```

是因为你的 **Python 脚本文件名是 `pymysql.py`**，这会导致 Python 在导入时 **优先加载你自己的 `pymysql.py` 文件**，而不是真正的 `pymysql` 库，从而引发命名冲突。

---

### 🔧 问题根源
- 你把脚本命名为：`/root/e2e/DB/pymysql.py`
- 当执行 `import pymysql` 时，Python 会先在当前目录查找 `pymysql.py`，于是导入了你自己写的脚本（而非第三方库）
- 因此 `pymysql.MySQLError` 不存在，因为你的脚本里没有定义它

---

### ✅ 解决方法

#### 第一步：**重命名你的脚本文件**
```bash
mv /root/e2e/DB/pymysql.py /root/e2e/DB/test_mysql_remote.py
```

#### 第二步：**删除自动生成的缓存文件（如果有）**
```bash
rm -f /root/e2e/DB/pymysql.pyc
rm -rf /root/e2e/DB/__pycache__/
```

#### 第三步：**重新运行脚本**
```bash
python /root/e2e/DB/test_mysql_remote.py
```

---

### ✅ 正确的脚本内容（再次确认）

确保 `test_mysql_remote.py` 内容如下：

```python
import pymysql
import sys

def test_mysql_connection():
    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='sz2025',
            charset='utf8mb4'
        )
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION();")
                version = cursor.fetchone()[0]
                print("✅ 成功连接 MySQL！")
                print(f"MySQL 版本: {version}")
    except pymysql.Error as e:  # 使用 pymysql.Error 更通用
        print(f"❌ 连接失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_mysql_connection()
```

> 💡 小提示：也可以使用 `pymysql.Error`（它是 `MySQLError` 的父类），兼容性更好。

---

### ✅ 验证是否修复
运行后如果看到类似输出，说明成功：
```
✅ 成功连接 MySQL！
MySQL 版本: 8.0.39
```

---

### 🚫 永远不要用库名作为你的脚本文件名！
比如：`numpy.py`, `requests.py`, `pymysql.py`, `json.py` 等，都会导致类似问题。

---

现在你应该可以顺利验证 MySQL 远程登录了！

### USER
怎么插入到数据库中
root@23-94-247-158-host:~/e2e/DB# ls
conn.py  __pycache__  README.md  低空经济毕业生.xlsx
root@23-94-247-158-host:~/e2e/DB#

### ASSISTANT
你想把 Excel 文件 `低空经济毕业生.xlsx` 中的数据插入到 MySQL 数据库中。以下是完整的 Python 脚本方案，使用 `pandas` 读取 Excel，用 `pymysql` + `SQLAlchemy`（或直接用 `pymysql`）写入 MySQL。

> ✅ 推荐使用 **SQLAlchemy + pandas.to_sql()**，简单高效。但如果不想引入 SQLAlchemy，也可以用纯 `pymysql` 批量插入。

---

### 步骤概览
1. 安装依赖
2. 读取 Excel
3. 连接 MySQL
4. 创建表（如果不存在）
5. 插入数据

---

## ✅ 方案一：使用 `pandas + SQLAlchemy`（推荐）

### 1. 安装依赖
```bash
pip install pandas openpyxl pymysql sqlalchemy
```

> `openpyxl` 用于读取 `.xlsx` 文件。

---

### 2. 创建脚本 `import_excel_to_mysql.py`

```python
import pandas as pd
from sqlalchemy import create_engine
import sys

# 数据库配置
DB_HOST = '127.0.0.1'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = 'sz2025'
DB_NAME = 'low_altitude_db'  # 自定义数据库名

# Excel 文件路径
EXCEL_FILE = '低空经济毕业生.xlsx'
SHEET_NAME = 0  # 或指定工作表名，如 'Sheet1'

def main():
    # 1. 读取 Excel
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
        print(f"✅ 读取 Excel 成功，共 {len(df)} 行数据")
        print("前几行数据预览：")
        print(df.head())
    except Exception as e:
        print(f"❌ 读取 Excel 失败: {e}")
        sys.exit(1)

    # 2. 创建数据库引擎（自动创建数据库）
    engine_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    engine = create_engine(engine_url, echo=False)

    # 3. 确保数据库存在（SQLAlchemy 不会自动建库，需手动）
    with engine.connect() as conn:
        conn.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.execute(f"USE `{DB_NAME}`")

    # 4. 写入 MySQL 表（表名：graduates）
    try:
        df.to_sql(
            name='graduates',        # 表名
            con=engine,
            if_exists='replace',     # 如果表存在：'fail'（报错）, 'replace'（替换）, 'append'（追加）
            index=False,             # 不写入 pandas 的 index
            chunksize=1000           # 批量插入，提高性能
        )
        print(f"✅ 数据已成功插入到数据库 `{DB_NAME}` 的表 `graduates` 中！")
    except Exception as e:
        print(f"❌ 插入数据库失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

### 3. 运行脚本
```bash
python import_excel_to_mysql.py
```

---

### 📝 说明
- 表名默认为 `graduates`，会根据 Excel 列名自动创建字段（字段类型由 pandas 推断，通常为 `TEXT` 或 `BIGINT`）。
- 如果你希望 **追加数据** 而不是替换，把 `if_exists='replace'` 改为 `'append'`。
- 如果 Excel 有中文列名，MySQL 也能正常支持（因为用了 `utf8mb4`）。

---

## ✅ 方案二：纯 `pymysql` 批量插入（不依赖 SQLAlchemy）

如果你不想用 SQLAlchemy，也可以这样做：

```python
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
```

---

### 🔍 后续验证
你可以进入 MySQL 查看数据：

```bash
docker exec -it mysql-remote mysql -uroot -psz2025 -D low_altitude_db -e "SELECT * FROM graduates LIMIT 5;"
```

---

### 💡 建议
- 如果数据量大（>1万行），方案一（SQLAlchemy + to_sql）性能更好。
- 确保 Excel 文件编码无问题，列名不要包含特殊字符（如空格、`-` 等，可用下划线 `_`）。

需要我帮你根据实际 Excel 列结构调整建表语句吗？你可以贴出 `head -n 3 低空经济毕业生.xlsx`（或描述列名），我可以生成更精确的建表 SQL。

### USER
docker 安装phpmyadmin 并且能够查看刚才的mysql数据

### ASSISTANT
要使用 **Docker 安装 phpMyAdmin** 并连接到你之前启动的 MySQL 容器（名为 `mysql-remote`，密码 `sz2025`），请按以下步骤操作：

---

### ✅ 前提条件
- 你已经运行了 MySQL 容器：
  ```bash
  docker run -d --name mysql-remote -e MYSQL_ROOT_PASSWORD=sz2025 -e MYSQL_ROOT_HOST=% -p 3306:3306 mysql:8.0 --default-authentication-plugin=mysql_native_password
  ```

> 注意：**phpMyAdmin 默认只能通过容器名连接 MySQL（在同一 Docker 网络中）**，所以推荐使用 **Docker 自定义网络** 或 **`--link`（已弃用，不推荐）**。我们采用更标准的方式：**创建自定义 bridge 网络**。

---

## ✅ 正确做法：使用 Docker 自定义网络

### 第 1 步：创建一个自定义网络（如果还没有）
```bash
docker network create mysql-net
```

### 第 2 步：**重新启动 MySQL 容器（加入网络）**
> 如果你之前的 `mysql-remote` 已经在运行，先删掉它（数据会丢失，如果你没挂载卷）：
```bash
docker stop mysql-remote
docker rm mysql-remote
```

然后重新运行（加入网络）：
```bash
docker run -d \
  --name mysql-remote \
  --network mysql-net \
  -e MYSQL_ROOT_PASSWORD=sz2025 \
  -e MYSQL_ROOT_HOST=% \
  mysql:8.0 \
  --default-authentication-plugin=mysql_native_password
```
> 注意：**这里不需要 `-p 3306:3306` 也能被 phpMyAdmin 访问**（因为同网络容器可直接通信），但如果你还需要本地连接 MySQL，可以保留 `-p 3306:3306`。

完整版（保留端口映射）：
```bash
docker run -d \
  --name mysql-remote \
  --network mysql-net \
  -e MYSQL_ROOT_PASSWORD=sz2025 \
  -e MYSQL_ROOT_HOST=% \
  -p 3306:3306 \
  mysql:8.0 \
  --default-authentication-plugin=mysql_native_password
```

### 第 3 步：启动 phpMyAdmin 容器（加入同一网络）

```bash
docker run -d \
  --name phpmyadmin \
  --network mysql-net \
  -e PMA_HOST=mysql-remote \
  -e PMA_PORT=3306 \
  -e PMA_USER=root \
  -e PMA_PASSWORD=sz2025 \
  -p 8080:80 \
  phpmyadmin/phpmyadmin:latest
```

---

### 🔍 参数说明
| 参数 | 说明 |
|------|------|
| `--network mysql-net` | 和 MySQL 在同一网络，可通过容器名通信 |
| `-e PMA_HOST=mysql-remote` | 指向 MySQL 容器名（不是 localhost！） |
| `-e PMA_USER=root` | 登录用户名 |
| `-e PMA_PASSWORD=sz2025` | 密码 |
| `-p 8080:80` | 将 phpMyAdmin 的 80 端口映射到宿主机 8080 |

---

### ✅ 访问 phpMyAdmin
在浏览器打开：
```
http://<你的服务器IP>:8080
```

例如：
```
http://23.94.247.158:8080
```

> 💡 如果是本地测试，用 `http://localhost:8080`

你应该会看到 phpMyAdmin 登录页，并且**自动填入了 root / sz2025**（因为通过环境变量预配置了）。

---

### 🔒 安全建议（生产环境）
- 不要暴露 phpMyAdmin 到公网，或加上 HTTP Basic Auth / IP 白名单。
- 不要使用 root 用户，建议在 MySQL 中创建专用用户（如 `pma`）并授权。

---

### 🧪 验证是否能查看你导入的 Excel 数据
1. 登录 phpMyAdmin
2. 左侧选择数据库 `low_altitude_db`
3. 点击表 `graduates`
4. 查看数据是否和 Excel 一致 ✅

---

### ❌ 常见问题排查

#### 1. **“ mysqli::real_connect(): (HY000/2002): Connection refused”**
- 原因：`PMA_HOST` 没指向正确的 MySQL 容器名，或不在同一网络。
- 解决：确认 `--network` 相同，且 `PMA_HOST=mysql-remote`（和 MySQL 容器名一致）。

#### 2. **“Access denied for user 'root'@'...'”**
- 原因：MySQL 的 root 用户不允许从 phpMyAdmin 容器 IP 登录。
- 解决：确保启动 MySQL 时加了 `-e MYSQL_ROOT_HOST=%`，或进入 MySQL 手动授权：
  ```sql
  CREATE USER 'root'@'%' IDENTIFIED BY 'sz2025';
  GRANT ALL PRIVILEGES ON *.* TO 'root'@'%';
  FLUSH PRIVILEGES;
  ```

#### 3. **页面打不开**
- 检查端口：`docker ps` 看 phpMyAdmin 是否映射到 8080
- 检查防火墙：服务器是否开放 8080 端口？

---

现在你就可以通过 Web 界面轻松管理 `low_altitude_db` 数据库了！

### USER

fa7679215d6dbf9386061978d41203bf5249ee1b00d4d8dc96f5354e8ed3844c
(test) root@23-94-247-158-host:~/e2e/DB# docker run -d \
  --name phpmyadmin \
  --network mysql-net \
  -e PMA_HOST=mysql-remote \
  -e PMA_PORT=3306 \
  -e PMA_USER=root \
  -e PMA_PASSWORD=sz2025 \
  -p 8080:80 \
  phpmyadmin/phpmyadmin:latest
7a70d7e1fdf2b33295ec682c4240a2c90a97ea598699942285b6f052e7fce215
docker: Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint phpmyadmin (13ba258df726607d82b8dc281fec6cf338547a841b024b34f76d2a17331a27e9): failed to bind host port for 0.0.0.0:8080:172.19.0.3:80/tcp: address already in use

Run 'docker run --help' for more information
(test) root@23-94-247-158-host:~/e2e/DB#

### ASSISTANT
你遇到的错误是：

```
failed to bind host port for 0.0.0.0:8080:172.19.0.3:80/tcp: address already in use
```

### ❌ 问题原因：
**宿主机的 8080 端口已经被占用**，无法再绑定新的服务。

可能是：
- 你**已经运行了一个 phpMyAdmin 容器**（或其它服务）占用了 8080 端口。
- 或者之前启动过 phpMyAdmin 但没有正确停止/删除。

---

### ✅ 解决方案（任选其一）

---

#### ✅ 方法 1：**停止并删除已占用 8080 端口的容器**

1. 查看哪些容器正在运行并占用了 8080：
   ```bash
   docker ps --format "table {{.Names}}\t{{.Ports}}"
   ```

2. 如果看到有容器映射了 `8080`，比如旧的 `phpmyadmin`，就停掉并删除：
   ```bash
   docker stop phpmyadmin
   docker rm phpmyadmin
   ```

   > 如果容器名不是 `phpmyadmin`，请根据 `docker ps` 输出替换。

3. 再次运行你的命令：
   ```bash
   docker run -d \
     --name phpmyadmin \
     --network mysql-net \
     -e PMA_HOST=mysql-remote \
     -e PMA_PORT=3306 \
     -e PMA_USER=root \
     -e PMA_PASSWORD=sz2025 \
     -p 8080:80 \
     phpmyadmin/phpmyadmin:latest
   ```

---

#### ✅ 方法 2：**换一个宿主机端口（推荐，快速解决）**

比如改用 **8081** 端口：

```bash
docker run -d \
  --name phpmyadmin \
  --network mysql-net \
  -e PMA_HOST=mysql-remote \
  -e PMA_PORT=3306 \
  -e PMA_USER=root \
  -e PMA_PASSWORD=sz2025 \
  -p 8081:80 \
  phpmyadmin/phpmyadmin:latest
```

然后访问：
```
http://23.94.247.158:8081
```

> ✅ 这是最简单、安全的做法，避免冲突。

---

#### 🔍 附加：如何查看哪个进程占用了 8080 端口？

```bash
sudo lsof -i :8080
# 或
sudo netstat -tulnp | grep :8080
```

如果发现是某个 `docker-proxy` 进程，说明确实是 Docker 容器在用。

---

### 💡 小建议
- 给容器起固定名字（如你已经做了 `--name phpmyadmin`），方便管理。
- 启动前先 `docker stop phpmyadmin && docker rm phpmyadmin` 确保没有残留。

---

现在你可以用 **8081 端口** 或 **清理旧容器后用 8080**，顺利访问 phpMyAdmin 了！  
访问后应该能直接看到 `low_altitude_db` 数据库和 `graduates` 表 ✅

### USER

(test) root@23-94-247-158-host:~/e2e/DB# docker rm 7a70d7e1fdf2b33295ec682c4240a2c90a97ea598699942285b6f052e7fce215
7a70d7e1fdf2b33295ec682c4240a2c90a97ea598699942285b6f052e7fce215
(test) root@23-94-247-158-host:~/e2e/DB# docker run -d   --name phpmyadmin   --network mysql-net   -e PMA_HOST=mysql-remote   -e PMA_PORT=3306   -e PMA_USER=root   -e PMA_PASSWORD=sz2025   -p 8081:80   phpmyadmin/phpmyadmin:latest
4f5da68922c09872a6bae3c48c25d3116010f5dd182deb2668eee73fcb9af780
docker: Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint phpmyadmin (2bdc06e761e868c4fa209fcd074a8f94e020c9bed0d23e693a2860be10b4e08d): failed to bind host port for 0.0.0.0:8081:172.19.0.3:80/tcp: address already in use

Run 'docker run --help' for more information
(test) root@23-94-247-158-host:~/e2e/DB#

### ASSISTANT
你遇到了一个 **看似矛盾但其实常见的 Docker 网络端口绑定问题**：

```
failed to bind host port for 0.0.0.0:8081: ... address already in use
```

但你刚删掉容器，为什么还“already in use”？

---

### 🔍 真正原因：**内核端口处于 TIME_WAIT 状态 或 Docker 内部残留**

虽然你删除了容器，但：
- 操作系统可能还未释放端口（尤其是刚停掉的服务）。
- **更可能的是：你之前运行的容器虽然被 `docker rm` 删除了，但它并没有被 `docker stop`，而是处于“已退出但未清理网络”的状态**，或者有**多个容器尝试绑定同一个端口**。

不过从报错看，`8081` 是新端口，按理不该被占。所以更可能是：

> 🚨 **Docker 的 `docker-proxy` 进程没有及时退出，仍持有端口。**

---

### ✅ 终极解决步骤

#### 第 1 步：**确认 8081 是否真的被占用**
```bash
sudo ss -tulnp | grep 8081
# 或
sudo lsof -i :8081
```

如果看到输出，比如：
```
COMMAND   PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
docker-pr 12345 root   4u  IPv6 123456      0t0  TCP *:8081 (LISTEN)
```

说明 **docker-proxy 进程还在运行**，即使容器已删。

#### 第 2 步：**强制杀死占用 8081 的进程（如果有）**
```bash
sudo fuser -k 8081/tcp
# 或根据 PID 杀
sudo kill -9 <PID>
```

> ⚠️ 注意：`fuser` 可能需要安装：`apt install psmisc`

#### 第 3 步：**清理所有已停止/残留容器（安全操作）**
```bash
# 停止所有运行中的 phpmyadmin（防止重复）
docker stop phpmyadmin 2>/dev/null || true

# 删除所有已停止的容器（包括异常退出的）
docker container prune -f
```

#### 第 4 步：**换一个“更冷门”的端口（比如 8888），快速绕过问题**
```bash
docker run -d \
  --name phpmyadmin \
  --network mysql-net \
  -e PMA_HOST=mysql-remote \
  -e PMA_PORT=3306 \
  -e PMA_USER=root \
  -e PMA_PASSWORD=sz2025 \
  -p 8888:80 \
  phpmyadmin/phpmyadmin:latest
```

然后访问：
```
http://23.94.247.158:8888
```

✅ 这几乎一定能成功，因为 8888 很少被占用。

---

### 💡 额外建议：使用 `--rm` 临时测试（开发时推荐）

```bash
docker run -it --rm \
  --name phpmyadmin \
  --network mysql-net \
  -e PMA_HOST=mysql-remote \
  -e PMA_USER=root \
  -e PMA_PASSWORD=sz2025 \
  -p 8888:80 \
  phpmyadmin/phpmyadmin:latest
```

- `-it`：前台运行，便于看日志
- `--rm`：退出后自动清理，不会残留网络/端口

等确认能访问后，再用 `-d` 后台运行。

---

### ✅ 验证是否成功

运行后执行：
```bash
docker ps
```

看到 `phpmyadmin` 正常运行，并且 `0.0.0.0:8888->80/tcp`，就说明成功了。

然后浏览器打开 `http://23.94.247.158:8888`，应该能直接登录并看到你的 `low_altitude_db` 数据库！

---

如果还是不行，请贴出：
```bash
docker network inspect mysql-net
docker ps -a
sudo ss -tuln | grep ':8'
```

我可以进一步帮你诊断。但大概率换端口（8888/9999）就能解决！

### USER

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

  File "/home/sz/miniconda3/envs/test/lib/python3.11/site-packages/pymysql/connections.py", line 649, in connect
    sock = socket.create_connection(
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/sz/miniconda3/envs/test/lib/python3.11/socket.py", line 863, in create_connection
    raise exceptions[0]
  File "/home/sz/miniconda3/envs/test/lib/python3.11/socket.py", line 848, in create_connection
    sock.connect(sa)
ConnectionRefusedError: [Errno 111] Connection refused

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/root/e2e/DB/conn.py", line 17, in <module>
    conn = pymysql.connect(
           ^^^^^^^^^^^^^^^^
  File "/home/sz/miniconda3/envs/test/lib/python3.11/site-packages/pymysql/connections.py", line 361, in __init__
    self.connect()
  File "/home/sz/miniconda3/envs/test/lib/python3.11/site-packages/pymysql/connections.py", line 716, in connect
    raise exc
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server on '127.0.0.1' ([Errno 111] Connection refused)")
(test) root@23-94-247-158-host:~/e2e/DB#

### ASSISTANT
你的错误是：

```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server on '127.0.0.1' ([Errno 111] Connection refused)")
```

这说明 **Python 脚本无法连接到本地的 MySQL 服务（3306 端口）**。

---

### 🔍 原因分析

你之前用 Docker 启动了 MySQL 容器，并映射了 `-p 3306:3306`，**理论上应该可以通过 `127.0.0.1:3306` 访问**。但出现 "Connection refused" 通常意味着：

#### ✅ 可能原因 1：**MySQL 容器没有正常运行**
运行以下命令检查：
```bash
docker ps
```

你应该能看到类似：
```
CONTAINER ID   IMAGE       COMMAND                  ...   PORTS                    NAMES
fa7679215d6d   mysql:8.0   "docker-entrypoint.s…"   ...   0.0.0.0:3306->3306/tcp   mysql-remote
```

> ❌ 如果 `mysql-remote` **不在列表中**，说明容器已退出（可能启动失败）。

#### ✅ 可能原因 2：**MySQL 容器启动失败（比如初始化错误）**
查看日志：
```bash
docker logs mysql-remote
```

常见问题：
- 内存不足
- 数据目录权限问题（如果你挂载了 volume）
- 重复启动导致端口冲突（但你用了 `-p 3306:3306`，应该没问题）

#### ✅ 可能原因 3：**你删除过容器但没重新正确启动**
你之前删过 `phpmyadmin` 容器，**是否也误删或没重启 `mysql-remote`？**

---

### ✅ 解决步骤

#### 第 1 步：**确保 MySQL 容器正在运行**

```bash
# 停止并删除旧的（如果有）
docker stop mysql-remote 2>/dev/null
docker rm mysql-remote 2>/dev/null

# 重新启动（确保映射 3306 端口）
docker run -d \
  --name mysql-remote \
  --network mysql-net \
  -e MYSQL_ROOT_PASSWORD=sz2025 \
  -e MYSQL_ROOT_HOST=% \
  -p 3306:3306 \
  mysql:8.0 \
  --default-authentication-plugin=mysql_native_password
```

> 💡 加上 `--network mysql-net` 是为了和 phpMyAdmin 通信，但**不影响宿主机通过 127.0.0.1:3306 访问**。

#### 第 2 步：**确认 3306 端口在宿主机监听**

```bash
ss -tulnp | grep 3306
# 或
netstat -tulnp | grep 3306
```

你应该看到：
```
tcp6  0  0 :::3306  :::*  LISTEN  .../docker-proxy
```

> ✅ 有 `docker-proxy` 监听 3306 就说明端口已正确映射。

#### 第 3 步：**本地测试连接 MySQL**

```bash
mysql -h 127.0.0.1 -P 3306 -u root -psz2025 -e "SELECT 1;"
```

如果成功，输出：
```
+---+
| 1 |
+---+
| 1 |
+---+
```

如果失败，说明 MySQL 容器没起来或密码不对。

#### 第 4 步：**再运行你的 Python 脚本**

现在应该可以连接了！

---

### 🛠️ 附加建议：增强脚本健壮性

在 `conn.py` 开头加个连接测试：

```python
import pymysql
import time

def wait_for_mysql(host, port, user, password, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            conn = pymysql.connect(host=host, port=port, user=user, password=password)
            conn.close()
            return True
        except:
            time.sleep(2)
    raise Exception("MySQL 未在 30 秒内启动！")

# 在连接前加：
wait_for_mysql('127.0.0.1', 3306, 'root', 'sz2025')
```

---

### ✅ 总结

你的问题 **不是代码问题，而是 MySQL 容器没正常运行或端口未监听**。

**执行以下命令即可修复：**

```bash
docker stop mysql-remote 2>/dev/null
docker rm mysql-remote 2>/dev/null
docker run -d \
  --name mysql-remote \
  --network mysql-net \
  -e MYSQL_ROOT_PASSWORD=sz2025 \
  -e MYSQL_ROOT_HOST=% \
  -p 3306:3306 \
  mysql:8.0 \
  --default-authentication-plugin=mysql_native_password
```

然后再次运行 `python conn.py`。

> 💡 提醒：如果你在云服务器（如阿里云、腾讯云），确保**安全组开放了 3306 端口**（但本地连接不需要，因为走 loopback）。

---

运行成功后，你就可以用 phpMyAdmin（8888 端口）和 Python 脚本同时访问同一个 MySQL 数据了！

### USER

(test) root@23-94-247-158-host:~/e2e/DB# docker ps
CONTAINER ID   IMAGE                           COMMAND                  CREATED         STATUS         PORTS                                                                                      NAMES
14780ef31eb7   phpmyadmin/phpmyadmin:latest    "/docker-entrypoint.…"   3 minutes ago   Up 3 minutes   0.0.0.0:9081->80/tcp, [::]:9081->80/tcp                                                    phpmyadmin
fa7679215d6d   mysql:8.0                       "docker-entrypoint.s…"   8 minutes ago   Up 8 minutes   3306/tcp, 33060/tcp                                                                        mysql-remote
e24b36cb3089   memgraph/memgraph-mage:latest   "/usr/lib/memgraph/m…"   3 months ago    Up 3 months    0.0.0.0:7444->7444/tcp, [::]:7444->7444/tcp, 0.0.0.0:7687->7687/tcp, [::]:7687->7687/tcp   memgraph
(test) root@23-94-247-158-host:~/e2e/DB# docker logs mysql-remote
2025-11-20 02:02:26+00:00 [Note] [Entrypoint]: Entrypoint script for MySQL Server 8.0.44-1.el9 started.
2025-11-20 02:02:26+00:00 [Note] [Entrypoint]: Switching to dedicated user 'mysql'
2025-11-20 02:02:26+00:00 [Note] [Entrypoint]: Entrypoint script for MySQL Server 8.0.44-1.el9 started.
2025-11-20 02:02:26+00:00 [Note] [Entrypoint]: Initializing database files
2025-11-20T02:02:26.451707Z 0 [Warning] [MY-011068] [Server] The syntax '--skip-host-cache' is deprecated and will be removed in a future release. Please use SET GLOBAL host_cache_size=0 instead.
2025-11-20T02:02:26.451780Z 0 [Warning] [MY-010918] [Server] 'default_authentication_plugin' is deprecated and will be removed in a future release. Please use authentication_policy instead.
2025-11-20T02:02:26.451796Z 0 [System] [MY-013169] [Server] /usr/sbin/mysqld (mysqld 8.0.44) initializing of server in progress as process 80
2025-11-20T02:02:26.458227Z 1 [System] [MY-013576] [InnoDB] InnoDB initialization has started.
2025-11-20T02:02:27.017542Z 1 [System] [MY-013577] [InnoDB] InnoDB initialization has ended.
2025-11-20T02:02:28.198173Z 6 [Warning] [MY-010453] [Server] root@localhost is created with an empty password ! Please consider switching off the --initialize-insecure option.
2025-11-20T02:02:28.421400Z 6 [Warning] [MY-013360] [Server] Plugin mysql_native_password reported: ''mysql_native_password' is deprecated and will be removed in a future release. Please use caching_sha2_password instead'
2025-11-20 02:02:33+00:00 [Note] [Entrypoint]: Database files initialized
2025-11-20 02:02:33+00:00 [Note] [Entrypoint]: Starting temporary server
2025-11-20T02:02:33.519216Z 0 [Warning] [MY-011068] [Server] The syntax '--skip-host-cache' is deprecated and will be removed in a future release. Please use SET GLOBAL host_cache_size=0 instead.
2025-11-20T02:02:33.520360Z 0 [Warning] [MY-010918] [Server] 'default_authentication_plugin' is deprecated and will be removed in a future release. Please use authentication_policy instead.
2025-11-20T02:02:33.520380Z 0 [System] [MY-010116] [Server] /usr/sbin/mysqld (mysqld 8.0.44) starting as process 124
2025-11-20T02:02:33.534608Z 1 [System] [MY-013576] [InnoDB] InnoDB initialization has started.
2025-11-20T02:02:34.051455Z 1 [System] [MY-013577] [InnoDB] InnoDB initialization has ended.
2025-11-20T02:02:34.535668Z 0 [Warning] [MY-010068] [Server] CA certificate ca.pem is self signed.
2025-11-20T02:02:34.535761Z 0 [System] [MY-013602] [Server] Channel mysql_main configured to support TLS. Encrypted connections are now supported for this channel.
2025-11-20T02:02:34.542719Z 0 [Warning] [MY-011810] [Server] Insecure configuration for --pid-file: Location '/var/run/mysqld' in the path is accessible to all OS users. Consider choosing a different directory.
2025-11-20T02:02:34.577753Z 0 [System] [MY-011323] [Server] X Plugin ready for connections. Socket: /var/run/mysqld/mysqlx.sock
2025-11-20T02:02:34.578040Z 0 [System] [MY-010931] [Server] /usr/sbin/mysqld: ready for connections. Version: '8.0.44'  socket: '/var/run/mysqld/mysqld.sock'  port: 0  MySQL Community Server - GPL.
2025-11-20 02:02:34+00:00 [Note] [Entrypoint]: Temporary server started.
'/var/lib/mysql/mysql.sock' -> '/var/run/mysqld/mysqld.sock'
2025-11-20T02:02:34.606989Z 8 [Warning] [MY-013360] [Server] Plugin mysql_native_password reported: ''mysql_native_password' is deprecated and will be removed in a future release. Please use caching_sha2_password instead'
Warning: Unable to load '/usr/share/zoneinfo/iso3166.tab' as time zone. Skipping it.
Warning: Unable to load '/usr/share/zoneinfo/leap-seconds.list' as time zone. Skipping it.
Warning: Unable to load '/usr/share/zoneinfo/leapseconds' as time zone. Skipping it.
Warning: Unable to load '/usr/share/zoneinfo/tzdata.zi' as time zone. Skipping it.
Warning: Unable to load '/usr/share/zoneinfo/zone.tab' as time zone. Skipping it.
Warning: Unable to load '/usr/share/zoneinfo/zone1970.tab' as time zone. Skipping it.

2025-11-20 02:02:36+00:00 [Note] [Entrypoint]: Stopping temporary server
2025-11-20T02:02:36.254494Z 10 [System] [MY-013172] [Server] Received SHUTDOWN from user root. Shutting down mysqld (Version: 8.0.44).
2025-11-20T02:02:39.507647Z 0 [System] [MY-010910] [Server] /usr/sbin/mysqld: Shutdown complete (mysqld 8.0.44)  MySQL Community Server - GPL.
2025-11-20 02:02:40+00:00 [Note] [Entrypoint]: Temporary server stopped

2025-11-20 02:02:40+00:00 [Note] [Entrypoint]: MySQL init process done. Ready for start up.

2025-11-20T02:02:40.447981Z 0 [Warning] [MY-011068] [Server] The syntax '--skip-host-cache' is deprecated and will be removed in a future release. Please use SET GLOBAL host_cache_size=0 instead.
2025-11-20T02:02:40.448651Z 0 [Warning] [MY-010918] [Server] 'default_authentication_plugin' is deprecated and will be removed in a future release. Please use authentication_policy instead.
2025-11-20T02:02:40.448671Z 0 [System] [MY-010116] [Server] /usr/sbin/mysqld (mysqld 8.0.44) starting as process 1
2025-11-20T02:02:40.455668Z 1 [System] [MY-013576] [InnoDB] InnoDB initialization has started.
2025-11-20T02:02:40.934518Z 1 [System] [MY-013577] [InnoDB] InnoDB initialization has ended.
2025-11-20T02:02:41.333534Z 0 [Warning] [MY-010068] [Server] CA certificate ca.pem is self signed.
2025-11-20T02:02:41.333576Z 0 [System] [MY-013602] [Server] Channel mysql_main configured to support TLS. Encrypted connections are now supported for this channel.
2025-11-20T02:02:41.340829Z 0 [Warning] [MY-011810] [Server] Insecure configuration for --pid-file: Location '/var/run/mysqld' in the path is accessible to all OS users. Consider choosing a different directory.
2025-11-20T02:02:41.381965Z 0 [System] [MY-011323] [Server] X Plugin ready for connections. Bind-address: '::' port: 33060, socket: /var/run/mysqld/mysqlx.sock
2025-11-20T02:02:41.382005Z 0 [System] [MY-010931] [Server] /usr/sbin/mysqld: ready for connections. Version: '8.0.44'  socket: '/var/run/mysqld/mysqld.sock'  port: 3306  MySQL Community Server - GPL.
2025-11-20T02:07:19.267261Z 8 [Warning] [MY-013360] [Server] Plugin mysql_native_password reported: ''mysql_native_password' is deprecated and will be removed in a future release. Please use caching_sha2_password instead'
(test) root@23-94-247-158-host:~/e2e/DB# python conn.py
Traceback (most recent call last):
  File "/home/sz/miniconda3/envs/test/lib/python3.11/site-packages/pymysql/connections.py", line 649, in connect
    sock = socket.create_connection(
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/sz/miniconda3/envs/test/lib/python3.11/socket.py", line 863, in create_connection
    raise exceptions[0]
  File "/home/sz/miniconda3/envs/test/lib/python3.11/socket.py", line 848, in create_connection
    sock.connect(sa)
ConnectionRefusedError: [Errno 111] Connection refused

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/root/e2e/DB/conn.py", line 17, in <module>
    conn = pymysql.connect(
           ^^^^^^^^^^^^^^^^
  File "/home/sz/miniconda3/envs/test/lib/python3.11/site-packages/pymysql/connections.py", line 361, in __init__
    self.connect()
  File "/home/sz/miniconda3/envs/test/lib/python3.11/site-packages/pymysql/connections.py", line 716, in connect
    raise exc
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server on '127.0.0.1' ([Errno 111] Connection refused)")
(test) root@23-94-247-158-host:~/e2e/DB#

### ASSISTANT
你已经非常接近成功了！问题的关键在于：

> ❗ **你的 MySQL 容器虽然在运行，但没有将 3306 端口映射到宿主机！**

---

### 🔍 证据来自 `docker ps` 的输出：

```bash
CONTAINER ID   IMAGE     ...   PORTS                            NAMES
fa7679215d6d   mysql:8.0 ...   3306/tcp, 33060/tcp              mysql-remote
```

注意：这里只有 **`3306/tcp`**，**没有 `0.0.0.0:3306->3306/tcp`**！

这意味着：
- MySQL 在容器内部监听 3306
- ❌ **但没有暴露给宿主机**
- 所以你在宿主机上运行 `python conn.py`（连接 `127.0.0.1:3306`）会 **Connection refused**

而 phpMyAdmin 能工作，是因为它和 MySQL 在同一个 Docker 网络（`mysql-net`），通过容器名 `mysql-remote` 直连，**不走宿主机端口**。

---

### ✅ 解决方案：**重新运行 MySQL 容器，并加上 `-p 3306:3306`**

#### 第 1 步：删除当前的 MySQL 容器
```bash
docker stop mysql-remote
docker rm mysql-remote
```

#### 第 2 步：**重新启动，确保加上 `-p 3306:3306`**

```bash
docker run -d \
  --name mysql-remote \
  --network mysql-net \
  -e MYSQL_ROOT_PASSWORD=sz2025 \
  -e MYSQL_ROOT_HOST=% \
  -p 3306:3306 \
  mysql:8.0 \
  --default-authentication-plugin=mysql_native_password
```

> 💡 `-p 3306:3306` 是关键！它把容器的 3306 映射到宿主机的 3306。

#### 第 3 步：验证端口是否映射成功

```bash
docker ps
```

你应该看到：
```
...   0.0.0.0:3306->3306/tcp, :::3306->3306/tcp   mysql-remote
```

#### 第 4 步：测试本地连接（可选）

```bash
# 安装 MySQL 客户端（如果没装）
sudo apt install mysql-client -y

# 测试连接
mysql -h 127.0.0.1 -P 3306 -u root -psz2025 -e "SELECT 1;"
```

成功输出 `1` 表示连接 OK。

#### 第 5 步：运行你的 Python 脚本

```bash
python conn.py
```

现在应该能成功插入数据！

---

### 📌 为什么之前没加 `-p 3306:3306`？

可能你在某次启动时漏掉了这个参数。**Docker 默认不会暴露端口**，必须显式用 `-p` 指定。

---

### 🛡️ 补充建议（可选）

如果你**只希望 Python 脚本能访问 MySQL，而不对外开放 3306**，也可以：

#### 方法：让 Python 脚本也在 Docker 网络中运行（高级）

但对你当前场景，**加上 `-p 3306:3306` 是最简单直接的方案**。

---

### ✅ 总结

| 问题 | 原因 | 解决 |
|------|------|------|
| `Connection refused` | MySQL 容器未映射 3306 端口到宿主机 | 重启容器，加上 `-p 3306:3306` |

现在执行：

```bash
docker stop mysql-remote && docker rm mysql-remote
docker run -d --name mysql-remote --network mysql-net -e MYSQL_ROOT_PASSWORD=sz2025 -e MYSQL_ROOT_HOST=% -p 3306:3306 mysql:8.0 --default-authentication-plugin=mysql_native_password
python conn.py
```

✅ 即可成功插入 Excel 数据到 MySQL！

插入后，你也能在 phpMyAdmin（`http://<IP>:9081`）中看到 `low_altitude_db.graduates` 表的数据。

### USER
现在python能运行成功，phpmyadmin运行失败了

### ASSISTANT
非常好！现在 **Python 能成功连接 MySQL**，说明 MySQL 容器已正确运行并映射了 `3306` 端口。

但你说 **phpMyAdmin 运行失败了**，我们来快速定位并修复！

---

### 🔍 第一步：确认 phpMyAdmin 当前状态

运行：
```bash
docker ps -a
```

找到 `phpmyadmin` 容器的状态（`Up` 还是 `Exited`？）

如果状态是 **Exited (非 0)**，说明它启动失败了。

---

### 📌 最可能的原因

你**重新创建了 `mysql-remote` 容器**，但 **phpMyAdmin 容器仍然指向旧的网络或旧的容器 ID**，或者它启动时 MySQL 还没 ready。

但更关键的是：**你现在的 `mysql-remote` 是否还在 `mysql-net` 网络中？**

运行：
```bash
docker inspect mysql-remote | grep NetworkMode
docker network inspect mysql-net
```

确保 `mysql-remote` 和 `phpmyadmin` **都在 `mysql-net` 网络中**。

---

### ✅ 推荐操作：**重建 phpMyAdmin 容器（最干净）**

#### 1. 删除旧的 phpMyAdmin
```bash
docker stop phpmyadmin 2>/dev/null
docker rm phpmyadmin
```

#### 2. 确保 MySQL 容器在 `mysql-net` 中（你之前已经加了 `--network mysql-net`，应该没问题）

验证：
```bash
docker inspect mysql-remote -f '{{.NetworkSettings.Networks}}'
```
输出应包含 `"mysql-net"`。

#### 3. 重新运行 phpMyAdmin（使用空闲端口，比如 9081）

```bash
docker run -d \
  --name phpmyadmin \
  --network mysql-net \
  -e PMA_HOST=mysql-remote \
  -e PMA_PORT=3306 \
  -e PMA_USER=root \
  -e PMA_PASSWORD=sz2025 \
  -p 9081:80 \
  phpmyadmin/phpmyadmin:latest
```

> ✅ 注意：`PMA_HOST=mysql-remote` 是容器名，**不是 127.0.0.1**！

#### 4. 查看 phpMyAdmin 日志（如果还是失败）

```bash
docker logs phpmyadmin
```

常见错误：
- `mysqli::real_connect(): (HY000/2002): Connection refused` → MySQL 容器不在同一网络，或名字不对
- `Access denied` → 密码错，或 root 没有 `%` 权限

---

### ✅ 验证网络连通性（关键！）

你可以临时进入 phpMyAdmin 容器，测试是否能 ping 通 MySQL：

```bash
# 启动一个临时容器（同网络）
docker run -it --rm --network mysql-net --entrypoint /bin/sh phpmyadmin/phpmyadmin

# 在容器内执行（查看是否能解析 mysql-remote）
nslookup mysql-remote

# 测试 3306 端口是否通（安装 telnet 或使用 nc）
apk add busybox-extras  # phpmyadmin 是 alpine 镜像
telnet mysql-remote 3306
```

如果 `telnet` 连不上，说明网络或 MySQL 有问题。

---

### 💡 另一种可能性：MySQL 的 `root@%` 用户没建好？

虽然你设置了 `-e MYSQL_ROOT_HOST=%`，但某些 MySQL 8 镜像版本**不会自动创建 `root@%` 用户**。

#### 修复方法：手动授权

进入 MySQL 容器：
```bash
docker exec -it mysql-remote mysql -uroot -psz2025
```

执行：
```sql
CREATE USER 'root'@'%' IDENTIFIED BY 'sz2025';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
```

> ⚠️ 生产环境不要这么干，开发测试可以。

---

### ✅ 最终验证

1. 浏览器访问：`http://23.94.247.158:9081`
2. 应该自动登录（因为设置了 `PMA_USER` 和 `PMA_PASSWORD`）
3. 左侧看到 `low_altitude_db` 数据库 → 成功！

---

### 🔒 总结 Checklist

| 项目 | 状态 |
|------|------|
| ✅ MySQL 容器运行中 | `docker ps` 看到 `mysql-remote` |
| ✅ MySQL 映射了 3306 端口 | `0.0.0.0:3306->3306/tcp` |
| ✅ MySQL 和 phpMyAdmin 在同一网络 | `--network mysql-net` |
| ✅ `PMA_HOST=mysql-remote`（容器名） | 不是 localhost 或 127.0.0.1 |
| ✅ root 用户有远程权限（`root@%`） | 手动授权最保险 |

---

现在请执行：
```bash
docker rm -f phpmyadmin
docker run -d --name phpmyadmin --network mysql-net -e PMA_HOST=mysql-remote -e PMA_USER=root -e PMA_PASSWORD=sz2025 -p 9081:80 phpmyadmin/phpmyadmin
```

然后访问 `http://23.94.247.158:9081`，应该就能看到你的数据了！🎉

如果还有问题，请贴出：
```bash
docker logs phpmyadmin
```

### USER
我的phpmyadmin没有密码？

### ASSISTANT
这个问题很关键：你说 **“phpMyAdmin 没有密码”**，通常意味着：

> ✅ **phpMyAdmin 打开后直接进入了管理界面，没有要求输入用户名/密码**

这**不是** phpMyAdmin 本身没有密码，而是因为你通过环境变量 **预配置了用户名和密码**（`PMA_USER` 和 `PMA_PASSWORD`），所以它自动登录了！

---

### 🔍 为什么会出现“无密码”现象？

你启动 phpMyAdmin 的命令中包含了：

```bash
-e PMA_USER=root \
-e PMA_PASSWORD=sz2025 \
```

👉 这会让 phpMyAdmin **自动使用 root/sz2025 登录 MySQL**，跳过登录页面。

所以你看到的“没有密码”，其实是 **自动登录成功了** ✅

---

### ✅ 如何验证？

1. 打开浏览器访问：`http://你的IP:9081`
2. 看页面右上角：
   - 如果显示：`root@mysql-remote` 或类似
   - 左侧能看到数据库（如 `low_altitude_db`）
   → 说明你已经以 `root` 身份登录！

3. 点击顶部菜单 **“用户账户”**（User accounts）
   - 你会看到 MySQL 的用户列表（包括 `root@%`）
   - 证明你确实拥有最高权限

---

### ⚠️ 安全提醒（非常重要！）

虽然方便，但 **自动登录 + root 权限 + 暴露到公网 = 高危！**

#### 如果你在公网服务器（如 23.94.247.158）：
- 任何人都能访问 `http://23.94.247.158:9081` 并直接获得 root 权限！
- 你的数据库可能被删、被加密勒索、被挖矿！

---

### ✅ 建议的安全做法（至少选一种）

#### ✅ 方案 1：**去掉自动登录，手动输入密码**
启动时 **不要设置** `PMA_USER` 和 `PMA_PASSWORD`：

```bash
docker run -d \
  --name phpmyadmin \
  --network mysql-net \
  -e PMA_HOST=mysql-remote \
  -p 9081:80 \
  phpmyadmin/phpmyadmin:latest
```

这样每次访问都会要求输入用户名/密码（更安全）。

---

#### ✅ 方案 2：**限制 IP 访问（推荐）**
用 Nginx 或 iptables 限制只有你的 IP 能访问 9081。

或者用 SSH 隧道：
```bash
# 本地终端执行（Mac/Linux）
ssh -L 9081:localhost:9081 root@23.94.247.158
```
然后本地浏览器访问 `http://localhost:9081`，流量通过 SSH 加密。

---

#### ✅ 方案 3：**创建专用 MySQL 用户给 phpMyAdmin**
不要用 root！在 MySQL 中执行：

```sql
CREATE USER 'pma_user'@'%' IDENTIFIED BY 'StrongPassword123!';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER ON `low_altitude_db`.* TO 'pma_user'@'%';
FLUSH PRIVILEGES;
```

然后启动 phpMyAdmin 时用这个用户：
```bash
-e PMA_USER=pma_user \
-e PMA_PASSWORD=StrongPassword123! \
```

---

### ❓ 如何“退出”自动登录？

- 清除浏览器 cookie（phpMyAdmin 会存会话）
- 或直接 **重启 phpMyAdmin 容器（不带 PMA_USER/PMA_PASSWORD）**

---

### ✅ 总结

| 问题 | 真相 |
|------|------|
| “phpMyAdmin 没有密码” | 实际是 **自动登录** 了，密码是 `sz2025` |
| 安全吗？ | ❌ 公网暴露 + 自动 root 登录 = **非常危险** |
| 怎么办？ | ✅ 去掉自动登录 / 限制 IP / 用专用用户 |

---

你现在可以：
1. 先确认数据是否可见（说明功能正常）
2. 然后按上述建议提升安全性

需要我帮你生成一个“安全版”的 phpMyAdmin 启动命令吗？