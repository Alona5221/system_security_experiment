"""Tkinter GUI for S/Key authentication client."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from client.client_core import ClientCore
from client.config import DEFAULT_CHAIN_LENGTH, DEFAULT_HOST, DEFAULT_PORT
from client.skey_client import SKeyClient
from common.constants import REQUEST_TYPES


class ClientUI:
    """Main client window and user interactions."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("S/Key 身份认证客户端")
        self.root.geometry("980x700")

        self.challenge_seed = ""
        self.challenge_index = 0
        self.captcha_id = ""

        self.var_host = tk.StringVar(value=DEFAULT_HOST)
        self.var_port = tk.StringVar(value=str(DEFAULT_PORT))
        self.var_username = tk.StringVar()
        self.var_password = tk.StringVar()
        self.var_chain_length = tk.StringVar(value=str(DEFAULT_CHAIN_LENGTH))
        self.var_captcha_show = tk.StringVar(value="(未获取)")
        self.var_captcha_input = tk.StringVar()
        self.var_log_username = tk.StringVar()
        self.var_log_result = tk.StringVar(value="")

        self._build_widgets()

    def _build_widgets(self) -> None:
        frm = ttk.Frame(self.root, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(frm, text="服务器地址").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_host, width=20).grid(row=row, column=1, sticky="w")
        ttk.Label(frm, text="端口").grid(row=row, column=2, sticky="w")
        ttk.Entry(frm, textvariable=self.var_port, width=10).grid(row=row, column=3, sticky="w")

        row += 1
        ttk.Label(frm, text="用户名").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_username, width=20).grid(row=row, column=1, sticky="w")
        ttk.Label(frm, text="主口令").grid(row=row, column=2, sticky="w")
        ttk.Entry(frm, textvariable=self.var_password, show="*", width=20).grid(row=row, column=3, sticky="w")

        row += 1
        ttk.Label(frm, text="链长度").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_chain_length, width=10).grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(frm, text="当前验证码").grid(row=row, column=0, sticky="w")
        ttk.Label(frm, textvariable=self.var_captcha_show, foreground="blue").grid(row=row, column=1, sticky="w")
        ttk.Label(frm, text="验证码输入").grid(row=row, column=2, sticky="w")
        ttk.Entry(frm, textvariable=self.var_captcha_input, width=20).grid(row=row, column=3, sticky="w")

        row += 1
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=row, column=0, columnspan=4, sticky="w", pady=8)

        ttk.Button(btn_frame, text="获取挑战", command=self.on_request_challenge).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="登录", command=self.on_login).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="重协商", command=self.on_renegotiate).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="注册", command=self.on_register).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="查看日志", command=self.on_query_logs).pack(side=tk.LEFT, padx=5)

        row += 1
        ttk.Label(frm, text="状态输出").grid(row=row, column=0, sticky="w")
        row += 1
        self.txt_status = tk.Text(frm, height=10, width=110)
        self.txt_status.grid(row=row, column=0, columnspan=4, sticky="nsew")

        row += 1
        filter_frame = ttk.Frame(frm)
        filter_frame.grid(row=row, column=0, columnspan=4, sticky="w", pady=(8, 0))
        ttk.Label(filter_frame, text="日志筛选-用户名").pack(side=tk.LEFT)
        ttk.Entry(filter_frame, textvariable=self.var_log_username, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Label(filter_frame, text="结果").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.var_log_result, width=10, values=["", "success", "fail"]).pack(
            side=tk.LEFT, padx=5
        )

        row += 1
        cols = ("id", "created_at", "username", "client_ip", "action", "result", "reason", "seq_no", "detail")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", height=14)
        headers = ["ID", "时间", "用户名", "IP", "操作", "结果", "原因", "序列号", "详情"]
        widths = [60, 180, 100, 120, 120, 80, 120, 80, 200]
        for col, title, width in zip(cols, headers, widths):
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="center")
        self.tree.grid(row=row, column=0, columnspan=4, sticky="nsew", pady=6)

        frm.rowconfigure(row, weight=1)
        frm.columnconfigure(3, weight=1)

    def _client(self) -> ClientCore:
        return ClientCore(self.var_host.get().strip(), int(self.var_port.get().strip() or 0))

    def _log_status(self, text: str) -> None:
        self.txt_status.insert(tk.END, text + "\n")
        self.txt_status.see(tk.END)

    def _send(self, req_type: str, data: dict) -> dict:
        payload = {"type": req_type, "data": data}
        return self._client().send_request(payload)

    def on_register(self) -> None:
        """Register user with generated seed and chain tail."""
        username = self.var_username.get().strip()
        password = self.var_password.get().strip()
        if not username or not password:
            messagebox.showwarning("提示", "请输入用户名和主口令")
            return

        chain_length = int(self.var_chain_length.get().strip() or DEFAULT_CHAIN_LENGTH)
        seed = SKeyClient.generate_seed()
        chain_tail = SKeyClient.compute_chain_tail(password, seed, chain_length)
        resp = self._send(
            REQUEST_TYPES["REGISTER"],
            {"username": username, "seed": seed, "chain_length": chain_length, "chain_tail": chain_tail},
        )
        self._log_status(f"[注册] {resp}")

    def on_request_challenge(self) -> None:
        """Request challenge and display captcha."""
        username = self.var_username.get().strip()
        resp = self._send(REQUEST_TYPES["REQUEST_CHALLENGE"], {"username": username})
        self._log_status(f"[获取挑战] {resp}")
        if resp.get("ok"):
            data = resp.get("data", {})
            self.challenge_seed = data.get("seed", "")
            self.challenge_index = int(data.get("current_index", 0))
            self.captcha_id = data.get("captcha_id", "")
            self.var_captcha_show.set(data.get("captcha_code", ""))

    def on_login(self) -> None:
        """Compute OTP locally and submit login request."""
        username = self.var_username.get().strip()
        password = self.var_password.get().strip()
        captcha_input = self.var_captcha_input.get().strip()

        if not self.challenge_seed or not self.captcha_id:
            messagebox.showwarning("提示", "请先获取挑战")
            return

        try:
            otp = SKeyClient.compute_otp(password, self.challenge_seed, self.challenge_index)
        except ValueError as exc:
            self._log_status(f"[登录] 计算 OTP 失败: {exc}")
            return

        resp = self._send(
            REQUEST_TYPES["LOGIN"],
            {
                "username": username,
                "captcha_id": self.captcha_id,
                "captcha_input": captcha_input,
                "otp": otp,
            },
        )
        self._log_status(f"[登录] {resp}")

        if resp.get("ok"):
            self.challenge_index = int(resp.get("data", {}).get("next_index", self.challenge_index - 1))
            self.var_captcha_input.set("")

    def on_renegotiate(self) -> None:
        """Regenerate seed and chain tail then renegotiate sequence."""
        username = self.var_username.get().strip()
        password = self.var_password.get().strip()
        chain_length = int(self.var_chain_length.get().strip() or DEFAULT_CHAIN_LENGTH)

        seed = SKeyClient.generate_seed()
        new_chain_tail = SKeyClient.compute_chain_tail(password, seed, chain_length)
        resp = self._send(
            REQUEST_TYPES["RENEGOTIATE"],
            {
                "username": username,
                "new_seed": seed,
                "chain_length": chain_length,
                "new_chain_tail": new_chain_tail,
            },
        )
        self._log_status(f"[重协商] {resp}")

    def on_query_logs(self) -> None:
        """Query and render logs in Treeview."""
        username = self.var_log_username.get().strip()
        result = self.var_log_result.get().strip()
        resp = self._send(REQUEST_TYPES["QUERY_LOGS"], {"username": username, "result": result, "limit": 200})
        self._log_status(f"[日志查询] {resp.get('message')}")

        if not resp.get("ok"):
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in resp.get("data", {}).get("logs", []):
            self.tree.insert(
                "",
                tk.END,
                values=(
                    row.get("id", ""),
                    row.get("created_at", ""),
                    row.get("username", ""),
                    row.get("client_ip", ""),
                    row.get("action", ""),
                    row.get("result", ""),
                    row.get("reason", ""),
                    row.get("seq_no", ""),
                    row.get("detail", ""),
                ),
            )
