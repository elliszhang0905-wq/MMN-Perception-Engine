from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    ListFlowable, ListItem, KeepTogether,
)

FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
pdfmetrics.registerFont(TTFont("MMN-CN", FONT_PATH))
F = "MMN-CN"

styles = getSampleStyleSheet()
body = ParagraphStyle("BodyCN", parent=styles["BodyText"], fontName=F, fontSize=9.2,
                      leading=14, textColor=colors.HexColor("#111111"), spaceAfter=6)
small = ParagraphStyle("SmallCN", parent=body, fontSize=7.5, leading=10.5,
                       textColor=colors.HexColor("#666666"), spaceAfter=2)
h1 = ParagraphStyle("H1CN", parent=body, fontSize=17, leading=22, spaceAfter=5,
                    textColor=colors.HexColor("#111111"))
h2 = ParagraphStyle("H2CN", parent=body, fontSize=13.5, leading=18, spaceBefore=11,
                    spaceAfter=7, textColor=colors.HexColor("#111111"))
h3 = ParagraphStyle("H3CN", parent=body, fontSize=10.5, leading=15, spaceBefore=6,
                    spaceAfter=4, textColor=colors.HexColor("#111111"))
table_head = ParagraphStyle("TableHead", parent=small, fontSize=7.6, leading=10,
                            textColor=colors.HexColor("#666666"))
table_body = ParagraphStyle("TableBody", parent=body, fontSize=8.2, leading=11.5, spaceAfter=0)

def P(text, style=body): return Paragraph(text, style)

def bullets(items, level=0):
    return ListFlowable(
        [ListItem(P(item), leftIndent=8) for item in items],
        bulletType="bullet", leftIndent=15 + level * 10, bulletFontName=F,
        bulletFontSize=6, bulletOffsetY=1.5, spaceAfter=7,
    )

def table(data, widths, header=True):
    rows = []
    for ri, row in enumerate(data):
        rows.append([P(cell, table_head if header and ri == 0 else table_body) for cell in row])
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("FONTNAME", (0,0), (-1,-1), F),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LINEBELOW", (0,0), (-1,-1), .35, colors.HexColor("#E4E4E4")),
    ]
    if header:
        commands += [("LINEBELOW", (0,0), (-1,0), .6, colors.HexColor("#D2D2D2"))]
    t.setStyle(TableStyle(commands))
    return t

def page_header_footer(c, doc):
    c.saveState()
    c.setFont(F, 7.5); c.setFillColor(colors.HexColor("#777777"))
    c.drawString(doc.leftMargin, letter[1] - 28, "Data Analytics report")
    c.drawRightString(letter[0] - doc.rightMargin, letter[1] - 28, "Jul 18, 2026 · MMN")
    c.setStrokeColor(colors.HexColor("#E5E5E5")); c.setLineWidth(.5)
    c.line(doc.leftMargin, letter[1] - 36, letter[0] - doc.rightMargin, letter[1] - 36)
    c.drawRightString(letter[0] - doc.rightMargin, 22, str(doc.page))
    c.restoreState()

