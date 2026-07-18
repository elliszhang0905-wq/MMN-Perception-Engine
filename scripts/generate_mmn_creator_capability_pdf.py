from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

W, H = 960, 540
FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
pdfmetrics.registerFont(TTFont("MMN-CN", FONT_PATH))
F = "MMN-CN"

C = {
    "bg": HexColor("#07162B"), "panel": HexColor("#0C213D"), "panel2": HexColor("#102A49"),
    "blue": HexColor("#23B7FF"), "cyan": HexColor("#40E0D0"), "orange": HexColor("#FFB24A"),
    "red": HexColor("#FF6B6B"), "green": HexColor("#55D98A"), "white": HexColor("#F4F8FC"),
    "text": HexColor("#D7E4F1"), "muted": HexColor("#8FA6BF"), "line": HexColor("#244565"),
    "dark": HexColor("#061121"),
}

def ytop(y, h=0): return H - y - h

def fit_size(text, max_width, size, minimum=6):
    while size > minimum and pdfmetrics.stringWidth(str(text), F, size) > max_width:
        size -= .5
    return size

def txt(c, text, x, y, w, h, size=12, color=None, bold=False, align="left", valign="top"):
    text = str(text or "")
    size = fit_size(text.replace("\n", ""), w, size)
    c.setFont(F, size)
    c.setFillColor(color or C["text"])
    lines = text.split("\n")
    leading = size * 1.35
    total = len(lines) * leading
    base = ytop(y, h) + h - leading if valign == "top" else ytop(y, h) + (h + total) / 2 - leading
    for i, line in enumerate(lines):
        width = pdfmetrics.stringWidth(line, F, size)
        xx = x if align == "left" else (x + w - width if align == "right" else x + (w - width) / 2)
        c.drawString(xx, base - i * leading + size * .18, line)

def round_rect(c, x, y, w, h, fill, stroke=None, radius=8, width=1):
    c.setFillColor(fill); c.setStrokeColor(stroke or fill); c.setLineWidth(width)
    c.roundRect(x, ytop(y, h), w, h, radius, fill=1, stroke=1)

def line(c, x1, y1, x2, y2, color=None, width=1):
    c.setStrokeColor(color or C["line"]); c.setLineWidth(width)
    c.line(x1, H-y1, x2, H-y2)

def arrow(c, x1, y1, x2, y2, color=None, width=1.5):
    color = color or C["blue"]
    line(c, x1, y1, x2, y2, color, width)
    c.setFillColor(color); c.setStrokeColor(color)
    c.saveState(); c.translate(x2, H-y2)
    c.rotate(0 if x2 >= x1 else 180)
    p = c.beginPath(); p.moveTo(0,0); p.lineTo(-7,4); p.lineTo(-7,-4); p.close()
    c.drawPath(p, fill=1, stroke=0); c.restoreState()

def label(c, text, x, y, w, color):
    round_rect(c, x, y, w, 22, C["panel2"], color, 5, .8)
    txt(c, text, x+4, y+4, w-8, 14, 8, color, align="center")

def title(c, kicker, heading, subtitle=""):
    txt(c, kicker, 40, 24, 440, 18, 8.5, C["blue"])
    txt(c, heading, 40, 48, 880, 38, 23, C["white"])
    if subtitle: txt(c, subtitle, 42, 92, 850, 24, 10, C["muted"])

def master(c, page):
    c.setFillColor(C["bg"]); c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(C["blue"]); c.rect(0,H-6,W,6,fill=1,stroke=0)
    txt(c, "MMN · 汽车营销决策操作系统", 36, 514, 300, 14, 7, C["muted"])
    txt(c, "内部能力介绍 · 2026.07", 735, 514, 180, 14, 7, C["muted"], align="right")
    txt(c, str(page), 922, 514, 18, 14, 7, C["muted"], align="right")

def bullet(c, text, x, y, w, color, size=9):
    c.setFillColor(color); c.circle(x+4, H-y-6, 3, fill=1, stroke=0)
    txt(c, text, x+16, y-1, w-16, 20, size, C["text"])

def finish(c): c.showPage()

