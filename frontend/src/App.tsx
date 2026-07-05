import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

type View = 'mail' | 'accounts';

type MailAccount = {
  id: number;
  email: string;
  display_name: string | null;
  provider: string | null;
  auth_type: string;
  imap_host: string | null;
  imap_port: number | null;
  imap_security: string;
  smtp_host: string | null;
  smtp_port: number | null;
  smtp_security: string;
  is_active: boolean;
  has_secret: boolean;
};

type MailFolder = {
  id: number;
  account_id: number;
  name: string;
  path: string;
  delimiter: string | null;
  role: string | null;
};

type ConnectivityResult = {
  ok: boolean;
  error: string | null;
};

type ConnectivityReport = {
  imap: ConnectivityResult;
  smtp: ConnectivityResult;
};

type AccountForm = {
  email: string;
  display_name: string;
  provider: string;
  password: string;
  imap_host: string;
  imap_port: number;
  imap_security: 'ssl' | 'starttls' | 'none';
  smtp_host: string;
  smtp_port: number;
  smtp_security: 'ssl' | 'starttls' | 'none';
};

declare global {
  interface Window {
    API_BASE_URL?: string;
  }
}

const env = import.meta.env as Record<string, string | undefined>;
const API_BASE_URL = (window.API_BASE_URL || env.VITE_API_BASE_URL || env.API_BASE_URL || 'http://localhost:8000').replace(
  /\/$/,
  '',
);

const initialAccountForm: AccountForm = {
  email: '',
  display_name: '',
  provider: 'custom',
  password: '',
  imap_host: '',
  imap_port: 993,
  imap_security: 'ssl',
  smtp_host: '',
  smtp_port: 587,
  smtp_security: 'starttls',
};

const folders = [
  { name: 'Inbox', count: 12 },
  { name: 'Starred', count: 3 },
  { name: 'Sent', count: 0 },
  { name: 'Archive', count: 48 },
  { name: 'Trash', count: 2 },
];

const messages = [
  {
    sender: 'Product Updates',
    subject: 'Weekly release notes',
    snippet: 'A compact summary of account settings, sync status, and UI changes.',
    time: '09:42',
    unread: true,
  },
  {
    sender: 'Finance Team',
    subject: 'Invoice review',
    snippet: 'Please confirm the attached invoice before Friday.',
    time: 'Yesterday',
    unread: true,
  },
  {
    sender: 'Ops Monitor',
    subject: 'Storage usage report',
    snippet: 'Disk cache is healthy. Attachment cache cleanup completed.',
    time: 'Mon',
    unread: false,
  },
];

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        message = payload.detail;
      }
    } catch {
      // Keep the status message when the response is not JSON.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

function accountPayload(form: AccountForm) {
  return {
    email: form.email,
    display_name: form.display_name || null,
    provider: form.provider || null,
    password: form.password,
    imap_host: form.imap_host,
    imap_port: Number(form.imap_port),
    imap_security: form.imap_security,
    smtp_host: form.smtp_host,
    smtp_port: Number(form.smtp_port),
    smtp_security: form.smtp_security,
  };
}

function App() {
  const [view, setView] = useState<View>('mail');

  return (
    <main className="min-h-screen bg-panel text-ink">
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[220px_1fr]">
        <aside className="border-b border-line bg-white lg:border-b-0 lg:border-r">
          <div className="flex h-16 items-center border-b border-line px-5">
            <div>
              <p className="text-sm font-semibold">AI Mail</p>
              <p className="text-xs text-slate-500">local@example.invalid</p>
            </div>
          </div>
          <nav className="space-y-1 p-3">
            <button
              className={`flex h-10 w-full items-center rounded-md px-3 text-left text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 ${
                view === 'mail' ? 'bg-slate-100 font-medium' : 'hover:bg-slate-100'
              }`}
              onClick={() => setView('mail')}
              type="button"
            >
              Mail
            </button>
            <button
              className={`flex h-10 w-full items-center rounded-md px-3 text-left text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 ${
                view === 'accounts' ? 'bg-slate-100 font-medium' : 'hover:bg-slate-100'
              }`}
              onClick={() => setView('accounts')}
              type="button"
            >
              Settings
            </button>
          </nav>
        </aside>

        {view === 'mail' ? <MailView /> : <AccountsView />}
      </div>
    </main>
  );
}

function MailView() {
  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[minmax(300px,420px)_1fr]">
      <section className="border-b border-line bg-white lg:border-b-0 lg:border-r">
        <div className="flex h-16 items-center justify-between border-b border-line px-4">
          <div>
            <h1 className="text-base font-semibold">Inbox</h1>
            <p className="text-xs text-slate-500">12 unread</p>
          </div>
          <button
            className="rounded-md border border-line px-3 py-1.5 text-sm hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-accent/30"
            type="button"
          >
            Sync
          </button>
        </div>
        <nav className="grid grid-cols-2 gap-2 border-b border-line p-3 sm:grid-cols-5 lg:hidden">
          {folders.map((folder) => (
            <button className="rounded-md border border-line px-2 py-1.5 text-sm" key={folder.name} type="button">
              {folder.name}
            </button>
          ))}
        </nav>
        <div className="divide-y divide-line">
          {messages.map((message) => (
            <article className="cursor-pointer bg-white p-4 hover:bg-slate-50" key={message.subject}>
              <div className="flex items-start justify-between gap-3">
                <h2 className="text-sm font-semibold">{message.sender}</h2>
                <time className="shrink-0 text-xs text-slate-500">{message.time}</time>
              </div>
              <p className="mt-1 text-sm font-medium">{message.subject}</p>
              <p className="mt-1 line-clamp-2 text-sm leading-5 text-slate-600">{message.snippet}</p>
              {message.unread ? <span className="mt-3 block h-2 w-2 rounded-full bg-accent" /> : null}
            </article>
          ))}
        </div>
      </section>

      <section className="flex min-w-0 flex-col bg-panel">
        <header className="flex h-16 items-center justify-between border-b border-line bg-white px-6">
          <div className="min-w-0">
            <h2 className="truncate text-base font-semibold">Weekly release notes</h2>
            <p className="truncate text-xs text-slate-500">From Product Updates to you</p>
          </div>
          <button
            className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-white hover:bg-teal-800 focus:outline-none focus:ring-2 focus:ring-accent/30"
            type="button"
          >
            Summarize
          </button>
        </header>
        <div className="flex-1 overflow-auto p-6">
          <article className="max-w-3xl rounded-md border border-line bg-white p-6 shadow-sm">
            <p className="text-xs text-slate-500">Today at 09:42</p>
            <h3 className="mt-2 text-lg font-semibold">Weekly release notes</h3>
            <p className="text-sm leading-6 text-slate-700">
              Account settings now show sync health, recent cleanup runs, and the current cache footprint. The message
              list keeps unread and starred states visible during refreshes.
            </p>
            <div className="mt-6 rounded-md border border-line bg-panel p-4">
              <p className="text-sm font-semibold">Summary</p>
              <p className="mt-1 text-sm text-slate-600">
                The release focuses on account visibility, lower cache churn, and clearer message states during
                background refreshes.
              </p>
            </div>
          </article>
        </div>
      </section>
    </div>
  );
}

