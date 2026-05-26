# -*- coding: utf-8 -*-
"""
M6 人工追溯审核界面（桌面 Tkinter 版，双击直接运行）

运行方式：
  python scripts/m6_review_ui.py
  或双击项目根目录的 m6_review.bat

审核文件：data/search_results/batch_<timestamp>/experiment/M6_review.json
"""
from __future__ import annotations

import json
import re
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# 路径 & 数据加载
# ─────────────────────────────────────────────────────────────────────────────

_SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data"
SEARCH_RESULTS_DIR = DATA_DIR / "search_results"
EVIDENCE_UNITS_PATH = DATA_DIR / "processed" / "evidence_units.jsonl"

_SOURCE_REQUIREMENTS: dict[str, dict[str, str]] = {}


def _load_source_requirements() -> None:
    try:
        from ui.state import DEFAULT_REQUIREMENTS  # type: ignore[import]
        for r in DEFAULT_REQUIREMENTS:
            rid = str(r.get("需求编号", "")).strip()
            if rid:
                _SOURCE_REQUIREMENTS[rid] = {
                    "stakeholder": str(r.get("提出方", "")).strip(),
                    "text": str(r.get("需求内容", "")).strip(),
                }
        return
    except Exception:
        pass
    state_path = PROJECT_ROOT / "ui" / "state.py"
    if not state_path.exists():
        return
    src = state_path.read_text(encoding="utf-8")
    for rid, stakeholder, text in re.findall(
        r'"需求编号":\s*"(R\d+)".*?"提出方":\s*"([^"]*)".*?"需求内容":\s*"([^"]*)"',
        src, re.DOTALL,
    ):
        _SOURCE_REQUIREMENTS[rid] = {"stakeholder": stakeholder, "text": text}


def _find_batches() -> list[Path]:
    if not SEARCH_RESULTS_DIR.exists():
        return []
    batches = []
    for d in sorted(SEARCH_RESULTS_DIR.iterdir(), reverse=True):
        if d.is_dir() and d.name.startswith("batch_"):
            if (d / "experiment" / "G4_results.json").exists():
                batches.append(d)
    return batches


def _review_path(batch_dir: Path) -> Path:
    return batch_dir / "experiment" / "M6_review.json"


def _load_pool_lookup(batch_dir: Path) -> dict[str, dict[str, str]]:
    """从 sampled_requirements.jsonl 构建 req_id → {stakeholder, text} 映射。"""
    path = batch_dir / "experiment" / "sampled_requirements.jsonl"
    lookup: dict[str, dict[str, str]] = {}
    if not path.exists():
        return lookup
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            rid = obj.get("requirement_id", "")
            if rid:
                lookup[rid] = {
                    "stakeholder": obj.get("stakeholder", ""),
                    "text": obj.get("requirement_text", ""),
                }
    return lookup


def _patch_source_text(review_data: dict, batch_dir: Path) -> None:
    """补填缺失的 source_text，以及旧文件中缺失的 decomposition_correct 字段。"""
    pool_lookup = _load_pool_lookup(batch_dir)
    for rs in review_data.get("requirement_sets", []):
        if not rs.get("source_text"):
            src_id = rs.get("source_requirement_id", "")
            info = pool_lookup.get(src_id) or _SOURCE_REQUIREMENTS.get(src_id)
            if info:
                rs["source_text"] = info.get("text", "")
                if not rs.get("stakeholder"):
                    rs["stakeholder"] = info.get("stakeholder", "")
        for er in rs.get("engineering_requirements", []):
            rev = er.setdefault("review", {})
            if "decomposition_correct" not in rev:
                rev["decomposition_correct"] = None


def _load_review(batch_dir: Path) -> dict[str, Any] | None:
    """加载已有的 M6_review.json；不存在返回 None（由 script 26 生成，UI 不生成）。"""
    path = _review_path(batch_dir)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    _patch_source_text(data, batch_dir)
    return data


