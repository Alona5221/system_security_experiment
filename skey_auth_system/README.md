# S/Key 身份认证系统（Python C/S 桌面版）

本项目实现课程实验《基于 S/Key 协议的身份认证系统设计与实现》，采用 **本地可运行的 C/S 架构**：
- 服务端：Python + socket + sqlite3
- 客户端：Python + tkinter（桌面 GUI）
- 核心认证：S/Key 一次性口令链（SHA-256）
- 通信协议：JSON 文本行协议（UTF-8，消息以 `\n` 结束）

## 目录结构

```text
skey_auth_system/
├─ server/
│  ├─ server_main.py
│  ├─ server_core.py
│  ├─ auth_service.py
│  ├─ skey_service.py
│  ├─ captcha_service.py
│  ├─ db.py
│  ├─ models.py
│  └─ config.py
├─ client/
│  ├─ client_main.py
│  ├─ client_ui.py
│  ├─ client_core.py
│  ├─ skey_client.py
│  └─ config.py
├─ common/
│  ├─ protocol.py
│  ├─ utils.py
│  └─ constants.py
├─ data/
│  └─ auth_system.db.txt
├─ logs/
│  └─ server.log
├─ README.md
└─ requirements.txt
```


> 说明：仓库中使用 `data/auth_system.db.txt` 作为文本占位；服务端启动会自动创建真实的 `data/auth_system.db` 二进制 SQLite 文件。

## 环境要求

- Python 3.9+
- 标准库依赖（tkinter、socket、sqlite3、hashlib、threading、datetime、secrets、logging、json）

## 安装依赖

```bash
pip install -r requirements.txt
```

> 本项目仅使用标准库，`requirements.txt` 为占位说明。

## 运行方式

在项目根目录 `skey_auth_system` 下执行：

```bash
python server/server_main.py
python client/client_main.py
```

## 功能说明

### 1) 注册（register）
客户端输入用户名、主口令、链长度：
- 本地生成随机 `seed`
- 本地生成 `xN`（链尾）
- 发送 `username/seed/chain_length/chain_tail`
- 服务端保存用户状态（不保存主口令）

### 2) 获取挑战（request_challenge）
服务端返回：
- `seed`
- `current_index`
- `captcha_id`
- `captcha_code`
- `expires_in`

### 3) 登录（login）
客户端输入用户名、主口令、验证码，按挑战信息本地计算 OTP：
- 若服务端当前保存 `x_current_index`
- 客户端提交 `x_(current_index - 1)`

服务端验证：
`sha256(submitted_otp) == current_hash`

成功后：
- `current_hash = submitted_otp`
- `current_index -= 1`

### 4) 重协商（renegotiate）
当序列耗尽（`current_index == 0`）后：
- 客户端输入主口令并发起重协商
- 本地生成新 seed 和新链尾
- 服务端更新链参数，可继续登录

### 5) 日志查询（query_logs）
支持：
- 全部日志
- 按用户名筛选
- 按结果（success/fail）筛选
- 时间倒序显示

GUI 使用 `ttk.Treeview` 显示日志字段：
- ID/时间/用户名/IP/操作/结果/原因/序列号/详情

## S/Key 算法实现

设：
- 主口令：`password`
- 随机种子：`seed`
- `H = sha256_hex`

定义：
- `x0 = H(password + ":" + seed)`
- `x1 = H(x0)`
- ...
- `xN = H(xN-1)`

服务器初始化保存：
- `seed`
- `chain_length = N`
- `current_index = N`
- `current_hash = xN`

登录时提交：
- `otp = x_(current_index - 1)`

验证规则：
- `H(otp) == current_hash`

## 错误码

- USER_NOT_FOUND
- USER_EXISTS
- USER_DISABLED
- INVALID_REQUEST
- CAPTCHA_NOT_FOUND
- CAPTCHA_EXPIRED
- CAPTCHA_USED
- CAPTCHA_MISMATCH
- OTP_INVALID
- SEQUENCE_EXHAUSTED
- NETWORK_ERROR
- DB_ERROR
- INTERNAL_ERROR

## 可演示测试场景

1. 正常注册
2. 正常登录
3. 错误验证码登录失败
4. 错误主口令导致 OTP 校验失败
5. 重放旧 OTP 失败
6. 验证码过期失败（等待 60 秒后测试）
7. 链长度设为 3 快速验证耗尽
8. 序列耗尽后重协商成功
9. 查看成功/失败日志

## 说明

- 所有时间字段统一使用 ISO 字符串（UTC）。
- 所有哈希值统一为小写十六进制。
- 所有失败场景返回 `ok=false/message/error_code` 并写审计日志。