def build(out):
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out), pagesize=(W,H), pageCompression=1)
    c.setTitle("MMN达人蒸馏与孵化能力介绍"); c.setAuthor("MMN")

    # 1 cover
    c.setFillColor(C["bg"]); c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(HexColor("#0B2948")); c.rect(612,0,348,H,fill=1,stroke=0)
    c.setStrokeColor(C["blue"]); c.setLineWidth(1.2)
    for i in range(6): c.circle(750, 320, 78+i*17, fill=0, stroke=1)
    c.setFillColor(C["panel"]); c.circle(750,320,73,fill=1,stroke=1)
    txt(c,"MMN",692,184,116,45,26,C["white"],align="center")
    txt(c,"CREATOR INTELLIGENCE",680,235,140,18,7,C["cyan"],align="center")
    txt(c,"MMN",48,46,120,28,17,C["blue"])
    txt(c,"达人蒸馏 / 孵化能力介绍",48,118,520,58,29,C["white"])
    txt(c,"把达人从“资源名单”转化为有证据、可比较、可调用的企业内容资产",50,190,500,46,13,C["text"])
    line(c,50,260,540,260,C["line"],1)
    for i,(t,col) in enumerate([("真实内容证据",C["blue"]),("多模态理解",C["cyan"]),("交叉质检",C["orange"]),("人工审核边界",C["green"])]): label(c,t,50+i*122,284,105,col)
    txt(c,"面向品牌、内容营销、媒介与用户洞察团队",50,430,440,22,10,C["muted"])
    txt(c,"2026.07",50,462,100,20,9,C["blue"])
    finish(c)

    # 2 business value
    master(c,2); title(c,"01 · BUSINESS VALUE","让达人选择从“看流量”走向“看内容能力”","MMN回答三个业务问题：他擅长讲什么、怎么讲、适合承担什么营销任务。")
    cols=[("传统做法的盲区",C["red"],["依赖粉丝量与互动率","标签粗、代表作证据缺失","Brief与达人能力错配","项目经验难以复用"]),("MMN的处理方式",C["blue"],["核验账号身份与来源","拆解代表作的内容结构","识别专业与视觉表达","共同证据质检后入库"]),("企业获得的结果",C["green"],["可比较的达人能力档案","更贴合人选的Campaign Brief","可复用的选题与结构方法","持续积累企业内容Know-how"])]
    for i,(head,col,items) in enumerate(cols):
        x=44+i*284; round_rect(c,x,140,252,310,C["panel"],col,9,1)
        c.setFillColor(C["panel2"]); c.setStrokeColor(col); c.circle(x+30,H-176,17,fill=1,stroke=1)
        txt(c,str(i+1),x+21,165,18,16,10,col,align="center")
        txt(c,head,x+58,158,165,30,14,C["white"])
        for j,it in enumerate(items): bullet(c,it,x+20,228+j*48,210,col,9.5)
    arrow(c,300,294,323,294,C["blue"]); arrow(c,584,294,607,294,C["green"])
    txt(c,"业务价值：减少达人选错、Brief错配和经验无法沉淀造成的重复投入。",42,478,850,18,8,C["muted"])
    finish(c)

    # 3 loop
    master(c,3); title(c,"02 · CAPABILITY LOOP","六步形成可追溯的达人内容能力资产","每一步都有来源、状态和失败边界；证据不足时不生成确定性标签。")
    steps=[("01","身份门禁","主页ID与达人名称核验\n错配即停止"),("02","内容采集","主页、作品、指标、评论\n保留缺失字段"),("03","代表作筛选","综合表现、稳定性与差异性\n不是简单点赞Top N"),("04","多模态理解","字幕 / ASR / OCR / 画面 / 镜头\n形成内容证据"),("05","模型交叉质检","共同证据与置信度门槛\n冲突转人工"),("06","资产沉淀与反馈","能力档案、Brief建议、方法资产\n结果持续回流")]
    for i,s in enumerate(steps):
        x=32+i*151; col=C["orange"] if i==4 else (C["green"] if i==5 else C["blue"])
        round_rect(c,x,150,132,230,C["panel2"] if i%2 else C["panel"],col,8,1)
        txt(c,s[0],x+12,169,35,18,8,col); txt(c,s[1],x+12,208,108,34,12,C["white"])
        line(c,x+12,258,x+120,258,C["line"]); txt(c,s[2],x+12,285,108,58,8,C["text"])
        if i<5: arrow(c,x+133,265,x+149,265,C["muted"],1)
    round_rect(c,120,408,720,52,C["dark"],C["cyan"],7,1)
    txt(c,"反馈闭环",145,425,85,18,9,C["cyan"]); txt(c,"传播表现、内容审核与业务结果回流，修正达人标签、任务匹配规则和企业内容方法库",240,421,560,22,9,C["text"])
    finish(c)

    # 4 map
    master(c,4); title(c,"03 · CAPABILITY MAP","四层能力地图：从数据事实到营销调用","底层能力不直接外显；甲方看到的是有证据的业务结论和可执行资产。")
    layers=[(360,"数据与身份层",C["blue"],"账号身份核验 · 平台来源 · 作品与互动指标 · 评论证据 · 缺失值保留"),(292,"内容理解层",C["cyan"],"平台字幕 · 短/长视频转写 · 专用OCR · 视觉场景 · 镜头结构 · 产品实体"),(224,"判断与质检层",C["orange"],"账号定位 · 内容DNA · 视觉形态 · 共同证据门禁 · 冲突拦截 · 人工复核"),(156,"业务应用层",C["green"],"达人初筛 · Campaign匹配 · Brief建议 · 新账号孵化 · 方法论沉淀 · 舆情辅助验证")]
    for i,(yy,n,col,items) in enumerate(layers):
        inset=i*28; round_rect(c,55+inset,yy,850-inset*2,50,C["panel"],col,7,1)
        txt(c,n,75+inset,yy+16,125,18,10.5,col); txt(c,items,210+inset,yy+15,650-inset*2,20,8.6,C["text"])
    txt(c,"MMN多模态策略输出",340,122,280,22,13,C["white"],align="center")
    arrow(c,480,355,480,207,C["blue"],1.2)
    txt(c,"模型名称属于内部质检配置；对客户统一呈现为MMN多模态策略输出。",42,478,850,18,8,C["muted"])
    finish(c)

    # 5 scenarios
    master(c,5); title(c,"04 · CLIENT SCENARIOS","六类甲方场景可以直接调用","同一套达人证据可以被品牌、内容、媒介和洞察团队复用。")
    scenarios=[("达人初筛与建档","判断账号真实性、内容赛道、代表作和基础风险","候选达人档案"),("车型上市Campaign","按传播任务匹配技术解释、体验或生活方式达人","达人组合与Brief"),("内容能力诊断","拆解选题、开场、叙事、证据使用和视觉表达","内容DNA"),("新账号孵化","沉淀固定栏目、首批选题和30天验证节奏","孵化方案"),("竞品达人研究","比较不同账号的专业能力与表达方式","能力对标图谱"),("舆情辅助验证","识别评论中的车型疑问、争议和专业纠偏","平台级候选信号")]
    colors=[C["blue"],C["cyan"],C["orange"],C["green"],C["blue"],C["orange"]]
    for i,s in enumerate(scenarios):
        col=i%3; row=i//3; x=44+col*294; y=145+row*145; round_rect(c,x,y,270,122,C["panel2"] if row else C["panel"],colors[i],8,1)
        c.setFillColor(C["panel2"]); c.setStrokeColor(colors[i]); c.circle(x+25,H-y-25,14,fill=1,stroke=1)
        txt(c,str(i+1),x+17,y+16,16,16,8,colors[i],align="center"); txt(c,s[0],x+52,y+16,190,24,12,C["white"])
        txt(c,s[1],x+17,y+58,230,32,8.5,C["text"]); label(c,s[2],x+148,y+92,104,colors[i])
    txt(c,"边界：达人评论只代表当前账号与样本范围，不外推为全市场需求。",42,478,850,18,8,C["muted"])
    finish(c)

    # 6 deliverables
    master(c,6); title(c,"05 · DELIVERABLES","一次达人诊断，形成四类可复用交付物","交付不是黑盒分数，而是结论、证据、建议与边界同时存在。")
    blocks=[("A","达人能力档案",C["blue"],["身份与来源记录","账号定位与内容赛道","代表作与入选理由","专业能力与表达特征"]),("B","内容DNA",C["cyan"],["核心选题与内容支柱","开场和叙事结构","视觉形态与镜头特征","证据使用和语言方式"]),("C","营销调用建议",C["orange"],["适用车型与传播阶段","适合承担的营销任务","Campaign Brief建议","合作前复核事项"]),("D","企业内容资产",C["green"],["可检索的能力标签","可复用的选题方法","脚本结构和内容规则","项目结果反馈记录"])]
    for i,(n,head,col,items) in enumerate(blocks):
        x=43+i*229; round_rect(c,x,145,205,310,C["panel"],col,8,1)
        txt(c,n,x+18,166,40,34,22,col); txt(c,head,x+18,219,165,26,13,C["white"]); line(c,x+18,261,x+185,261,C["line"])
        for j,it in enumerate(items): bullet(c,it,x+18,298+j*40,168,col,8.5)
    finish(c)

    # 7 comparison
    master(c,7); title(c,"06 · DIFFERENTIATION","MMN不是另一张达人名单","传统达人库负责资源管理；MMN补足内容能力判断和策略调用。")
    rows=[("主要回答","有哪些达人","为什么适合当前任务"),("核心数据","粉丝、互动、报价、合作记录","代表作、内容结构、视听证据、受众反馈"),("标签方式","平台标签或人工经验","证据支持的能力标签与适用任务"),("使用环节","资源搜索与采购管理","人选判断、Brief、内容策略与复盘"),("风险控制","依赖人工抽查","身份门禁、模型冲突拦截、人工审核"),("沉淀结果","项目级名单","跨项目复用的企业内容资产")]
    x0=55; widths=[150,320,380]; yy=140
    for i,(t,w) in enumerate(zip(["比较维度","传统达人库","MMN达人内容能力资产"],widths)):
        c.setFillColor(HexColor("#124F78") if i==2 else C["panel2"]); c.setStrokeColor(C["line"]); c.rect(x0+sum(widths[:i]),ytop(yy,42),w,42,fill=1,stroke=1)
        txt(c,t,x0+sum(widths[:i])+12,yy+13,w-24,18,10,C["white"])
    for ri,r in enumerate(rows):
        y=yy+42+ri*45
        for ci,t in enumerate(r):
            x=x0+sum(widths[:ci]); c.setFillColor(C["panel2"] if ri%2 else C["panel"]); c.setStrokeColor(C["line"]); c.rect(x,ytop(y,45),widths[ci],45,fill=1,stroke=1)
            txt(c,t,x+12,y+14,widths[ci]-24,20,8.8,C["blue"] if ci==0 else (C["white"] if ci==2 else C["text"]))
    txt(c,"两者是互补关系：现有达人库可继续承载报价、合同与合作管理，MMN负责内容能力判断。",42,478,850,18,8,C["muted"])
    finish(c)

    # 8 quality gate
    master(c,8); title(c,"07 · QUALITY GATE","从“模型给答案”改为“证据达到门槛才发布”","底层采用多模型独立观察与共同证据校验；客户侧统一看到MMN质检状态。")
    flow=[("真实内容证据","字幕、画面、OCR、镜头、作品来源",C["blue"]),("独立多模态观察","不同模型分别看同一素材",C["cyan"]),("共同证据审计","结论、证据ID和置信度必须达标",C["orange"])]
    for i,(h,d,col) in enumerate(flow):
        x=45+i*235; round_rect(c,x,160,205,116,C["panel"],col,8,1); txt(c,h,x+16,181,170,24,12,C["white"]); txt(c,d,x+16,225,170,30,8,C["text"])
        if i<2: arrow(c,x+206,218,x+230,218,C["muted"])
    arrow(c,720,218,750,190,C["green"]); arrow(c,720,222,750,280,C["red"])
    round_rect(c,752,145,160,78,HexColor("#0E3A35"),C["green"],8,1); txt(c,"一致",770,164,50,20,12,C["green"]); txt(c,"形成待审核结论",770,193,120,18,8,C["text"])
    round_rect(c,752,250,160,78,HexColor("#3A202A"),C["red"],8,1); txt(c,"不一致",770,269,60,20,12,C["red"]); txt(c,"禁止发布，转人工复核",770,298,125,18,8,C["text"])
    round_rect(c,110,360,740,64,C["dark"],C["line"],7,1); txt(c,"四条硬门槛",135,381,90,20,9,C["orange"])
    for i,t in enumerate(["身份一致","来源可追溯","共同证据存在","冲突已处理"]): label(c,t,250+i*145,377,115,C["green"] if i==3 else C["orange"])
    txt(c,"双模型一致不等于事实；最终结论仍需在企业业务语境下由人工确认。",42,478,850,18,8,C["muted"])
    finish(c)

    # 9 maturity
    master(c,9); title(c,"08 · CURRENT MATURITY","当前能力成熟度：已运行、已实现、待真实验收","客观区分实装状态，避免把单元测试或配置完成描述为生产可用。")
    groups=[(145,"已实际运行并形成数据",C["green"],["身份校验与TikHub采集","代表作筛选与证据入库","平台字幕与Qwen VL视觉证据","达人档案、作品拆解和舆情辅助页面"]),(250,"代码已实现并通过相关测试",C["blue"],["Qwen 3.7主视觉与3.6降级","Kimi独立视觉复核","专用OCR与长视频异步ASR","Qwen+DeepSeek共同证据门禁与页面拦截"]),(355,"上线前仍需完成",C["orange"],["轮换后新Key的真实调用","达人完整业务流端到端验收","生产环境时延、成本与并发验证","企业Gold Set与人工阈值确认"])]
    for y,head,col,items in groups:
        round_rect(c,52,y,856,78,C["panel"],col,7,1); c.setFillColor(col); c.rect(52,ytop(y,78),6,78,fill=1,stroke=0)
        txt(c,head,76,y+19,205,28,10.5,col)
        for i,it in enumerate(items): bullet(c,it,300+(i%2)*295,y+17+(i//2)*31,275,col,8)
    txt(c,"当前对外状态建议：核心达人资产流程可演示；新增多模型链路完成真实API验收后再标记为生产可用。",42,478,850,18,8,C["muted"])
    finish(c)

    # 10 pilot
    master(c,10); title(c,"09 · PILOT PROPOSAL","建议从一个车型项目开始验证","先在有限达人和真实任务中验证判断质量，再逐步扩大企业内容资产范围。")
    weeks=[("第1周","口径与样本","确定车型、传播阶段、达人范围和人工审核标准"),("第2周","采集与诊断","建立达人档案，提取代表作与多模态内容证据"),("第3周","任务匹配","形成达人组合、内容DNA和Campaign Brief建议"),("第4周","人工复核与沉淀","确认可用标签、争议案例和企业方法资产")]
    for i,(wk,head,desc) in enumerate(weeks):
        x=48+i*224; col=C["green"] if i==3 else C["blue"]; round_rect(c,x,155,200,176,C["panel"],col,8,1); label(c,wk,x+16,173,62,col)
        txt(c,head,x+16,218,165,26,12,C["white"]); txt(c,desc,x+16,267,165,40,8,C["text"])
        if i<3: arrow(c,x+201,242,x+220,242,C["muted"],1)
    round_rect(c,115,365,730,64,HexColor("#0B2B47"),C["cyan"],7,1); txt(c,"试点验收看什么",140,388,105,18,9,C["cyan"])
    txt(c,"身份错配率 · 证据完整度 · 人工认可率 · Brief可执行性 · 单达人处理成本与时延",260,384,550,22,9,C["white"])
    txt(c,"MMN把碎片化达人信息转化为可执行的内容决策，并通过反馈持续沉淀汽车营销Know-how。",100,454,760,24,10.5,C["blue"],align="center")
    finish(c)

    c.save()

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "output/pdf/MMN-达人蒸馏与孵化能力介绍-20260718.pdf"
    build(target)
