# -*- coding: utf-8 -*-
"""
专家整体评审界面（Tkinter 桌面版）

评审单位：一条原始需求 vs 两份工程化需求集合（A / B，已盲化）
评审维度（逐条维度选择 A更好 / 平局 / B更好）：
  - 拆分准确性  decomposition：是否正确理解并拆解了原始需求
  - 技术可信度  accuracy     ：具体数值/配置/参数是否可信
  - 完整性      completeness ：重要方面有无遗漏
  - 可操作性    actionability：工程师能否直接用于指导工作
  - 总体推荐    overall      ：综合推荐哪份

运行：
  python scripts/expert_review_ui.py [--reviewer 1|2]
  或双击 expert_review.bat
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import font as tkfont
from tkinter import messagebox, ttk

_SCRIPT_DIR  = Path(__file__).resolve().parent
PROJECT_ROOT = _SCRIPT_DIR.parent
DATA_DIR     = PROJECT_ROOT / "data" / "processed"
SAMPLE_PATH  = DATA_DIR / "expert_sample.json"

DIMS = [
    ("decomposition",  "拆分准确性", "是否正确理解并完整拆解了原始需求的所有方面"),
    ("accuracy",       "技术可信度", "具体数值、配置、参数是否有工程依据、可信可用"),
    ("traceability",   "可追溯  性", "数值/参数是否能追溯到规范条文或厂商资料（不是凭空写的）"),
    ("completeness",   "完    整  性", "重要工程方面有无遗漏，覆盖是否全面"),
    ("actionability",  "可 操 作 性", "工程师能否直接据此指导设计/采购/施工"),
    ("overall",        "总 体 推 荐", "综合来看，哪份更值得信赖、推荐用于实际工程"),
]
CHOICES = ["A 更好", "平  局", "B 更好"]
CHOICE_VALS = ["A", "tie", "B"]

# 高亮数字和工程单位的正则
_NUM_RE = re.compile(
    r"\d+\.?\d*\s*(?:MPa|bar|°C|℃|秒|s|分钟|min|mm|cm|m|%|ppm|m³/h|kW|Hz|V|A|bar|kPa|rpm)"
    r"|\b\d{1,3}(?:\.\d+)?(?=\s*(?:MPa|bar|°C|秒|分钟|mm|%))",
    re.IGNORECASE,
)


class ExpertReviewApp(tk.Tk):
    def __init__(self, reviewer: str) -> None:
        super().__init__()
        self.reviewer = reviewer          # "expert1" or "expert2"
        self.records: list[dict] = []
        self.idx = 0

        self._load_data()
        self.title(f"专家整体评审  [{reviewer}]  —  v3 工程需求质量对比")
        self.geometry("1400x860")
        self.minsize(1100, 700)
        self._build_ui()
        self._load_record()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── 数据 ──────────────────────────────────────────────────────────────────

    def _load_data(self) -> None:
        if not SAMPLE_PATH.exists():
            messagebox.showerror("找不到样本文件",
                f"请先运行：\n  python scripts/58_sample_for_expert_review.py\n\n"
                f"期望路径：{SAMPLE_PATH}")
            self.destroy(); sys.exit(1)
        with open(SAMPLE_PATH, encoding="utf-8") as f:
            self.records = json.load(f)
        # 找到第一条未完成的
        for i, r in enumerate(self.records):
            if not r.get(self.reviewer, {}).get("overall"):
                self.idx = i; break
        else:
            self.idx = 0

    def _save(self) -> None:
        with open(SAMPLE_PATH, "w", encoding="utf-8") as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)

    # ── UI 构建 ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        bold_font   = tkfont.Font(family="Microsoft YaHei", size=11, weight="bold")
        label_font  = tkfont.Font(family="Microsoft YaHei", size=10)
        text_font   = tkfont.Font(family="Microsoft YaHei", size=10)
        header_font = tkfont.Font(family="Microsoft YaHei", size=12, weight="bold")

        # ── 顶部：进度 + 原始需求 ──────────────────────────────────────────
        top = tk.Frame(self, bg="#2c3e50", pady=6)
        top.pack(fill=tk.X)

        self._prog_var = tk.StringVar()
        tk.Label(top, textvariable=self._prog_var, bg="#2c3e50", fg="white",
                 font=bold_font).pack(side=tk.LEFT, padx=12)

        self._layer_var = tk.StringVar()
        tk.Label(top, textvariable=self._layer_var, bg="#e67e22", fg="white",
                 font=label_font, padx=6, pady=2).pack(side=tk.LEFT, padx=6)

        tk.Button(top, text="💾 保存", command=self._save,
                  bg="#27ae60", fg="white", relief=tk.FLAT,
                  font=label_font, padx=10).pack(side=tk.RIGHT, padx=8)
        tk.Button(top, text="📊 导出CSV", command=self._export_csv,
                  bg="#2980b9", fg="white", relief=tk.FLAT,
                  font=label_font, padx=10).pack(side=tk.RIGHT, padx=4)

        # 原始需求区
        req_frame = tk.LabelFrame(self, text=" 原始需求 ", font=bold_font,
                                  bg="#ecf0f1", padx=8, pady=4)
        req_frame.pack(fill=tk.X, padx=10, pady=(6, 0))

        self._req_id_var = tk.StringVar()
        tk.Label(req_frame, textvariable=self._req_id_var,
                 bg="#ecf0f1", font=bold_font, fg="#8e44ad").pack(anchor=tk.W)
        self._req_text = tk.Text(req_frame, height=3, wrap=tk.WORD, relief=tk.FLAT,
                                 font=text_font, bg="#ecf0f1", state=tk.DISABLED)
        self._req_text.pack(fill=tk.X)

        # ── 下部：评审维度（先 pack 确保空间，再让中部 expand 填剩余）──────
        bottom = tk.Frame(self, bg="white", pady=6)
        bottom.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 6))

        # ── 中部：两份输出对比（PanedWindow）──────────────────────────────
        pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=6,
                              bg="#bdc3c7", sashrelief=tk.RAISED)
        pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        for side, attr in [("A", "_text_a"), ("B", "_text_b")]:
            frame = tk.LabelFrame(pane, text=f" 方案 {side} ", font=bold_font,
                                  padx=4, pady=4)
            pane.add(frame, stretch="always")
            scroll = tk.Scrollbar(frame)
            scroll.pack(side=tk.RIGHT, fill=tk.Y)
            txt = tk.Text(frame, wrap=tk.WORD, yscrollcommand=scroll.set,
                          font=text_font, state=tk.DISABLED, spacing1=3,
                          relief=tk.FLAT, bg="#fdfefe")
            txt.pack(fill=tk.BOTH, expand=True)
            scroll.config(command=txt.yview)
            txt.tag_config("num", foreground="#c0392b", font=
                           tkfont.Font(family="Microsoft YaHei", size=10, weight="bold"))
            txt.tag_config("bullet", foreground="#2980b9")
            setattr(self, attr, txt)

        # 维度评分
        dim_frame = tk.LabelFrame(bottom, text=" 整体评价（每条选择哪份更好）",
                                  font=bold_font, bg="white", padx=10, pady=6)
        dim_frame.pack(fill=tk.X)

        self._dim_vars: dict[str, tk.StringVar] = {}
        for row_idx, (key, label, hint) in enumerate(DIMS):
            var = tk.StringVar(value="")
            self._dim_vars[key] = var

            tk.Label(dim_frame, text=f"{label}：", font=bold_font,
                     bg="white", width=12, anchor=tk.E).grid(
                row=row_idx, column=0, sticky=tk.E, pady=3)
            tk.Label(dim_frame, text=hint, font=label_font,
                     bg="white", fg="#7f8c8d", anchor=tk.W).grid(
                row=row_idx, column=1, sticky=tk.W, padx=6)

            rb_frame = tk.Frame(dim_frame, bg="white")
            rb_frame.grid(row=row_idx, column=2, sticky=tk.W, padx=20)
            for val, text in zip(CHOICE_VALS, CHOICES):
                color = ("#2ecc71" if val == "A" else
                         "#95a5a6" if val == "tie" else "#e74c3c")
                tk.Radiobutton(rb_frame, text=text, variable=var, value=val,
                               bg="white", font=label_font, fg=color,
                               activebackground="white",
                               command=self._on_rating_change).pack(
                    side=tk.LEFT, padx=14)

        # 备注
        note_row = tk.Frame(bottom, bg="white")
        note_row.pack(fill=tk.X, pady=(6, 0))
        tk.Label(note_row, text="备注：", font=bold_font, bg="white",
                 width=8, anchor=tk.E).pack(side=tk.LEFT)
        self._note_var = tk.StringVar()
        tk.Entry(note_row, textvariable=self._note_var, font=label_font,
                 relief=tk.GROOVE).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

        # 导航按钮
        nav = tk.Frame(bottom, bg="white", pady=4)
        nav.pack(fill=tk.X)
        tk.Button(nav, text="← 上一条", command=self._prev,
                  font=label_font, width=12, relief=tk.GROOVE).pack(side=tk.LEFT, padx=10)
        self._status_var = tk.StringVar(value="")
        tk.Label(nav, textvariable=self._status_var, font=label_font,
                 bg="white", fg="#27ae60").pack(side=tk.LEFT, expand=True)
        tk.Button(nav, text="下一条 →", command=self._next,
                  font=bold_font, width=12, bg="#2980b9", fg="white",
                  relief=tk.FLAT).pack(side=tk.RIGHT, padx=10)

    # ── 数据 ↔ UI 绑定 ────────────────────────────────────────────────────────

    def _load_record(self) -> None:
        r = self.records[self.idx]
        n = len(self.records)
        done = sum(1 for rec in self.records
                   if rec.get(self.reviewer, {}).get("overall"))

        self._prog_var.set(f"进度  {self.idx + 1} / {n}  （已完成 {done}/{n}）")
        layer_label = {"A":"数值密集","B":"安全关键","C":"差异最大","D":"随机"}
        self._layer_var.set(f"层 {r['layer']}: {layer_label.get(r['layer'],'')}")

        self._req_id_var.set(
            f"{r['requirement_id']}  [{r.get('stakeholder','')}]")
        self._set_text(self._req_text, r["requirement_text"])

        self._set_shalls(self._text_a, r["shalls_a"])
        self._set_shalls(self._text_b, r["shalls_b"])

        # 恢复已有评分
        saved = r.get(self.reviewer, {})
        for key, var in self._dim_vars.items():
            var.set(saved.get(key, ""))
        self._note_var.set(saved.get("note", ""))
        self._update_status()

    def _save_current(self) -> None:
        r = self.records[self.idx]
        if self.reviewer not in r:
            r[self.reviewer] = {}
        for key, var in self._dim_vars.items():
            r[self.reviewer][key] = var.get()
        r[self.reviewer]["note"] = self._note_var.get()
        r[self.reviewer]["updated_at"] = datetime.now().isoformat()
        self._save()

    def _on_rating_change(self) -> None:
        self._save_current()
        self._update_status()

    def _update_status(self) -> None:
        filled = sum(1 for k in self._dim_vars if self._dim_vars[k].get())
        total  = len(self._dim_vars)
        if filled == total:
            self._status_var.set(f"✅ 本条已完成 ({filled}/{total} 维度)")
        else:
            self._status_var.set(f"⬜ 请完成全部 {total} 个维度 (已选 {filled}/{total})")

    # ── 文本填充 ──────────────────────────────────────────────────────────────

    def _set_text(self, widget: tk.Text, text: str) -> None:
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        widget.config(state=tk.DISABLED)

    def _set_shalls(self, widget: tk.Text, shalls: list[str]) -> None:
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        for i, shall in enumerate(shalls, 1):
            # 标号
            widget.insert(tk.END, f"{i}. ", "bullet")
            # 分段插入，高亮数字
            last = 0
            for m in _NUM_RE.finditer(shall):
                widget.insert(tk.END, shall[last:m.start()])
                widget.insert(tk.END, m.group(), "num")
                last = m.end()
            widget.insert(tk.END, shall[last:] + "\n\n")
        widget.config(state=tk.DISABLED)

    # ── 导航 ──────────────────────────────────────────────────────────────────

    def _prev(self) -> None:
        self._save_current()
        if self.idx > 0:
            self.idx -= 1
            self._load_record()

    def _next(self) -> None:
        self._save_current()
        if self.idx < len(self.records) - 1:
            self.idx += 1
            self._load_record()
        else:
            messagebox.showinfo("完成", "已到最后一条，所有条目评审完毕！\n点击 [导出CSV] 生成结果文件。")

    def _on_close(self) -> None:
        self._save_current()
        self.destroy()

    # ── 导出 ──────────────────────────────────────────────────────────────────

    def _export_csv(self) -> None:
        import csv
        self._save_current()
        out = DATA_DIR / f"expert_review_{self.reviewer}.csv"
        fields = (["requirement_id", "layer", "requirement_text",
                   "system_a", "system_b"] +
                  [f"{r}_{d}" for r in ["expert1","expert2","final"]
                   for d in ["decomposition","accuracy","traceability",
                              "completeness","actionability","overall","note"]])
        with open(out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in self.records:
                row: dict = {
                    "requirement_id":   r["requirement_id"],
                    "layer":            r["layer"],
                    "requirement_text": r["requirement_text"][:80],
                    "system_a":         r["system_a"],
                    "system_b":         r["system_b"],
                }
                for rev in ("expert1", "expert2", "final"):
                    for dim in ["decomposition","accuracy","traceability",
                                "completeness","actionability","overall","note"]:
                        row[f"{rev}_{dim}"] = r.get(rev, {}).get(dim, "")
                w.writerow(row)
        messagebox.showinfo("导出完成", f"结果已写入：\n{out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reviewer", choices=["expert1", "expert2"], default="expert1",
                    help="当前评审人（expert1 或 expert2）")
    args = ap.parse_args()
    app = ExpertReviewApp(reviewer=args.reviewer)
    app.mainloop()


if __name__ == "__main__":
    main()