def _count_reviewed(review_data: dict) -> int:
    count = 0
    for rs in review_data.get("requirement_sets", []):
        for er in rs.get("engineering_requirements", []):
            rev = er.get("review", {})
            if bool(er.get("evidence")):
                if rev.get("decomposition_correct") is not None and rev.get("traceability_correct") is not None:
                    count += 1
            else:
                if rev.get("decomposition_correct") is not None:
                    count += 1
    return count


def _save_review(review_data: dict, batch_dir: Path) -> None:
    review_data["reviewed_count"] = _count_reviewed(review_data)
    review_data["last_saved_at"] = datetime.now().isoformat(timespec="seconds")
    _review_path(batch_dir).write_text(
        json.dumps(review_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 样式常量
# ─────────────────────────────────────────────────────────────────────────────

F_CN = ("Microsoft YaHei", 10)
F_CN_B = ("Microsoft YaHei", 10, "bold")
F_CN_BIG = ("Microsoft YaHei", 13, "bold")
F_CN_SM = ("Microsoft YaHei", 9)
F_MONO = ("Consolas", 9)

C_BG = "#f4f6f8"
C_SIDE = "#1e2d3d"
C_SIDE_FG = "#c8d8e8"
C_BLUE = "#2980b9"
C_GREEN = "#27ae60"
C_RED = "#e74c3c"
C_ORANGE = "#e67e22"
C_SECTION = "#2471a3"
C_WHITE = "#ffffff"


# ─────────────────────────────────────────────────────────────────────────────
# 主应用
# ─────────────────────────────────────────────────────────────────────────────

class M6ReviewApp:

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("M6 人工追溯审核")
        self.root.geometry("1440x900")
        self.root.minsize(1000, 680)
        self.root.configure(bg=C_BG)

        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        _load_source_requirements()

        self.batches: list[Path] = _find_batches()
        self.review_data: dict | None = None
        self.batch_dir: Path | None = None
        self.rs_idx: int = 0
        self.er_idx: int = 0
        self.unsaved: bool = False
        self.notes_text: tk.Text | None = None

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind_all("<MouseWheel>", self._global_scroll)

        if self.batches:
            self._select_batch(0)

    # ── UI 构建 ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        paned = tk.PanedWindow(
            self.root, orient=tk.HORIZONTAL,
            bg=C_BG, sashwidth=5, relief=tk.FLAT,
        )
        paned.pack(fill=tk.BOTH, expand=True)
        self._build_sidebar(paned)
        self._build_main(paned)

    def _build_sidebar(self, paned: tk.PanedWindow) -> None:
        left = tk.Frame(paned, bg=C_SIDE, width=290)
        left.pack_propagate(False)
        paned.add(left, minsize=220)

        tk.Label(
            left, text="M6  审核", bg=C_SIDE, fg="#ffffff",
            font=("Microsoft YaHei", 15, "bold"), pady=14,
        ).pack(fill=tk.X)

        tk.Label(left, text="实验批次", bg=C_SIDE, fg="#8fa8c0",
                 font=F_CN_SM).pack(anchor=tk.W, padx=14)

        self.batch_var = tk.StringVar()
        self.batch_combo = ttk.Combobox(
            left, textvariable=self.batch_var,
            state="readonly", font=F_MONO,
        )
        self.batch_combo["values"] = [b.name for b in self.batches]
        self.batch_combo.pack(fill=tk.X, padx=14, pady=(2, 10))
        self.batch_combo.bind("<<ComboboxSelected>>", self._on_batch_change)

        if not self.batches:
            tk.Label(
                left,
                text="未找到含 G4 结果的批次\n请先运行 21_run_experiment.py",
                bg=C_SIDE, fg=C_RED, font=F_CN_SM,
                justify=tk.LEFT, wraplength=240,
            ).pack(padx=14)

        self.progress_label = tk.Label(
            left, text="进度：0 / 0",
            bg=C_SIDE, fg=C_SIDE_FG, font=F_CN,
        )
        self.progress_label.pack(anchor=tk.W, padx=14, pady=(4, 2))

        self.progress_bar = ttk.Progressbar(left, mode="determinate", length=250)
        self.progress_bar.pack(padx=14, pady=(0, 8))

        self.save_btn = tk.Button(
            left, text="  保存审核结果",
            bg=C_GREEN, fg="white", font=F_CN_B,
            relief=tk.FLAT, pady=8, cursor="hand2",
            command=self._save,
        )
        self.save_btn.pack(fill=tk.X, padx=14, pady=(0, 2))

        self.unsaved_label = tk.Label(
            left, text="", bg=C_SIDE, fg=C_ORANGE, font=F_CN_SM,
        )
        self.unsaved_label.pack(anchor=tk.W, padx=14)

        self.last_saved_label = tk.Label(
            left, text="", bg=C_SIDE, fg="#607080", font=F_CN_SM,
        )
        self.last_saved_label.pack(anchor=tk.W, padx=14, pady=(0, 8))

        tk.Frame(left, bg="#2c3e50", height=1).pack(fill=tk.X, padx=14, pady=4)

        tk.Label(
            left, text="需求集导航", bg=C_SIDE, fg="#8fa8c0", font=F_CN_SM,
        ).pack(anchor=tk.W, padx=14, pady=(4, 2))

        rs_frame = tk.Frame(left, bg=C_SIDE)
        rs_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        rs_sb = tk.Scrollbar(rs_frame, orient=tk.VERTICAL)
        rs_sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.rs_listbox = tk.Listbox(
            rs_frame,
            bg="#253545", fg=C_SIDE_FG,
            selectbackground=C_BLUE, selectforeground="white",
            font=F_CN_SM, relief=tk.FLAT, borderwidth=0,
            yscrollcommand=rs_sb.set,
            activestyle="none", highlightthickness=0,
        )
        self.rs_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rs_sb.config(command=self.rs_listbox.yview)
        self.rs_listbox.bind("<<ListboxSelect>>", self._on_rs_select)

    def _build_main(self, paned: tk.PanedWindow) -> None:
        right = tk.Frame(paned, bg=C_BG)
        paned.add(right, minsize=640)

        self.rs_header = tk.Label(
            right, text="请在左侧选择实验批次",
            bg=C_BG, fg="#2c3e50",
            font=F_CN_BIG, anchor=tk.W, padx=16, pady=10,
        )
        self.rs_header.pack(fill=tk.X)

        src_lf = tk.LabelFrame(
            right, text="原始利益相关方需求",
            bg=C_BG, fg=C_SECTION, font=F_CN_B,
            padx=8, pady=4,
        )
        src_lf.pack(fill=tk.X, padx=14, pady=(0, 6))

        self.source_text_w = tk.Text(
            src_lf, height=3, wrap=tk.WORD,
            bg="#eaf4fb", fg="#2c3e50",
            font=F_CN, relief=tk.FLAT, padx=8, pady=6,
            state=tk.DISABLED, takefocus=False,
        )
        self.source_text_w.pack(fill=tk.X)

        nav = tk.Frame(right, bg=C_BG)
        nav.pack(fill=tk.X, padx=14, pady=4)

        self.prev_btn = tk.Button(
            nav, text=" <- 上一条 ",
            command=self._prev_er,
            bg=C_WHITE, fg="#2c3e50", font=F_CN, relief=tk.GROOVE, padx=6,
        )
        self.prev_btn.pack(side=tk.LEFT)

        self.er_pos_label = tk.Label(nav, text="", bg=C_BG, fg="#555", font=F_CN)
        self.er_pos_label.pack(side=tk.LEFT, padx=10)

        self.next_btn = tk.Button(
            nav, text=" 下一条 -> ",
            command=self._next_er,
            bg=C_WHITE, fg="#2c3e50", font=F_CN, relief=tk.GROOVE, padx=6,
        )
        self.next_btn.pack(side=tk.LEFT)

        self.jump_btn = tk.Button(
            nav, text=">> 下一条未审核",
            command=self._jump_unreviewed,
            bg=C_ORANGE, fg="white", font=F_CN,
            relief=tk.FLAT, padx=8, cursor="hand2",
        )
        self.jump_btn.pack(side=tk.RIGHT)

        det_outer = tk.Frame(right, bg=C_BG)
        det_outer.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 6))

        det_sb = tk.Scrollbar(det_outer, orient=tk.VERTICAL)
        det_sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.detail_canvas = tk.Canvas(
            det_outer, bg=C_BG,
            yscrollcommand=det_sb.set,
            highlightthickness=0,
        )
        self.detail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        det_sb.config(command=self.detail_canvas.yview)

        self.detail_frame = tk.Frame(self.detail_canvas, bg=C_BG)
        self._dwin = self.detail_canvas.create_window(
            (0, 0), window=self.detail_frame, anchor=tk.NW,
        )
        self.detail_frame.bind(
            "<Configure>",
            lambda e: self.detail_canvas.configure(
                scrollregion=self.detail_canvas.bbox("all")
            ),
        )
        self.detail_canvas.bind(
            "<Configure>",
            lambda e: self.detail_canvas.itemconfig(self._dwin, width=e.width),
        )

    # ── 鼠标滚轮 ──────────────────────────────────────────────────────────────

    def _global_scroll(self, event: tk.Event) -> None:
        try:
            x, y = self.root.winfo_pointerxy()
            w = self.root.winfo_containing(x, y)
            # notes_text 内不劫持滚轮（让 Text 自身处理）
            if self.notes_text is not None and w is self.notes_text:
                return
            # 向上找是否在 detail 区域内
            cur = w
            while cur is not None:
                if cur is self.detail_canvas or cur is self.detail_frame:
                    self.detail_canvas.yview_scroll(
                        int(-1 * (event.delta / 120)), "units"
                    )
                    return
                try:
                    cur = cur.master
                except Exception:
                    break
        except Exception:
            pass

    # ── 批次 / RS 加载 ────────────────────────────────────────────────────────

    def _select_batch(self, idx: int) -> None:
        self.batch_dir = self.batches[idx]
        self.batch_var.set(self.batch_dir.name)
        self.review_data = _load_review(self.batch_dir)
        self.rs_idx = 0
        self.er_idx = 0
        self.unsaved = False

        if self.review_data is None:
            self.rs_header.config(text=f"[{self.batch_dir.name}]  未找到 M6_review.json")
            self.source_text_w.config(state=tk.NORMAL)
            self.source_text_w.delete("1.0", tk.END)
            self.source_text_w.insert(
                "1.0",
                "审核文件尚未生成。\n"
                "请先运行实验脚本：\n"
                "  python scripts/26_run_three_rounds.py\n\n"
                "每轮 G4 结束后会自动生成 M6_review.json。",
            )
            self.source_text_w.config(state=tk.DISABLED)
            self.rs_listbox.delete(0, tk.END)
            self.progress_label.config(text="进度：-- / --")
            self.progress_bar["value"] = 0
            self.last_saved_label.config(text="")
            for w in self.detail_frame.winfo_children():
                w.destroy()
            return

        self._refresh_rs_list()
        self._refresh_main()
        self._update_progress()
        self._update_unsaved_ui()
        last = self.review_data.get("last_saved_at") or ""
        self.last_saved_label.config(text=f"上次保存：{last}" if last else "")

    def _on_batch_change(self, _event=None) -> None:
        name = self.batch_var.get()
        for i, b in enumerate(self.batches):
            if b.name == name:
                self._select_batch(i)
                return

    def _refresh_rs_list(self) -> None:
        self.rs_listbox.delete(0, tk.END)
        if not self.review_data:
            return
        for rs in self.review_data.get("requirement_sets", []):
            ers = rs.get("engineering_requirements", [])
            done = sum(
                1 for er in ers
                if (bool(er.get("evidence")) and
                    er.get("review", {}).get("decomposition_correct") is not None and
                    er.get("review", {}).get("traceability_correct") is not None)
                or (not bool(er.get("evidence")) and
                    er.get("review", {}).get("decomposition_correct") is not None)
            )
            total = len(ers)
            src_id = rs.get("source_requirement_id", "")
            sh = rs.get("stakeholder", "")[:8]
            if total > 0 and done == total:
                icon = "[OK]"
            elif done > 0:
                icon = "[ > ]"
            else:
                icon = "[   ]"
            self.rs_listbox.insert(tk.END, f"{icon} {src_id} {sh}  {done}/{total}")
        sz = self.rs_listbox.size()
        if sz > 0:
            sel = min(self.rs_idx, sz - 1)
            self.rs_listbox.selection_clear(0, tk.END)
            self.rs_listbox.selection_set(sel)
            self.rs_listbox.see(sel)

    def _on_rs_select(self, _event=None) -> None:
        sel = self.rs_listbox.curselection()
        if not sel:
            return
        new_idx = sel[0]
        if new_idx != self.rs_idx:
            self._flush_notes()
            self.rs_idx = new_idx
            self.er_idx = 0
            self._refresh_main()

    # ── 主内容刷新 ────────────────────────────────────────────────────────────

    def _refresh_main(self) -> None:
        if not self.review_data:
            return
        rs_list = self.review_data.get("requirement_sets", [])
        if not rs_list or self.rs_idx >= len(rs_list):
            return
        rs = rs_list[self.rs_idx]

        src_id = rs.get("source_requirement_id", "")
        stakeholder = rs.get("stakeholder", "")
        ers = rs.get("engineering_requirements", [])
        done = sum(
            1 for er in ers
            if (bool(er.get("evidence")) and
                er.get("review", {}).get("decomposition_correct") is not None and
                er.get("review", {}).get("traceability_correct") is not None)
            or (not bool(er.get("evidence")) and
                er.get("review", {}).get("decomposition_correct") is not None)
        )
        self.rs_header.config(
            text=f"[{src_id}]  {stakeholder}    （{done}/{len(ers)} 已审核）"
        )

        src_text = rs.get("source_text", "") or "（未找到原始需求文本）"
        self.source_text_w.config(state=tk.NORMAL)
        self.source_text_w.delete("1.0", tk.END)
        self.source_text_w.insert("1.0", src_text)
        self.source_text_w.config(state=tk.DISABLED)

        if self.er_idx >= len(ers):
            self.er_idx = 0
        self._refresh_er()

    def _refresh_er(self) -> None:
        if not self.review_data:
            return
        rs_list = self.review_data.get("requirement_sets", [])
        if not rs_list or self.rs_idx >= len(rs_list):
            return
        rs = rs_list[self.rs_idx]
        ers = rs.get("engineering_requirements", [])
        n = len(ers)

        self.prev_btn.config(state=tk.NORMAL if self.er_idx > 0 else tk.DISABLED)
        self.next_btn.config(
            state=tk.NORMAL if self.er_idx < n - 1 else tk.DISABLED
        )
        self.er_pos_label.config(
            text=f"ER  {self.er_idx + 1} / {n}" if n else "无 ER"
        )

        for w in self.detail_frame.winfo_children():
            w.destroy()
        self.notes_text = None

        if not ers:
            tk.Label(
                self.detail_frame, text="该需求集没有工程需求条目",
                bg=C_BG, fg="#aaa", font=F_CN,
            ).pack(pady=30)
            return

        er = ers[self.er_idx]
        PAD = {"padx": 12, "pady": 3}

        # ER 标题行
        hdr = tk.Frame(self.detail_frame, bg=C_BG)
        hdr.pack(fill=tk.X, **PAD)
        tk.Label(
            hdr, text=er.get("er_id", ""),
            bg=C_BG, fg="#2c3e50",
            font=("Microsoft YaHei", 12, "bold"),
        ).pack(side=tk.LEFT)
        tk.Label(
            hdr,
            text=f"   [{er.get('requirement_type', '')}]   [{er.get('support_status', '')}]",
            bg=C_BG, fg="#666", font=F_CN_SM,
        ).pack(side=tk.LEFT)

        tk.Label(
            self.detail_frame,
            text=f"验证方法：{er.get('verification_method', '')}",
            bg=C_BG, fg="#888", font=F_CN_SM,
        ).pack(anchor=tk.W, **PAD)

        # Shall Statement
        self._section("Shall Statement")
        self._ro_text(er.get("shall_statement", ""), bg="#eaf4fb", height=5)

        # 验收准则
        criteria = er.get("acceptance_criteria") or []
        if criteria:
            self._section("验收准则")
            for i, c in enumerate(criteria, 1):
                tk.Label(
                    self.detail_frame,
                    text=f"{i}.  {c}",
                    bg=C_BG, fg="#333", font=F_CN,
                    anchor=tk.W, justify=tk.LEFT, wraplength=800,
                ).pack(anchor=tk.W, padx=20, pady=1)

        # 证据
        ev_list = er.get("evidence") or []
        self._section(f"证据（{len(ev_list)} 条）")
        if ev_list:
            for ev in ev_list:
                lf = tk.LabelFrame(
                    self.detail_frame,
                    text=f"  {ev.get('ev_id', '')}   {ev.get('source_file', '')}",
                    bg=C_BG, fg="#555", font=F_MONO, padx=6, pady=4,
                )
                lf.pack(fill=tk.X, padx=12, pady=3)
                t = tk.Text(
                    lf, height=4, wrap=tk.WORD,
                    bg="#f8f8f8", fg="#333", font=F_CN,
                    relief=tk.FLAT, padx=8, pady=4,
                    state=tk.NORMAL, takefocus=False,
                )
                t.insert("1.0", ev.get("text", "（无文本）"))
                t.config(state=tk.DISABLED)
                t.pack(fill=tk.X)
        else:
            tk.Label(
                self.detail_frame, text="该 ER 无关联证据",
                bg=C_BG, fg="#aaa", font=F_CN,
            ).pack(anchor=tk.W, padx=20, pady=4)

        # 审核区
        tk.Frame(self.detail_frame, bg="#dde3ea", height=1).pack(
            fill=tk.X, padx=12, pady=(14, 4)
        )
        self._section("审核判断")

        review = er.get("review", {})
        has_evidence = bool(ev_list)

        # 拆分合理性
        tk.Label(
            self.detail_frame,
            text="【拆分合理性】这条 shall 是原始需求的合理拆分？",
            bg=C_BG, fg="#333", font=F_CN_B,
        ).pack(anchor=tk.W, padx=12, pady=(6, 2))

        decomp_val = review.get("decomposition_correct")
        self.decomp_var = tk.StringVar(
            value="true" if decomp_val is True
            else "false" if decomp_val is False
            else "null"
        )
        decomp_frame = tk.Frame(self.detail_frame, bg=C_BG)
        decomp_frame.pack(anchor=tk.W, padx=12, pady=(0, 6))
        for val, label, color in [
            ("true",  "  合理（true）  ", C_GREEN),
            ("false", "  不合理（false）  ", C_RED),
            ("null",  "  未审核（null）  ", "#888"),
        ]:
            tk.Radiobutton(
                decomp_frame, text=label,
                variable=self.decomp_var, value=val,
                bg=C_BG, fg=color,
                font=("Microsoft YaHei", 11, "bold"),
                activebackground=C_BG,
                command=self._on_decomp_change,
            ).pack(side=tk.LEFT, padx=6)

        # 证据支撑性
        tk.Label(
            self.detail_frame,
            text="【证据支撑性】引用证据是否支持该 shall？",
            bg=C_BG, fg="#333" if has_evidence else "#aaa", font=F_CN_B,
        ).pack(anchor=tk.W, padx=12, pady=(4, 2))

        if not has_evidence:
            tk.Label(
                self.detail_frame,
                text="（该 ER 无证据，仅判断拆分合理性，溯源精度维度不适用）",
                bg=C_BG, fg="#aaa", font=F_CN_SM,
            ).pack(anchor=tk.W, padx=20, pady=(0, 4))

        trace_val = review.get("traceability_correct")
        self.verdict_var = tk.StringVar(
            value="true" if trace_val is True
            else "false" if trace_val is False
            else "null"
        )
        rb_frame = tk.Frame(self.detail_frame, bg=C_BG)
        rb_frame.pack(anchor=tk.W, padx=12, pady=(0, 6))
        for val, label, color in [
            ("true",  "  支持（true）  ", C_GREEN),
            ("false", "  不支持（false）  ", C_RED),
            ("null",  "  未审核（null）  ", "#888"),
        ]:
            tk.Radiobutton(
                rb_frame, text=label,
                variable=self.verdict_var, value=val,
                bg=C_BG, fg=color if has_evidence else "#bbb",
                font=("Microsoft YaHei", 11, "bold"),
                activebackground=C_BG,
                command=self._on_verdict_change,
                state=tk.NORMAL if has_evidence else tk.DISABLED,
            ).pack(side=tk.LEFT, padx=6)

        tk.Label(
            self.detail_frame, text="审核备注",
            bg=C_BG, fg="#555", font=F_CN,
        ).pack(anchor=tk.W, padx=12, pady=(8, 2))

        self.notes_text = tk.Text(
            self.detail_frame, height=3, wrap=tk.WORD,
            bg=C_WHITE, fg="#333", font=F_CN,
            relief=tk.GROOVE, padx=6, pady=4,
        )
        self.notes_text.pack(fill=tk.X, padx=12, pady=(0, 20))
        self.notes_text.insert("1.0", review.get("notes", "") or "")
        self.notes_text.bind("<KeyRelease>", self._on_notes_change)

        self.detail_canvas.yview_moveto(0)

    def _section(self, text: str) -> None:
        tk.Label(
            self.detail_frame, text=text,
            bg=C_BG, fg=C_SECTION, font=F_CN_B,
        ).pack(anchor=tk.W, padx=12, pady=(10, 2))

    def _ro_text(self, text: str, bg: str = C_WHITE, height: int = 4) -> None:
        t = tk.Text(
            self.detail_frame, height=height, wrap=tk.WORD,
            bg=bg, fg="#333", font=F_CN,
            relief=tk.FLAT, padx=8, pady=6,
            state=tk.NORMAL, takefocus=False,
        )
        t.insert("1.0", text)
        t.config(state=tk.DISABLED)
        t.pack(fill=tk.X, padx=12, pady=(0, 4))

    # ── 事件处理 ──────────────────────────────────────────────────────────────

    def _flush_notes(self) -> None:
        try:
            if self.notes_text is not None and self.review_data:
                ers = (
                    self.review_data["requirement_sets"][self.rs_idx]
                    ["engineering_requirements"]
                )
                if self.er_idx < len(ers):
                    ers[self.er_idx]["review"]["notes"] = (
                        self.notes_text.get("1.0", "end-1c")
                    )
        except Exception:
            pass

    def _on_verdict_change(self) -> None:
        if not self.review_data:
            return
        er = (
            self.review_data["requirement_sets"][self.rs_idx]
            ["engineering_requirements"][self.er_idx]
        )
        v = self.verdict_var.get()
        new_val = True if v == "true" else (False if v == "false" else None)
        if new_val != er["review"]["traceability_correct"]:
            er["review"]["traceability_correct"] = new_val
            self._mark_unsaved()
            self._update_progress()
            self._refresh_rs_list()
            rs = self.review_data["requirement_sets"][self.rs_idx]
            ers = rs.get("engineering_requirements", [])
            done = sum(
                1 for e in ers
                if (bool(e.get("evidence")) and
                    e.get("review", {}).get("decomposition_correct") is not None and
                    e.get("review", {}).get("traceability_correct") is not None)
                or (not bool(e.get("evidence")) and
                    e.get("review", {}).get("decomposition_correct") is not None)
            )
            src_id = rs.get("source_requirement_id", "")
            sh = rs.get("stakeholder", "")
            self.rs_header.config(
                text=f"[{src_id}]  {sh}    （{done}/{len(ers)} 已审核）"
            )

    def _on_decomp_change(self) -> None:
        if not self.review_data:
            return
        er = (
            self.review_data["requirement_sets"][self.rs_idx]
            ["engineering_requirements"][self.er_idx]
        )
        v = self.decomp_var.get()
        new_val = True if v == "true" else (False if v == "false" else None)
        if new_val != er["review"].get("decomposition_correct"):
            er["review"]["decomposition_correct"] = new_val
            self._mark_unsaved()
            self._update_progress()
            self._refresh_rs_list()
            rs = self.review_data["requirement_sets"][self.rs_idx]
            ers = rs.get("engineering_requirements", [])
            done = sum(
                1 for e in ers
                if (bool(e.get("evidence")) and
                    e.get("review", {}).get("decomposition_correct") is not None and
                    e.get("review", {}).get("traceability_correct") is not None)
                or (not bool(e.get("evidence")) and
                    e.get("review", {}).get("decomposition_correct") is not None)
            )
            src_id = rs.get("source_requirement_id", "")
            sh = rs.get("stakeholder", "")
            self.rs_header.config(
                text=f"[{src_id}]  {sh}    （{done}/{len(ers)} 已审核）"
            )

    def _on_notes_change(self, _event=None) -> None:
        if not self.review_data or self.notes_text is None:
            return
        er = (
            self.review_data["requirement_sets"][self.rs_idx]
            ["engineering_requirements"][self.er_idx]
        )
        new_notes = self.notes_text.get("1.0", "end-1c")
        if new_notes != er["review"].get("notes", ""):
            er["review"]["notes"] = new_notes
            self._mark_unsaved()

    def _prev_er(self) -> None:
        if self.er_idx > 0:
            self._flush_notes()
            self.er_idx -= 1
            self._refresh_er()

    def _next_er(self) -> None:
        if not self.review_data:
            return
        n = len(
            self.review_data["requirement_sets"][self.rs_idx]
            .get("engineering_requirements", [])
        )
        if self.er_idx < n - 1:
            self._flush_notes()
            self.er_idx += 1
            self._refresh_er()

    def _jump_unreviewed(self) -> None:
        if not self.review_data:
            return
        self._flush_notes()
        ers = (
            self.review_data["requirement_sets"][self.rs_idx]
            .get("engineering_requirements", [])
        )
        for i in range(self.er_idx + 1, len(ers)):
            e = ers[i]
            rev = e.get("review", {})
            if bool(e.get("evidence")):
                incomplete = (rev.get("decomposition_correct") is None
                              or rev.get("traceability_correct") is None)
            else:
                incomplete = rev.get("decomposition_correct") is None
            if incomplete:
                self.er_idx = i
                self._refresh_er()
                return
        messagebox.showinfo("提示", "本需求集已无未审核条目。")

    def _save(self) -> None:
        if not self.review_data or not self.batch_dir:
            return
        self._flush_notes()
        _save_review(self.review_data, self.batch_dir)
        self.unsaved = False
        self._update_unsaved_ui()
        last = self.review_data.get("last_saved_at", "")
        self.last_saved_label.config(text=f"上次保存：{last}")
        messagebox.showinfo(
            "保存成功",
            f"已保存至：\n{_review_path(self.batch_dir)}",
        )

    def _mark_unsaved(self) -> None:
        self.unsaved = True
        self._update_unsaved_ui()

    def _update_unsaved_ui(self) -> None:
        if self.unsaved:
            self.unsaved_label.config(text="[!] 有未保存的更改")
            self.save_btn.config(bg=C_ORANGE)
        else:
            self.unsaved_label.config(text="")
            self.save_btn.config(bg=C_GREEN)

    def _update_progress(self) -> None:
        if not self.review_data:
            self.progress_label.config(text="进度：0 / 0")
            self.progress_bar["value"] = 0
            return
        total = self.review_data.get("total_ers", 0)
        reviewed = _count_reviewed(self.review_data)
        self.progress_label.config(text=f"进度：{reviewed} / {total}")
        self.progress_bar["maximum"] = max(total, 1)
        self.progress_bar["value"] = reviewed

    def _on_close(self) -> None:
        if self.unsaved:
            ans = messagebox.askyesnocancel(
                "未保存的更改",
                "有未保存的审核更改，是否保存后退出？",
            )
            if ans is None:
                return
            if ans:
                self._flush_notes()
                if self.review_data and self.batch_dir:
                    _save_review(self.review_data, self.batch_dir)
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    M6ReviewApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
