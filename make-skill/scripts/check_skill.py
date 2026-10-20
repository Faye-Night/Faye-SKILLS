#!/usr/bin/env python3
"""校验一个 DSH skill 目录是否符合规范、是否可移植。

用法：
    python check_skill.py <skill目录>

退出码 0 = 全部通过（可能有 warning），1 = 有 FAIL。
"""

import os
import re
import sys

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# JWT、11 位手机号、邮箱
SECRET_PATTERNS = [
    ("JWT", re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
    ("手机号", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("邮箱", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")),
]
# 绝对路径：Windows 盘符、Unix home、DSH 安装目录
ABS_PATH_PATTERNS = [
    ("Windows 盘符", re.compile(r"(?<![<\w])[A-Za-z]:[\\/]{1,2}[^\s`'\")\]]+")),
    ("Unix 绝对路径", re.compile(r"(?<![\w<])/(?:home|Users|usr|etc|opt|var|root|tmp)/[^\s`'\")\]]*")),
]
# 指向 skill 目录之外的相对引用
ESCAPE_RE = re.compile(r"\]\(\.\./")
# 正文里的相对链接与裸路径引用
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
BARE_REF_RE = re.compile(r"`((?:references|scripts|assets)/[^`\s]+)`")

results = []


def ok(msg):
    results.append(("PASS", msg))


def warn(msg):
    results.append(("WARN", msg))


def fail(msg):
    results.append(("FAIL", msg))


def read_frontmatter(text):
    """返回 (frontmatter dict, 正文, 错误说明)。"""
    if not text.startswith("---"):
        return None, text, "SKILL.md 必须以 --- 开头的 frontmatter 起始"
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", text, re.S)
    if not m:
        return None, text, "frontmatter 未闭合（缺少结束的 ---）"
    raw = m.group(1)
    body = text[m.end():]
    fm = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()
    return fm, body, None


def main():
    if len(sys.argv) < 2:
        print("用法: python check_skill.py <skill目录>")
        return 2
    skill_dir = os.path.abspath(sys.argv[1])
    if not os.path.isdir(skill_dir):
        print(f"FAIL  目录不存在: {skill_dir}")
        return 1
    dir_name = os.path.basename(skill_dir)
    skill_md = os.path.join(skill_dir, "SKILL.md")

    # --- 1. SKILL.md 存在 ---
    if not os.path.isfile(skill_md):
        fail(f"缺少 {dir_name}/SKILL.md")
        report()
        return 1
    with open(skill_md, encoding="utf-8") as f:
        text = f.read()

    # --- 2. frontmatter ---
    fm, body, err = read_frontmatter(text)
    if err:
        fail(err)
        report()
        return 1
    name = fm.get("name", "")
    desc = fm.get("description", "")
    if not name:
        fail("frontmatter 缺少 name")
    elif not NAME_RE.match(name):
        fail(f"name 不是 kebab-case: {name!r}")
    elif name != dir_name:
        fail(f"name ({name}) 与目录名 ({dir_name}) 不一致")
    else:
        ok(f"name = {name}（kebab-case，与目录名一致）")

    if not desc:
        fail("frontmatter 缺少 description（模型只靠它决定是否加载）")
    elif len(desc) > 500:
        fail(f"description {len(desc)} 字符，超过 500 上限，会被截断")
    elif len(desc) < 30:
        warn(f"description 只有 {len(desc)} 字符，可能不足以让模型匹配到")
    else:
        ok(f"description {len(desc)} 字符（上限 500）")

    for key in ("whenToUse", "disable-model-invocation", "user-invocable"):
        if key in fm:
            ok(f"可选字段 {key} = {fm[key]}")
    unknown = set(fm) - {"name", "description", "whenToUse",
                         "disable-model-invocation", "user-invocable"}
    if unknown:
        warn(f"frontmatter 有非标准键（DSH 会忽略）: {', '.join(sorted(unknown))}")

    # --- 3. 相对链接可达且不越界 ---
    refs = set()
    for m in LINK_RE.finditer(body):
        target = m.group(1).split("#")[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:", "/")):
            continue
        refs.add(target)
    for m in BARE_REF_RE.finditer(body):
        refs.add(m.group(1))

    for ref in sorted(refs):
        resolved = os.path.normpath(os.path.join(skill_dir, ref))
        if not resolved.startswith(skill_dir + os.sep):
            fail(f"相对引用越出 skill 目录: {ref}")
        elif not os.path.exists(resolved):
            fail(f"相对引用指向不存在的文件: {ref}")
        else:
            ok(f"引用可达: {ref}")

    if ESCAPE_RE.search(body):
        fail("正文含 ../ 形式的越界链接（skill 被单独复制后会断）")

    # --- 4. 绝对路径（可移植性）---
    for label, pat in ABS_PATH_PATTERNS:
        hits = pat.findall(body)
        # 排除文档里显式举例的占位符写法
        hits = [h for h in hits if "<" not in h]
        if hits:
            fail(f"正文含硬编码{label}（应用 <DSH_HOME> 等占位符）: {hits[0]}")
        else:
            ok(f"无硬编码{label}")

    # --- 5. 凭据 ---
    for label, pat in SECRET_PATTERNS:
        hits = pat.findall(text)
        if hits:
            fail(f"疑似真实{label}: {hits[0][:40]}…")
    if not any(s == "FAIL" and "疑似真实" in m for s, m in results):
        ok("未发现 JWT / 手机号 / 邮箱等真实凭据")

    # --- 6. references/ 与正文互相对应 ---
    ref_dir = os.path.join(skill_dir, "references")
    if os.path.isdir(ref_dir):
        on_disk = {f"references/{n}" for n in os.listdir(ref_dir)
                   if os.path.isfile(os.path.join(ref_dir, n))}
        mentioned = {r for r in refs if r.startswith("references/")}
        for orphan in sorted(on_disk - mentioned):
            warn(f"references/{orphan.split('/', 1)[1]} 存在但正文未引用（可能该删）")
        if on_disk and not mentioned:
            warn("references/ 目录存在但正文完全没引用")

    # --- 7. 正文长度 ---
    lines = len(body.strip().splitlines())
    if lines > 200:
        warn(f"正文 {lines} 行，偏长，考虑把细节拆到 references/")
    else:
        ok(f"正文 {lines} 行")

    return report()


def report():
    fails = [r for r in results if r[0] == "FAIL"]
    warns = [r for r in results if r[0] == "WARN"]
    for level, msg in results:
        print(f"{level:<4}  {msg}")
    print()
    if fails:
        print(f"结果: FAIL —— {len(fails)} 项错误，{len(warns)} 项警告")
        return 1
    print(f"结果: PASS —— {len(warns)} 项警告")
    return 0


if __name__ == "__main__":
    sys.exit(main())
