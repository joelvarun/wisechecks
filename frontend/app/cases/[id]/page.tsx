import { getDedup, getEvents } from '../../../lib/api';
import { CaseTabs } from '../../../components/CaseTabs';

export default async function CaseDetail({ params }: { params: { id: string } }) {
  const [events, dedup] = await Promise.all([getEvents(params.id), getDedup(params.id)]);
  return <div className='p-5'>
    <div className='mb-3'>
      <h1 className='text-2xl font-bold'>Case Workspace #{params.id}</h1>
      <div className='text-sm text-slate-600'>Wisedocs-style chronology/timeline/dedup/chat/reports with evidence traceability</div>
    </div>
    <CaseTabs events={events} dedup={dedup} />
  </div>;
}
