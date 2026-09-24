# -*- coding: utf-8 -*-
"""
数字大小写转换工具 — 图形界面

运行：python main.py
依赖：仅需 Python 标准库 tkinter（无需额外安装）
"""

import sys
import os
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox

from converter import to_chinese, parse_chinese


def _resource_path(relative):
    """兼容源码运行与 PyInstaller 打包后的资源路径。"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def _enable_dpi_awareness():
    """Windows 高分屏下启用 DPI 感知，避免界面模糊。"""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

# ---------- 配色 ----------
BG = "#f5f6fa"          # 窗口背景
CARD = "#ffffff"        # 卡片背景
PRIMARY = "#2f6fed"     # 主色
PRIMARY_DARK = "#1f57c9"
TEXT = "#1f2430"        # 主文字
SUBTEXT = "#6b7280"     # 次要文字
BORDER = "#e2e5ec"
SUCCESS = "#16a34a"
ERROR = "#dc2626"

FONT_UI = ("Microsoft YaHei UI", 10)
FONT_UI_SM = ("Microsoft YaHei UI", 9)
FONT_TITLE = ("Microsoft YaHei UI", 16, "bold")
FONT_SUBTITLE = ("Microsoft YaHei UI", 9)
FONT_RESULT = ("Microsoft YaHei UI", 15, "bold")
FONT_MONO = ("Consolas", 11)


class NumberCaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("数字大小写转换工具")

        # 设置窗口图标
        try:
            self.root.iconbitmap(_resource_path("icon.ico"))
        except Exception:
            pass

        # 按系统 DPI 缩放窗口尺寸（默认按 96dpi 逻辑值设计）
        self.scale = root.winfo_fpixels("1i") / 96.0
        w, h = int(760 * self.scale), int(640 * self.scale)
        self.root.geometry(f"{w}x{h}")
        self.root.minsize(int(680 * self.scale), int(580 * self.scale))
        self.root.configure(bg=BG)

        # 状态变量
        self.mode_upper = tk.BooleanVar(value=True)    # 大写 / 小写
        self.mode_money = tk.BooleanVar(value=True)    # 金额 / 普通
        self.auto_detect = tk.BooleanVar(value=True)   # 自动识别方向
        self.history = []

        self._setup_style()
        self._build_ui()

    # ------------------------------------------------------------------
    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TCheckbutton",
                        background=CARD, foreground=TEXT,
                        font=FONT_UI, focuscolor=CARD)
        style.map("TCheckbutton",
                  background=[("active", CARD)],
                  foreground=[("active", PRIMARY)])

        style.configure("TCombobox",
                        fieldbackground=CARD, background=CARD,
                        foreground=TEXT, arrowcolor=PRIMARY,
                        font=FONT_UI, padding=4)

    # ------------------------------------------------------------------
    def _build_ui(self):
        # 顶部标题栏
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=24, pady=(18, 10))

        tk.Label(header, text="数字大小写转换",
                 bg=BG, fg=TEXT, font=FONT_TITLE).pack(anchor="w")
        tk.Label(header, text="支持阿拉伯数字 ⇄ 中文大小写、财务金额格式",
                 bg=BG, fg=SUBTEXT, font=FONT_SUBTITLE).pack(anchor="w", pady=(2, 0))

        # 输入卡片
        input_card = tk.Frame(self.root, bg=CARD, highlightthickness=1,
                              highlightbackground=BORDER)
        input_card.pack(fill="x", padx=24, pady=(4, 10))

        inner = tk.Frame(input_card, bg=CARD)
        inner.pack(fill="x", padx=16, pady=14)

        tk.Label(inner, text="输入内容", bg=CARD, fg=SUBTEXT,
                 font=FONT_UI_SM).pack(anchor="w")

        entry_row = tk.Frame(inner, bg=CARD)
        entry_row.pack(fill="x", pady=(6, 0))

        self.entry = tk.Entry(entry_row, font=("Microsoft YaHei UI", 13),
                              bg="#fafbfd", fg=TEXT, relief="flat",
                              insertbackground=PRIMARY,
                              highlightthickness=1,
                              highlightbackground=BORDER,
                              highlightcolor=PRIMARY)
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self.do_convert())
        self.entry.bind("<KeyRelease>", self._on_typing)

        clear_btn = tk.Button(entry_row, text="清空", command=self.clear_all,
                              bg="#eef1f7", fg=TEXT, font=FONT_UI,
                              relief="flat", cursor="hand2",
                              activebackground="#e0e5ef",
                              padx=14, pady=6)
        clear_btn.pack(side="left")

        tk.Label(inner, text="提示：输入阿拉伯数字自动转中文，输入中文自动转回数字",
                 bg=CARD, fg=SUBTEXT, font=("Microsoft YaHei UI", 8)
                 ).pack(anchor="w", pady=(6, 0))

        # 选项卡片
        opt_card = tk.Frame(self.root, bg=CARD, highlightthickness=1,
                            highlightbackground=BORDER)
        opt_card.pack(fill="x", padx=24, pady=(0, 10))

        opt_inner = tk.Frame(opt_card, bg=CARD)
        opt_inner.pack(fill="x", padx=16, pady=12)

        # 第一行：大小写 + 格式
        row1 = tk.Frame(opt_inner, bg=CARD)
        row1.pack(fill="x")

        tk.Label(row1, text="中文写法", bg=CARD, fg=SUBTEXT,
                 font=FONT_UI_SM, width=8, anchor="w").pack(side="left")

        self.rdo_upper = ttk.Radiobutton(row1, text="大写（壹贰叁）",
                                         variable=self.mode_upper, value=True,
                                         command=self._on_option_change)
        self.rdo_upper.pack(side="left", padx=(0, 16))
        self.rdo_lower = ttk.Radiobutton(row1, text="小写（一二三）",
                                         variable=self.mode_upper, value=False,
                                         command=self._on_option_change)
        self.rdo_lower.pack(side="left")

        # 第二行：应用场景 + 自动识别
        row2 = tk.Frame(opt_inner, bg=CARD)
        row2.pack(fill="x", pady=(10, 0))

        tk.Label(row2, text="输出格式", bg=CARD, fg=SUBTEXT,
                 font=FONT_UI_SM, width=8, anchor="w").pack(side="left")

        self.chk_money = ttk.Checkbutton(row2, text="财务金额格式（元角分）",
                                         variable=self.mode_money,
                                         command=self._on_option_change)
        self.chk_money.pack(side="left", padx=(0, 16))

        self.chk_auto = ttk.Checkbutton(row2, text="自动识别方向",
                                        variable=self.auto_detect,
                                        command=self._on_option_change)
        self.chk_auto.pack(side="left")

        # 转换按钮
        btn_row = tk.Frame(self.root, bg=BG)
        btn_row.pack(fill="x", padx=24, pady=(0, 10))

        self.convert_btn = tk.Button(btn_row, text="转 换",
                                     command=self.do_convert,
                                     bg=PRIMARY, fg="white",
                                     font=("Microsoft YaHei UI", 11, "bold"),
                                     relief="flat", cursor="hand2",
                                     activebackground=PRIMARY_DARK,
                                     activeforeground="white",
                                     pady=9)
        self.convert_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.copy_btn = tk.Button(btn_row, text="复制结果",
                                  command=self.copy_result,
                                  bg="#eef1f7", fg=TEXT,
                                  font=("Microsoft YaHei UI", 10),
                                  relief="flat", cursor="hand2",
                                  activebackground="#e0e5ef",
                                  padx=18, pady=9)
        self.copy_btn.pack(side="left")

        # 结果卡片
        res_card = tk.Frame(self.root, bg=CARD, highlightthickness=1,
                            highlightbackground=BORDER)
        res_card.pack(fill="x", padx=24, pady=(0, 10))

        res_inner = tk.Frame(res_card, bg=CARD)
        res_inner.pack(fill="x", padx=16, pady=14)

        res_header = tk.Frame(res_inner, bg=CARD)
        res_header.pack(fill="x")
        tk.Label(res_header, text="转换结果", bg=CARD, fg=SUBTEXT,
                 font=FONT_UI_SM).pack(side="left")
        self.direction_label = tk.Label(res_header, text="", bg=CARD,
                                        fg=PRIMARY, font=("Microsoft YaHei UI", 8))
        self.direction_label.pack(side="right")

        self.result_var = tk.StringVar(value="等待输入…")
        self.result_label = tk.Label(res_inner, textvariable=self.result_var,
                                     bg=CARD, fg=SUBTEXT, font=FONT_RESULT,
                                     wraplength=int(660 * self.scale),
                                     justify="left", anchor="w")
        self.result_label.pack(fill="x", pady=(8, 0))

        # 历史记录
        hist_card = tk.Frame(self.root, bg=CARD, highlightthickness=1,
                             highlightbackground=BORDER)
        hist_card.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        hist_inner = tk.Frame(hist_card, bg=CARD)
        hist_inner.pack(fill="both", expand=True, padx=16, pady=12)

        hist_header = tk.Frame(hist_inner, bg=CARD)
        hist_header.pack(fill="x")
        tk.Label(hist_header, text="历史记录", bg=CARD, fg=SUBTEXT,
                 font=FONT_UI_SM).pack(side="left")
        tk.Button(hist_header, text="清除", command=self.clear_history,
                  bg=CARD, fg=SUBTEXT, font=("Microsoft YaHei UI", 8),
                  relief="flat", cursor="hand2", activebackground=CARD,
                  activeforeground=PRIMARY).pack(side="right")

        list_wrap = tk.Frame(hist_inner, bg=CARD)
        list_wrap.pack(fill="both", expand=True, pady=(6, 0))

        self.hist_list = tk.Listbox(list_wrap, font=("Microsoft YaHei UI", 10),
                                    bg="#fafbfd", fg=TEXT, relief="flat",
                                    highlightthickness=1,
                                    highlightbackground=BORDER,
                                    selectbackground="#dbe6ff",
                                    selectforeground=TEXT,
                                    activestyle="none")
        self.hist_list.pack(side="left", fill="both", expand=True)
        self.hist_list.bind("<Double-Button-1>", self._reuse_history)

        sb = ttk.Scrollbar(list_wrap, orient="vertical",
                           command=self.hist_list.yview)
        sb.pack(side="right", fill="y")
        self.hist_list.config(yscrollcommand=sb.set)

        self.entry.focus_set()

    # ------------------------------------------------------------------
    # 事件处理
    # ------------------------------------------------------------------
    def _on_typing(self, event=None):
        """输入时实时预览（轻量，不做完整转换）。"""
        text = self.entry.get().strip()
        if not text:
            self._set_result("等待输入…", SUBTEXT, "")
            return
        try:
            result, direction = self._convert(text)
            self._set_result(result, TEXT, direction)
        except Exception:
            # 输入过程中不报错，静默等待
            pass

    def _on_option_change(self):
        """选项变化时立即重新转换。"""
        text = self.entry.get().strip()
        if text:
            self.do_convert()

    def _convert(self, text):
        """根据当前选项执行转换，返回 (结果, 方向说明)。"""
        money = self.mode_money.get()

        # 是否为阿拉伯数字输入
        probe = text.replace(",", "").replace("，", "").lstrip("-+").lstrip("负")
        is_arabic = bool(probe) and all(c.isdigit() or c == "." for c in probe) \
            and probe.count(".") <= 1

        if self.auto_detect.get():
            if is_arabic:
                result = to_chinese(text, upper=self.mode_upper.get(), money=money)
                tag = "大写" if self.mode_upper.get() else "小写"
                direction = f"阿拉伯数字 → 中文{tag}" + ("（金额）" if money else "")
            else:
                result = parse_chinese(text)
                direction = "中文 → 阿拉伯数字"
        else:
            # 强制方向：按用户勾选的大写/小写决定输出
            if is_arabic:
                result = to_chinese(text, upper=self.mode_upper.get(), money=money)
                tag = "大写" if self.mode_upper.get() else "小写"
                direction = f"阿拉伯数字 → 中文{tag}" + ("（金额）" if money else "")
            else:
                result = to_chinese(parse_chinese(text),
                                    upper=self.mode_upper.get(), money=money)
                direction = f"中文 → 中文{'大写' if self.mode_upper.get() else '小写'}"

        return result, direction

    def do_convert(self):
        text = self.entry.get().strip()
        if not text:
            self._set_result("请先输入内容", ERROR, "")
            return
        try:
            result, direction = self._convert(text)
        except Exception as e:
            self._set_result(f"转换失败：{e}", ERROR, "")
            return
        self._set_result(result, TEXT, direction)
        self._add_history(text, result)

    def _set_result(self, text, color, direction):
        self.result_var.set(text)
        self.result_label.config(fg=color)
        self.direction_label.config(text=direction)

    def _add_history(self, src, dst):
        item = f"{src}  →  {dst}"
        if self.history and self.history[0] == item:
            return
        self.history.insert(0, item)
        self.history = self.history[:50]
        self._refresh_history()

    def _refresh_history(self):
        self.hist_list.delete(0, tk.END)
        for item in self.history:
            self.hist_list.insert(tk.END, "  " + item)

    def _reuse_history(self, event=None):
        sel = self.hist_list.curselection()
        if not sel:
            return
        item = self.history[sel[0]]
        src = item.split("  →  ")[0]
        self.entry.delete(0, tk.END)
        self.entry.insert(0, src)
        self.do_convert()

    def clear_history(self):
        self.history.clear()
        self._refresh_history()

    def clear_all(self):
        self.entry.delete(0, tk.END)
        self._set_result("等待输入…", SUBTEXT, "")
        self.entry.focus_set()

    def copy_result(self):
        result = self.result_var.get()
        if not result or result in ("等待输入…", "请先输入内容"):
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(result)
        original = self.copy_btn.cget("text")
        self.copy_btn.config(text="已复制 ✓", fg=SUCCESS)
        self.root.after(1200, lambda: self.copy_btn.config(text=original, fg=TEXT))


def main():
    _enable_dpi_awareness()
    root = tk.Tk()
    NumberCaseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
