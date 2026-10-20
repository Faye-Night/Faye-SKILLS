# Faye-SKILL

个人 DSH skill 集合。每个 skill 是一个自包含目录，按 [DSH skills 规范](https://dshx.dev/docs/internals/skills/) 组织，可直接复制到 DSH 的 skill 目录使用。

## Skill 列表

| # | Skill | 功能 |
| --- | --- | --- |
| 1 | [make-har](https://github.com/Faye-Night/Faye-SKILL/tree/master/make-har) | 制作 [qd](https://github.com/qd-today/qd)（签到助手）可用的签到 HAR 模板。覆盖完整链路：侦察浏览器/逆向 SPA bundle 找到签到接口 → 确认认证 header 与请求体 → 写 qd 模板（`success_asserts` / `failed_asserts` / `extract_variables` / `__log__` 水滴变化回报）→ 本地用 qd 引擎跑四场景回归 → 按仓库规范落盘。适用于「给某网站或 APP 做每日签到」「HAR 模板断言写不对」「签到接口鉴权失败也返回 200」这类场景。 |

> 表格里的链接指向 **skill 目录**而不是 `SKILL.md`，因为 skill 除了正文还带 `references/` 参考资料，只保存单个文件会丢掉目录结构。

## 安装

skill 有两种生效范围，按需要选一个：

| 范围 | 放到哪里 | 说明 |
| --- | --- | --- |
| 项目级 | `<项目根>/.dsh/skills/<skill-name>/` | 只在该项目（含 `.git` 的目录）里可见，适合随项目一起提交 |
| 用户级 | `<DSH_HOME>/skills/<skill-name>/` | 全局可见。Windows 下 `DSH_HOME` 通常是 `C:\Users\<你>\.dsh` |

复制时**必须整个目录一起复制**（含 `references/`），只拷 `SKILL.md` 会让正文里的相对链接失效。

也可以用 `git clone` 拿到全部 skill 后再挑：

```powershell
git clone https://github.com/Faye-Night/Faye-SKILL.git
Copy-Item -Recurse "Faye-SKILL\make-har" "$env:USERPROFILE\.dsh\skills\make-har"
```

安装后在 DSH 会话里调用 `skill({ name: "make-har" })` 加载，或直接说「用 make-har 做一个 XX 的签到」让它自动匹配。

## 目录结构

```
Faye-SKILL/
├── README.md
├── .gitattributes
├── .gitignore
└── make-har/
    ├── SKILL.md              # skill 正文（frontmatter + 五阶段流程）
    └── references/
        ├── recon.md          # 侦察与逆向：CDP 探测、SPA bundle、浏览器锁库时读凭据
        └── qd-engine.md      # qd 引擎行为：断言优先级、jinja 陷阱、api:// 协议
```

## 添加新 skill 的约定

- **一个 skill 一个目录**，目录名等于 skill 名，且必须符合 kebab-case（`^[a-z0-9]+(?:-[a-z0-9]+)*$`），如 `make-har`
- 目录内必须有 `SKILL.md`，frontmatter 至少包含 `name` 和 `description`
- `description` 不超过 500 字符，写清**什么时候该用**（模型只靠 name + description 决定是否加载，正文它看不到）
- 参考资料、脚本、模板放在该 skill 目录内，正文用相对路径引用，不要引用仓库外的文件
- 不在仓库里放真实凭据（token、Cookie、手机号等），示例一律用 `<YOUR_TOKEN>` 这类占位符
- 新增后更新本 README 的 Skill 列表表格

## 参考

- [DSH Skills 文档](https://dshx.dev/docs/internals/skills/)
- [qd 项目](https://github.com/qd-today/qd)
