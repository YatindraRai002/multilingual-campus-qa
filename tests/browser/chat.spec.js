const {test, expect} = require('@playwright/test');

test('chat is the home screen with five source-backed suggestions', async ({page}) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('heading', {name:'Your campus. Your language.'})).toBeVisible();
  await expect(page.locator('.chat-suggestion')).toHaveCount(5);
  await expect(page.getByLabel('Reply language')).toHaveValue('auto');
  await expect(page.locator('#chat-experiment')).toHaveCount(0);
  await page.screenshot({path:'results/chat-ui-desktop.png',fullPage:true});
  expect(errors).toEqual([]);
});

test('all five broad questions return detailed demo answers in English, Hindi and Tamil', async ({page,request}) => {
  const before = await (await request.get('/api/experiments')).json();
  const topics = (await (await request.get('/api/chat/suggestions')).json()).questions;
  expect(topics).toHaveLength(5);
  await page.goto('/');
  for (const language of ['en','hi','ta']) {
    for (const topic of topics) {
      await page.getByLabel('Your campus question').fill(topic.questions[language]);
      const responsePromise = page.waitForResponse(r => r.url().endsWith('/api/chat') && r.request().method() === 'POST');
      await page.getByLabel('Your campus question').press('Enter');
      const response = await responsePromise;
      expect(response.status()).toBe(200);
      expect(response.request().postDataJSON().language).toBeNull();
      const answer = await response.json();
      expect(answer.language).toBe(language);
      expect(answer.answer_method).toBe('prepared_demo');
      expect(answer.is_demo).toBe(true);
      expect(answer.answer_sections).toHaveLength(4);
      expect(answer.generated_answer.length).toBeGreaterThan(900);
      expect(answer.model_inference_performed).toBe(false);
      expect(answer.research_scored).toBe(false);
      expect(answer.citations.length).toBeGreaterThan(0);
      await expect(page.locator('.chat-message.assistant').last()).toHaveAttribute('lang',language);
      await expect(page.locator('.chat-message.assistant .chat-answer-text').last()).toHaveText(answer.generated_answer);
      await expect(page.locator('.chat-message.assistant').last().locator('.citation').first()).toHaveAttribute('href',answer.citations[0].url);
      await expect(page.locator('.chat-message.assistant').last().locator('.demo-answer-section')).toHaveCount(4);
      await expect(page.locator('.chat-message.assistant').last().locator('.chat-demo-label')).toBeVisible();
      await expect(page.locator('.chat-message.assistant').last().locator('.demo-answer-title')).toBeInViewport();
      await expect(page.locator('.chat-topic-chip').first()).toHaveAttribute('lang',language);
      await expect(page.getByRole('button', {name:'Send message'})).toBeEnabled();
    }
    await page.screenshot({path:`results/chat-ui-${language}.png`,fullPage:true});
  }
  const after = await (await request.get('/api/experiments')).json();
  expect(after.runs.map(r => [r.run_id,r.completed])).toEqual(before.runs.map(r => [r.run_id,r.completed]));
  await page.getByRole('button', {name:'New chat'}).click();
  await expect(page.locator('.chat-message')).toHaveCount(0);
  await expect(page.locator('.chat-suggestion')).toHaveCount(5);
});

test('suggestions switch language and send the selected question', async ({page}) => {
  await page.goto('/');
  await page.getByLabel('Reply language').selectOption('hi');
  await expect(page.locator('.chat-suggestion').first()).toHaveAttribute('lang','hi');
  const responsePromise = page.waitForResponse(r => r.url().endsWith('/api/chat') && r.request().method() === 'POST');
  await page.locator('.chat-suggestion').first().click();
  const answer = await (await responsePromise).json();
  expect(answer.language).toBe('hi');
  await expect(page.locator('.chat-message.assistant').last()).toHaveAttribute('lang','hi');
  await expect(page.locator('#chat-followups')).toBeVisible();
});

test('mobile chat stays within the viewport before and after a Tamil reply', async ({page,request}) => {
  await page.setViewportSize({width:390,height:844});
  const topics = (await (await request.get('/api/chat/suggestions')).json()).questions;
  await page.goto('/');
  await expect(page.locator('.chat-suggestion')).toHaveCount(5);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({path:'results/chat-ui-mobile.png',fullPage:true});
  await page.getByLabel('Your campus question').fill(topics[0].questions.ta);
  const responsePromise = page.waitForResponse(r => r.url().endsWith('/api/chat') && r.request().method() === 'POST');
  await page.getByRole('button', {name:'Send message'}).click();
  expect((await (await responsePromise).json()).language).toBe('ta');
  await expect(page.locator('.chat-message.assistant').last()).toHaveAttribute('lang','ta');
  await expect(page.getByLabel('Your campus question')).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({path:'results/chat-ui-mobile-tamil.png',fullPage:true});
});

test('unavailable model gives a Hindi notice while quick questions remain usable', async ({page,request}) => {
  test.setTimeout(90000);
  const system = await (await request.get('/api/system')).json();
  test.skip(system.inference.ready, 'The native model is available; the unavailable branch is covered by isolated API tests.');
  await page.goto('/');
  await page.getByLabel('Your campus question').fill('सन 2040 में मेरे कमरे का आवंटन क्या होगा?');
  const pending = page.waitForResponse(r => r.url().endsWith('/api/chat') && r.request().method() === 'POST');
  await page.getByRole('button',{name:'Send message'}).click();
  const response = await pending;
  expect(response.status()).toBe(200);
  const answer = await response.json();
  expect(answer.language).toBe('hi');
  await expect(page.locator('.chat-message.assistant').last()).toHaveAttribute('lang','hi');
  await expect(page.locator('.chat-message.error')).toHaveCount(0);
  await expect(page.locator('.chat-topic-chip')).toHaveCount(5);
});
