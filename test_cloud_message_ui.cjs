// Standalone regression test: node tests/test_cloud_message_ui.cjs
// No npm/browser/database dependency. Uses synthetic messages only.
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
class Element {
 constructor(tag='div'){this.tagName=tag;this.children=[];this.listeners={};this.value='';this.textContent='';this.hidden=false;this.dataset={};this.style={};this.classList={add(){},remove(){},toggle(){}};}
 append(...children){this.children.push(...children);}
 appendChild(child){this.children.push(child);}
 replaceChildren(...children){this.children=[...children];}
 addEventListener(type,handler){this.listeners[type]=handler;}
 setAttribute(){}
 click(){return this.listeners.click?.();}
}
async function flush(){for(let i=0;i<6;i++)await new Promise(resolve=>setImmediate(resolve));}
async function main(){
 const elements=new Map();
 const get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
 const records=[
  ...Array.from({length:35},(_,i)=>({message_id:'S'+i,send_time:`2026-09-${String(16+i%14).padStart(2,'0')}T12:30:00+07:00`,name:'Người A',body:'Nguồn trước tháng'})),
  ...Array.from({length:65},(_,i)=>({message_id:'O'+i,send_time:`2026-10-${String(1+i%15).padStart(2,'0')}T09:00:00+07:00`,name:'Người B',body:'Báo cáo tăng ca'}))
 ];
 const requests=[];
 const fetch=async(url,options)=>{
  requests.push(String(url));
  let data;
  if(url==='/api/config')data={room:{room_id:'123',room_name:'Demo'},has_chatwork_key:true,has_ai_key:true,ai_provider:'gemini',ai_model:'demo'};
  else if(String(url).startsWith('/api/messages?'))data={messages:records,message_count:100,target_month_count:65};
  else if(url==='/api/sync')data={received:100,added:0,updated:0,unchanged:100};
  else throw Error('Unexpected URL '+url);
  return {ok:true,status:200,json:async()=>({success:true,data})};
 };
 const document={
  getElementById:get,
  createElement:tag=>new Element(tag),
  querySelector:selector=>selector==='meta[name="csrf-token"]'?{content:'csrf'}:new Element(),
  querySelectorAll:()=>[]
 };
 get('sourceMonth').value='';
 const context=vm.createContext({document,fetch,location:{assign(){}},URL,console,Date,Intl,Number,String,Object,Array,Error,Promise,Set,setTimeout,clearTimeout});
 const script=fs.readFileSync(path.join(__dirname,'../cloud/static/cloud.js'),'utf8');
 vm.runInContext(script,context,{filename:'cloud.js'});
 await flush();
 assert.equal(vm.runInContext("messageTime('2026-09-25T00:59:12+00:00')",context),'25/09/2026 07:59:12');
 assert.equal(vm.runInContext("messageTime('2026-09-30T18:30:00Z')",context),'01/10/2026 01:30:00');
 assert.equal(vm.runInContext("messageTime(null)",context),'');
 assert.equal(get('messages').children[0].children[1].children[0].children[0].style.whiteSpace,'nowrap');
 assert.equal(get('messages').children[0].tagName,'table','Initial config loads existing messages automatically');
 assert.equal(get('messages').children[0].children[1].children.length,100,'Displays all 100 cached messages, including context');
 assert.match(get('messageViewSummary').textContent,/100\/100/);
 get('messageStart').value='2026-10-15';get('messageEnd').value='2026-10-01';
 vm.runInContext('renderMessages()',context);
 assert.match(get('messages').children[0].textContent,/Từ ngày/,'Reverse dates show an actionable error');
 assert.match(get('messageViewSummary').textContent,/100 tin/,'Reversed dates do not discard cached messages');
 get('messageStart').value='2026-10-01';get('messageEnd').value='2026-10-15';
 vm.runInContext('renderMessages()',context);
 assert.equal(get('messages').children[0].children[1].children.length,65,'October range displays 65 messages');
 get('messageStart').value='2026-10-01';get('messageEnd').value='2026-10-15';
 get('sourceMonth').value='2026-09';
 await get('sourceMonth').listeners.change();await flush();
 assert.equal(get('messageStart').value,'','Switching month clears old start date');
 assert.equal(get('messageEnd').value,'','Switching month clears old end date');
 await get('syncButton').listeners.click();await flush();
 assert.ok(requests.includes('/api/sync'),'Sync API called');
 assert.ok(requests.filter(r=>r.startsWith('/api/messages?')).length>=3,'Sync auto refreshes the message list');
 assert.equal(get('messages').children[0].tagName,'table');
 assert.equal(get('messages').children[0].children[1].children.length,100);
 // Filtering by Vietnamese sender should remain distinct from full source content.
 get('messageSender').value='không tồn tại';vm.runInContext('renderMessages()',context);
 assert.match(get('messages').children[0].textContent,/không có tin khớp bộ lọc/);
 assert.equal(requests.filter(r=>r==='/api/sync').length,1);
 console.log('PASS: 100 records visible, reversed date warning, corrected date shows 65, month switch reset, sync refresh, keyword filtering');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
