import Link from 'next/link';
import { getCases } from '../lib/api';

export default async function Home() {
  const cases = await getCases();
  return <div className='flex h-screen'>
    <aside className='w-56 p-4 border-r bg-white'>
      <h1 className='font-bold text-lg mb-4'>WiseChecks</h1>
      <nav className='space-y-2 text-sm'><div>Cases</div><div>Uploads</div><div>Settings</div></nav>
    </aside>
    <main className='p-6 flex-1'>
      <h2 className='text-xl font-semibold mb-4'>Cases</h2>
      <table className='w-full bg-white border'>
        <thead><tr className='text-left'><th className='p-2'>Case #</th><th>Claimant</th><th>Insurer</th></tr></thead>
        <tbody>{cases.map((c:any)=><tr key={c.id} className='border-t'><td className='p-2'><Link className='text-blue-600 underline' href={`/cases/${c.id}`}>{c.case_number}</Link></td><td>{c.claimant_name}</td><td>{c.insurer}</td></tr>)}</tbody>
      </table>
    </main>
  </div>;
}
