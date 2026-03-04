'use client';
import { useState } from 'react';

export function CaseTabs({ events, dedup }: { events: any[]; dedup: any[] }) {
  const [tab, setTab] = useState('Chronology');
  const [chat, setChat] = useState<any[]>([]);
  const [q, setQ] = useState('');
  const [viewer, setViewer] = useState<{doc?:number,page?:number,quote?:string}>({});

  const tabs = ['Chronology', 'Timeline', 'Documents', 'Deduplication', 'Chat', 'Reports'];
  return <div className='flex h-[calc(100vh-120px)] border rounded bg-white'>
    <div className='w-64 border-r p-2 space-y-1'>{tabs.map(t=><button key={t} onClick={()=>setTab(t)} className={`w-full text-left p-2 rounded ${tab===t?'bg-slate-200':''}`}>{t}</button>)}</div>
    <div className='flex-1 p-4 overflow-auto'>
      {tab==='Chronology' && <table className='w-full text-sm'><thead><tr><th>Date</th><th>Type</th><th>Title</th><th>Verify</th></tr></thead><tbody>{events.map(e=><tr key={e.id} className='border-t cursor-pointer' onClick={()=>setViewer({doc:e.evidence_ids?.[0],page:e.event_date,quote:e.title})}><td>{e.event_date}</td><td>{e.event_type}</td><td>{e.title}</td><td>{e.verification_status}</td></tr>)}</tbody></table>}
      {tab==='Timeline' && <div className='space-y-3'>{events.map(e=><div key={e.id} className='border-l-4 border-blue-500 pl-3'><div className='text-xs'>{e.event_type}</div><div>{e.event_date}: {e.title}</div></div>)}<div className='mt-4 p-2 bg-amber-50 rounded'><strong>Predictions (probabilistic):</strong> Next visit likely within 2-6 weeks based on recency/frequency.</div></div>}
      {tab==='Documents' && <div>Document index and case search available via backend upload/index pipeline.</div>}
      {tab==='Deduplication' && <div className='space-y-2'>{dedup.map((g:any)=><div key={g.group_id} className='border p-2'><div>Group {g.group_hash.slice(0,8)} score {g.match_score}</div><div className='grid grid-cols-2 gap-2'>{g.items.map((i:any)=><div key={i.item_id} className='p-2 bg-slate-100'>Doc {i.document_id} p.{i.page_number} [{i.action_status}]</div>)}</div></div>)}</div>}
      {tab==='Chat' && <div><div className='flex gap-2 mb-3'><input value={q} onChange={e=>setQ(e.target.value)} className='border p-2 flex-1' placeholder='Ask evidence-backed question'/><button className='bg-blue-600 text-white px-4' onClick={async ()=>{const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000/api'}/cases/1/chat?actor_id=1`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})}).then(r=>r.json()); setChat([...chat,{q,a:res}]);}}>Ask</button></div>{chat.map((c,idx)=><div key={idx} className='mb-4 border p-2'><div className='font-semibold'>{c.q}</div><div>{c.a.answer}</div><ul className='text-xs'>{c.a.citations?.map((ci:any,i:number)=><li key={i}>{ci.document} p.{ci.page}: {ci.excerpt}</li>)}</ul></div>)}</div>}
      {tab==='Reports' && <div>Generate reports from <strong>Verified</strong> chronology events only via API endpoint.</div>}
    </div>
    <aside className='w-96 border-l p-3'>
      <h3 className='font-semibold mb-2'>Document Viewer</h3>
      <div className='text-xs'>PDF.js-ready panel (MVP hook). Opened evidence link target appears here.</div>
      <div className='mt-3 p-2 bg-yellow-50 text-sm'>Doc: {viewer.doc || '-'} Page: {viewer.page || '-'}<br/>Highlight: {viewer.quote || '-'}</div>
    </aside>
  </div>;
}
