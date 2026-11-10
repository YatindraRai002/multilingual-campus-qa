const $ = (selector, root = document) => root.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const number = value => value === null || value === undefined ? '—' : Number(value).toLocaleString('en-IN');
const decimal = (value, places = 2) => value === null || value === undefined ? '—' : Number(value).toFixed(places);
const date = value => value ? new Date(value).toLocaleString('en-IN', {timeZone:'Asia/Kolkata',day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'}) + ' IST' : '—';
const label = {overview:'Overview', datasets:'Benchmark data', training:'Model & training', experiments:'Experiments', campus:'Campus knowledge', chat:'Grounded chat', review:'Human review', reports:'Reports & provenance'};
let navigation = 0, page = 'overview', cache = {}, polling = null;
let studyRefresh = null;

async function api(path, options = {}) {
  const response = await fetch('/api' + path, {headers:{'Content-Type':'application/json'}, ...options});
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail || data));
  return data;
}
function toast(message) {
  const element = $('#toast');
  element.textContent = message;
  element.classList.add('visible');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => element.classList.remove('visible'), 6500);
}
function badge(status, text = status) { return `<span class="badge ${esc(status)}">${esc(text.replaceAll('_', ' '))}</span>`; }
function heading(kicker, title, subtitle, action = '') {
  return `<div class="page-heading"><div><div class="eyebrow">${esc(kicker)}</div><h1>${title}</h1><p>${subtitle}</p></div><div class="heading-actions">${action}</div></div>`;
}
function card(title, subtitle, body, extra = '') {
  return `<section class="card ${extra}"><div class="card-heading"><div><h2>${title}</h2><p>${subtitle}</p></div></div><div class="card-body">${body}</div></section>`;
}
function empty(title = 'Evaluation not yet performed.', text = 'Results will appear here after a real experiment completes.', action = '') {
  return `<div class="empty-state"><div class="empty-icon">⌁</div><h3>${title}</h3><p>${text}</p>${action}</div>`;
}
function details(rows) { return `<dl class="detail-list">${rows.map(([key,value]) => `<div><dt>${esc(key)}</dt><dd>${esc(value)}</dd></div>`).join('')}</dl>`; }
function citationMarkup(citation, retrieved) {
  const source = retrieved.find(item => item.source_document_id === citation.document_id);
  const review = source?.reviewer_kind === 'ai' ? 'AI source check · human review pending' :
    source?.reviewer_kind === 'human' ? 'Human-reviewed source' : 'Review provenance unavailable';
  return `<a class="citation" href="${esc(citation.url)}" target="_blank" rel="noopener">[${esc(citation.label)}] ${esc(citation.title)} ↗<br><small>${esc(review)}</small></a>`;
}
function blockers(items) { return items.length ? `<div class="blocker-list"><strong>Execution prerequisites</strong><ul>${items.map(item => `<li>${esc(item)}</li>`).join('')}</ul></div>` : '<div class="mini-note">Compute prerequisites passed.</div>'; }
function distribution(languages) {
  const glyph = {en:'A',hi:'अ',ta:'அ'}, color = {en:'#9eb481',hi:'#c6a576',ta:'#83aaa0'};
  return languages.map(language => `<div class="distribution-row"><span class="language-icon ${language.code}" lang="${language.code}">${glyph[language.code]}</span><div><div class="language-title">${esc(language.name)}<small>${language.code.toUpperCase()}</small></div><div class="language-bar"><span style="--width:${language.test_bar_percent}%;--color:${color[language.code]}"></span></div></div><div class="language-value">${number(language.splits.test)}<small>test questions</small></div></div>`).join('');
}
function experimentRows(experiments, runs) {
  return Object.entries(experiments).map(([letter,experiment]) => {
    const run = runs.find(item => item.experiment === letter);
    return `<div class="experiment-row"><span class="experiment-letter ${letter === 'D' ? 'proposed' : ''}">${letter}</span><div class="experiment-info"><strong>${esc(experiment.name)}</strong><small>${experiment.lora ? 'LoRA adapter' : 'Original weights'} · ${experiment.rag ? 'Verified retrieval' : 'No retrieval'}</small></div>${run ? badge(run.status) : '<span class="empty-value">—</span>'}</div>`;
  }).join('');
}
function runOptions(runs) { return `<option value="">Select an experiment run</option>` + runs.map(run => `<option value="${esc(run.run_id)}">${run.experiment} · ${run.track} · ${run.run_id.slice(0,8)} · ${run.status}</option>`).join(''); }

