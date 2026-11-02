const fs = require('fs');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
let html=fs.readFileSync('static/login.html','utf8').replace(/{% if error %}[\s\S]*?{% endif %}/,'');
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
const page=await browser.newPage({viewport:{width:1150,height:700},deviceScaleFactor:1.5});
await page.route('https://**/*',route=>route.abort());
await page.setContent(html);
await page.screenshot({path:'tmp/report/login.png'});
await browser.close();
})();
