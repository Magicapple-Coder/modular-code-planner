# 模块拆分模式与各技术栈惯例

供 `modular-code-planner` 工作流 A（规划前读取对应技术栈小节）与工作流 C（拆分手法）使用。

---

## 一、通用分层模型

```
入口层  →  业务层  →  领域/数据层  →  公共工具层
（只装配）  （用例编排）  （实体/仓储）   （无业务语义）
```

约束：

- 依赖只能自左向右，**左侧不得引用右侧之上**。
- 同层之间尽量不互相引用；必须引用时说明理由。
- 公共工具层不得反过来 import 业务层（最常见违规）。

### 一个文件一类变化

判断「该类变化」的口径：需求变更时，会因同一个原因被同时修改的代码，应放在同一个文件；因不同原因被修改的代码，应分属不同文件。这条比「代码看起来像不像」更可靠。

---

## 二、拆分手法（按优先级）

| 手法 | 适用信号 | 说明 |
|---|---|---|
| 按职责块提取 | 文件里有注释分区、`# ===== xxx =====` 标题 | 最安全，几乎不用改逻辑 |
| 按类型/模型提取 | 文件内混杂多个类/接口/常量 | 抽到 `models/`、`types/`，通常零逻辑变更 |
| 按数据访问提取 | 文件里同时有 SQL/ORM 调用与业务判断 | 抽到 `repository/`、`dao/` |
| 按纯函数提取 | 无副作用、只依赖入参的计算逻辑 | 抽到 `utils/` 或领域内的 `rules.py`（避免大杂烩 utils） |
| 按适配器提取 | 同一职责有多套外部实现（HTTP/DB/MQ） | 定义端口接口 + 实现文件 |
| 薄聚合层过渡 | 外部大量引用原文件符号 | 原文件保留 re-export，后续再收敛 |

**改名与移动分离**：本节手法只做「移动」。确需改名时单独成一步，避免 diff 不可读。

---

## 三、各技术栈惯例

### Python

```
project/
├── src/<pkg>/
│   ├── __main__.py / cli.py      # 入口，只做参数解析与装配，≤100 行
│   ├── config.py                 # 配置读取与校验
│   ├── domain/                   # 纯领域模型与规则，不 import 框架
│   ├── services/                 # 用例编排
│   ├── repositories/             # 数据访问
│   ├── api/ 或 routers/          # HTTP 层
│   └── utils/                    # 无业务语义工具，禁止无限膨胀
└── tests/
```

- 包级 `__init__.py` 用于 re-export 公开 API；重构期可在此加过渡导出。
- 注意 `importlib`、`getattr(module, name)`、装饰器注册表、Django `AppConfig`、pytest `conftest.py` 自动发现、`entry_points` 字符串路径——这些是字符串引用，改名/移动会静默失效。
- 循环依赖检测：`pydeps`, `python -X importtime`, 或 `import-linter`。

### JavaScript / TypeScript

```
src/
├── main.ts(x) / index.ts         # 入口，只装配
├── app/                          # 应用级初始化、路由注册
├── features/<feature>/           # 按功能垂直切分：组件+hook+API 同目录
│   ├── components/
│   ├── hooks/
│   ├── api.ts
│   └── types.ts
├── shared/                       # 跨功能复用：ui/、utils/、types/
└── lib/                          # 第三方封装适配
```

- 优先**按功能垂直切分**，而非按技术类型横向切（`components/` 里塞 200 个文件同样是巨型文件问题的变体）。
- 注意 barrel file（`index.ts` 再导出）会掩盖依赖方向，也可能引入循环依赖；重构后检查 `madge --circular src`。
- 注意动态 `import()`、`require.context`、路由字符串、`React.lazy` 的路径字符串、Vue 全局组件注册。
- 组件文件可放宽到软 400 / 硬 600；逻辑层（hooks/service）建议保持软 300 / 硬 500。

### Java / Kotlin

```
src/main/java/<pkg>/
├── Application.java              # 启动类，只做装配
├── controller/  (或 api/)
├── service/     (接口 + impl/)
├── domain/      (entity/vo/dto)
├── repository/
└── config/
```

- 包 = 模块的天然边界；拆分优先「拆包 + 拆类」而非「拆方法」。
- 注意 Spring 组件扫描（`@ComponentScan` 范围）、`@MapperScan`、`application.yml` 里的 `type-aliases-package`、MyBatis XML namespace 必须同步更新。
- 循环依赖检测：`jdeps --cycle` 或 ArchUnit 规则。

### Go

```
cmd/<app>/main.go                 # 入口，≤100 行
internal/
├── handler/  service/  repository/  domain/
├── config/
└── pkg/                          # 可被外部导入的公共库
```

- 按包拆分，避免 `utils` 包；包名即职责。
- 注意 `init()` 副作用、`_ "pkg"` 匿名导入注册、`embed` 指令的相对路径（移动文件会破坏 embedding）。
- 循环依赖由编译器直接报错，是 Go 的天然优势。

### C#

- 拆到独立 `.cs` 文件 + `partial class` 过渡；注意 `namespace`、`csproj` 的 `Compile Include` 通配、DI 注册与 `[assembly: ...]` 特性。
- 检测：`dotnet list package --include-transitive` 无关；结构问题用 NDepend 或 Roslyn 分析器。

---

## 四、常见反模式

| 反模式 | 症状 | 处理 |
|---|---|---|
| 上帝对象 | 单类/单文件 >1000 行，方法间共享大量可变状态 | 先识别共享状态，按状态簇拆，再迁方法 |
| utils 黑洞 | `utils.py`/`helpers.ts` 无限增长 | 按领域拆分为 `date_utils`、`string_utils` 或下沉到使用方 |
| 万能 service | `service.py` 里塞所有用例 | 按聚合根/用例拆多个 service |
| 隐式顺序依赖 | 模块级代码依赖 import 顺序 | 显式初始化函数，禁止 import 副作用 |
| 循环依赖 | A 引用 B，B 引用 A | 抽共享类型/接口到第三方模块 |
| 复制粘贴型拆分 | 拆完两文件里有相同代码块 | 先提取公共块，再拆 |

---

## 五、对外接口兼容策略

拆分后原文件对外符号有三种处理方式：

| 策略 | 适用 | 做法 | 代价 |
|---|---|---|---|
| A 全量更新引用 | 引用方少（<10 处）且都在本仓库 | 更新所有 import | 一次性大 diff |
| B re-export 过渡层 | 引用方多 / 是包对外 API | 原文件保留 `from .new_module import X` 并标记 `@deprecated` | 多一层间接 |
| C 兼容包装 | 需要对旧签名做适配 | 保留同名函数转调新实现 | 需维护包装 |

选择原则：**库/对外发布包优先 B+C，应用内部优先 A**。方案阶段必须明确写出选了哪个及理由。

---

## 六、不要拆的信号

- 文件虽长但只有一个职责、且没有可分离的状态（例如一张很长的查找表、一段生成的常量）。
- 拆分会导致大量参数传递/上下文穿透（把 10 个参数塞进函数只为「拆开」）。
- 文件是稳定的、几乎不再修改的遗留代码，且没有测试覆盖——拆分的风险大于收益。

以上情况应记录在方案中并说明「不拆」的理由，而不是硬拆。