function AccountsView() {
  const queryClient = useQueryClient();
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [form, setForm] = useState<AccountForm>(initialAccountForm);
  const [formTest, setFormTest] = useState<ConnectivityReport | null>(null);
  const [savedTest, setSavedTest] = useState<ConnectivityReport | null>(null);

  const accountsQuery = useQuery({
    queryKey: ['accounts'],
    queryFn: () => apiFetch<MailAccount[]>('/accounts'),
  });

  const accounts = accountsQuery.data ?? [];
  const activeAccountId = selectedAccountId ?? accounts[0]?.id ?? null;
  const activeAccount = useMemo(
    () => accounts.find((account) => account.id === activeAccountId) ?? null,
    [accounts, activeAccountId],
  );

  const foldersQuery = useQuery({
    queryKey: ['account-folders', activeAccountId],
    queryFn: () => apiFetch<MailFolder[]>(`/accounts/${activeAccountId}/folders`),
    enabled: activeAccountId !== null,
  });

  const createAccount = useMutation({
    mutationFn: () =>
      apiFetch<MailAccount>('/accounts', {
        method: 'POST',
        body: JSON.stringify(accountPayload(form)),
      }),
    onSuccess: (account) => {
      setSelectedAccountId(account.id);
      setForm(initialAccountForm);
      setFormTest(null);
      void queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });

  const testDraftSettings = useMutation({
    mutationFn: () =>
      apiFetch<ConnectivityReport>('/accounts/test', {
        method: 'POST',
        body: JSON.stringify(accountPayload(form)),
      }),
    onSuccess: setFormTest,
  });

  const testSavedSettings = useMutation({
    mutationFn: (accountId: number) =>
      apiFetch<ConnectivityReport>(`/accounts/${accountId}/test`, {
        method: 'POST',
      }),
    onSuccess: setSavedTest,
  });

  const syncFolders = useMutation({
    mutationFn: (accountId: number) =>
      apiFetch<{ account_id: number; folders: MailFolder[] }>(`/accounts/${accountId}/folders/sync`, {
        method: 'POST',
      }),
    onSuccess: (_result, accountId) => {
      void queryClient.invalidateQueries({ queryKey: ['account-folders', accountId] });
    },
  });

  return (
    <section className="min-w-0 bg-panel">
      <header className="flex h-16 items-center justify-between border-b border-line bg-white px-5">
        <div>
          <h1 className="text-base font-semibold">Accounts</h1>
          <p className="text-xs text-slate-500">{API_BASE_URL}</p>
        </div>
        <button
          className="rounded-md border border-line px-3 py-1.5 text-sm hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-accent/30"
          onClick={() => void accountsQuery.refetch()}
          type="button"
        >
          Refresh
        </button>
      </header>

      <div className="grid gap-4 p-4 xl:grid-cols-[360px_minmax(360px,1fr)]">
        <form
          className="rounded-md border border-line bg-white p-4 shadow-sm"
          onSubmit={(event) => {
            event.preventDefault();
            createAccount.mutate();
          }}
        >
          <h2 className="text-sm font-semibold">New account</h2>
          <div className="mt-4 grid gap-3">
            <TextField
              label="Email"
              onChange={(email) => setForm((current) => ({ ...current, email }))}
              type="email"
              value={form.email}
            />
            <TextField
              label="Display name"
              onChange={(display_name) => setForm((current) => ({ ...current, display_name }))}
              value={form.display_name}
            />
            <TextField
              label="Provider"
              onChange={(provider) => setForm((current) => ({ ...current, provider }))}
              value={form.provider}
            />
            <TextField
              label="Password"
              onChange={(password) => setForm((current) => ({ ...current, password }))}
              type="password"
              value={form.password}
            />
            <div className="grid gap-3 sm:grid-cols-[1fr_96px_128px]">
              <TextField
                label="IMAP host"
                onChange={(imap_host) => setForm((current) => ({ ...current, imap_host }))}
                value={form.imap_host}
              />
              <NumberField
                label="Port"
                onChange={(imap_port) => setForm((current) => ({ ...current, imap_port }))}
                value={form.imap_port}
              />
              <SecurityField
                label="Security"
                onChange={(imap_security) => setForm((current) => ({ ...current, imap_security }))}
                value={form.imap_security}
              />
            </div>
            <div className="grid gap-3 sm:grid-cols-[1fr_96px_128px]">
              <TextField
                label="SMTP host"
                onChange={(smtp_host) => setForm((current) => ({ ...current, smtp_host }))}
                value={form.smtp_host}
              />
              <NumberField
                label="Port"
                onChange={(smtp_port) => setForm((current) => ({ ...current, smtp_port }))}
                value={form.smtp_port}
              />
              <SecurityField
                label="Security"
                onChange={(smtp_security) => setForm((current) => ({ ...current, smtp_security }))}
                value={form.smtp_security}
              />
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-white hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={createAccount.isPending}
              type="submit"
            >
              Save
            </button>
            <button
              className="rounded-md border border-line px-3 py-1.5 text-sm hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={testDraftSettings.isPending}
              onClick={() => testDraftSettings.mutate()}
              type="button"
            >
              Test
            </button>
          </div>
          <StatusLine
            error={createAccount.error ?? testDraftSettings.error}
            report={formTest}
            text={createAccount.isSuccess ? 'Saved' : null}
          />
        </form>

        <div className="grid gap-4">
          <section className="rounded-md border border-line bg-white shadow-sm">
            <div className="flex h-12 items-center justify-between border-b border-line px-4">
              <h2 className="text-sm font-semibold">Saved accounts</h2>
              <span className="text-xs text-slate-500">{accounts.length}</span>
            </div>
            {accountsQuery.isLoading ? <p className="p-4 text-sm text-slate-500">Loading</p> : null}
            {accountsQuery.error ? <p className="p-4 text-sm text-red-700">{errorMessage(accountsQuery.error)}</p> : null}
            <div className="divide-y divide-line">
              {accounts.map((account) => (
                <button
                  className={`flex w-full items-center justify-between gap-3 px-4 py-3 text-left hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-accent/30 ${
                    account.id === activeAccountId ? 'bg-slate-50' : ''
                  }`}
                  key={account.id}
                  onClick={() => {
                    setSelectedAccountId(account.id);
                    setSavedTest(null);
                  }}
                  type="button"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-medium">{account.email}</span>
                    <span className="block truncate text-xs text-slate-500">
                      {account.imap_host}:{account.imap_port} · {account.imap_security}
                    </span>
                  </span>
                  <span className="shrink-0 rounded-md border border-line px-2 py-1 text-xs text-slate-600">
                    {account.has_secret ? 'Stored' : 'No secret'}
                  </span>
                </button>
              ))}
            </div>
          </section>

          <section className="rounded-md border border-line bg-white shadow-sm">
            <div className="flex min-h-12 flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-2">
              <div className="min-w-0">
                <h2 className="truncate text-sm font-semibold">{activeAccount?.email ?? 'Folders'}</h2>
                <p className="text-xs text-slate-500">{foldersQuery.data?.length ?? 0} folders</p>
              </div>
              <div className="flex gap-2">
                <button
                  className="rounded-md border border-line px-3 py-1.5 text-sm hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={activeAccountId === null || testSavedSettings.isPending}
                  onClick={() => activeAccountId !== null && testSavedSettings.mutate(activeAccountId)}
                  type="button"
                >
                  Test
                </button>
                <button
                  className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-white hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={activeAccountId === null || syncFolders.isPending}
                  onClick={() => activeAccountId !== null && syncFolders.mutate(activeAccountId)}
                  type="button"
                >
                  Sync folders
                </button>
              </div>
            </div>
            <StatusLine error={testSavedSettings.error ?? syncFolders.error} report={savedTest} text={syncFolders.isSuccess ? 'Folders synced' : null} />
            {foldersQuery.isLoading ? <p className="p-4 text-sm text-slate-500">Loading</p> : null}
            {foldersQuery.error ? <p className="p-4 text-sm text-red-700">{errorMessage(foldersQuery.error)}</p> : null}
            <div className="divide-y divide-line">
              {(foldersQuery.data ?? []).map((folder) => (
                <div className="grid gap-1 px-4 py-3 sm:grid-cols-[160px_1fr_96px]" key={folder.id}>
                  <p className="truncate text-sm font-medium">{folder.name}</p>
                  <p className="truncate text-sm text-slate-600">{folder.path}</p>
                  <p className="text-sm text-slate-500">{folder.role ?? 'folder'}</p>
                </div>
              ))}
              {activeAccountId !== null && !foldersQuery.isLoading && (foldersQuery.data ?? []).length === 0 ? (
                <p className="p-4 text-sm text-slate-500">No folders</p>
              ) : null}
            </div>
          </section>
        </div>
      </div>
    </section>
  );
}

function TextField({
  label,
  onChange,
  type = 'text',
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  type?: string;
  value: string;
}) {
  return (
    <label className="grid gap-1 text-xs font-medium text-slate-600">
      <span>{label}</span>
      <input
        className="h-10 rounded-md border border-line bg-white px-3 text-sm text-ink outline-none focus:ring-2 focus:ring-accent/30"
        onChange={(event) => onChange(event.target.value)}
        type={type}
        value={value}
      />
    </label>
  );
}

function NumberField({ label, onChange, value }: { label: string; onChange: (value: number) => void; value: number }) {
  return (
    <label className="grid gap-1 text-xs font-medium text-slate-600">
      <span>{label}</span>
      <input
        className="h-10 rounded-md border border-line bg-white px-3 text-sm text-ink outline-none focus:ring-2 focus:ring-accent/30"
        min={1}
        max={65535}
        onChange={(event) => onChange(Number(event.target.value))}
        type="number"
        value={value}
      />
    </label>
  );
}

function SecurityField({
  label,
  onChange,
  value,
}: {
  label: string;
  onChange: (value: AccountForm['imap_security']) => void;
  value: AccountForm['imap_security'];
}) {
  return (
    <label className="grid gap-1 text-xs font-medium text-slate-600">
      <span>{label}</span>
      <select
        className="h-10 rounded-md border border-line bg-white px-3 text-sm text-ink outline-none focus:ring-2 focus:ring-accent/30"
        onChange={(event) => onChange(event.target.value as AccountForm['imap_security'])}
        value={value}
      >
        <option value="ssl">SSL</option>
        <option value="starttls">STARTTLS</option>
        <option value="none">None</option>
      </select>
    </label>
  );
}

function StatusLine({
  error,
  report,
  text,
}: {
  error: Error | null;
  report: ConnectivityReport | null;
  text: string | null;
}) {
  if (error) {
    return <p className="mt-3 text-sm text-red-700">{errorMessage(error)}</p>;
  }
  if (report) {
    return (
      <p className="mt-3 text-sm text-slate-600">
        IMAP {report.imap.ok ? 'ok' : report.imap.error} · SMTP {report.smtp.ok ? 'ok' : report.smtp.error}
      </p>
    );
  }
  if (text) {
    return <p className="mt-3 text-sm text-slate-600">{text}</p>;
  }
  return null;
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'Request failed';
}

export default App;