def build(out):
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(out), pagesize=letter, leftMargin=44, rightMargin=44,
                            topMargin=48, bottomMargin=35, title="MMN达人蒸馏与孵化能力说明",
                            author="MMN")
    story = []

    story += [P("MMN达人蒸馏 / 孵化能力说明", h1),
              P("面向汽车企业品牌、内容营销、媒介与用户洞察团队的当前能力口径", small),
              Spacer(1, 8), P("Executive Summary", h2),
              bullets([
                  "MMN达人蒸馏的目标，是把达人从一张资源名单转化为有证据、可比较、可调用的企业内容资产。",
                  "系统回答三个业务问题：达人擅长讲什么、如何表达、适合承担什么车型和传播任务。",
                  "当前已形成身份校验、内容采集、代表作筛选、多模态证据、内容DNA草稿、模型质检和人工审核的基本闭环。",
                  "核心达人资产流程已经实际运行；新增多视觉模型、专用OCR和长视频转写已完成代码与测试，仍需真实API端到端验收。",
              ]),
              P("一、业务问题与定位", h2),
              P("传统达人筛选主要依赖粉丝量、互动率、平台标签和人工经验。这些信息适合资源搜索，却很难判断达人是否真正适合当前车型、品牌定位和内容任务。MMN补足的是内容能力判断：分析代表作中的选题、叙事、专业解释、视觉表达和受众反馈，并把判断与具体作品证据关联。"),
              P("对外建议使用的产品名称", h3),
              P("MMN达人内容能力诊断与资产沉淀。底层模型名称属于内部质检配置，客户侧统一呈现为MMN多模态策略输出。"),
              P("二、当前能力总览", h2),
              table([
                  ["能力模块", "系统处理", "主要产出", "当前状态"],
                  ["身份门禁", "核对主页ID、平台和达人名称；不一致即停止", "可追溯账号身份", "已实际运行"],
                  ["内容采集", "采集主页、作品、指标、评论并保留缺失字段", "标准化达人与作品数据", "已实际运行"],
                  ["代表作筛选", "综合互动表现、稳定性、差异性和噪声因素", "代表作及入选理由", "已实际运行"],
                  ["多模态理解", "字幕、ASR、OCR、画面和镜头结构分析", "内容与视觉证据", "部分实际运行；新增链路待验收"],
                  ["交叉质检", "检查结论一致性、共同证据和置信度", "质检状态与冲突原因", "代码与测试完成；待真实验收"],
                  ["资产沉淀", "保存达人、作品、证据、来源和版本", "达人档案与内容方法资产", "已实际运行"],
              ], [82, 190, 145, 105]),
              PageBreak()]

    story += [P("三、能力闭环", h2),
              table([
                  ["步骤", "处理内容", "硬边界"],
                  ["1. 身份校验", "主页ID、平台、达人名称核验", "错配时不抓作品、不抓评论、不入库"],
                  ["2. 数据采集", "主页、作品、指标、评论及来源记录", "缺失值保留为空，不伪造为零"],
                  ["3. 代表作筛选", "综合表现、稳定性与内容差异", "不采用简单点赞Top N"],
                  ["4. 多模态证据", "字幕、语音转写、OCR、画面和镜头", "看不到的信息不推测"],
                  ["5. 模型质检", "共同证据、结论一致性、置信度", "超时、冲突或证据不足时禁止发布"],
                  ["6. 资产沉淀", "达人档案、内容DNA、任务建议与方法资产", "未经人工确认的结果仍是待审核推断"],
              ], [85, 245, 195]),
              P("四、可形成的内容能力判断", h2),
              table([
                  ["判断域", "可识别内容", "典型用途"],
                  ["账号定位", "专家科普、产品评测、行业评论、使用建议、生活方式等", "达人初筛与账号定位"],
                  ["选题能力", "技术科普、车型评测、场景问题、行业议题等", "Campaign选题和内容支柱"],
                  ["叙事结构", "问答解释、问题拆解、对比评测、演示验证、访谈等", "Brief和脚本结构"],
                  ["表达方式", "专业严谨、口语交流、情绪表达、推广表达等", "品牌调性和人选匹配"],
                  ["视觉形态", "人物口播、产品演示、图文讲解、多镜头剪辑等", "拍摄方式和制作资源判断"],
                  ["受众反馈", "车型疑问、产品争议、专业纠偏、购买影响", "舆情辅助验证"],
              ], [90, 265, 170]),
              P("五、模型质检规则", h2),
              bullets([
                  "达人内容结论必须引用已入库的真实证据ID。",
                  "视觉判断需要具备独立视觉观察证据；单一视觉模型不能直接形成最终视觉标签。",
                  "不同判断模型需要在分类和共同证据上达成一致，并达到最低置信度门槛。",
                  "模型未完成、证据不重合或结论冲突时，状态转为manual_required，不发布正式达人DNA。",
              ]),
              PageBreak()]

    story += [P("六、汽车企业可以使用的场景", h2),
              table([
                  ["业务场景", "MMN可以回答的问题", "交付物"],
                  ["达人初筛与建档", "账号是否匹配、主要做什么、代表作和基础风险是什么", "候选达人档案"],
                  ["车型上市Campaign", "谁适合技术解释、体验表达、疑虑澄清或生活方式内容", "达人组合与Campaign Brief"],
                  ["达人内容能力诊断", "达人擅长什么选题、如何开场、如何组织证据和视觉表达", "内容DNA"],
                  ["新账号孵化", "适合建立哪些栏目、首批选题和30天验证节奏", "账号孵化方案"],
                  ["竞品达人研究", "不同账号在专业能力和表达方式上有什么差异", "达人能力对标图谱"],
                  ["舆情辅助验证", "当前达人受众在讨论哪些车型问题、争议和纠偏", "平台级候选信号"],
              ], [105, 275, 145]),
              P("七、一次达人诊断的交付物", h2),
              table([
                  ["交付类别", "主要内容"],
                  ["达人能力档案", "身份与来源、账号定位、内容赛道、代表作和专业表达特征"],
                  ["内容DNA", "核心选题、内容支柱、开场、叙事结构、视觉形态和语言方式"],
                  ["营销调用建议", "适用车型、传播阶段、营销任务、Brief建议和合作前复核事项"],
                  ["企业内容资产", "可检索标签、可复用选题方法、脚本结构、内容规则和反馈记录"],
              ], [120, 405]),
              P("八、与传统达人库的关系", h2),
              table([
                  ["比较维度", "传统达人库", "MMN达人内容能力资产"],
                  ["主要回答", "有哪些达人", "为什么适合当前任务"],
                  ["核心数据", "粉丝、互动、报价、合作记录", "代表作、内容结构、视听证据、受众反馈"],
                  ["使用环节", "资源搜索和采购管理", "人选判断、Brief、内容策略和复盘"],
                  ["风险控制", "依赖人工抽查", "身份门禁、模型冲突拦截和人工审核"],
                  ["沉淀结果", "项目级名单", "跨项目复用的企业内容资产"],
              ], [90, 205, 230]),
              P("两者不是替代关系。现有达人库可以继续承载报价、合同和合作管理；MMN负责内容能力判断和策略调用。"),
              PageBreak()]

    story += [P("九、当前成熟度", h2),
              P("已实际运行并形成数据", h3),
              bullets(["身份校验与TikHub采集。", "代表作筛选、证据入库和达人档案。", "平台字幕与Qwen VL视觉证据。", "作品拆解、舆情辅助判断和审核页面。"]),
              P("代码已实现并通过相关测试", h3),
              bullets(["Qwen 3.7主视觉和Qwen 3.6降级。", "Kimi独立视觉复核。", "专用OCR和长视频异步ASR。", "Qwen与DeepSeek共同证据门禁及页面发布拦截。"]),
              P("上线前仍需完成", h3),
              bullets(["轮换后新API Key的真实调用。", "达人完整业务流端到端验收。", "生产环境时延、成本和并发验证。", "企业Gold Set及人工审核阈值确认。"]),
              P("十、不能直接承诺的能力", h2),
              bullets([
                  "不能根据少量代表作概括账号全部内容。",
                  "不能根据单个评论区推断全市场需求或真实销量影响。",
                  "不能仅凭内容能力判断达人真实报价、交付质量或销售转化能力。",
                  "不能保证外部平台或模型永不返回错误数据；系统通过身份门禁、证据校验和人工复核降低风险。",
                  "新增多模型链路未完成真实API验收前，不对外描述为生产可用。",
              ]),
              P("十一、建议的试点方式", h2),
              table([
                  ["阶段", "主要工作", "验收重点"],
                  ["第1周：口径与样本", "确定车型、传播阶段、达人范围和人工审核标准", "样本与任务口径一致"],
                  ["第2周：采集与诊断", "建立达人档案，提取代表作与多模态证据", "身份准确、证据完整"],
                  ["第3周：任务匹配", "形成达人组合、内容DNA和Brief建议", "业务团队认为可执行"],
                  ["第4周：复核与沉淀", "确认标签、争议案例和企业方法资产", "形成可复用规则"],
              ], [110, 265, 150]),
              P("试点建议关注：身份错配率、证据完整度、人工认可率、Brief可执行性、单达人处理成本与时延。", body),
              P("口径与资料范围", h2),
              P(
                  "• 本说明基于MMN当前达人蒸馏代码、数据库证据和相关测试状态，日期为2026年7月18日。<br/>"
                  "• “已实际运行”表示已有真实数据记录；“代码已实现”表示功能和相关测试完成，但不等同于生产验收。<br/>"
                  "• MMN是一套面向汽车行业的营销决策操作系统。本模块属于内容资产与策略方法论沉淀，不承担经销商销售管理职能。",
                  small,
              )]

    doc.build(story, onFirstPage=page_header_footer, onLaterPages=page_header_footer)

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "output/pdf/MMN-达人蒸馏与孵化能力说明-干净文字版-20260718.pdf"
    build(target)
