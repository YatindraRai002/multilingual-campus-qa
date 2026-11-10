const { test, expect } = require('@playwright/test');

test('real dataset dashboard, navigation, and compute prerequisites', async ({page,request}) => {
  const history = await (await request.get('/api/experiments')).json();
  const training = await (await request.get('/api/training')).json();
  const campus = await (await request.get('/api/college-faq/summary')).json();
  const models = await (await request.get('/api/models')).json();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('heading', {name:'A clearer view of every experiment.'})).toBeVisible();
  await expect(page.getByText('13,921', {exact:true})).toBeVisible();
  if (!history.count) await expect(page.getByText('Evaluation not yet performed.', {exact:true}).first()).toBeVisible();
  else await expect(page.getByRole('heading',{name:'Research results'})).toBeVisible();
  await page.screenshot({path:'results/dashboard-desktop.png',fullPage:true});
  await page.locator('nav a[data-page="datasets"]').click();
  await expect(page.getByRole('heading', {name:'Three languages. Traceable origins.'})).toBeVisible();
  await page.getByRole('button', {name:'Load English validation examples'}).click();
  await expect(page.locator('#samples details').first()).toBeVisible();
  await page.locator('nav a[data-page="training"]').click();
  if (!training.runs[0]?.logs.length) await expect(page.getByText('No loss values recorded.', {exact:false})).toBeVisible();
  else {
    await expect(page.locator('.chart')).toBeVisible();
    await expect(page.locator('#training-chart')).toContainText('Best validation loss');
    if (Number.isFinite(training.runs[0].payload.best_validation_loss))
      await expect(page.locator('#training-chart')).toContainText(training.runs[0].payload.best_validation_loss.toFixed(4));
    await page.screenshot({path:'results/training-dashboard.png',fullPage:true});
  }
  await page.locator('nav a[data-page="experiments"]').click();
  const preflightResponse = page.waitForResponse(response => response.url().includes('/api/evaluation/preflight'));
  await page.getByRole('button', {name:'Check prerequisites'}).click();
  const preflight = await (await preflightResponse).json();
  if (preflight.ready) await expect(page.getByRole('button', {name:'Start evaluation'})).toBeEnabled();
  else await expect(page.getByRole('button', {name:'Start evaluation'})).toBeDisabled();
  await page.locator('nav a[data-page="campus"]').click();
  if (!campus.corpus.count) await expect(page.getByText('Campus corpus not yet collected.', {exact:true})).toBeVisible();
  else await expect(page.getByRole('heading',{name:'Verified FAQ corpus'})).toBeVisible();
  await page.locator('nav a[data-page="chat"]').click();
  if (!models.adapter || !campus.ingestion) {
    await page.getByLabel('Your campus question').fill('Where is the library?');
    await page.getByRole('button', {name:'Ask question'}).click();
    await expect(page.locator('.chat-message.error')).toBeVisible();
  }
  await page.locator('nav a[data-page="review"]').click();
  if (!history.count) await expect(page.getByText('No predictions to review.', {exact:true})).toBeVisible();
  const reviewable = history.runs.find(run => run.completed > 0 && run.track === 'benchmark');
  if (reviewable) {
    await page.locator('#review-run').selectOption(reviewable.run_id);
    await page.locator('.review-prediction').first().click();
    await expect(page.getByRole('heading', {name:'Reference evidence for human review'})).toBeVisible();
    await expect(page.locator('.annotation-form')).toBeVisible();
    await expect(page.locator('.annotation-form input[name="reviewer"]')).toHaveValue('');
  }
  else await expect(page.getByLabel('Experiment run')).toBeVisible();
  await page.locator('nav a[data-page="reports"]').click();
  await page.locator('[data-report="REPRODUCIBILITY.md"]').click();
  await expect(page.locator('#report-content')).toContainText('Reproducibility');
  expect(errors).toEqual([]);
});

test('responsive dashboard has accessible mobile navigation', async ({page}) => {
  await page.setViewportSize({width:390,height:844});
  await page.goto('/');
  await expect(page.getByRole('heading', {name:'A clearer view of every experiment.'})).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole('button', {name:'Toggle navigation'}).click();
  await expect(page.locator('#sidebar')).toHaveClass(/open/);
  await page.locator('nav a[data-page="datasets"]').click();
  await expect(page.getByRole('heading', {name:'Three languages. Traceable origins.'})).toBeVisible();
  await page.waitForFunction(() => document.querySelector('#sidebar').getBoundingClientRect().right <= 1);
  await page.screenshot({path:'results/dashboard-mobile.png',fullPage:true});
});

test('trained campus chat returns a real cited answer with visible review provenance', async ({page,request}) => {
  test.setTimeout(120000);
  const campus = await (await request.get('/api/college-faq/summary')).json();
  const models = await (await request.get('/api/models')).json();
  test.skip(!models.adapter || campus.corpus.version !== 'b07405a784a7045c', 'Requires the completed local campus pilot.');
  const before = await (await request.get('/api/experiments')).json();
  await page.goto('/#chat');
  await page.getByLabel('Your campus question').fill("At SRMIST's Kattankulathur campus: What temple does SRMIST list among its campus worship places?");
  const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/chat') && response.request().method() === 'POST', {timeout:100000});
  await page.getByRole('button', {name:'Ask question'}).click();
  const response = await responsePromise;
  expect(response.status()).toBe(200);
  const answer = await response.json();
  expect(answer.research_scored).toBe(false);
  expect(answer.abstained).toBe(false);
  expect(answer.citations.length).toBeGreaterThan(0);
  await expect(page.locator('.chat-message.assistant a.citation').first()).toHaveAttribute('href', answer.citations[0].url);
  await expect(page.locator('.chat-message.assistant')).toContainText('AI source check · human review pending');
  await page.screenshot({path:'results/chat-dashboard.png',fullPage:true});
  const after = await (await request.get('/api/experiments')).json();
  expect(after.count).toBe(before.count);
  expect(after.runs.map(run => [run.run_id,run.completed])).toEqual(before.runs.map(run => [run.run_id,run.completed]));
});
