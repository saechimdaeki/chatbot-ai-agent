const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');

function setup() {
  const nodes = new Map();
  const source = fs.readFileSync('frontend/app.js', 'utf8');
  const context = vm.createContext({
    sessionStorage: {getItem:()=>'',removeItem:()=>{}},
    document: {querySelector(selector) {
      if (!nodes.has(selector)) nodes.set(selector, {innerHTML:'',addEventListener(){}});
      return nodes.get(selector);
    }},
    window: {addEventListener(){}}, location:{hash:'#chat'},
    fetch(){throw new Error('Initial chat must not fetch old history');},
    setTimeout, clearTimeout, AbortController,
  });
  vm.runInContext(source.slice(0, source.lastIndexOf('\nif(token)')), context);
  return {context, nodes};
}

test('authenticated chat starts empty without fetching stored history', async () => {
  const {context,nodes} = setup();
  await vm.runInContext("member={id:1,name:'테스트'}; render()", context);
  const html = nodes.get('#content').innerHTML;
  assert.ok(html.includes('chat-welcome'));
  assert.ok(html.includes('이전 기록'));
});

test('navigation retains only messages from the current page session', async () => {
  const {context,nodes} = setup();
  await vm.runInContext("member={id:1}; currentMessages=[{role:'user',text:'이번 대화'}]; render()", context);
  assert.ok(nodes.get('#messages').innerHTML.includes('이번 대화'));
});
