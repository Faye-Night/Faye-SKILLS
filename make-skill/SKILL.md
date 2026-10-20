---
name: make-skill
description: 把一个流程或经验固化成 DSH skill，发布到 skill 仓库并安装为全局/项目级 skill。当需要新建或修改 SKILL.md、决定内容该放正文还是 references/、校验 skill 目录是否合规且可移植（越界引用、硬编码路径、真实凭据）、更新 skill 仓库 README 表格、或把 skill 装进 DSH_HOME 并登记启用时使用。Also for authoring DSH SKILL.md, validating skill portability, and publishing skills to a git repository.
---

# 制作 DSH skill 并发布

目标产物：一个自包含的 skill 目录——`<name>/SKILL.md` 加可选的 `references/`、`scripts/`。它必须同时满足两件事：DSH 能加载，且**整个目录被复制到任何机器上都不失效**。

**核心原则：skill 是给"未来的模型"看的操作手册，不是给人看的文档。** 唯一的验收标准是——下次遇到同类任务，照着它能不能一次做对。

## 阶段一：先判断该不该做成 skill

三问，任一答「否」就停：

| 问题 | 答否时该去哪 |
| --- | --- |
| 这套流程会重复用第二次以上吗？ | 一次性任务，当场做完就行 |
| 模型需要在**动手之前**就知道吗？ | 事后记录，写进项目 README |
| 它是**规范**（must，每次都必须遵守）吗？ | 那是 `AGENTS.md` / `CONTRIBUTING.md` 的职责 |

第三条最容易搞错。规范类内容（目录命名、提交前清凭据）应放 `AGENTS.md`：它每次会话自动注入、跨工具通用（Claude Code / Codex 也读）。skill 只按需加载，且只有 DSH 认。把规范塞进 skill，换工具就丢了。

**同一个事实只能有一个真相源。** skill 里需要提到规范时，写「以 `AGENTS.md` 为准，此处不重复」，而不是复述一遍——复述迟早漂移。

## 阶段二：定三件事

1. **触发条件**——用户会怎么开口？把这些说法写进 `description`，中文英文都覆盖。
2. **正文 / 参考资料的切分**——正文放**决策与顺序**（判断依据、阶段流程、踩过的坑）；`references/` 放**查表用的细节**（API 签名、源码行号、协议行为）。正文超过 200 行就该拆。
3. **目录名**——kebab-case，必须等于 frontmatter 的 `name`，也就是用户以后调用时写的名字。

## 阶段三：写 SKILL.md

frontmatter 只有两个键必需：

```yaml
---
name: make-skill
description: 一句话说清"做什么"+"什么时候用"。模型只靠 name 和 description 决定要不要加载，正文它看不到。
---
```

- `description` **不超过 500 字符**（超了被截断），且必须含触发词——用户不会说"用 skill"，他会说"帮我做一个 XX 的 YY"。
- 可选键：`whenToUse`、`disable-model-invocation`、`user-invocable`。其余键 DSH 忽略。

正文写法：

- **短句、断言式**。写「必须实际请求一次」，不写「建议考虑进行实际请求验证」。
- **并列项用表格**，不要长段落罗列。
- **每个坑写清「会怎么坏 + 怎么改」**，只写「注意 X」没有用。
- **命令给可复制的代码块**并标语言。
- 没验证的事标「未验证」，不要编。

## 阶段四：校验

自带脚本，一条命令查完：

```powershell
python <skill目录>\scripts\check_skill.py <skill目录>
```

它查八项：目录名与 `name` 一致、`description` 长度、正文相对链接可达且不越界、无硬编码绝对路径、无真实凭据、`references/` 与正文互相对应、正文行数。

**FAIL 必须全清，WARN 逐条判断。** 两类最常踩：

- **越界引用**：正文写 `../../AGENTS.md` 或引用仓库里别的目录。skill 一旦被单独复制到 `<DSH_HOME>\skills` 就断链。要么内联内容，要么不写。
- **硬编码绝对路径**：盘符路径（`<盘符>:\...`）、Unix 路径（`/home/<用户>/...`）。一律换成 `<DSH_HOME>`、`<仓库根>` 这类占位符。

## 阶段五：发布到 skill 仓库

仓库根 `README.md` 的 Skill 表格加一行，链接指向 **skill 目录**而不是 `SKILL.md`：

```markdown
| 2 | [make-skill](https://github.com/<用户>/<仓库>/tree/master/make-skill) | 功能一句话 |
```

指向目录的理由：skill 除正文还带 `references/`、`scripts/`，用户只保存单个文件会丢结构；`/tree/master/<name>` 还能让用户直接下载整个目录。

## 阶段六：装成全局 skill

1. **整个目录复制**（含 `references/`、`scripts/`）到 `<DSH_HOME>\skills\<name>\`。只拷 `SKILL.md` 会让相对链接失效。
2. **登记启用**：编辑 `<DSH_HOME>\skills-manager\state.json`，把 skill 名加进 `enabledSkills.dsh` 数组。改完先用 `ConvertFrom-Json` 解析一次确认没写坏。
3. 会话里调 `skill({ name: "<name>" })` 验证：能加载、正文渲染正常、相对链接可达。

## 检查清单

- [ ] `check_skill.py` 无 FAIL
- [ ] `description` 含触发词、≤500 字符
- [ ] 正文没有指向 skill 目录之外的引用
- [ ] 没有硬编码绝对路径、没有真实凭据
- [ ] README 表格已加行，链接指向目录
- [ ] 已复制到全局目录并登记 `enabledSkills.dsh`
- [ ] `skill` 工具能加载

参考资料：[references/dsh-skill-spec.md](references/dsh-skill-spec.md)（发现优先级、frontmatter 全键、热重载行为）、[references/case-make-har.md](references/case-make-har.md)（一个成品 skill 的切分决策复盘）。
