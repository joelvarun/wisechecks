const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export async function getCases() { return fetch(`${API}/cases`, { cache: 'no-store' }).then(r => r.json()); }
export async function getEvents(caseId: string) { return fetch(`${API}/cases/${caseId}/events`, { cache: 'no-store' }).then(r => r.json()); }
export async function getDedup(caseId: string) { return fetch(`${API}/cases/${caseId}/dedup`, { cache: 'no-store' }).then(r => r.json()); }
export async function ask(caseId: string, question: string) {
  return fetch(`${API}/cases/${caseId}/chat?actor_id=1`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ question }) }).then(r=>r.json());
}
