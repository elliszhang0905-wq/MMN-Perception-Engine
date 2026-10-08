/* GEO uses the existing MMN api() for authentication and CSRF. */
(() => {
  'use strict';
  const tabs = [['overview','概览'],['questions','问题库'],['sampling','采样任务'],['evidence','回答证据'],['diagnostics','诊断与改进'],['settings','设置']];
  const channels = [['','全部渠道'],['ark_model_api','模型接口样本'],['ark_assistant_api','助手接口样本'],['doubao_app_manual','人工App样本']];
  const categories = [['category','无品牌品类选择'],['scenario','场景选择'],['comparison','竞品比较'],['recognition','品牌与车型认知'],['concern','产品疑虑']];
  const categoryLabel = value => categories.find(([key])=>key===value)?.[1]||'类别未识别';
  const labels = {draft:'草稿',queued:'等待执行',running:'执行中',completed:'已完成',completed_with_errors:'完成但有失败',cancelled:'已取消',blocked:'条件阻塞',failed:'失败',uncertain:'结果未知',approved:'已审核',executed:'已执行',success:'有效回答',unverified:'未核验',supported:'基准支持',contradicted:'基准冲突'};
  const s = {cap:null,projects:[],projectOffset:0,projectTotal:0,catalog:[],catalogOffset:0,catalogTotal:0,project:'',tab:'overview',offset:0,limit:20,total:0,data:{},filters:{},detail:null,editor:null,preview:null,error:'',notice:'',epoch:0,summaryEpoch:0,ready:false,initPromise:null,fieldIndex:0,pending:new Set(),pageOffsets:{}};
  const el = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const list = value => Array.isArray(value) ? value : [];
  const display = value => value == null ? '暂无数据' : typeof value === 'object' ? JSON.stringify(value) : String(value);
  const admin = () => s.cap?.role === 'admin';
  const prefix = () => '/projects/' + encodeURIComponent(s.project);
  const button = (title, action, data = {}, disabled = false) => '<button type="button" data-geo-action="' + esc(action) + '"' + Object.entries(data).map(([k,v]) => ' data-' + k + '="' + esc(v) + '"').join('') + (disabled ? ' disabled' : '') + '>' + esc(title) + '</button>';
  const empty = message => '<p class="geo-empty">' + esc(message) + '</p>';
  const pill = value => '<span class="geo-pill">' + esc(labels[value] || value || '未知') + '</span>';
  const details = (title, content, open=false) => '<details class="geo-expand"'+(open?' open':'')+'><summary>' + esc(title) + '</summary>' + content + '</details>';
  const panel = (title, content, note = '') => '<section class="geo-panel"><h3>' + esc(title) + '</h3>' + (note ? '<p class="geo-note">' + esc(note) + '</p>' : '') + content + '</section>';
  const kv = pairs => '<dl class="geo-kv">' + pairs.map(([k,v]) => '<div><dt>' + esc(k) + '</dt><dd>' + esc(display(v)) + '</dd></div>').join('') + '</dl>';
  const opts = (items, value) => items.map(item => {const [v,l] = Array.isArray(item) ? item : [item,item]; return '<option value="' + esc(v) + '"' + (String(value ?? '') === String(v) ? ' selected' : '') + '>' + esc(l) + '</option>';}).join('');
  function localDateValue(value) {
    if(!value)return '';
    const date=new Date(value);if(Number.isNaN(date.getTime()))return '';
    const pad=number=>String(number).padStart(2,'0');
    return date.getFullYear()+'-'+pad(date.getMonth()+1)+'-'+pad(date.getDate())+'T'+pad(date.getHours())+':'+pad(date.getMinutes())+(date.getSeconds()?':'+pad(date.getSeconds()):'');
  }
  function isoDateValue(value, label) {
    if(!value)throw new Error('请填写'+label+'，时间按本机时区保存。');
    const date=new Date(value);
    if(Number.isNaN(date.getTime()))throw new Error(label+'格式无效，请重新选择日期和时间。');
    return date.toISOString();
  }
  const apiModeForSurface = surface => surface==='doubao_app_manual'?'manual':surface==='ark_assistant_api'?'assistant':s.cap?.provider?.api_mode||'responses';
  function field(name, label, value = '', type = 'text', choices, required = false) {
    const id = 'geo-field-' + name + '-' + (++s.fieldIndex);
    if(type==='datetime-local')value=localDateValue(value);
    let control;
    if (choices) control = '<select id="' + id + '" name="' + esc(name) + '"' + (required ? ' required' : '') + '>' + opts(choices,value) + '</select>';
    else if (type === 'textarea') control = '<textarea id="' + id + '" name="' + esc(name) + '" rows="3"' + (required ? ' required' : '') + '>' + esc(value) + '</textarea>';
    else if (type === 'checkbox') control = '<input id="' + id + '" name="' + esc(name) + '" type="checkbox" value="true"' + (value ? ' checked' : '') + '>';
    else control = '<input id="' + id + '" name="' + esc(name) + '" type="' + esc(type) + '" value="' + esc(value) + '"' + (required ? ' required' : '') + (type === 'number' ? (name==='repeat_index'?' min="1" step="1"':' min="0" step="any"') : type==='datetime-local'?' step="1"':'') + '>';
    return '<div class="geo-field">' + '<label for="' + id + '">' + esc(label) + '</label>' + control + '</div>';
  }
  const form = (kind, fields, title, id = '', attributes = {}) => '<form class="geo-form" data-geo-form="' + esc(kind) + '" data-id="' + esc(id) + '"'+Object.entries(attributes).map(([key,value])=>' data-'+key+'="'+esc(value)+'"').join('')+'><div class="geo-form-grid">' + fields + '</div><div class="geo-toolbar"><button type="submit">' + esc(title) + '</button>' + button('收起','close-editor') + '</div></form>';
  const query = (extra = {},scope='main') => '?' + new URLSearchParams({limit:s.limit,offset:scope==='main'?s.offset:(s.pageOffsets[scope]||0),...Object.fromEntries(Object.entries({...s.filters,...extra}).filter(([,v]) => v !== '' && v != null))}).toString();
  async function request(path, body) {
    if (body != null && !admin()) throw new Error('当前权限只支持查看与导出，请联系项目管理员。');
    if (typeof api !== 'function') throw new Error('MMN 会话服务未就绪，请刷新页面后重试。');
    const result = await api('/api/geo' + path, body == null ? {} : {method:'POST',body:JSON.stringify(body)});
    if (!result || result.ok !== true) throw new Error(result?.error || '请求未成功，请检查权限或稍后重试。');
    return result.data;
  }
  async function init() {
    if (s.initPromise) return s.initPromise;
    const authEpoch=s.authEpoch||0;
    s.initPromise = (async () => {
      bind();
      try {
        const cap=await request('/capabilities');
        if(authEpoch!==(s.authEpoch||0))return;
        s.cap=cap;
        if (el('geo-nav-entry')) el('geo-nav-entry').hidden = !s.cap.enabled;
        if (el('geo-cockpit-summary')) el('geo-cockpit-summary').hidden = !s.cap.enabled;
        s.ready = true;
        if (!s.cap.enabled) {if(el('geo-root')) el('geo-root').innerHTML='';return;}
      } catch(error) {if(authEpoch!==(s.authEpoch||0))return;s.error=error.message;render();s.initPromise=null;}
    })();
    return s.initPromise;
  }
  async function load() {
    if (!s.ready) await init();
    if (!s.cap?.enabled) return;
    const epoch = ++s.epoch;
    s.error = '';
    if (el('geo-root')) el('geo-root').setAttribute?.('aria-busy','true');
    try {
      const projects = await request('/projects?limit=100&offset='+s.projectOffset);
      if(epoch!==s.epoch)return;
      s.projects=list(projects.items);s.projectTotal=projects.total||0;
      if(admin()){const catalog=await request('/catalog?limit=100&offset='+s.catalogOffset);if(epoch!==s.epoch)return;s.catalog=list(catalog.items);s.catalogTotal=catalog.total||0;}
      if(!s.projects.some(p=>String(p.id)===String(s.project)))s.project=s.projects[0]?.id || '';
      if(s.appImport&&s.appImport.project!==s.project)s.appImport=null;
      if (!s.project) {
        const catalog=await request('/catalog?limit=100&offset='+s.catalogOffset);
        if(epoch!==s.epoch)return;
        s.catalog=list(catalog.items);s.catalogTotal=catalog.total||0;
        s.data={};s.total=0;render();return;
      }
      const projectPath=prefix();
      let data;
      if(s.tab==='overview') data={metrics:await request(projectPath+'/metrics'+query()),batches:await request(projectPath+'/batches'+query()),observations:await request(projectPath+'/observations'+query({status:'needs_review'}))};
      else if(s.tab==='questions')data={questions:await request(projectPath+'/questions'+query())};
      else if(s.tab==='sampling')data={questions:await request(projectPath+'/questions?limit=100&offset=0&active=true'),conditions:await request(projectPath+'/conditions?limit=100&offset=0'),batches:await request(projectPath+'/batches'+query())};
      else if(s.tab==='evidence')data={observations:await request(projectPath+'/observations'+query()),questions:await request(projectPath+'/questions?limit=100&offset=0'),comparisons:await request(projectPath+'/app-comparisons'+query({},'comparisons'))};
      else if(s.tab==='diagnostics')data={diagnostics:await request(projectPath+'/diagnostics'+query()),actions:await request(projectPath+'/actions'+query({},'actions')),retests:await request(projectPath+'/retests'+query({},'retests')),batches:await request(projectPath+'/batches?limit=100&offset=0')};
      else data={facts:await request(projectPath+'/facts'+query()),audit:await request(projectPath+'/audit'+query({},'audit')),catalog:await request('/catalog?limit=100&offset='+s.catalogOffset)};
      if(epoch!==s.epoch)return;
      s.data=data;
      if(data.catalog)s.catalog=list(data.catalog.items);
      const paged = data[{overview:'batches',questions:'questions',sampling:'batches',evidence:'observations',diagnostics:'diagnostics',settings:'facts'}[s.tab]];
      s.total=Number(paged?.total || 0);
      render();
    } catch(error) {if(epoch===s.epoch){s.error=error.message;render();}}
    finally {if(epoch===s.epoch)el('geo-root')?.setAttribute?.('aria-busy','false');}
  }
  const selected = () => s.projects.find(p=>String(p.id)===String(s.project)) || {};
  const channelName = channel => channels.find(c=>c[0]===channel)?.[1] || ({api:'模型接口样本',assistant_api:'助手接口样本',doubao_api:'模型接口样本',doubao_assistant_api:'助手接口样本'}[channel]) || channel || '未知渠道';
  const originBadge = record => record?.evidence_origin==='offline_fixture'||record?.offline_fixture_n>0 ? '<span class="geo-pill">离线测试样本'+(record.offline_fixture_n?' '+esc(record.offline_fixture_n)+'条':'')+'</span>' : record?.evidence_origin==='manual_import'?'<span class="geo-pill">人工导入证据</span>':'';
  function conditionText(condition) {
    const c=condition||{};
    const modeLabel={unknown:'联网状态未知',search_enabled:'请求联网',non_search:'非联网'}[c.mode||'unknown']||c.mode;
    const parts=[channelName(c.surface),c.api_mode,modeLabel,c.condition_hash];
    if(admin() && c.model)parts.push(c.model);
    return parts.filter(Boolean).join(' · ') || '条件未知';
  }
  function pagination(total=s.total,scope='main') {
    const offset=scope==='main'?s.offset:(s.pageOffsets[scope]||0);return '<div class="geo-pagination">' + button('上一页','previous',{scope},offset===0) + '<span>' + esc(total ? (offset+1)+'—'+Math.min(offset+s.limit,total)+' / '+total : '0 条记录') + '</span>' + button('下一页','next',{scope},offset+s.limit>=total) + '</div>';
  }
  function table(headers, rows) {
    return rows.length ? '<div class="geo-table-wrap"><table><thead><tr>'+headers.map(h=>'<th scope="col">'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(cell=>'<td>'+cell+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>' : empty('暂无记录。管理员可在此创建或导入证据。');
  }
  function projectForm() {
    const paging=s.catalogTotal>100?'<div class="geo-toolbar">'+button('上一页车型','catalog-previous',{},s.catalogOffset===0)+button('下一页车型','catalog-next',{},s.catalogOffset+100>=s.catalogTotal)+'<small>车型 '+esc(s.catalogOffset+1)+'—'+esc(Math.min(s.catalogOffset+100,s.catalogTotal))+' / '+esc(s.catalogTotal)+'</small></div>':'';
    return details('创建 GEO 项目',paging+form('project',field('name','项目名称','','text',null,true)+field('target_key','目标车型','', 'text',list(s.catalog).map(c=>[c.key,c.brand+' '+c.name]),true)+field('batch_budget','单批预算（CNY）','', 'number')+field('day_budget','每日预算（CNY）','','number')+field('max_questions','最多问题数',50,'number')+field('max_repeats','最多重复次数',3,'number')+field('max_concurrency','最多并发数',1,'number')+field('max_output_tokens','输出上限',2048,'number'),'创建项目'));
  }
  function render() {
    const root=el('geo-root');if(!root)return;
    if(s.exportFile&&s.exportFile.project!==s.project){URL.revokeObjectURL(s.exportFile.url);s.exportFile=null;}
    s.fieldIndex=0;
    if(!s.cap?.enabled){root.innerHTML=s.error?'<p role="alert">'+esc(s.error)+'</p>'+button('重试','retry-init'):'';return;}
    let content='';
    if(!s.project)content=panel('开始 GEO 基线',empty('尚无项目。先从 MMN 车型主数据创建项目，再建立问题库与采样条件。')+(admin()?projectForm():'<p>请联系管理员创建项目。</p>'));
    else content=({overview:overview,questions:questions,sampling:sampling,evidence:evidence,diagnostics:diagnostics,settings:settings}[s.tab])();
    root.innerHTML='<div class="geo-module"><header class="geo-header"><div><h2>GEO</h2><p>购车问题中的车型认知、回答证据与改进验证</p></div><div class="geo-toolbar"><label for="geo-project">项目</label><select id="geo-project" data-geo-project>'+opts(s.projects.map(p=>[p.id,p.name]),s.project)+'</select>'+button('刷新','refresh')+(s.projectTotal>100?button('上一页项目','project-previous',{},s.projectOffset===0)+button('下一页项目','project-next',{},s.projectOffset+100>=s.projectTotal):'')+'</div></header>'+
      '<p class="geo-boundary">'+(s.cap.real_sampling_enabled?'真实采样能力已开放；每次计划仍需通过条件与预算检查。':'离线开发 · 真实采样暂时阻塞，可创建阻塞计划与导入人工App样本。')+'</p>'+
      (!admin()?'<p class="geo-note">当前权限：只读，可查看证据与导出。</p>':'')+
      '<nav class="geo-tabs" aria-label="GEO 模块">'+tabs.map(([key,label])=>'<button type="button" data-geo-action="tab" data-tab="'+key+'" aria-current="'+(s.tab===key?'page':'false')+'">'+label+'</button>').join('')+'</nav>'+
      (admin()&&s.project?projectForm():'')+
      (s.error?'<div class="geo-alert" role="alert">'+esc(s.error)+' '+button('重试','refresh')+'</div>':'')+
      (s.notice?'<p class="geo-notice" role="status">'+esc(s.notice)+'</p>':'')+
      (s.exportFile?'<a class="geo-download" href="'+esc(s.exportFile.url)+'" download="'+esc(s.exportFile.filename)+'">下载 CSV</a>':'')+
      '<div id="geo-content">'+content+'</div></div>';
  }
  function metricsCards(metrics) {
    const groups=list(metrics?.groups);
    if(!groups.length)return empty('暂无数据。先建立问题库并获取有效回答，指标将按渠道和条件独立显示。');
    return '<div class="geo-metric-groups">'+groups.map((g,i)=>{
      const rates=g.metrics||g.answer_level_rates||g.rates||{};
      const metricLabel=key=>({mention_rate:'提及率',recommendation_rate:'推荐率',first_recommendation_rate:'首位推荐率',recommendation_share:'推荐份额',fact_error_rate:'事实错误率',citation_rate:'引用率',fact_accuracy:'事实准确率'}[key]||key);
      const percent=value=>value==null?'暂无数据':(Number(value)*100).toFixed(1)+'%';
      const cards=Object.entries(rates).map(([key,value])=>{
        const judgmentKey={mention_rate:'mention',recommendation_rate:'recommendation'}[key];
        const coverage=g.judgment_coverage?.[judgmentKey];
        return '<article><span>'+esc(metricLabel(key))+'</span><strong>'+esc(percent(value))+'</strong><small>等权问题数 '+esc(display(g.equal_weight_question_n?.[key]))+'</small><small>回答级分母 '+esc(display(g.denominators?.[key]))+' · 命中 '+esc(display(g.numerators?.[key]))+'</small><small>回答级比率 '+esc(percent(g.answer_level_rates?.[key]))+'</small>'+
          (judgmentKey?'<small>判定覆盖率 '+esc(percent(coverage?.rate))+'</small><small>已判定 '+esc(display(coverage?.judged_n))+' / 候选回答 '+esc(display(coverage?.candidate_n))+' · 未判定 '+esc(display(coverage?.unresolved_n))+'</small><small>适用问题数 '+esc(display(g.eligible_question_n?.[judgmentKey]))+' · 已判定问题数 '+esc(display(g.equal_weight_judged_question_n?.[judgmentKey]))+'</small>':'')+'</article>';
      }).join('');
      const zeroJudgments=kv(['mention','recommendation'].map(key=>[(key==='mention'?'提及':'推荐')+'零判定问题',g.zero_judgment_question_ids?.[key]==null?null:list(g.zero_judgment_question_ids[key]).join('、')||'无']));
      const subsets=table(['问题适用范围','有效样本 / 问题数','等权提及 / 推荐'],['branded','unbranded'].filter(key=>g.sets?.[key]).map(key=>{const subset=g.sets[key];return [key==='branded'?'有品牌问题':'无品牌问题',esc(display(subset.valid_n))+' / '+esc(display(subset.question_n)),esc(percent(subset.metrics?.mention_rate))+' / '+esc(percent(subset.metrics?.recommendation_rate))];}));
      const repeat=table(['问题版本','有效 / 运行 / 失败','提及 / 推荐重复分布'],list(g.repeat_consistency).map(r=>[esc(r.question_version_id),esc(r.valid_n)+' / '+esc(r.total_n)+' / '+esc(r.failed_n),esc(display(r.mention))+' / '+esc(display(r.recommendation))]));
      const runtimeQuality=details('运行质量',kv([['有效回答占比',percent(Number.isFinite(g.total_n)&&g.total_n>0&&Number.isFinite(g.valid_n)&&g.valid_n>=0?g.valid_n/g.total_n:null)],['拒答数',g.refused_n],['空答案数',g.empty_n],['分析缺失数',g.analysis_missing_n],['无法分析数',g.invalid_answer_n],['待执行数',g.pending_n],['已取消数',g.cancelled_n],['条件阻塞数',g.blocked_n],['结果未知数',g.uncertain_n],['已复核回答数',g.reviewed_n]])+'<p class="geo-note">有效回答占比使用运行总数为分母；分析与复核计数可能重叠，不能相加当作请求总数。</p>');
      const citations=table(['引用类型 / 域名','等权引用率','回答级命中'],['structured','text_link'].flatMap(kind=>Object.entries(g.citation_rates?.[kind]||{}).map(([domain,rate])=>[esc(kind==='structured'?'结构化引用':'文本链接')+' · '+esc(domain),esc(percent(rate)),esc(display(g.citation_counts?.[kind]?.[domain]))])));
      return panel(conditionText(g.condition||g)+' · '+channelName(g.channel),originBadge(g)+runtimeQuality+kv([['口径',(g.aggregation||metrics.aggregation)==='question_equal_weight'?'按问题等权':'按回答聚合'],['采样日期',g.sampled_at_min&&g.sampled_at_max?g.sampled_at_min+'—'+g.sampled_at_max:null],['有效样本数',g.valid_n??g.valid_answer_count??g.valid_count??g.sample_count],['运行总数',g.total_n??g.request_count??g.total_count],['失败数',g.failed_n],['待复核数',g.needs_review_n],['定义版本',metrics.definition_version||metrics.version],['事实覆盖率',percent(g.fact_coverage)],['无可核验引用数',g.no_verifiable_citation_n]])+'<div class="geo-metrics">'+cards+'</div>'+zeroJudgments+details('问题适用范围',subsets)+details('重复稳定性',repeat)+details('引用率与计费边界',citations+kv([['引用分母',g.citation_denominator_n],['引用能力覆盖率',percent(g.citation_capability_coverage)],['已知费用',g.cost?.known_total],['未知计费次数',g.cost?.unknown_attempt_n],['结果未知计费次数',g.cost?.billing_uncertain_attempt_n]]))+button('查看对应证据','metric-evidence',{group:i}), '条件或渠道不同分别展示，默认按问题等权；回答级分母与命中另列。判定覆盖不足与零判定问题须复核，不能只读正向比率。观测差异不能直接归因为内容动作。');
    }).join('')+'</div>';
  }
  function overview() {
    return panel('当前项目',originBadge(selected())+kv([['项目',selected().name],['目标车型',list(selected().entities).find(e=>e.key===selected().target_key)?.name||'未关联车型'],['数据边界','仅本项目已保存证据']])+filterForm(field('channel','统计渠道',s.filters.channel,'text',channels)+field('batch_id','基线或复测批次编号',s.filters.batch_id))+button('建立问题库','tab',{tab:'questions'})+button('安排基线','tab',{tab:'sampling'})+button('查看待复核','review-needed'))+
      panel('指标与运行质量',metricsCards(s.data.metrics))+
      panel('最近任务',batchTable(list(s.data.batches?.items))+pagination(s.data.batches?.total||0))+
      panel('待复核证据',observationTable(list(s.data.observations?.items)));
  }
  function questionForm(q={}) {
    return form('question',field('text','问题全文',q.text,'textarea',null,true)+field('category','问题类别',q.category||'category','text',categories)+field('intent','购车意图',q.intent)+field('budget','预算条件',q.budget)+field('scenario','用车场景',q.scenario)+field('segment','人群',q.segment)+field('year','事实适用年款（可选）',q.year)+field('trim','事实适用配置（可选）',q.trim)+field('market','事实适用市场（可选）',q.market)+field('temperature','事实适用温度（可选）',q.temperature)+field('target_entities','适用车型键（逗号分隔）',list(q.target_entities).join(','))+field('competitors','竞品键（逗号分隔）',list(q.competitors).join(','))+field('source','来源',q.source||'人工编辑')+field('unbranded','无品牌问题',q.unbranded,'checkbox')+field('recommendation_eligible','推荐指标适用',q.recommendation_eligible!==false,'checkbox')+field('ranking_eligible','排序指标适用',!!q.ranking_eligible,'checkbox')+field('fact_eligible','事实指标适用',!!q.fact_eligible,'checkbox')+field('active','启用',q.active!==false,'checkbox'),'保存新版本',q.id);
  }
  function filterForm(fields) {return '<form class="geo-filter geo-form" data-geo-form="filters"><div class="geo-form-grid">'+fields+'</div><button type="submit">应用筛选</button>'+button('清除筛选','clear-filters')+'</form>';}
  function questions() {
    const items=list(s.data.questions?.items);
    return panel('问题库',filterForm(field('category','类别',s.filters.category,'text',[['','全部类别'],...categories])+field('active','启用状态',s.filters.active,'text',[['','全部'],['true','启用'],['false','停用']])+field('search','搜索全文',s.filters.search))+
      '<div class="geo-toolbar">'+button('导出问题 CSV','export',{kind:'questions'})+(admin()?button('新建问题','new-question')+button('生成50个可编辑示例','examples'):'')+'</div>'+
      '<p class="geo-note">编辑会生成新版本，历史采样保留旧问题。示例不代表真实用户需求或搜索量。</p>'+
      (s.editor?.kind==='question'?questionForm(s.editor.item):'')+
      table(['问题与版本','类别 / 适用范围','状态','操作'],items.map(q=>['<b>'+esc(q.text)+'</b><small>版本 '+esc(q.version)+'</small>',esc(categoryLabel(q.category))+'<small>'+esc([q.budget,q.scenario,q.segment].filter(Boolean).join(' · '))+'</small>',pill(q.active?'启用':'停用'),button('版本历史','question-versions',{id:q.id})+(admin()?button('编辑新版本','edit-question',{id:q.id})+button(q.active?'停用':'启用','question-state',{id:q.id,active:!q.active}):'')]))+pagination()+
      (s.detail?.kind==='versions'?panel('问题版本历史',table(['版本','问题全文','来源'],list(s.detail.items).map(q=>[esc(q.version),esc(q.text),esc(q.source)]))):'')+
      (admin()?details('导入问题 CSV',form('import-csv',field('csv','CSV 内容（含 text、category 等表头）','','textarea',null,true),'校验并导入')+'<p class="geo-note">格式、长度、重复项与车型关联由服务端校验，错误不会静默略过。</p>'):''));
  }
  function batchTable(items) {
    return table(['任务','状态 / 进度','费用','操作'],items.map(b=>[esc(b.id),pill(b.status)+(b.paused?' 已暂停':'')+'<small>'+esc(b.done_count??0)+' / '+esc(b.total_count??b.manifest?.planned_calls??'未知')+'</small>',esc(display(b.cost))+'<small>'+esc(display(b.unknown_cost_items))+'</small>',button('查看任务','batch-detail',{id:b.id})+(admin()?['pause','resume','cancel','retry'].map(cmd=>button({pause:'暂停',resume:'继续',cancel:'取消',retry:'续跑失败'}[cmd],'batch-control',{id:b.id,command:cmd},!s.cap.real_sampling_enabled&&cmd==='resume')).join(''):'')]));
  }
  function sampling() {
    const qs=list(s.data.questions?.items), cs=list(s.data.conditions?.items);
    const checks=(name,items,label)=>'<fieldset><legend>'+label+'</legend>'+items.map(i=>'<label class="geo-check"><input type="checkbox" name="'+name+'" value="'+esc(i.version_id||i.id)+'"> '+esc(name==='question_version_ids'?i.text:conditionText(i))+'</label>').join('')+(!items.length?empty('暂无可选择项，请先创建。'):'')+'</fieldset>';
    let preview='';
    if(s.preview)preview=panel('计划预估',kv([['问题数',s.preview.question_count],['条件数',s.preview.condition_count],['重复次数',s.preview.repeats],['计划调用数',s.preview.planned_calls],['估计费用',s.preview.estimated_cost],['最大预留费用',s.preview.max_reserved_cost],['币种',s.preview.currency],['未知单价项',s.preview.unknown_cost_items]])+
      list(s.preview.blocked_reasons).map(r=>'<p class="geo-warning">'+esc(display(r))+'</p>').join('')+
      button(s.cap.real_sampling_enabled?'创建采样任务':'创建阻塞计划','create-batch')+
      '<p class="geo-note">创建阻塞计划不会触发真实调用。价格未知不会显示为免费。</p>');
    return panel('采样条件',table(['渠道与条件','输出 / 超时','能力'],cs.map(c=>[esc(conditionText(c)),esc(c.max_output_tokens)+' / '+esc(c.timeout_seconds)+'秒',esc(display(c.capabilities))]))+(admin()?details('新增条件',form('condition',field('surface','采样渠道','ark_model_api','text',[['ark_model_api','模型接口'],['ark_assistant_api','助手接口'],['doubao_app_manual','人工App']])+kv([['模型接口模式',apiModeForSurface('ark_model_api')],['说明','接口模式依采样渠道与服务器配置确定']])+field('mode','联网条件','non_search','text',[['non_search','非联网'],['search_enabled','请求联网']])+field('max_output_tokens','输出上限',2048,'number')+field('timeout_seconds','超时秒数',60,'number'),'保存条件')):''),
      '每个模型、模式与联网条件分别保存；模型由后台配置，不能在客户页面任意填写。')+
      (admin()?panel('安排问题 × 条件 × 重复次数','<form data-geo-form="preview" class="geo-form">'+checks('question_version_ids',qs,'问题版本')+checks('condition_ids',cs,'采样条件')+field('repeats','重复次数',3,'number')+'<button type="submit">检查能力并预估</button></form>'):'')+
      preview+panel('采样任务',batchTable(list(s.data.batches?.items))+pagination())+
      (s.detail?.kind==='batch'?panel('任务详情',kv([['任务编号',s.detail.item.id],['状态',labels[s.detail.item.status]||s.detail.item.status],['失败分类',s.detail.item.error_summary],['未知费用',s.detail.item.unknown_cost_items]])+details('冻结条件清单',table(['冻结问题版本','问题全文'],list(s.detail.item.manifest?.questions).map(q=>[esc(q.version_id||q.id)+' · v'+esc(q.version),esc(q.text)]))+table(['冻结条件编号','渠道与模式'],list(s.detail.item.manifest?.conditions).map(c=>[esc(c.id),esc(conditionText(c))]))+kv([['重复次数',s.detail.item.manifest?.repeats]]))+(admin()?form('resolve-uncertain',field('observation_id','待确认观测编号','','text',list(s.detail.item.uncertain_observation_ids).map(id=>[id,id]))+field('reason','人工确认依据','','textarea',null,true),'确认未知结果状态',s.detail.item.id):'')):'');
  }
  function observationTable(items) {
    return table(['问题与回答','渠道 / 条件','状态 / 时间','证据'],items.map(o=>['<b>'+esc(o.question?.text||o.question_text||o.question_version_id)+'</b><small>'+esc(String(o.answer||'无回答全文').slice(0,150))+'</small>',originBadge(o)+esc(channelName(o.channel))+'<small>'+esc(conditionText(o.condition))+'</small>',pill(o.status)+'<small>'+esc(o.sampled_at)+'</small>',button('查看回答与复核','evidence',{id:o.id})]));
  }
  function appForm() {
    const unknown=[['unknown','未知'],['on','开启'],['off','关闭']];
    const frozen=s.appImport,questions=frozen?frozen.questions:list(s.data.questions?.items),question=questions.find(q=>(q.version_id||q.id)===frozen?.question_version_id);
    const questionFields=field('question_version_id',frozen?'冻结问题版本':'关联问题版本',frozen?.question_version_id||'','text',questions.map(q=>[q.version_id||q.id,(frozen?'冻结 v'+(q.version||'未知')+' · ':'')+q.text]),true)+field('question_text',frozen?'冻结问题全文':'App问题全文',question?.text||'','textarea',null,true).replace('name="question_text"', 'name="question_text"'+(frozen?' readonly':''));
    return (frozen?'<p class="geo-note">当前导入绑定复测冻结版本，当前问题库的新版本不会替换它。选择冻结问题与条件，并核对回答及重复序号。</p>'+button('结束复测导入','clear-app-import'):'')+form('app-import',questionFields+field('answer','回答全文（只有截图时留空）','','textarea')+field('sampled_at','采样时间（按本机时区）','','datetime-local',null,true)+field('new_session','是否新会话','unknown','text',[['unknown','未知'],['true','是'],['false','否']])+field('personalization','账号个性化','unknown','text',unknown)+field('visible_search','可见联网状态','unknown','text',unknown)+field('platform_trace_id','平台记录编号')+field('actual_model','可见模型标识（不可见留空）')+field('paired_observation_id','配对接口证据编号（可选）')+field('batch_id',frozen?'冻结复测批次编号':'复测或人工批次编号（可选）',frozen?.batch_id||'').replace('name="batch_id"','name="batch_id"'+(frozen?' readonly':''))+
      (frozen?field('condition_id','冻结人工条件',frozen.condition_id,'text',frozen.conditions.map(c=>[c.id,conditionText(c)]),true):'')+field('repeat_index','重复序号（从1开始，可选）',frozen?1:'','number')+
      '<div class="geo-field"><label for="geo-screenshot">截图证据（PNG / JPEG，最大2MB）</label><input id="geo-screenshot" name="screenshot" type="file" accept="image/png,image/jpeg"></div>','导入人工App样本');
  }
  function reviewForm(o) {
    return form('review',field('kind','修订类型','entity','text',[['entity','车型提及 / 推荐'],['fact','事实判定']])+field('entity_key','车型键','','text',list(selected().entities).map(e=>[e.key,e.name]))+field('fact_index','事实序号（从0开始）','','number')+field('mentioned','提及状态','','text',[['','保持原判断'],['true','提及'],['false','未提及']])+field('recommended','推荐状态','','text',[['','保持原判断'],['true','推荐'],['false','未推荐']])+field('rank','明确排序（空白不改）','','number')+field('needs_review','是否待复核','','text',[['','保持'],['true','是'],['false','否']])+field('verdict','事实判定','','text',[['','保持原判断'],['supported','基准支持'],['contradicted','基准冲突'],['unverified','未核验']])+field('evidence','回答原文片段（提及 / 推荐 / 排名须填写）','','textarea')+field('reason','修订依据','','textarea',null,true),'保存人工复核',o.id);
  }
  function observationDetail(o) {
    const facts=list(o.analysis?.fact_checks),automatic=o.automatic_analysis;
    const truth=value=>value==null?'未知':value?'是':'否';
    const entityDecision=value=>value?'提及 '+truth(value.mentioned)+' / 推荐 '+truth(value.recommended)+' / 排名 '+display(value.rank)+' / 待复核 '+truth(value.needs_review):'暂无自动判定';
    const position=value=>value?.start==null||value?.end==null?'字符位置未知':'字符位置 '+value.start+'—'+value.end+'（Unicode字符，从0开始，末位不含）';
    const entities=list(o.analysis?.entities);
    const entityName=key=>list(o.entities).find(e=>e.key===key)?.name||key;
    const citationKind=kind=>({structured:'结构化引用',text_link:'文本链接'}[kind]||'引用类型未知');
    const verification=value=>({not_fetched:'未取网页全文',unverified:'未核验',not_verified:'未核验'}[value]||'未核验来源内容');
    const elapsed=a=>{if(typeof a.started_at!=='string'||typeof a.finished_at!=='string')return '未知';const start=Date.parse(a.started_at),end=Date.parse(a.finished_at);return Number.isFinite(start)&&Number.isFinite(end)&&end>=start?((end-start)/1000).toFixed(3)+'秒':'未知';};
    const usageText=a=>a.usage&&typeof a.usage==='object'?'输入token '+display(a.usage.input_tokens??a.usage.prompt_tokens)+' / 输出token '+display(a.usage.output_tokens??a.usage.completion_tokens)+(a.usage.missing_reason?' · 用量部分缺失':''):'用量未返回';
    const runtime='<h4>调用与运行记录</h4>'+(list(o.attempts).length?table(['尝试 / 状态','记录时间 / 耗时','用量','费用（CNY）'],list(o.attempts).map(a=>[esc(a.attempt_index)+' · '+pill(a.status),esc(a.started_at||'未知')+'<small>'+esc(a.finished_at||'未知')+' · '+esc(elapsed(a))+'</small>',esc(usageText(a)),esc(a.cost==null?'费用未知':a.cost)+(a.billing_uncertain?'<small>计费待核对</small>':'')])):empty(o.channel==='doubao_app_manual'?'人工导入未发生本系统接口调用，用量与调用耗时不可观察。':'暂无接口调用记录，不能据此推断未计费。'));
    return panel('原回答与判定',originBadge(o)+kv([['问题',o.question?.text||o.question_text||o.question_version_id],['时间',o.sampled_at],['渠道',channelName(o.channel)],['条件',conditionText(o.condition)],...(admin()?[['实际模型',o.actual_model||'未知']]:[]),['请求编号',o.request_id],['联网已请求',o.search_requested==null?'未知':o.search_requested?'是':'否'],['联网已观察',o.search_observed==null?'未知':o.search_observed?'是':'否']])+
      '<h4>原始回答全文</h4><pre class="geo-answer">'+esc(o.answer||'无可核对全文；只有截图不能生成精确自动指标。')+'</pre>'+
      '<p class="geo-note">原始回答保持不变；自动判定与人工复核后的当前有效判定分别展示。统计采用当前有效判定。</p>'+
      '<h4>提及、推荐与明确排序片段</h4>'+table(['车型','自动判定','当前有效判定','原回答片段与字符位置'],entities.map(e=>{const prior=list(automatic?.entities).find(original=>original.entity_key===e.entity_key);return [esc(entityName(e.entity_key)),esc(entityDecision(prior)),esc(entityDecision(e)),esc(e.evidence)+'<small>'+esc(position(e))+'</small>'+(prior?'<small>自动片段：'+esc(prior.evidence)+' · '+esc(position(prior))+'</small>':'')];}))+
      '<h4>引用证据</h4>'+(!list(o.citations).length?empty('未提供可验证引用'):table(['标题','引用来源','类型 / 核验状态','片段'],list(o.citations).map(c=>[esc(c.title),safeLink(c.url),esc(citationKind(c.kind||c.source_type))+'<small>'+esc(verification(c.verification||c.verification_status))+'</small>',esc(c.excerpt||c.text)])))+
      runtime+'<h4>事实核验</h4>'+table(['断言与字符位置','自动判定','当前有效判定','核验依据'],facts.map((f,index)=>{const prior=list(automatic?.fact_checks)[index];return [esc(f.claim||f.field)+'<small>'+esc(position(f))+'</small>'+(prior?'<small>自动断言：'+esc(prior.claim||prior.field)+'</small>':''),prior?pill(prior.verdict):'暂无自动判定',pill(f.verdict),esc(f.reason||f.evidence)+'<small>基准编号 '+esc(display(f.baseline_id))+'</small>'];}))+
      details('冻结事实基准',table(['车型 / 年款 / 配置','字段 / 值 / 工况','适用市场 / 日期','来源'],list(o.facts).map(f=>[esc(f.entity_key)+' / '+esc(f.year)+' / '+esc(f.trim),esc(f.field)+' / '+esc(display(f.value))+' '+esc(f.unit)+' '+esc(f.cycle),esc(f.market)+'<small>'+esc(f.effective_from)+'—'+esc(f.effective_to)+'</small>',safeLink(f.source_url)+'<small>'+esc(f.source_excerpt)+'</small>'])))+
      '<h4>复核记录</h4>'+table(['类型 / 审核人','原判定 → 新判定','依据与时间'],list(o.reviews).map(r=>[esc(r.kind)+'<small>'+esc(r.actor)+'</small>',esc(display(r.old))+' → '+esc(display(r.new??r.changes)),esc(r.reason)+'<small>'+esc(r.created_at)+'</small>']))+
      (admin()?details('人工修订（保留原答案）',reviewForm(o))+details('管理员：脱敏原始 JSON','<pre>'+esc(JSON.stringify(o.raw_response??null,null,2))+'</pre>'):'')+
      list(o.screenshots).map(im=>button('读取截图证据','screenshot',{id:o.id,screenshot:im.id})).join('')+(s.detail?.image?'<img class="geo-evidence-image" alt="人工App截图证据" src="'+esc(s.detail.image)+'">':''));
  }
  function safeLink(url) {
    try {const parsed=new URL(url);if(!['https:','http:'].includes(parsed.protocol))return esc(url);return '<a href="'+esc(parsed.href)+'" target="_blank" rel="noopener noreferrer">'+esc(url)+'</a>';}catch{return esc(url);}
  }
  function evidence() {
    return panel('回答证据',filterForm(field('channel','渠道',s.filters.channel,'text',channels)+field('status','状态',s.filters.status,'text',[['','全部'],['completed','有效'],['failed','失败'],['uncertain','结果未知'],['needs_review','待复核']])+field('batch_id','批次编号',s.filters.batch_id)+field('search','搜索回答',s.filters.search))+
      button('导出证据 CSV','export',{kind:'observations'})+observationTable(list(s.data.observations?.items))+pagination())+
      (s.detail?.kind==='observation'?observationDetail(s.detail.item):'')+
      (admin()?panel('人工App样本导入',details('填写问题、全文与可见条件',appForm(),!!s.appImport),'未知字段保持未知。仅截图不生成精确自动指标；App与接口、助手样本分开统计。'):'')+
      panel('App 与接口配对',table(['App / 接口证据','观测差异','边界提示'],list(s.data.comparisons?.items).map(c=>[button('查看App证据','evidence',{id:c.app_observation_id})+button('查看接口证据','evidence',{id:c.api_observation_id}),esc(display(c.differences)),esc(warningText(c.warnings))]))+pagination(s.data.comparisons?.total||0,'comparisons'),'同问题、相近时间的配对相似，不证明全量等价。');
  }
  function actionForm(a={}) {
    return form('action',field('title','改进任务',a.title,'text',null,true)+field('diagnosis','问题 / 待验证假设',a.diagnosis,'textarea',null,true)+field('observation_ids','证据编号（逗号分隔）',list(a.observation_ids).join(','))+field('product_point','涉及产品点',a.product_point)+field('fact_to_add','拟补充事实',a.fact_to_add,'textarea')+field('content_structure','建议内容结构',a.content_structure,'textarea')+field('carrier','建议公开载体',a.carrier)+field('owner','负责人',a.owner)+field('status','状态',a.status||'draft','text',[['draft','草稿'],['approved','已审核'],['executed','已执行']])+field('execution_evidence','实际执行证据',a.execution_evidence,'textarea')+field('executed_at','实际执行时间（按本机时区）',a.executed_at,'datetime-local'),'保存改进任务',a.id);
  }
  function diagnosticReviewForm(d) {
    return panel('人工复核诊断',kv([['原诊断',d.label],['原判断性质',d.statement_type==='hypothesis'?'待验证假设':'观测'],['对应证据',d.evidence],['原建议',d.action_suggestion],['冻结证据版本',d.source_hash]])+
      '<div class="geo-toolbar">'+list(d.observation_ids).map(id=>button('查看对应原回答','evidence',{id})).join('')+'</div>'+
      form('diagnostic-review',field('decision','复核结论','accepted','text',[['accepted','采纳原诊断'],['modified','修订后采纳'],['rejected','不采纳']])+field('label','修订诊断（修订后采纳时使用）',d.label,'textarea')+field('action_suggestion','修订建议（修订后采纳时使用）',display(d.action_suggestion),'textarea')+field('statement_type','修订判断性质',d.statement_type||'hypothesis','text',[['observation','观测'],['hypothesis','待验证假设']])+field('reason','人工复核依据','','textarea',null,true),'保存人工复核',d.id,{'source-hash':d.source_hash}),
      '本次审批绑定所示证据版本。证据更新后须刷新并重新复核；车型判定复核不等于诊断审批。');
  }
  function warningText(value) {
    const translations={
      question_mismatch:'前后问题版本或清单不同',entity_mismatch:'前后车型范围或别名不同',
      fact_baseline_mismatch:'前后使用的事实基准不同',condition_mismatch:'前后采样条件不同',
      schema_mismatch:'前后记录结构版本不同，无法按同一口径比较',schema_version_mismatch:'前后记录结构版本不同，无法按同一口径比较',
      manifest_mismatch:'前后冻结的采样清单不同',
      missing_valid_baseline:'尚无有效基线回答',missing_valid_retest:'尚无有效复测回答',retest_incomplete:'复测回答尚未收齐',
      execution_time_unknown:'改进动作的实际执行时间未知',baseline_time_unknown:'基线样本的采样时间未知',retest_time_unknown:'复测样本的采样时间未知',
      baseline_after_execution:'基线样本采集晚于改进动作执行',sample_not_after_execution:'复测样本未在改进动作执行后采集',
      manual_sample_scope_mismatch:'人工样本条件与冻结基线不一致',
      new_session_unknown:'是否使用新会话未知',personalization_unknown:'账号个性化状态未知',visible_search_unknown:'联网状态未知',
      new_session_mismatch:'前后新会话条件不一致',personalization_mismatch:'前后账号个性化状态不一致',visible_search_mismatch:'前后联网状态不一致',
      model_identity_unknown:'实际模型标识未知',actual_model_mismatch:'前后实际模型版本不一致',
      app_sample_invalid:'人工App样本没有有效可分析回答',api_sample_invalid:'接口样本没有有效可分析回答',
      time_unknown:'配对样本的采样时间未知',samples_not_close_in_time:'配对样本采样时间相差超过24小时',
      model_changed:'模型版本不同',search_capability_changed:'联网能力不同',question_set_changed:'问题清单不同',conditions_changed:'采样条件不同'
    };
    const warnings=Array.isArray(value)?value:value?[value]:[];
    return warnings.length?warnings.map(warning=>translations[warning]||'需核对条件').join('；'):'暂无条件警示';
  }
  function diagnostics() {
    const ds=list(s.data.diagnostics?.items).filter(d=>admin()||(['accepted','modified'].includes(d.review_status)&&d.reviewer&&d.reviewed_at)), actions=list(s.data.actions?.items), retests=list(s.data.retests?.items);
    const reviewLabel=status=>({unreviewed:'待人工复核',accepted:'已采纳',modified:'修订后采纳',rejected:'不采纳',stale_review:'证据已更新，须重新复核'}[status]||'待人工复核');
    return panel('诊断与证据',table(['诊断','性质 / 样本边界','证据','建议','人工复核'],ds.map(d=>[esc(d.label),esc(d.statement_type==='hypothesis'?'待验证假设':'观测')+'<small>'+esc(display(d.evidence))+'</small>',list(d.observation_ids).map(id=>button('查看回答','evidence',{id})).join(''),esc(display(d.action_suggestion)),pill(reviewLabel(d.review_status))+'<small>'+esc(d.reviewer)+' '+esc(d.reviewed_at)+'</small>'+(admin()?button('复核诊断','review-diagnostic',{id:d.id}):'')]))+pagination()+(admin()&&s.editor?.kind==='diagnostic-review'?diagnosticReviewForm(s.editor.item):''),'规则诊断与建议需要独立人工复核，相关性不等于原因。')+
      panel('内容改进任务',(admin()?button('新建改进任务','new-action'):'')+(s.editor?.kind==='action'?actionForm(s.editor.item):'')+
      table(['任务 / 负责人','状态 / 执行证据','关联证据','操作'],actions.map(a=>[esc(a.title)+'<small>'+esc(a.owner)+'</small>',pill(a.status)+'<small>'+esc(a.execution_evidence||'尚无实际执行证据')+' '+esc(a.executed_at)+'</small>',list(a.observation_ids).map(id=>button('查看证据','evidence',{id})).join(''),admin()?button('编辑任务','edit-action',{id:a.id})+button('同条件复测','retest-form',{id:a.id},a.status!=='executed'):'']))+
      pagination(s.data.actions?.total||0,'actions')+(s.editor?.kind==='retest'?form('retest',field('baseline_batch_id','基线批次','','text',list(s.data.batches?.items).map(b=>[b.id,b.id+' · '+(labels[b.status]||b.status)]),true),'创建同条件复测',s.editor.item.id):''),'仅创建任务不能标记优化完成。已执行必须有实际时间与执行证据。')+
      panel('同条件复测',table(['复测 / 基线','可比性','观测差异','证据'],retests.map(r=>[esc(r.id)+'<small>'+esc(r.baseline_batch_id)+'</small>',esc(r.comparable?'同条件可比':'条件不匹配 / 尚不可比')+'<small>'+esc(warningText(r.warnings))+'</small>',esc(r.comparable?display(r.comparison):'暂无可比差异'),button('查看复测回答','batch-evidence',{id:r.batch_id})+(admin()&&r.manual===true?button('导入人工复测回答','retest-app-import',{id:r.batch_id}):'')]))+pagination(s.data.retests?.total||0,'retests'),'无真实基线不显示提升数。人工App复测请导入回答并填写复测批次编号。');
  }
  function factsForm(f={}) {
    return form('fact',field('logical_id','事实逻辑编号（修订沿用）',f.logical_id)+field('entity_key','车型键',f.entity_key,'text',list(selected().entities).map(e=>[e.key,e.name]),true)+field('year','年款',f.year)+field('trim','配置',f.trim)+field('market','市场',f.market||'中国')+field('field','事实字段',f.field,'text',null,true)+field('value','事实值',f.value,'text',null,true)+field('unit','单位',f.unit)+field('cycle','测试工况（如 CLTC / WLTC）',f.cycle)+field('condition_field','适用条件字段',Object.keys(f.conditions||{})[0]||'market','text',[['market','市场'],['year','年款'],['trim','配置'],['temperature','温度']])+field('condition_value','适用条件值',Object.values(f.conditions||{})[0]||'')+field('effective_from','生效日期',f.effective_from,'date')+field('effective_to','失效日期',f.effective_to,'date')+field('source_url','来源链接',f.source_url,'url')+field('source_excerpt','来源原文',f.source_excerpt,'textarea')+field('reviewer','审核人',f.reviewer)+field('state','审核状态',f.state||'draft','text',[['draft','草稿'],['approved','已审核'],['rejected','未通过']]),'保存事实新版本');
  }
  function aliasesForm() {
    const entities=list(selected().entities);
    return '<form data-geo-form="aliases" class="geo-form">'+entities.map((e,i)=>'<fieldset><legend>'+esc(e.name||e.key)+'</legend>'+field('alias_'+i,'别名（逗号分隔）',list(e.aliases).join(','))+field('year_'+i,'年款',e.year)+field('trim_'+i,'配置',e.trim)+'</fieldset>').join('')+field('add_entity','增加关联车型','','text',[['','不新增'],...list(s.catalog).filter(c=>!entities.some(e=>e.key===c.key)).map(c=>[c.key,c.name])])+'<button type="submit">保存项目别名</button></form>';
  }
  function settings() {
    return panel('事实基准与审核',(admin()?button('新增事实版本','new-fact'):'')+(s.editor?.kind==='fact'?factsForm(s.editor.item):'')+
      table(['车型 / 年款配置','字段 / 值','适用范围与版本','审核','操作'],list(s.data.facts?.items).map(f=>[esc(f.entity_key)+'<small>'+esc(f.year)+' '+esc(f.trim)+'</small>',esc(f.field)+'<small>'+esc(display(f.value))+' '+esc(f.unit)+' '+esc(f.cycle)+'</small>',esc(f.market)+'<small>'+esc(f.effective_from)+'—'+esc(f.effective_to)+' · v'+esc(f.version)+'</small>',pill(f.state)+'<small>'+esc(f.reviewer)+'</small>',admin()?button('新增修订版本','edit-fact',{id:f.id}):'']))+pagination(),'审核需要年款、配置、市场、日期、来源与审核人；修订不覆盖旧批次基准。')+
      panel('车型与别名',admin()?aliasesForm():kv(list(selected().entities).map(e=>[e.name,list(e.aliases).join('、')])),'主车型来自 MMN 车型主数据；别名修改不会改变已冻结批次。')+
      panel('配额、能力与权限',kv([['当前权限',s.cap.role],['真实采样',s.cap.real_sampling_enabled?'开放':'阻塞'],['配额',s.cap.quotas],['缺失条件',s.cap.missing]]), '凭证只在服务器配置。前端不读取、保存或导出 API Key。')+
      (admin()?details('管理员技术配置（只读）',kv([['工作方式',s.cap.worker_mode],['接口能力',s.cap.provider],['价格配置',s.cap.pricing]])):'')+
      panel('审计与导出','<div class="geo-toolbar">'+['questions','observations','metrics','audit'].map(kind=>button('导出'+({questions:'问题',observations:'证据',metrics:'指标',audit:'审计'}[kind]),'export',{kind})).join('')+'</div>'+table(['事件 / 时间','执行者','记录 / 详情'],list(s.data.audit?.items).map(a=>[esc(a.event)+'<small>'+esc(a.created_at)+'</small>',esc(a.actor),esc(a.record_id)+'<small>'+esc(display(a.detail))+'</small>']))+pagination(s.data.audit?.total||0,'audit'));
  }
  function split(value) {return String(value||'').split(/[,，\n]/).map(v=>v.trim()).filter(Boolean);}
  function formValues(node) {const data=new FormData(node);return {data,get:name=>String(data.get(name)||'').trim(),num:name=>data.get(name)==null||data.get(name)===''?null:Number(data.get(name)),bool:name=>data.get(name)==='true'};}
  const idempotency = () => typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : 'geo-'+Date.now()+'-'+Math.random().toString(36).slice(2);
  function showMutationError(node, message, refreshRequired=false) {
    let alert=node.querySelector?.('.geo-form-error');
    if(!alert){alert=document.createElement('div');alert.className='geo-form-error geo-alert';alert.setAttribute('role','alert');node.prepend(alert);}
    alert.innerHTML='<p>'+esc(message)+'</p>'+(refreshRequired?button('刷新诊断与证据','refresh'):'<button type="submit">重试保存</button>');
    el('geo-root')?.querySelector?.('.geo-notice')?.remove();
  }
  async function submit(event) {
    const node=event.target;if(!node?.dataset?.geoForm)return;
    event.preventDefault();const kind=node.dataset.geoForm;
    if(kind!=='filters'&&!admin()){s.error='当前权限只支持查看与导出，请联系项目管理员。';showMutationError(node,s.error);return;}
    const originProject=s.project, epoch=s.epoch;const v=formValues(node),id=node.dataset.id;const pendingKey=originProject+':'+kind+':'+(id||'');if(s.pending.has(pendingKey))return;s.pending.add(pendingKey);for(const control of list(Array.from(node.querySelectorAll?.('button[type=submit]')||[])))control.disabled=true;
    try {
      s.error='';
      if(kind==='filters'){s.filters=Object.fromEntries(['category','active','search','channel','status','batch_id'].map(k=>[k,v.get(k)]).filter(([,value])=>value));s.offset=0;s.detail=null;await load();return;}
      let result, path, body;
      if(kind==='project'){
        const target=s.catalog.find(c=>c.key===v.get('target_key'));if(!target)throw new Error('请选择 MMN 车型主数据中的目标车型。');
        path='/projects';body={name:v.get('name'),target_key:target.key,entities:[target],budget:Object.fromEntries(['batch_budget','day_budget','max_questions','max_repeats','max_concurrency','max_output_tokens'].map(k=>[k,v.num(k)]))};
      } else if(kind==='question'){
        path=id?'/questions/'+encodeURIComponent(id)+'/versions':prefix()+'/questions';
        body=Object.fromEntries(['text','category','intent','budget','scenario','segment','source','year','trim','market','temperature'].map(k=>[k,v.get(k)]));
        if(!body.category)body.category='category';
        if(!categories.some(([key])=>key===body.category))throw new Error('请选择已定义的问题类别。');
        for(const key of ['unbranded','recommendation_eligible','ranking_eligible','fact_eligible','active'])body[key]=v.bool(key);
        body.target_entities=split(v.get('target_entities'));body.competitors=split(v.get('competitors'));
      } else if(kind==='import-csv'){path=prefix()+'/questions/import';body={csv:v.get('csv')};}
      else if(kind==='diagnostic-review'){
        if(!id||!node.dataset.sourceHash||!v.get('reason'))throw new Error('人工复核需要诊断、冻结证据版本与复核依据。');
        if(!['accepted','modified','rejected'].includes(v.get('decision')))throw new Error('请选择明确的人工复核结论。');
        path=prefix()+'/diagnostics/reviews';body={diagnostic_id:id,source_hash:node.dataset.sourceHash,decision:v.get('decision'),reason:v.get('reason')};
        if(body.decision==='modified'){
          if(!v.get('label')||!v.get('action_suggestion')||!['observation','hypothesis'].includes(v.get('statement_type')))throw new Error('修订后采纳需填写修订诊断、建议与判断性质。');
          body.changes={label:v.get('label'),action_suggestion:v.get('action_suggestion'),statement_type:v.get('statement_type')};
        }
      }
      else if(kind==='condition'){path=prefix()+'/conditions';body=Object.fromEntries(['surface','api_mode','mode'].map(k=>[k,v.get(k)]));body.api_mode=apiModeForSurface(body.surface);body.max_output_tokens=v.num('max_output_tokens');body.timeout_seconds=v.num('timeout_seconds');}
      else if(kind==='preview'){
        body={question_version_ids:v.data.getAll('question_version_ids'),condition_ids:v.data.getAll('condition_ids'),repeats:v.num('repeats')};
        if(!body.question_version_ids.length||!body.condition_ids.length||!Number.isInteger(body.repeats)||body.repeats<1)throw new Error('至少选择一个问题版本和一个条件，并填写正整数重复次数。');
        result=await request(prefix()+'/batches/preview',body);
        if(originProject!==s.project||epoch!==s.epoch)return;
        s.preview={...result,input:body,idempotency_key:idempotency()};render();return;
      } else if(kind==='review'){
        const changes={};for(const key of ['mentioned','recommended','needs_review'])if(v.get(key))changes[key]=v.get(key)==='true';
        if(v.get('rank'))changes.rank=v.num('rank');if(v.get('verdict'))changes.verdict=v.get('verdict');if(v.get('evidence'))changes.evidence=v.get('evidence');
        path='/observations/'+encodeURIComponent(id)+'/reviews';body={kind:v.get('kind'),reason:v.get('reason'),changes};
        if(body.kind==='entity')body.entity_key=v.get('entity_key');else body.fact_index=v.num('fact_index');
      } else if(kind==='app-import'){
        path=prefix()+'/app-imports';body=Object.fromEntries(['question_version_id','question_text','answer','sampled_at','platform_trace_id'].map(k=>[k,v.get(k)]));
        body.sampled_at=isoDateValue(body.sampled_at,'采样时间');if(v.get('actual_model'))body.actual_model=v.get('actual_model');
        body.new_session=v.get('new_session')==='true'?true:v.get('new_session')==='false'?false:'unknown';
        body.personalization=v.get('personalization')||'unknown';body.visible_search=v.get('visible_search')||'unknown';
        for(const k of ['paired_observation_id','batch_id','condition_id'])if(v.get(k))body[k]=v.get(k);
        if(v.get('repeat_index')){body.repeat_index=v.num('repeat_index');if(!Number.isInteger(body.repeat_index)||body.repeat_index<1)throw new Error('重复序号须为从1开始的正整数。');}
        if(s.appImport){if(body.batch_id!==s.appImport.batch_id)throw new Error('当前表单绑定冻结复测批次，请勿更改批次编号。');const frozen=s.appImport.questions.find(q=>(q.version_id||q.id)===body.question_version_id);if(!frozen||frozen.text!==body.question_text)throw new Error('请选择本复测冻结的问题版本与原问题全文，不能使用当前新版。');if(!s.appImport.conditions.some(c=>c.id===body.condition_id))throw new Error('请选择本复测冻结的人工条件。');}
        const file=v.data.get('screenshot');if(file?.size){if(!['image/png','image/jpeg'].includes(file.type)||file.size>2*1024*1024)throw new Error('截图须为 PNG / JPEG，且不超过2MB。');body.screenshot_base64=await readImage(file);body.screenshot_mime=file.type;}
        if(!body.answer&&!body.screenshot_base64)throw new Error('请提供回答全文或截图证据。');
      } else if(kind==='action'){
        path=id?'/actions/'+encodeURIComponent(id):prefix()+'/actions';
        body=Object.fromEntries(['title','diagnosis','product_point','fact_to_add','content_structure','carrier','owner','status','execution_evidence','executed_at'].map(k=>[k,v.get(k)]));body.observation_ids=split(v.get('observation_ids'));if(body.executed_at)body.executed_at=isoDateValue(body.executed_at,'实际执行时间');
        if(body.status==='executed'&&(!body.execution_evidence||!body.executed_at))throw new Error('标记已执行需要实际执行证据和执行时间。');
      } else if(kind==='retest'){const action=list(s.data.actions?.items).find(a=>String(a.id)===String(id));if(action?.status!=='executed'||!action.execution_evidence||!action.executed_at)throw new Error('同条件复测需要已执行动作的实际执行证据和时间。');path='/actions/'+encodeURIComponent(id)+'/retest';body={baseline_batch_id:v.get('baseline_batch_id'),idempotency_key:s.editor?.idempotency_key||idempotency()};}
      else if(kind==='resolve-uncertain'){if(!v.get('observation_id')||!v.get('reason'))throw new Error('请填写待确认观测编号与人工确认依据。');path='/batches/'+encodeURIComponent(id)+'/control';body={command:'resolve_uncertain',observation_id:v.get('observation_id'),reason:v.get('reason')};}
      else if(kind==='fact'){path=prefix()+'/facts';body=Object.fromEntries(['logical_id','entity_key','year','trim','market','field','value','unit','cycle','conditions','effective_from','effective_to','source_url','source_excerpt','reviewer','state'].map(k=>[k,v.get(k)]));body.conditions=v.get('condition_field')&&v.get('condition_value')?{[v.get('condition_field')]:v.get('condition_value')}:{};}
      else if(kind==='aliases'){
        path=prefix()+'/entities';const entities=list(selected().entities).map((e,i)=>({...e,aliases:split(v.get('alias_'+i)),year:v.get('year_'+i),trim:v.get('trim_'+i)}));const added=s.catalog.find(c=>c.key===v.get('add_entity'));if(added)entities.push(added);body={entities};
      } else return;
      result=await request(path,body);
      if(originProject!==s.project||epoch!==s.epoch)return;
      if(kind==='project')s.project=result.id;
      s.notice='已保存。历史回答与冻结版本保留。';s.editor=null;s.preview=null;
      if(kind==='review'&&s.detail?.kind==='observation')s.detail.item=await request('/observations/'+encodeURIComponent(id));
      await load();
      if(kind==='diagnostic-review')await loadSummary();
    }catch(error){if(originProject===s.project&&epoch===s.epoch){s.error=error.message+(kind==='diagnostic-review'?' 请刷新诊断与证据后重新复核。':'');s.notice='';showMutationError(node,s.error,kind==='diagnostic-review');}}finally{s.pending.delete(pendingKey);for(const control of Array.from(node.querySelectorAll?.('button[type=submit]')||[]))control.disabled=false;}
  }
  function readImage(file) {return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(new Error('截图读取失败，请重新选择文件。'));reader.readAsDataURL(file);});}
  async function exportData(kind) {
    const originProject=s.project,epoch=s.epoch;
    const data=await request(prefix()+'/export?kind='+encodeURIComponent(kind));
    if(originProject!==s.project||epoch!==s.epoch)return;
    if(s.exportFile)URL.revokeObjectURL(s.exportFile.url);
    const csv=data.csv.startsWith('\ufeff')?data.csv:'\ufeff'+data.csv;
    s.exportFile={project:s.project,url:URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),filename:data.filename||'geo-'+kind+'.csv'};
    s.notice='导出已生成，请点击下载 CSV。';render();
  }
  async function click(event) {
    const node=event.target.closest?.('[data-geo-action]');if(!node||node.disabled)return;
    const a=node.dataset.geoAction,id=node.dataset.id,originProject=s.project;
    event.preventDefault?.();
    try{
      if(a==='tab'){s.tab=node.dataset.tab;s.filters={};s.offset=0;s.pageOffsets={};s.detail=null;s.editor=null;s.preview=null;await load();return;}
      if(a==='refresh'){if(s.editor?.kind==='diagnostic-review')s.editor=null;await load();return;}
      if(a==='retry-init'){await init();await load();return;}
      if(a==='previous'||a==='next'){const scope=node.dataset.scope||'main';if(scope==='main')s.offset=Math.max(0,s.offset+(a==='next'?s.limit:-s.limit));else s.pageOffsets[scope]=Math.max(0,(s.pageOffsets[scope]||0)+(a==='next'?s.limit:-s.limit));s.detail=null;await load();return;}
      if(a==='clear-filters'){s.filters={};s.offset=0;await load();return;}
      if(a==='close-editor'){s.editor=null;render();return;}
      if(a==='project-next'||a==='project-previous'){s.projectOffset=Math.max(0,s.projectOffset+(a==='project-next'?100:-100));s.project='';s.offset=0;s.pageOffsets={};s.detail=null;s.editor=null;s.preview=null;s.data={};await load();return;}
      if(a==='catalog-next'||a==='catalog-previous'){s.catalogOffset=Math.max(0,s.catalogOffset+(a==='catalog-next'?100:-100));await load();return;}
      if(a==='export'){await exportData(node.dataset.kind);return;}
      if(a==='review-needed'){s.tab='evidence';s.filters={status:'needs_review'};s.offset=0;await load();return;}
      if(a==='batch-evidence'){s.tab='evidence';s.filters={batch_id:id};s.offset=0;s.detail=null;await load();return;}
      if(a==='metric-evidence'){const group=list(s.data.metrics?.groups)[Number(node.dataset.group)]||{};if(!group.evidence_scope_hash)throw new Error('统计证据范围缺失，请刷新指标后重新查看。');s.tab='evidence';s.filters={...group.evidence_filters,metric_scope:group.evidence_scope_hash};s.offset=0;s.detail=null;await load();return;}
      if(a==='evidence'){
        const epoch=++s.epoch;const item=await request('/observations/'+encodeURIComponent(id));
        if(originProject!==s.project||epoch!==s.epoch)return;
        s.detail={kind:'observation',item};s.tab='evidence';
        if(!s.data.observations)await load();else render();return;
      }
      if(a==='question-versions'){
        const epoch=++s.epoch;const result=await request('/questions/'+encodeURIComponent(id)+'/versions?limit=100&offset=0');
        if(originProject!==s.project||epoch!==s.epoch)return;s.detail={kind:'versions',items:list(result.items)};render();return;
      }
      if(a==='batch-detail'){const epoch=++s.epoch;const item=await request('/batches/'+encodeURIComponent(id));if(originProject!==s.project||epoch!==s.epoch)return;s.detail={kind:'batch',item};render();return;}
      if(a==='screenshot'){
        const epoch=s.epoch;const image=await request('/observations/'+encodeURIComponent(id)+'/screenshots/'+encodeURIComponent(node.dataset.screenshot));
        if(originProject!==s.project||epoch!==s.epoch||s.detail?.item?.id!==id)return;
        if(!['image/png','image/jpeg'].includes(image.mime)||!/^[A-Za-z0-9+/=]+$/.test(image.base64))throw new Error('截图格式不可显示。');
        s.detail.image='data:'+image.mime+';base64,'+image.base64;render();return;
      }
      if(!admin())throw new Error('当前权限只支持查看与导出。');
      if(a.startsWith('new-')){s.editor={kind:a.slice(4),item:{}};render();return;}
      if(a.startsWith('edit-')){const kind=a.slice(5);const collection={question:'questions',action:'actions',fact:'facts'}[kind];s.editor={kind,item:list(s.data[collection]?.items).find(i=>String(i.id)===id)||{}};render();return;}
      if(a==='clear-app-import'){s.appImport=null;render();return;}
      if(a==='retest-app-import'){const epoch=++s.epoch;const batch=await request('/batches/'+encodeURIComponent(id));if(originProject!==s.project||epoch!==s.epoch)return;const manifest=batch.manifest||{};const questions=list(manifest.questions),conditions=list(manifest.conditions);if(manifest.manual!==true||!questions.length||!conditions.length||!conditions.every(c=>c.surface==='doubao_app_manual'))throw new Error('仅人工App复测批次可通过此入口导入，请核对冻结清单。');s.appImport={project:s.project,batch_id:id,questions,conditions,question_version_id:questions[0].version_id||questions[0].id,condition_id:conditions[0].id};s.tab='evidence';s.offset=0;s.filters={batch_id:id};s.detail=null;s.editor=null;await load();return;}
      if(a==='retest-form'){s.editor={kind:'retest',item:{id},idempotency_key:idempotency()};render();return;}
      if(a==='review-diagnostic'){const item=list(s.data.diagnostics?.items).find(d=>String(d.id)===String(id));if(!item?.source_hash)throw new Error('诊断证据版本缺失，请刷新后重新复核。');s.editor={kind:'diagnostic-review',item};render();return;}
      const epoch=s.epoch;
      if(a==='examples')await request(prefix()+'/questions/examples',{});
      else if(a==='question-state')await request('/questions/'+encodeURIComponent(id)+'/state',{active:node.dataset.active==='true'});
      else if(a==='batch-control')await request('/batches/'+encodeURIComponent(id)+'/control',{command:node.dataset.command,...(node.dataset.command==='retry'?{reason:'用户在任务页确认继续失败项'}:{})});
      else if(a==='create-batch'&&s.preview)await request(prefix()+'/batches',{...s.preview.input,idempotency_key:s.preview.idempotency_key});
      else return;
      if(originProject!==s.project||epoch!==s.epoch)return;s.notice='操作已保存，请查看最新状态。';await load();
    }catch(error){if(originProject===s.project){s.error=error.message;render();}}
  }
  function bind() {
    const root=el('geo-root');if(root&&!root.dataset?.geoBound){root.addEventListener('click',click);root.addEventListener('submit',submit);root.addEventListener('change',async event=>{
      if(event.target.dataset?.geoProject!==undefined){s.project=event.target.value;s.appImport=null;s.offset=0;s.pageOffsets={};s.filters={};s.detail=null;s.editor=null;s.preview=null;s.notice='';s.data={};render();await load();return;}
      const form=event.target.closest?.('[data-geo-form="app-import"]');
      if(!s.appImport||!form)return;
      if(event.target.name==='question_version_id'){const question=s.appImport.questions.find(q=>(q.version_id||q.id)===event.target.value);if(question){s.appImport.question_version_id=question.version_id||question.id;const input=form.querySelector('[name=question_text]');if(input)input.value=question.text;}}
      if(event.target.name==='condition_id'&&s.appImport.conditions.some(c=>c.id===event.target.value))s.appImport.condition_id=event.target.value;
    });if(root.dataset)root.dataset.geoBound='true';}
    const summary=el('geo-cockpit-summary');if(summary&&!summary.dataset?.geoBound){summary.addEventListener('click',async event=>{
      const node=event.target.closest?.('[data-geo-summary]');if(!node)return;
      s.project=node.dataset.project;s.projectOffset=Number(node.dataset.projectOffset||0);s.tab=node.dataset.observation?'evidence':'diagnostics';s.offset=0;s.pageOffsets={};s.filters={};s.detail=null;
      if(typeof showPage==='function')showPage('geo');await load();
      if(node.dataset.observation&&s.project===node.dataset.project){const epoch=++s.epoch;try{const item=await request('/observations/'+encodeURIComponent(node.dataset.observation));if(epoch!==s.epoch||s.project!==node.dataset.project)return;s.detail={kind:'observation',item};render();}catch(error){if(epoch===s.epoch){s.error=error.message;render();}}}
    });if(summary.dataset)summary.dataset.geoBound='true';}
  }
  async function loadSummary() {
    if(!s.ready)await init();const box=el('geo-cockpit-summary');if(!box||!s.cap?.enabled)return;
    const epoch=++s.summaryEpoch;
    const model=typeof state!=='undefined'?String(state.config?.model||''):'';
    box.innerHTML='';
    try{
      let project,projectOffset=0;
      while(true){
        const data=await request('/projects?limit=100&offset='+projectOffset);if(epoch!==s.summaryEpoch)return;
        project=list(data.items).find(p=>{const target=list(p.entities).find(e=>e.key===p.target_key);return p.target_key===model||target?.name===model||list(target?.aliases).includes(model);});
        if(project||projectOffset+100>=Number(data.total||0))break;projectOffset+=100;
      }
      if(!project){box.innerHTML='<div class="geo-summary"><b>GEO · 当前车型尚无项目</b><p>尚无已人工复核诊断</p></div>';return;}
      const data=await request('/projects/'+encodeURIComponent(project.id)+'/cockpit-summary');if(epoch!==s.summaryEpoch)return;
      const reviewed=list(data.reviewed_diagnostics).filter(d=>d.reviewer&&d.reviewed_at&&list(d.observation_ids).length);
      const ids=new Set(reviewed.flatMap(d=>list(d.observation_ids)));
      const actions=list(data.actions).filter(a=>list(a.observation_ids).some(id=>ids.has(id)));
      const evidenceText=value=>typeof value==='string'?value:Array.isArray(value)?value.map(evidenceText).filter(Boolean).join('；'):value&&typeof value==='object'?value.excerpt||value.answer_excerpt||value.quote||value.text||value.snippet||'':'';
      const openButton=(title,observation='')=>'<button type="button" data-geo-summary data-project="'+esc(project.id)+'" data-project-offset="'+projectOffset+'"'+(observation?' data-observation="'+esc(observation)+'"':'')+'>'+esc(title)+'</button>';
      const diagnoses=reviewed.length?'<div class="geo-summary-diagnostics">'+reviewed.map(d=>'<article>'+originBadge(d)+'<b>'+esc(d.label)+'</b><p>'+esc(evidenceText(d.evidence)||'请查看对应回答原文')+'</p><small>人工复核：'+esc(d.reviewer)+' · '+esc(d.reviewed_at)+'</small><div>'+list(d.observation_ids).map(id=>openButton('查看已复核证据',id)).join('')+'</div></article>').join('')+'</div>':'<p>尚无已人工复核诊断</p>';
      box.innerHTML='<div class="geo-summary"><div><b>GEO · '+esc(data.project_name||project.name)+'</b>'+originBadge(data)+diagnoses+
        (reviewed.length?'<ul>'+actions.map(a=>'<li>'+esc(a.title)+' · '+esc(labels[a.status]||a.status||'未知状态')+'</li>').join('')+'</ul>':'')+
        '</div>'+openButton('查看人工复核诊断')+'</div>';
    }catch(error){if(epoch===s.summaryEpoch)box.innerHTML='<p role="alert">GEO 摘要读取失败：'+esc(error.message)+'</p>';}
  }
  window.MMNGeo={init,load,loadSummary};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
  window.addEventListener?.('mmn:auth-ready',()=>{const authEpoch=s.authEpoch=(s.authEpoch||0)+1;if(s.exportFile)URL.revokeObjectURL(s.exportFile.url);s.exportFile=null;s.cap=null;s.project='';s.projects=[];s.projectOffset=0;s.projectTotal=0;s.catalog=[];s.catalogOffset=0;s.catalogTotal=0;s.data={};s.detail=null;s.editor=null;s.appImport=null;s.preview=null;s.filters={};s.notice='';s.error='';++s.epoch;++s.summaryEpoch;if(el('geo-root'))el('geo-root').innerHTML='';if(el('geo-cockpit-summary'))el('geo-cockpit-summary').innerHTML='';s.ready=false;s.initPromise=null;init().then(()=>{if(authEpoch===s.authEpoch&&el('geo')?.classList?.contains('active'))load();});});
  window.addEventListener?.('mmn:vehicle-context-updated',loadSummary);
})();
