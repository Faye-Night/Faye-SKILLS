# DSH skill 规范速查

来源：`https://raw.githubusercontent.com/deepseek-ai/deepseek-harness/master/docs/subsystems/skills.zh.md`（仓库默认分支是 `master`，不是 `main`）。

## 本地发现优先级

| Rank | Source | 根目录 |
| --- | --- | --- |
| 100 | `project-dsh` | `<项目根>/.dsh/skills` |
| 200 | `project-agents` | `<项目根>/.agents/skills` |
| 300 | `custom` | `Config.customSkillDirs` |
| 400 | `user-dsh` | `<DSH_HOME>/skills` |
| 500 | `user-agents` | `<agentsHome>/skills` |
| 600 | `bundled` | `Config.bundledSkillDir` / `DSH_BUNDLED_SKILL_DIR` |

- **项目根 = 包含 `.git` 的最近祖先目录**；找不到时用当前 cwd。
- 用户 DSH 根会跳过自己的 `.system` 子目录。
- rank 只在**同一层**内裁决重名；跨层时最近层直接赢。
- 同一层内：项目条目 > runtime 条目 > 用户条目。

## skill 身份

- 名称 kebab-case：`^[a-z0-9]+(?:-[a-z0-9]+)*$`，否则该 skill 不被收录。
- 本地提供方接受两种形态：目录包 `<name>/SKILL.md`、扁平文件 `<name>.md`。
- **嵌套递归 `**/SKILL.md` 不受支持**——不能把 skill 放在 `skills/group/<name>/SKILL.md`。

## frontmatter

| 键 | 必需 | 说明 |
| --- | --- | --- |
| `name` | 是 | 必须等于目录名 |
| `description` | 是 | 模型只靠它决定是否加载；`catalogDescriptionMaxLength` 默认 500，超了截断 |
| `whenToUse` | 否 | 额外路由提示 |
| `disable-model-invocation` | 否 | 设 `true` 后模型不可调用，只能用户调用 |
| `user-invocable` | 否 | 省略默认 `true`；设 `false` 后只能模型调用 |

未列出的键 DSH 会忽略（会存进 `metadata`，但不参与路由）。四个调用策略组合都合法，只有两个都为 `false` 时才是"仅受信代码可读"。

## 目录内容与资源解析

- 目录里的 `references/`、`scripts/`、`assets/` 都可以放，**正文用相对路径引用**。
- `resourceBase` 只在显式引用时才解析，**加载 skill 不会枚举目录**——所以 `references/` 里多放几个文件不增加加载成本。
- 因此相对链接必须真实存在，否则用户点开是 404。

## 热重载与失效

- Chokidar 监视现有根目录下**直属** bundle 与扁平条目的增删，以及直属 skill 条目的变更。
- bundle 内部资源文件变更**不算**目录变更（正文改了会重新读，资源文件不会被监视）。
- 面向模型的 `write` / `edit` 观测会同步使目录缓存失效；IDE / Git / shell 产生的变更由宿主 watcher 覆盖。
- 因此：改完 SKILL.md 通常立即生效，不需要重启 DSH；但**新增 skill 目录**如果宿主 watcher 没捕捉到，重启会话最稳。

## 会话目录机制（为什么 description 这么重要）

- 存活会话在第一个非空完整视图时注入一条持久的 user-role 目录消息，**只含 `name` + `description`**，不含正文、路径、来源。
- 后续每个模型步骤前计算 digest，变了就追加一条完整目录替换。
- 也就是说：**description 是唯一的路由信号**。写"一个有用的工具"等于没写；必须写用户会说的那些词。

## `skill` 工具行为

- `skill({ name })` 校验 kebab-case → 在目录中查找 → 用 `isModelInvocable` 拒绝无权访问 → 按调用方 cwd 重读完整定义 → 返回前再检查一次策略。
- 返回 `skill_content` / `skill_path` / `resourceBase`。
- 名称不匹配或已被移除时报"未知或已不可用"。
