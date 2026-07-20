# MMN 统一数据目录规范

## 唯一根目录

- 本地：`MMN_DATA_ROOT`，默认 `<repo>/data`
- 服务器容器：`MMN_DATA_ROOT=/app/data`
- 备份：`MMN_BACKUP_ROOT`，本地默认 `<repo>/backups`，服务器为 `/app/backups`
- `MMN_DATA_DIR` 暂作为兼容别名；新代码只使用 `MMN_DATA_ROOT` 和 `mmn_data.module_path()`。

## 板块目录

| 板块 | 规范相对路径 |
| --- | --- |
| 核心数据库 | `core/` |
| 产品评价与车型资产 | `modules/product_evaluation/` |
| 月度销量预警 | `modules/sales_warning/` |
| 市场与周报 | `modules/market_intelligence/` |
| 政策情报 | `modules/policy_intelligence/` |
| 达人与内容资产 | `modules/creator_assets/` |
| 机会与产品证据 | `modules/opportunity/` |
| RAG 资产 | `modules/rag/` |
| Eval 评测 | `modules/eval/` |
| 原始导入 | `imports/raw/` |
| 处理后导入 | `imports/processed/` |
| 运行状态与任务 | `runtime/` |
| 报告 | `reports/` |

## 调用规则

1. 模块不得自行拼接 `ROOT / "data"`，必须通过统一路径解析器。
2. 兼容期允许从旧路径读取，但所有新写入只能进入规范路径。
3. 原始文件、处理后资产和运行状态分开保存；处理文件必须保留来源文件名、周期和校验值。
4. 部署前必须同时生成代码备份、`/app/data` 数据备份和 SHA-256 校验清单。
5. 恢复操作不得直接覆盖当前数据；必须先做恢复前备份，并经过清单校验。

## 当前迁移策略

采用兼容迁移：先建立规范路径和统一解析器，再逐板块迁移；旧路径在全部消费者完成迁移前只读保留，避免一次性搬迁造成数据丢失。