async function overview() {
  const [system, dataset, languages, experiments, trainingData, knowledge, studyData] = await Promise.all([api('/system'),api('/datasets/summary'),api('/datasets/languages'),api('/experiments'),api('/training'),api('/college-faq/summary'),api('/studies')]);
  cache = {...cache, system, dataset, languages, experiments};
  const manifest = dataset.manifest, gpu = system.hardware.gpu;
  const baselineDone = trainingData.baseline_available;
  const trainingDone = trainingData.runs.some(run => run.status === 'completed');
  const activeStudy = studyData.latest?.status === 'running' ? studyData.latest : null;
  const modelsComplete = studyData.latest?.status === 'model_experiments_completed';
  const milestoneTitle = modelsComplete ? 'Model experiments completed.' : activeStudy ? `Current stage: ${activeStudy.stage.replaceAll('_',' ')}.` : !baselineDone ? 'Next milestone: original-model baseline.' : !trainingDone ? 'Next milestone: validation-selected LoRA training.' : !knowledge.ingestion ? 'Next milestone: paired evaluation and verified campus retrieval.' : 'Campus retrieval is indexed.';
  const milestoneText = modelsComplete ? 'Inspect the saved comparisons and source evidence. Human source certification and response factuality reviews remain pending.' : activeStudy ? 'The coordinator is executing the ordered study. Actual saved progress appears in the live banner. Available GPU memory is measured while this job is using it.' : !baselineDone ? (system.inference.ready ? 'The inference hardware gate passes. Run the original model on the sealed evaluation population.' : 'The active model does not currently pass its measured free-VRAM gate. Check the hardware report.') : !trainingDone ? 'The full baseline is recorded. Train the adapter with the prepared train and validation data.' : !knowledge.ingestion ? 'Complete matched benchmark B evaluation, review official FAQs and validate retrieval before campus experiments.' : 'Run the four campus configurations on the same reviewed questions and inspect their persisted results.';
  const phases = [['01','Benchmark',manifest ? 'Downloaded' : 'Pending',!!manifest],['02','Preprocessing',manifest ? 'Validated' : 'Pending',!!manifest],['03','Baseline',baselineDone ? 'Recorded' : activeStudy?.stage === 'benchmark_A' ? 'Running' : system.inference.ready ? 'Ready to run' : 'Check capacity',baselineDone],['04','LoRA training',trainingDone ? 'Adapter saved' : activeStudy?.stage === 'training' ? 'Running' : 'Pending',trainingDone],['05','Campus RAG',knowledge.ingestion ? 'Indexed' : 'Pending',!!knowledge.ingestion]];
  return heading('MULTILINGUAL QUESTION ANSWERING','A clearer view of<br>every experiment.','Benchmark-based LoRA adaptation and grounded campus answers across English, Hindi and Tamil.', '<a class="button" href="#reports"><span>↗</span> Research reports</a><a class="button primary" href="#experiments"><span>＋</span> New experiment</a>') +
  `<div class="status-strip"><div class="strip-left"><span class="status-symbol">✓</span><span><strong>Benchmark established.</strong> ${manifest ? 'Official datasets downloaded, validated and sealed with checksums.' : 'Prepare your official benchmark to begin.'}</span></div><a href="#datasets">View provenance <span>↗</span></a></div>
  <div class="kpi-grid">
    <div class="card kpi"><div class="kpi-top">Held-out questions<span class="kpi-icon">▤</span></div><div class="kpi-value">${number(manifest?.splits.test.total)}</div><div class="kpi-bottom"><span class="live-dot"></span>Two distinct benchmark populations</div></div>
    <div class="card kpi"><div class="kpi-top">Target languages<span class="kpi-icon">文</span></div><div class="kpi-value">${number(languages.languages.length)} <span class="kpi-unit">languages</span></div><div class="kpi-bottom">English · Hindi · Tamil</div></div>
    <div class="card kpi"><div class="kpi-top">Selected base model<span class="kpi-icon">⌘</span></div><div class="kpi-value">${esc(system.model.size_label || system.model.model_id.split("/").pop())} <span class="kpi-unit">Qwen 2.5</span></div><div class="kpi-bottom">Instruct · NF4 QLoRA configuration</div></div>
    <div class="card kpi"><div class="kpi-top">Experiment history<span class="kpi-icon">⊞</span></div><div class="kpi-value">${number(experiments.count)} <span class="kpi-unit">runs</span></div><div class="kpi-bottom">${experiments.count ? 'Persisted experiment records' : 'Evaluation not yet performed.'}</div></div>
  </div>
  <div class="two-column"><section class="card"><div class="card-heading"><div><h2>The research pipeline</h2><p>From a sealed benchmark to evidence-grounded answers</p></div>${badge('green',manifest ? 'Data prepared' : 'Setup')}</div><div class="pipeline">${phases.map((phase,index) => `<div class="pipeline-step ${phase[3] ? 'done' : index === 2 ? 'next' : ''}"><span class="step-number">${phase[3] ? '✓' : phase[0]}</span><div class="step-name">${phase[1]}</div><div class="step-caption">${phase[2]}</div></div>`).join('')}</div><div class="card-body"><div class="mini-note amber"><strong>${esc(milestoneTitle)}</strong> ${esc(milestoneText)} ${manifest?.training_languages_missing.length ? 'Independent training records are still required for missing languages.' : 'The approved IndicSQuAD Hindi/Tamil training supplement is prepared.'}</div></div><div class="card-footer"><span>Every stage has explicit validation gates</span><a href="#training">View setup ↗</a></div></section>
  ${card('Local compute','Measured hardware · active model profile',`<div class="hardware"><div class="hardware-device"><span class="chip">▦</span><div><strong>${esc(gpu?.name || 'GPU unavailable')}</strong><small>${esc(gpu?.compute_capability || '—')} compute capability · ${esc(system.last_cuda_audit === 'passed' ? 'CUDA test passed' : 'CUDA audit available in reports')}</small></div></div>${details([['Installed VRAM',`${gpu?.total_vram_gib || '—'} GiB`],['Recommended training GPU',`${system.model.recommended_training_vram_gib} GiB`],['System memory',`${system.hardware.ram_gib} GiB`]])}<div class="tag-row section-gap">${badge(system.training.ready ? 'green' : 'amber',system.training.ready ? 'Local GPU ready' : 'Check GPU capacity')}<a class="tag" href="/api/docs/ENVIRONMENT_REPORT.md" target="_blank" rel="noopener">Hardware report ↗</a></div></div>`)}</div>
  <div class="two-column"><section class="card"><div class="card-heading"><div><h2>Language coverage</h2><p>Actual held-out record counts from the dataset manifest</p></div><a class="more" href="#datasets" aria-label="View benchmark data">↗</a></div><div class="card-body">${distribution(languages.languages)}<div class="population-note"><span>ⓘ</span><div>Hindi and Tamil use IndicQA. English uses SQuAD v1.1.<br>These are separate populations, without a parallel translation mapping.</div></div></div><div class="card-footer"><span>Original test records preserved</span><a href="#datasets">Explore dataset ↗</a></div></section>
  <section class="card"><div class="card-heading"><div><h2>The four configurations</h2><p>Independent runs, traceable comparisons</p></div>${badge('green','A → D')}</div><div class="card-body">${experimentRows(system.experiments,experiments.runs)}</div><div class="card-footer"><span>D combines adaptation and retrieval</span><a href="#experiments">Open experiments ↗</a></div></section></div>
  <div class="section-title"><h2>Research results</h2><a href="#experiments">All experiments ↗</a></div>
  <section class="card">${experiments.count ? '<div class="card-body section-gap">'+historyTable(experiments.runs.slice(0,5))+'</div>' : empty('Evaluation not yet performed.','Accuracy, hallucination, retrieval and latency metrics will appear after actual model runs. Human-reviewed metrics remain pending until annotations are complete.','<a class="button small" href="#experiments">Set up an experiment ↗</a>')}</section>`;
}

