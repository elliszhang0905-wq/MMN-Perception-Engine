# MMN GEO 本机与 ECS 同步发布 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Independent release review follows the repository quality gate.

**Goal:** 将2026-10-08全部GEO代码、文档与已核验能力增量发布到本机8765和ECS，入口可见且数据受保护。

**Architecture:** 复用现有干净9月16日发布工作树，三方合并当天GEO差异，保留已上线周度调度、知识工作区和UI。GEO强制配置独立SQLite，车型目录从主库只读查询；模块开启，真实采样关闭、worker off、批次/日预算0。本机用受管只读发布，ECS从当前精确镜像叠加代码后走既有蓝绿门禁。

**Tech Stack:** Python标准库、原生JS/CSS、SQLite、launchd、Docker Compose、Git。

## Global Constraints

- 最新用户直接授权本机和服务器发布；原开发目录既有未提交文件不整体提交或覆盖。
- 不显示或提交密钥，不追加模型请求；之前累计最多3次额度已耗尽。
- 不覆盖业务数据库、导入文件、快照和既有配置秘密；GEO只写新的独立geo.sqlite。
- 保留旧本机物理release、ECS镜像、配置与一致性数据备份，代码回退不回滚业务数据。
- 不改DNS、代理、证书、域名或其他产品，不启用其他待验开关。
- 版本统一为beta-1.03-20261008-geo-1；公网入口、SSH维护通路和本机验收分开记录。

---

### Task 1: 冻结与增量整合

**Files:** 原目录geo/、geo.js、geo.css、scripts/run_geo_worker.py、tests/test_geo*、tests/fixtures/geo_semantic.json、GEO_*.md及当日研发档案；候选目录server.py、index.html、app.js、.env.example。
**Interfaces:** 输入output/geo-20261008/baseline和当前已安装release；输出可审查的当天差异、候选运行文件SHA256清单。

- [x] 核验本机listener/cwd及ECS镜像/配置/数据根，创建只读一致性备份并记录逐表内容指纹。
- [x] 以开工快照生成server/index/app三方补丁并合入现有发布基线，任何冲突逐段核对，保留已有功能。
- [x] 复制当天GEO专属代码/测试/文档，不复制output、.env或测试库；统一缓存版本和应用版本。

### Task 2: GEO独立数据边界

**Files:** geo/config.py、geo/api.py、tests/test_geo_config.py、tests/test_geo_api.py、.env.example、GEO_RUNBOOK.md。
**Interfaces:** MMN_GEO_DB_PATH只在后端读取；execute现有db_path仍为业务主库，GEO仓库使用显式独立路径；catalog从主库mode=ro读取，保持org/edition筛选。

- [x] 先增加真实临时SQLite行为测试：GEO项目只写独立库，catalog读取主库车型，主库hash不变，模块关闭不创建独立库。
- [x] 运行python3 -m unittest tests.test_geo_api tests.test_geo_config -v并保存预期RED失败。
- [x] 最小实现后端路径配置和只读车型目录，重新运行同一测试得到GREEN。
- [x] 发布配置仅增量MMN_GEO_ENABLED=true、MMN_GEO_DB_PATH=受管state/geo.sqlite或/app/data/geo.sqlite、真实=false、worker=off、两个预算0。

### Task 3: 新鲜验证与独立审查

**Files:** 候选测试/发布脚本及docs/研发档案/2026-10-08_v1.3_GEO双环境发布.md、MMN_CURRENT_STATE.md。
**Interfaces:** 输入候选制品，输出完整测试/浏览器/审查/数据保护证据。

- [x] 全量Python和Node合同、Python编译与JS语法、npm run check:mmn-state及完整release gate。所有浏览器发布前流程仅使用业务库副本、空配置、GEO真实off。
- [x] 实际浏览器点击GEO六页、创建测试项目/问题、阻塞计划、人工证据和导出；桌面/390px，检查控制台/网络与溢出，截图归档。
- [x] 按AGENTS要求独立审查需求、测试、实际diff；处理Critical/Required并重跑受影响检查。
- [x] 提交并推送独立发布分支和精确版本标签，禁止force push或捆绑旧脏文件。

### Task 4: 本机与ECS正式发布

**Files:** 受管runtime配置与发布回执；ECS仅代码overlay制品及发布元数据。
**Interfaces:** 输入已验证提交/overlay SHA256，输出两端真实版本、开关、listener/镜像身份与业务验证。

- [x] 本机publish preserve-state，再agent install并verify；安装失败使用原保护回退，不削弱验证。
- [x] ECS从当前精确镜像COPY当天代码增量，沿用现有MMN_DEPLOY_CODE_ONLY=true蓝绿流程；保留worker/scheduler/数据库服务和数据卷。
- [x] 两端检查health/ready、GEO能力/目录/项目列表及既有业务接口，实际浏览器登录并点击GEO；不触发付费模型、不写测试记录到正式库。
- [x] 核对主业务库逐表差异、独立GEO库、秘密字段不变、已有调度服务身份，记录真实副作用，不删除记录制造零漂移。
- [x] 更新状态包/发布回执，重新运行状态门禁，给出访问入口、版本、验证与残余限制。

### 最终验收限定

正式两端版本/API/配置/数据核验通过，既有业务逻辑内容零变化。正式本地浏览器因工具拦截受阻，以隔离真实浏览器和正式接口分别留证，不声称正式浏览器通过。公网入口仍为HTTP403/HTTPS连接失败。后续UI不部署、不新增收费调用。
