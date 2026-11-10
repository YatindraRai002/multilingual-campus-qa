const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: './tests/browser',
  outputDir: './results/browser-test-output',
  timeout: 45000,
  workers: 1,
  reporter: [['list']],
  use: {baseURL:process.env.CAMPUSQA_BASE_URL || 'http://127.0.0.1:8765',headless:true,channel:'msedge',viewport:{width:1440,height:1100}},
});
