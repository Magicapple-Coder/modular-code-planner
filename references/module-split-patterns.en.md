# Module split patterns and per-stack conventions

Used by workflow A (read the section for your stack before planning) and workflow C (extraction techniques) of `modular-code-planner`.

---

## 1. General layering model

```
entry layer  →  business layer  →  domain/data layer  →  shared utilities
(wiring only)   (use-case          (entities,             (no business
                 orchestration)     repositories)          semantics)
```

Constraints:

- Dependencies flow left to right only. **A layer may never import from the right of the arrow, nor from a layer above it.**
- Within a layer, modules should mostly not reference each other. If they must, state why.
- The shared utility layer must never import back into the business layer. This is the most common violation.

### One file, one kind of change

The test for "one kind of change": when a requirement shifts, code that gets modified together for the same reason belongs in the same file; code modified for different reasons belongs in different files. This is a more reliable signal than whether the code *looks* similar.

---

## 2. Extraction techniques, in priority order

| Technique | Signal | Notes |
|---|---|---|
| Extract by responsibility block | The file has comment banners or `# ===== section =====` headers | Safest; logic barely changes |
| Extract by type/model | Several unrelated classes, interfaces or constants in one file | Move to `models/`, `types/`; usually zero logic change |
| Extract by data access | SQL/ORM calls and business decisions side by side | Move to `repository/`, `dao/` |
| Extract pure functions | Side-effect-free logic that only depends on its arguments | Move to `utils/` or a domain-level `rules.py` — never a catch-all utils |
| Extract by adapter | One responsibility with several external implementations (HTTP/DB/MQ) | Define a port interface plus implementation files |
| Thin aggregation layer | Many external references to the original file's symbols | Keep re-exports in the original, converge later |

**Rename and move are separate operations.** These techniques move code. When a rename is genuinely required, do it as its own step so the diff stays readable.

---

## 3. Per-stack conventions

### Python

```
project/
├── src/<pkg>/
│   ├── __main__.py / cli.py      # entry: argument parsing and wiring only, <=100 lines
│   ├── config.py                 # config loading and validation
│   ├── domain/                   # pure domain models and rules, no framework imports
│   ├── services/                 # use-case orchestration
│   ├── repositories/             # data access
│   ├── api/ or routers/          # HTTP layer
│   └── utils/                    # semantics-free helpers, must not grow without limit
└── tests/
```

- Package-level `__init__.py` is the place to re-export the public API; a transition export works there during a refactor.
- Watch for `importlib`, `getattr(module, name)`, decorator registries, Django `AppConfig`, pytest's automatic `conftest.py` discovery, and `entry_points` string paths. These are string references: renaming or moving breaks them silently.
- Cycle detection: `pydeps`, `python -X importtime`, or `import-linter`.

### JavaScript / TypeScript

```
src/
├── main.ts(x) / index.ts         # entry: wiring only
├── app/                          # app-level init, route registration
├── features/<feature>/           # vertical slice: component + hook + API together
│   ├── components/
│   ├── hooks/
│   ├── api.ts
│   └── types.ts
├── shared/                       # cross-feature reuse: ui/, utils/, types/
└── lib/                          # third-party wrappers
```

- Prefer **vertical slices by feature** over horizontal slices by technical type. A `components/` directory holding 200 files is the same oversized-file problem wearing a different hat.
- Barrel files (`index.ts` re-exports) hide dependency direction and can create cycles. Check `madge --circular src` after a refactor.
- Watch dynamic `import()`, `require.context`, route strings, path strings in `React.lazy`, and global component registration in Vue.
- Component files can relax to soft 400 / hard 600. Keep logic layers (hooks, services) at soft 300 / hard 500.

### Java / Kotlin

```
src/main/java/<pkg>/
├── Application.java              # bootstrap class: wiring only
├── controller/  (or api/)
├── service/     (interface + impl/)
├── domain/      (entity/vo/dto)
├── repository/
└── config/
```

- Packages are the natural module boundary. Prefer splitting packages and classes over splitting methods.
- Watch Spring component scanning (`@ComponentScan` scope), `@MapperScan`, `type-aliases-package` in `application.yml`, and MyBatis XML namespaces. All must be updated together.
- Cycle detection: `jdeps --cycle`, or ArchUnit rules.

### Go

```
cmd/<app>/main.go                 # entry, <=100 lines
internal/
├── handler/  service/  repository/  domain/
├── config/
└── pkg/                          # libraries importable from outside
```

- Split by package; avoid a `utils` package. The package name *is* the responsibility.
- Watch `init()` side effects, anonymous registration imports (`_ "pkg"`), and the relative paths in `embed` directives — moving a file breaks embedding.
- Cycles are a compile error, which is Go's built-in advantage.

### C#

- Split into separate `.cs` files, using `partial class` as a transition. Watch `namespace`, `Compile Include` globs in the `.csproj`, DI registration, and `[assembly: ...]` attributes.
- Detection: `dotnet list package` is unrelated; use NDepend or Roslyn analyzers for structural problems.

---

## 4. Common anti-patterns

| Anti-pattern | Symptom | Treatment |
|---|---|---|
| God object | One class or file over 1000 lines, methods sharing large mutable state | Identify the shared state first, split by state cluster, then move methods |
| Utils black hole | `utils.py` or `helpers.ts` growing without end | Split by domain into `date_utils`, `string_utils`, or push helpers down to their callers |
| Universal service | `service.py` holding every use case | Split into several services by aggregate root or use case |
| Implicit ordering | Module-level code depending on import order | Explicit init functions; no import side effects |
| Dependency cycle | A imports B, B imports A | Extract shared types or interfaces into a third module |
| Copy-paste split | The two new files still contain identical blocks | Extract the common block first, then split |

---

## 5. Interface compatibility strategies

After a split, exported symbols from the original file can be handled three ways:

| Strategy | Fits when | How | Cost |
|---|---|---|---|
| A. Update every reference | Few callers (<10), all in this repo | Update all imports | One large diff |
| B. Re-export transition layer | Many callers, or it is the package's public API | Keep `from .new_module import X` in the original, marked `@deprecated` | An extra hop of indirection |
| C. Compatibility wrapper | The old signature needs adapting | Keep same-named functions that delegate to the new implementation | Wrapper maintenance |

Rule of thumb: **libraries and published packages prefer B and C; applications prefer A.** The plan must state which one was chosen and why.

---

## 6. Signals that you should *not* split

- The file is long but has a single responsibility and no separable state — a large lookup table, or a block of generated constants.
- Splitting would cause heavy parameter passing or context threading, e.g. forcing ten arguments into a function just to make it smaller.
- The file is stable legacy code that is barely touched and has no test coverage, so the risk of splitting exceeds the benefit.

Record these in the plan with the reason for not splitting, rather than forcing a split anyway.
