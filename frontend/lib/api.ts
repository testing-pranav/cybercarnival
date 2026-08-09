// Talks to Flask backend. Set NEXT_PUBLIC_API_URL in your hosting platform's
// env vars (e.g. Vercel project settings) to your deployed backend's URL,
// e.g. https://cybercarnival-backend.onrender.com. Falls back to localhost
// for local dev when unset.
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

export type ApiEvent = {
  id: string
  name: string
  fee: string
  team_size: string
  venue: string
  date: string
}

export async function fetchEvents(): Promise<ApiEvent[]> {
  const res = await fetch(`${API_URL}/api/events`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Could not load events from the server.')
  return res.json()
}

export type RegistrationPayload = {
  name: string
  email: string
  phone: string
  event_id: string
  college?: string
  team_members?: string[]
}

export class ApiValidationError extends Error {
  fields?: Record<string, string>
  constructor(message: string, fields?: Record<string, string>) {
    super(message)
    this.fields = fields
  }
}

export async function submitRegistration(
  payload: RegistrationPayload
): Promise<{ id: string; status: string }> {
  const res = await fetch(`${API_URL}/api/registrations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await res.json().catch(() => ({}))

  if (!res.ok) {
    throw new ApiValidationError(data.error || 'Registration failed.', data.fields)
  }

  return data
}