async function datasets() {
  const [dataset,languages] = await Promise.all([api('/datasets/summary'),api('/datasets/languages')]);
  const manifest = dataset.manifest;
  if (!manifest) return heading('BENCHMARK DATA','Establish your benchmark.','Start with official sources.') + empty('Dataset not yet prepared.','Run acquire and prepare from the project command line.');
  return heading('BENCHMARK DATA','Three languages.<br>Traceable origins.','Official IndicQA held out for Hindi and Tamil. SQuAD v1.1 provides a separate English track.','<a class="button" href="/api/docs/BENCHMARK_SELECTION.md" target="_blank" rel="noopener">Selection rationale ↗</a>') +
  `<div class="status-strip"><div class="strip-left"><span class="status-symbol">✓</span><span><strong>Sealed dataset version</strong> <code>${esc(manifest.version)}</code> · ${esc(date(manifest.created_at))}</span></div>${badge('green','Checksummed')}</div>
  <div class="two-column">${card('Evaluation language distribution','Counts preserved from official downloaded records',distribution(languages.languages))}${card('Split integrity','Source document grouping · seed 42',details([['Training records',number(manifest.splits.train.total)],['Validation records',number(manifest.splits.validation.total)],['Test records',number(manifest.splits.test.total)],['Training duplicates removed',number(manifest.training_duplicates_removed)],['Test records removed',number(manifest.test_records_removed)]]))}</div>
  <section class="card"><div class="card-heading"><div><h2>Dataset populations</h2><p>Different sources are kept separate in every metric report</p></div></div><div class="table-wrap"><table><thead><tr><th>Language</th><th>Sources</th><th>Train</th><th>Validation</th><th>Test</th><th>License</th></tr></thead><tbody>${languages.languages.map(language => `<tr><td><strong>${esc(language.name)}</strong></td><td>Test: ${esc(language.evaluation_dataset)}<small>Train: ${esc(language.training_dataset)}</small></td><td>${number(language.splits.train)}</td><td>${number(language.splits.validation)}</td><td>${number(language.splits.test)}</td><td>${language.code === 'en' ? 'CC BY-SA 4.0' : 'CC BY 4.0; inherited SQuAD obligations for translations'}</td></tr>`).join('')}</tbody></table></div><div class="card-footer"><span>No test data are used for training, tuning or checkpoint selection</span></div></section>
  <div class="status-strip ${manifest.training_languages_missing.length ? 'warning' : ''} section-gap"><div class="strip-left"><span class="status-symbol">${manifest.training_languages_missing.length ? '!' : '✓'}</span><span><strong>${manifest.training_languages_missing.length ? 'Training languages still missing.' : 'Approved Hindi/Tamil training extension prepared.'}</strong> IndicQA stays evaluation-only. Supplemental translated records map to original SQuAD training IDs and share document groups with English.</span></div></div>
  <div class="equal-column">${card('Quality & answerability','Audited without deleting held-out questions',`<div class="mini-note">The original <code>category: NO</code> annotation identifies unanswerable IndicQA questions. These support a real abstention evaluation.</div>${details(Object.entries(manifest.splits.test.answerability || {}).map(([language,counts]) => [language.toUpperCase(),`${number(counts.answerable)} answerable · ${number(counts.unanswerable || 0)} unanswerable`]))}${details(Object.entries(manifest.test_warning_counts).map(([key,count]) => [key.replaceAll('_',' '),number(count)]))}<small>Offset mismatches are source annotations, not repaired ground truth. Reference-text scoring remains available; span metrics require review.</small>`)}${card('Provenance & limitations','The similarly named resources are distinguished',`<p class="muted" style="font-size:11px">AI4Bharat IndicQA is an evaluation component of the broader Indic-QA paper benchmark. The paper's own release is hosted separately. This project retains the explicitly requested AI4Bharat source and documents the narrower scope.</p><div class="tag-row"><a class="tag" href="https://huggingface.co/datasets/ai4bharat/IndicQA" target="_blank" rel="noopener">Official dataset ↗</a><a class="tag" href="https://arxiv.org/abs/2407.13522" target="_blank" rel="noopener">Research paper ↗</a></div><div class="section-gap"><small>IndicQA revision</small><p class="mono long-id">${esc(manifest.indicqa_revision)}</p><small>English mapping: not established. Native IndicQA records are not claimed to be translations of SQuAD.</small></div>`)}</div>
  ${card('Inspect validation examples','Interactive inspection uses validation only. The test set stays outside the prompt-development interface.','<button class="button small" id="load-samples">Load English validation examples</button><div id="samples"></div>')}`;
}

function lossChart(logs) {
  const train = logs.filter(log => Number.isFinite(log.loss)).map(log => [log.step,log.loss]);
  const validation = logs.filter(log => Number.isFinite(log.eval_loss)).map(log => [log.step,log.eval_loss]);
  const points = [...train,...validation];
  if (!points.length) return '<div class="empty-chart"><span>No loss values recorded.</span></div>';
  // Coordinates scale the persisted backend log values; no research metrics are computed here.
  const maxStep = Math.max(...points.map(point => point[0]),1), maxLoss = Math.max(...points.map(point => point[1]),1);
  const path = series => series.map((point,index) => `${index ? 'L' : 'M'}${70+point[0]/maxStep*570},${165-point[1]/maxLoss*145}`).join(' ');
  const ticks = [0,.5,1].map(fraction => `<line x1="70" y1="${165-fraction*145}" x2="640" y2="${165-fraction*145}"/><text x="60" y="${169-fraction*145}" text-anchor="end">${decimal(maxLoss*fraction,2)}</text>`).join('');
  return `<svg class="chart" viewBox="0 0 660 195" role="img" aria-label="Recorded training and validation loss">${ticks}<line x1="70" y1="20" x2="70" y2="165"/><text x="70" y="12">Loss</text><text x="70" y="185">0</text><text x="355" y="185" text-anchor="middle">Training step</text><text x="640" y="185" text-anchor="end">${number(maxStep)}</text><path d="${path(train)}" stroke="#64925d"/><path d="${path(validation)}" stroke="#c0a16a"/></svg><div class="legend"><span style="--color:#64925d">Training loss</span><span style="--color:#c0a16a">Validation loss</span></div>`;
}
function trainingProgressMarkup(run) {
  if (!run) return lossChart([]) + '<div class="population-note">Training follows the completed full baseline.</div>';
  const payload = run.payload, last = [...run.logs].reverse().find(log => log.step !== undefined) || {};
  const duration = payload.duration_seconds ?? last.elapsed_seconds;
  const peak = payload.peak_gpu_memory_gib ?? last.gpu_peak_allocated_gib;
  return lossChart(run.logs) + badge(run.status) + `<div class="section-gap">${details([
    ['Recorded optimizer steps',`${number(last.step)} / ${number(payload.total_optimizer_steps || last.total_optimizer_steps)}`],
    ['Best validation loss',decimal(payload.best_validation_loss,4)],
    ['Recorded duration',Number.isFinite(duration) ? decimal(duration/60,1)+' min' : '—'],
    ['Peak allocated GPU memory',Number.isFinite(peak) ? decimal(peak,2)+' GiB' : '—']
  ])}</div>`;
}
async function training() {
  const [system,models,training] = await Promise.all([api('/system'),api('/models'),api('/training')]);
  const selected = models.base_model, tune = training.configuration, latest = training.runs[0];
  return heading('MODEL & ADAPTATION','Same base model.<br>A measurable adaptation.',`${esc(selected.model_id)}, the official chat template, and a separately saved LoRA adapter.`,'<a class="button" href="/api/docs/LORA_TRAINING_REPORT.md" target="_blank" rel="noopener">Training report ↗</a>') +
  `<div class="status-strip warning"><div class="strip-left"><span class="status-symbol">!</span><span><strong>${selected.study_amendment ? "Approved local GPU study." : "Selected model study."}</strong> Active model: ${esc(selected.model_id)}. Local CUDA compatibility is ${system.last_cuda_audit === 'passed' ? 'verified' : 'reported in the hardware audit'}.</span></div><a href="/api/docs/REPRODUCIBILITY.md" target="_blank" rel="noopener">Execution guide ↗</a></div>
  <div class="two-column">${card('Training & validation loss','<span id="training-run-label">'+(latest ? `Training ID: ${esc(latest.training_id)}` : 'Actual logs only · no simulated progress')+'</span>','<div id="training-chart">'+trainingProgressMarkup(latest)+'</div>')}${card('Official model','Pinned checkpoint · study amendment documented',details([['Model',selected.model_id],['License',selected.license],['Precision','NF4 + double quantization'],['Compute type','FP16'],['Input token limit',number(selected.max_input_tokens)],['Tokenizer','Official Qwen chat template']]) + `<div class="section-gap"><small>Immutable revision</small><p class="mono long-id">${esc(selected.revision || 'Resolve model before execution')}</p></div>`)}</div>
  <div class="equal-column">${card('LoRA configuration','Active configuration · actual hardware validation',details([['Rank / alpha',`${tune.lora_rank} / ${tune.lora_alpha}`],['Dropout',tune.lora_dropout],['Learning rate',tune.learning_rate],['Batch / accumulation',`${tune.batch_size} / ${tune.gradient_accumulation_steps}`],['Epochs',tune.epochs],['Sequence length',tune.max_sequence_length],['Gradient checkpointing',String(tune.gradient_checkpointing)],['Seed',tune.seed]]) + `<small>Targets: ${esc(tune.target_modules.join(', '))}</small>`)}${card('GPU availability & adapter','Current free memory for another GPU task',blockers([...training.readiness.blockers,...(training.missing_training_languages.length ? ['Missing training languages: '+training.missing_training_languages.join(', ')+'. Import independent licensed training data.'] : []),...(!latest && !training.baseline_available ? ['Run the full original-model benchmark baseline before training.'] : [])]) + `<div class="section-gap"><h3>LoRA adapter</h3>${models.adapter ? `<p class="mono long-id">${esc(models.adapter.adapter_path)}</p>${badge(models.adapter.status)}` : '<p class="muted" style="font-size:11px">No trained adapter exists yet. See the model registry for the selected artifact directory.</p>'}</div>`)}</div>
  ${card('Run the local study','The coordinator records each actual stage and job ID.',`<pre>python -m backend.cli run-study --phase all
# Follow results/studies/&lt;study-id&gt;/state.json
# After reviewing and ingesting the campus data:
python -m backend.cli run-study --phase campus --resume &lt;study-id&gt;</pre><small>The active study is shown in the live banner. Keep one GPU study running at a time. Training follows the full original-model baseline; campus acquisition follows matched benchmark evaluation.</small>`)}`;
}

function historyTable(runs) {
  if (!runs.length) return empty();
  return `<div class="table-wrap"><table><thead><tr><th aria-label="Select"></th><th>Run / configuration</th><th>Research track</th><th>Dataset version</th><th>Started</th><th>Status</th><th>Inspect</th></tr></thead><tbody>${runs.map(run => `<tr><td><input class="compare-check" type="checkbox" value="${esc(run.run_id)}" aria-label="Select run ${esc(run.run_id)} for comparison"></td><td><strong>${esc(run.experiment)} · ${esc(run.run_id.slice(0,8))}</strong><small>${number(run.completed)} / ${number(run.total)} records persisted</small></td><td>${esc(run.track)}${run.configuration.limit_per_language ? '<small>Pilot subset</small>' : ''}</td><td class="mono">${esc(run.dataset_version)}</td><td>${esc(date(run.created_at))}</td><td>${badge(run.status)}</td><td><button class="button small inspect-run" data-id="${esc(run.run_id)}">Inspect ↗</button></td></tr>`).join('')}</tbody></table></div>`;
}
function metricTile(title, metric) {
  const scored = metric?.value !== null && metric?.value !== undefined;
  const ci = metric?.confidence_interval;
  return `<div class="metric-tile"><small>${esc(title)}</small><div class="metric-value">${scored ? decimal(metric.value) + (metric.unit === 'percent' ? '<span class="kpi-unit">%</span>' : '') : '—'}</div><p>${scored ? `${number(metric.numerator)} / ${number(metric.denominator)} · ${ci ? `95% CI ${decimal(ci.lower)}–${decimal(ci.upper)}` : 'CI unavailable for this sample'}` : 'Insufficient validated data.'}</p><p class="section-gap">${esc(metric?.definition || '')}</p></div>`;
}
function metricsView(result) {
  if (!result || !Object.keys(result.populations || {}).length) return empty();
  return Object.entries(result.populations).map(([source,population]) => `<section class="card section-gap"><div class="card-heading"><div><h2>${esc(source)}</h2><p>Backend-calculated metrics · dataset ${esc(result.dataset_version || '')} · ${esc(date(result.computed_at))}</p></div></div><div class="card-body">${Object.entries(population.languages).map(([language,metrics]) => `<h3 class="section-gap">${esc(language.toUpperCase())} · ${number(metrics.count)} responses · ${number(metrics.human_reviewed)} reviewed</h3><div class="metric-grid">${metricTile('Answer accuracy',metrics.accuracy)}${metricTile('Exact match',metrics.exact_match)}${metricTile('Token F1',metrics.f1)}${metricTile('Hallucination incidence',metrics.hallucination_incidence)}${metricTile('Unsupported claim rate',metrics.unsupported_claim_rate)}${metricTile('Abstention accuracy',metrics.abstention_accuracy)}${metricTile('Retrieval Recall@K',metrics.recall_at_k)}${metricTile('Mean reciprocal rank',metrics.mrr)}</div><div class="section-gap">${details([['Mean total latency',metrics.latency.total_seconds.mean === null ? '—' : decimal(metrics.latency.total_seconds.mean,3)+' s'],['Median total latency',metrics.latency.total_seconds.median === null ? '—' : decimal(metrics.latency.total_seconds.median,3)+' s'],['P95 total latency',metrics.latency.total_seconds.p95 === null ? '—' : decimal(metrics.latency.total_seconds.p95,3)+' s'],['Mean retrieval latency',decimal(metrics.latency.retrieval_seconds.mean,3)+' s'],['Mean generation latency',decimal(metrics.latency.generation_seconds.mean,3)+' s'],['Generation throughput',decimal(metrics.latency.throughput.value)+' tokens/s']])}</div>`).join('')}<div class="mini-note section-gap">Language performance gap: <strong>${population.language_performance_gap.value === null ? 'Insufficient validated data.' : decimal(population.language_performance_gap.value)+' percentage points'}</strong> ${esc(population.language_performance_gap.note)}</div></div></section>`).join('');
}
async function experiments() {
  const [history,system] = await Promise.all([api('/experiments'),api('/system')]);
  cache.experiments = history;
  return heading('EXPERIMENTS','A fair comparison<br>starts with the same questions.','Keep benchmark and campus research tracks separate. Every run saves its population, configuration, predictions and timing.','<button class="button" id="refresh-page">↻ Refresh</button>') +
  `<div class="two-column">${card('Configure an evaluation','Jobs run asynchronously and return a unique run ID.',`<form id="evaluation-form"><div class="form-grid"><div class="field"><label for="track">Research track</label><select id="track"><option value="benchmark">Benchmark · IndicQA + SQuAD</option><option value="campus">Campus · reviewed SRM questions</option></select></div><div class="field"><label for="experiment">Configuration</label><select id="experiment">${Object.entries(system.experiments).map(([key,value]) => `<option value="${key}" ${['C','D'].includes(key) ? 'disabled' : ''}>${key} · ${esc(value.name)}</option>`).join('')}</select></div></div><label class="check-field"><input type="checkbox" id="pilot">Use a small pilot subset (50 per language). Pilots cannot satisfy the full-baseline training gate.</label><div class="inline-actions"><button class="button" type="button" id="preflight">Check prerequisites</button><button class="button primary" id="start-evaluation" disabled type="submit">Start evaluation ↗</button></div><div id="preflight-result"></div></form>`)}${card('Experimental conditions','A/B benchmark · A/B/C/D campus',experimentRows(system.experiments,history.runs))}</div>
  <section class="card"><div class="card-heading"><div><h2>Evaluation history</h2><p>Historical runs and predictions are retained</p></div><button class="button small" id="compare-runs" ${history.runs.length < 2 ? 'disabled' : ''}>Compare selected ↗</button></div>${historyTable(history.runs)}</section><div id="run-detail"></div><div id="comparison"></div>`;
}

async function campus() {
  const data = await api('/college-faq/summary');
  return heading('CAMPUS KNOWLEDGE','Official information.<br>Verified before retrieval.','SRM Institute of Science and Technology · Kattankulathur campus. The campus corpus is separate from benchmark training.','<a class="button" href="/api/docs/COLLEGE_FAQ_DATASET_REPORT.md" target="_blank" rel="noopener">Corpus report ↗</a>') +
  `<div class="status-strip warning"><div class="strip-left"><span class="status-symbol">!</span><span><strong>${data.corpus.count ? 'Official-source campus pilot.' : 'Collection follows benchmark evaluation.'}</strong> ${esc(data.corpus.message || 'Official-source checks and AI translation review are recorded separately from human review.')}</span></div></div>
  <div class="equal-column">${card('Verified FAQ corpus','Every answer retains its source and explicit review provenance',data.corpus.count ? details([['Corpus version',data.corpus.version],['Records',number(data.corpus.count)],['Source-checked records',number(data.corpus.eligible_verified_count)],['Human-verified records',number(data.corpus.human_verified_count)]]) + '<p class="population-note">AI-reviewed translations retain pending human review. Factuality scores require separate human response annotations.</p>' : empty('Campus corpus not yet collected.','Complete baseline evaluation, LoRA training and matched LoRA evaluation before acquiring campus FAQ ground truth.'))}${card('ChromaDB knowledge base','Versioned collections · multilingual metadata filters',data.ingestion ? details([['Collection',data.ingestion.collection],['Chunks',number(data.ingestion.chunks)],['Embedding model',data.ingestion.configuration.embedding_model],['Top K',data.ingestion.configuration.top_k]]) : empty('Index awaiting verified data.','Candidate embeddings must be evaluated on reviewed English, Hindi and Tamil retrieval validation queries before selection.'))}</div>
  ${card('Official source registry','Discovery entries are not verified policy records.',`<div class="table-wrap"><table><thead><tr><th>Source</th><th>Category</th><th>Status</th></tr></thead><tbody>${data.source_registry.sources.map(source => `<tr><td><a href="${esc(source.url)}" target="_blank" rel="noopener">${esc(source.title)} ↗</a><small>${esc(source.url)}</small></td><td>${esc(source.category)}</td><td>${badge('pending',source.status)}</td></tr>`).join('')}</tbody></table></div>`)}
  <div class="equal-column section-gap">${card('Grounding contract','A citation must resolve to retrieved evidence.',`<div class="mini-note">Question → script-aware language routing → multilingual embeddings → verified ChromaDB retrieval → Qwen generation → source-label validation.</div>${details([['Insufficient evidence','Abstain in the requested language'],['Unreviewed machine translations','Excluded from retrieval'],['Source freshness','Verification timestamp checked'],['Policy updates & deletions','New immutable corpus/index version']])}`)}${card('Campus experiment evidence','The four configurations use one reviewed question set.',`<p class="muted" style="font-size:11px">A and B receive no campus context. C and D receive retrieved official evidence from the same versioned index. The comparison engine checks the actual supplied contexts before accepting a C/D comparison.</p><p class="muted" style="font-size:11px">Campus FAQs are never merged into benchmark fine-tuning data.</p>`)}</div>`;
}

async function chat() {
  const [system,models] = await Promise.all([api('/system'),api('/models')]);
  return heading('GROUNDED CAMPUS CHAT','An answer with<br>somewhere to point.','Ask in English, Hindi or Tamil. Evidence and source citations travel with the answer.') +
  `<div class="chat-layout"><section class="card"><div class="card-heading"><div><h2>Campus assistant</h2><p>Interactive conversations are unscored and stay outside research results</p></div>${badge(system.inference.ready ? 'ready' : 'pending',system.inference.ready ? 'Compute ready' : 'Setup required')}</div><div class="chat-body" id="messages" aria-live="polite"><div class="chat-empty"><div class="language-glyphs"><span>A</span><span lang="hi">अ</span><span lang="ta">அ</span></div><h2>Ask with confidence in the evidence.</h2><p>The assistant needs a compatible GPU, a trained adapter for LoRA, and a verified index for retrieval.</p></div></div><form class="chat-compose" id="chat-form"><div class="form-grid"><div class="field"><label for="chat-language">Answer language</label><select id="chat-language"><option value="en">English</option><option value="hi">हिन्दी · Hindi</option><option value="ta">தமிழ் · Tamil</option></select></div><div class="field"><label for="chat-experiment">Configuration</label><select id="chat-experiment"><option value="D">D · LoRA + RAG</option><option value="C">C · Original + RAG</option><option value="B">B · LoRA</option><option value="A">A · Original</option></select></div></div><div class="field"><label class="sr-only" for="question">Your campus question</label><textarea id="question" rows="2" placeholder="Ask a question about SRM Kattankulathur…" required minlength="3" maxlength="2000"></textarea></div><div class="inline-actions"><button type="submit" class="button primary" id="send-chat">Ask question ↗</button><small>Evidence is required for grounded configurations.</small></div></form></section><aside>${card('Before the first answer','Visible prerequisites, never simulated replies',`<div class="mini-note amber">${system.inference.ready ? 'Compute gate passed. Check adapter and corpus availability.' : esc(system.inference.blockers[0])}</div>${details([['Model',system.model.model_id],['Adapter',models.adapter ? 'Available' : 'Not trained'],['Source policy','Official, reviewed records'],['Missing evidence','Explicit abstention']])}<a class="button small section-gap" href="#training">View training setup ↗</a>`)}</aside></div>`;
}

async function review() {
  const history = await api('/experiments');
  return heading('HUMAN REVIEW','Factuality needs<br>an evidence-based review.','Review factual correctness and each claim’s support. Human annotations drive accuracy and hallucination metrics.') +
  `<div class="status-strip"><div class="strip-left"><span class="status-symbol">✓</span><span><strong>Human metrics use human annotations.</strong> AI source review never fills human factuality scores. Unreviewed metrics stay marked “Insufficient validated data.”</span></div></div>
  ${card('Select an experiment','Review history is append-only; a correction creates a new annotation.',`<div class="field"><label for="review-run">Experiment run</label><select id="review-run">${runOptions(history.runs)}</select></div>`)}<div id="review-predictions">${history.runs.length ? '' : '<section class="card section-gap">'+empty('No predictions to review.','Run a real experiment first. Test fixtures never appear in this workspace.')+'</section>'}</div>`;
}

async function reports() {
  const documents = await api('/docs');
  return heading('REPORTS & PROVENANCE','A research trail<br>you can reproduce.','Hardware constraints, dataset origins, metric definitions and execution instructions are documented alongside the implementation.','<a class="button primary" href="/api/docs/REPRODUCIBILITY.md" target="_blank" rel="noopener">Reproduction guide ↗</a>') +
  `<div class="report-list">${documents.documents.map(document => `<a class="card report-link" href="${esc(document.url)}" data-report="${esc(document.name)}"><span class="kpi-icon">▧</span><div><strong>${esc(document.name.replace('.md','').replaceAll('_',' '))}</strong><small>Repository report · actual status and limitations</small></div><span class="arrow">↗</span></a>`).join('')}</div><div id="report-content" class="section-gap"></div>`;
}

const views = {overview,datasets,training,experiments,campus,chat,review,reports};
async function navigate() {
  const current = ++navigation;
  page = location.hash.slice(1).split('?')[0] || 'overview';
  if (!views[page]) page = 'overview';
  clearInterval(polling);
  clearInterval(studyRefresh);
  document.title = `${label[page]} · CampusQA Research`;
  $('#breadcrumb').textContent = label[page];
  document.querySelectorAll('[data-page]').forEach(link => { const active = link.dataset.page === page; link.classList.toggle('active',active); if (active) link.setAttribute('aria-current','page'); else link.removeAttribute('aria-current'); });
  $('#sidebar').classList.remove('open'); $('#menu-button').setAttribute('aria-expanded','false');
  $('#content').innerHTML = '<div class="loading-state"><span class="spinner"></span>Loading research records…</div>';
  try {
    const html = await views[page]();
    if (current !== navigation) return;
    $('#content').innerHTML = html;
    const headingElement = $('.page-heading');
    if (headingElement && ['overview','training','experiments'].includes(page)) {
      headingElement.insertAdjacentHTML('afterend','<div id="live-study-status" role="status" aria-live="polite"></div>');
      const updateStudy = async () => {
        try {
          const data = await api('/studies');
          const state = data.latest;
          const holder = $('#live-study-status');
          if (!state || !holder) return;
          let trainingDetail = '';
          if (state.stage === 'training' || page === 'training') {
            const trainingData = await api('/training');
            const latest = trainingData.runs[0];
            if (latest) {
              const log = [...latest.logs].reverse().find(item => item.step !== undefined);
              const counts = latest.payload.used_training_counts;
              trainingDetail = ` · training ${esc(latest.status)}${log ? ` · step ${number(log.step)} / ${number(log.total_optimizer_steps || latest.payload.total_optimizer_steps)}` : ''}${log?.loss !== undefined ? ` · loss ${decimal(log.loss,4)}` : ''}${counts ? ` · selected en ${number(counts.en)}, hi ${number(counts.hi)}, ta ${number(counts.ta)}` : ' · preparing training inputs'}`;
              if ($('#training-chart')) {
                $('#training-chart').innerHTML = trainingProgressMarkup(latest);
                $('#training-run-label').textContent = 'Training ID: ' + latest.training_id;
              }
            }
          }
          if (current !== navigation || !holder.isConnected) return;
          const studyLabel = state.status === 'model_experiments_completed' ? 'Model experiments completed' : `Study: ${state.stage?.replaceAll('_',' ') || state.status}`;
          const studyStatus = state.status === 'model_experiments_completed' ? 'Human review pending' : state.status.replaceAll('_',' ');
          holder.innerHTML = `<div class="status-strip"><div class="strip-left"><span class="status-symbol">⌁</span><span><strong>${esc(studyLabel)}</strong> · ${esc(studyStatus)}${state.active_run_id ? ` · ${number(state.completed_predictions)} / ${number(state.total_predictions)} predictions` : ''}${trainingDetail}<br><small>${esc(state.study_id)}${state.error ? ' · '+esc(state.error) : ''}</small></span></div></div>`;
        } catch (error) { /* The normal API state remains visible if study polling is unavailable. */ }
      };
      await updateStudy();
      studyRefresh = setInterval(updateStudy,5000);
    }
    $('#connection').innerHTML = '<span class="live-dot"></span>Local API connected';
    $('#connection').classList.remove('offline');
  } catch (error) {
    if (current !== navigation) return;
    $('#connection').classList.add('offline'); $('#connection').textContent = 'API unavailable';
    $('#content').innerHTML = `<div class="error-page"><h1>Could not open the workspace.</h1><p>${esc(error.message)}</p><button class="button" id="refresh-page">Try again</button></div>`;
  }
}

function evaluationBody() { return {track:$('#track').value,experiment:$('#experiment').value,limit_per_language:$('#pilot').checked ? 50 : null}; }
async function inspectRun(runId) {
  const [run,metrics,predictions] = await Promise.all([api('/experiments/'+runId),api('/experiments/'+runId+'/metrics'),api('/experiments/'+runId+'/predictions?limit=5')]);
  const holder = $('#run-detail');
  holder.innerHTML = `<div class="section-title"><h2>Run ${esc(runId)}</h2><div class="inline-actions"><a class="button small" href="/api/experiments/${esc(runId)}/export?format=json">JSON ↓</a><a class="button small" href="/api/experiments/${esc(runId)}/export?format=csv">CSV ↓</a><a class="button small" href="/api/experiments/${esc(runId)}/export?format=markdown">Report ↓</a></div></div>${card('Stored experiment configuration',date(run.created_at),`${badge(run.status)}${run.error ? blockers([run.error]) : ''}<details class="prediction-details"><summary>Configuration, hardware and generation parameters</summary><pre>${esc(JSON.stringify(run.configuration,null,2))}</pre></details>`)}${metricsView(metrics)}${card('Prediction inspection','First five persisted predictions',predictions.predictions.length ? predictions.predictions.map(predictionMarkup).join('') : empty('No predictions yet.','A queued or blocked run has no model outputs.'))}`;
  holder.scrollIntoView({behavior:'smooth',block:'start'});
}
function predictionMarkup(prediction) {
  return `<article class="prediction"><div class="tag-row">${badge(prediction.evaluation_status)}<span class="tag">${esc(prediction.language.toUpperCase())}</span><span class="tag">${esc(prediction.question_id)}</span></div><h3 class="section-gap">${esc(prediction.question)}</h3><p><strong>Reference:</strong> ${esc(prediction.reference_answer || '[unanswerable]')}</p><p><strong>Model:</strong> ${esc(prediction.generated_answer)}</p><details class="prediction-details"><summary>Evidence, citations & timing</summary><pre>${esc(JSON.stringify({context:prediction.context,source_document_id:prediction.source_document_id,context_document_ids:prediction.context_document_ids,relevant_document_ids:prediction.relevant_document_ids,citations:prediction.citations,retrieved:prediction.retrieved,total_seconds:prediction.total_seconds,generation_seconds:prediction.generation_seconds},null,2))}</pre></details></article>`;
}
async function loadReview(runId, offset = 0) {
  const target = $('#review-predictions');
  if (!runId) { target.innerHTML = ''; return; }
  const data = await api('/experiments/'+runId+'/predictions?limit=10&offset='+offset);
  target.innerHTML = `<section class="card section-gap"><div class="card-heading"><div><h2>Persisted predictions</h2><p>Run ${esc(runId)} · inspect the supplied evidence before annotating</p></div></div>${data.predictions.length ? data.predictions.map(prediction => predictionMarkup(prediction) + `<div class="card-body"><button class="button small review-prediction" data-id="${esc(prediction.prediction_id)}">${prediction.annotation ? 'Update human annotation' : 'Review this response'} ↗</button><div id="review-${esc(prediction.prediction_id)}"></div></div>`).join('') : empty('No predictions available.','Only real, persisted model outputs can be reviewed.')}<div class="card-footer"><button class="button small review-page" data-offset="${Math.max(0,offset-10)}" ${offset === 0 ? 'disabled' : ''}>Previous</button><span>Offset ${number(offset)} · run total ${number(data.total_run_predictions)}</span><button class="button small review-page" data-offset="${offset+10}" ${data.predictions.length < 10 ? 'disabled' : ''}>Next</button></div></section>`;
  cache.reviewPredictions = data.predictions;
}

document.addEventListener('click',async event => {
  const button = event.target.closest('button,a');
  if (!button) return;
  try {
    if (button.id === 'menu-button') { const open = $('#sidebar').classList.toggle('open'); button.setAttribute('aria-expanded',String(open)); }
    if (button.id === 'refresh-page') await navigate();
    if (button.id === 'load-samples') {
      button.disabled = true;
      const data = await api('/datasets/records?split=validation&language=en&limit=3');
      $('#samples').innerHTML = data.records.map(row => `<details class="prediction-details"><summary>${esc(row.question)}</summary><p class="muted" style="font-size:11px">${esc(row.context)}</p><p><strong>${esc(row.reference_answer)}</strong></p><small>${esc(row.benchmark_id)} · validation</small></details>`).join('');
      button.disabled = false;
    }
    if (button.id === 'preflight') {
      button.disabled = true;
      $('#preflight-result').textContent = 'Checking compute, data and model prerequisites…';
      const checked = await api('/evaluation/preflight',{method:'POST',body:JSON.stringify(evaluationBody())});
      $('#start-evaluation').disabled = !checked.ready;
      $('#preflight-result').innerHTML = checked.ready ? `<div class="mini-note section-gap">Ready to evaluate ${number(checked.record_count)} sealed records.</div>` : blockers(checked.blockers);
      button.disabled = false;
    }
    if (button.classList.contains('inspect-run')) await inspectRun(button.dataset.id);
    if (button.id === 'compare-runs') {
      const ids = [...document.querySelectorAll('.compare-check:checked')].map(input => input.value);
      if (ids.length < 2 || ids.length > 4) throw new Error('Select two to four persisted experiments.');
      const comparison = await api('/experiments/compare?run_ids='+ids.map(encodeURIComponent).join(','));
      $('#comparison').innerHTML = '<div class="section-title"><h2>Matched experiment comparison</h2></div>'+comparison.runs.map(item => `<h2 class="section-gap">${esc(item.run.experiment)} · ${esc(item.run.run_id)}</h2><div class="mini-note">Evidence: ${esc(item.run.configuration.context_condition)}</div>${metricsView(item.metrics)}`).join('');
      $('#comparison').scrollIntoView({behavior:'smooth'});
    }
    if (button.dataset.report) {
      event.preventDefault();
      const response = await fetch('/api/docs/'+encodeURIComponent(button.dataset.report));
      if (!response.ok) throw new Error('Could not load this report.');
      $('#report-content').innerHTML = `<article class="document-reader"><div class="inline-actions"><h2>${esc(button.dataset.report)}</h2><a class="button small" href="${esc(button.href)}" target="_blank" rel="noopener">Open original ↗</a></div><pre>${esc(await response.text())}</pre></article>`;
      $('#report-content').scrollIntoView({behavior:'smooth'});
    }
    if (button.classList.contains('review-page')) await loadReview($('#review-run').value,Number(button.dataset.offset));
    if (button.classList.contains('review-prediction')) {
      const id = button.dataset.id, prediction = cache.reviewPredictions.find(item => item.prediction_id === id);
      const evidence = await api('/predictions/'+id+'/evidence');
      $('#review-'+CSS.escape(id)).innerHTML = `<div class="review-panel"><h3>Reference evidence for human review</h3><p class="muted">${esc(evidence.policy)}</p><p>Supplied document IDs: <code>${esc(evidence.supplied_document_ids.join(', ') || 'none')}</code><br>Reference document IDs: <code>${esc(evidence.reference_document_ids.join(', ') || 'none')}</code></p>${evidence.reference_sources.map(source => `<p><a href="${esc(source.source_url)}" target="_blank" rel="noopener">${esc(source.source_title)} ↗</a><br><code>${esc(source.source_document_id)}</code><br>Source quote: ${esc(source.evidence_quote)}<br>Review: ${esc(source.reviewer_kind || "unrecorded")} · human review ${esc(source.human_review_status || "unrecorded")}<br>Translation: ${esc(source.translation_status || "unrecorded")}<br>Reference FAQ: ${esc(source.answer)}</p>`).join('')}</div><form class="review-panel annotation-form" data-id="${esc(id)}"><div class="form-grid"><div class="field"><label>Reviewer name<input name="reviewer" required minlength="2" maxlength="200"></label></div><div class="field"><label>Factual correctness<select name="correct" required><option value="">Select a judgment</option><option value="true" ${prediction.abstained && prediction.answerable ? 'disabled' : ''}>Correct</option><option value="false">Incorrect</option></select></label></div></div><div class="field"><label>Complete factual claim inventory (JSON)<textarea name="claims" rows="5" required spellcheck="false">${esc(JSON.stringify(prediction.annotation?.claims || [],null,2))}</textarea></label><small>Each item requires text, supported (true/false), and evidence_document_ids. Supported claims must cite the supplied context or official reference evidence you inspected. Use [] only when the response contains no factual claims.</small></div><div class="field"><label>Review notes<textarea name="notes" rows="2" maxlength="10000"></textarea></label></div><label class="check-field"><input type="checkbox" name="complete" required>I reviewed the reference evidence, and this inventory includes every factual claim.</label><button class="button primary" type="submit">Save human annotation</button></form>`;
    }
  } catch (error) { toast(error.message); if (button.tagName === 'BUTTON') button.disabled = false; }
});

document.addEventListener('change',event => {
  if (event.target.id === 'track') {
    for (const option of $('#experiment').options) option.disabled = $('#track').value === 'benchmark' && ['C','D'].includes(option.value);
    if ($('#track').value === 'benchmark' && ['C','D'].includes($('#experiment').value)) $('#experiment').value = 'A';
  }
  if (['track','experiment','pilot'].includes(event.target.id)) { $('#start-evaluation').disabled = true; $('#preflight-result').innerHTML = ''; }
  if (event.target.id === 'review-run') loadReview(event.target.value).catch(error => toast(error.message));
});

document.addEventListener('submit',async event => {
  const form = event.target;
  if (!['evaluation-form','chat-form'].includes(form.id) && !form.classList.contains('annotation-form')) return;
  event.preventDefault();
  const submit = $('[type="submit"]',form);
  submit.disabled = true;
  try {
    if (form.id === 'evaluation-form') {
      const result = await api('/evaluation/run',{method:'POST',body:JSON.stringify(evaluationBody())});
      $('#preflight-result').innerHTML = `<div class="mini-note section-gap" id="job-status">Queued job <code>${esc(result.run_id)}</code></div>`;
      polling = setInterval(async () => {
        try {
          const status = await api('/evaluation/status/'+result.run_id);
          if ($('#job-status')) $('#job-status').textContent = `${status.status} · ${status.completed} / ${status.total} records · ${status.run_id}`;
          if (!['queued','running'].includes(status.status)) { clearInterval(polling); toast('Experiment '+status.status); await navigate(); }
        } catch (error) { clearInterval(polling); toast(error.message); }
      },4000);
    }
    if (form.id === 'chat-form') {
      const question = $('#question').value.trim(), language = $('#chat-language').value;
      $('.chat-empty')?.remove();
      const messages = $('#messages');
      messages.insertAdjacentHTML('beforeend',`<div class="chat-message user" lang="${language}">${esc(question)}</div><div class="chat-message assistant" id="pending-chat"><span class="spinner"></span> Checking evidence and model prerequisites…</div>`);
      $('#question').value = '';
      try {
        const result = await api('/chat',{method:'POST',body:JSON.stringify({question,language,experiment:$('#chat-experiment').value})});
        $('#pending-chat').outerHTML = `<div class="chat-message assistant" lang="${language}">${esc(result.generated_answer)}${result.citations.map(citation => citationMarkup(citation, result.retrieved || [])).join('')}</div>`;
      } catch (error) { $('#pending-chat').outerHTML = `<div class="chat-message error">${esc(error.message)}</div>`; }
      messages.lastElementChild?.scrollIntoView({behavior:'smooth',block:'nearest'});
    }
    if (form.classList.contains('annotation-form')) {
      const data = new FormData(form), claims = JSON.parse(data.get('claims'));
      if (!Array.isArray(claims)) throw new Error('Claim inventory must be a JSON array.');
      await api('/predictions/'+form.dataset.id+'/annotations',{method:'POST',body:JSON.stringify({reviewer:data.get('reviewer'),correct:data.get('correct') === 'true',claims,claim_inventory_complete:true,notes:data.get('notes')})});
      toast('Human annotation saved. Backend metrics recomputed.');
      await loadReview($('#review-run').value);
    }
  } catch (error) { toast(error.message); }
  finally { if (submit.isConnected) submit.disabled = false; }
});

window.addEventListener('hashchange',navigate);
navigate();
