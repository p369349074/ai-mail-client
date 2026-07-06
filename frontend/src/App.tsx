import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

type View = 'mail' | 'accounts';
type Language = 'zh' | 'en';
type Theme = 'light' | 'dark';

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

type Copy = Record<string, string>;

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

const copy: Record<Language, Copy> = {
  zh: {
    appName: '邮件管理',
    appSubtitle: 'AI 邮箱客户端',
    mail: '邮件查看',
    settings: '邮箱账号',
    dashboard: '仪表盘',
    folders: '文件夹',
    aiTools: 'AI 助手',
    inbox: '收件箱',
    starred: '星标',
    sent: '已发送',
    archive: '归档',
    trash: '废纸篓',
    unread: '未读',
    sync: '刷新',
    searchPlaceholder: '搜索邮件…',
    loadedCount: '已加载 3 封',
    summarize: 'AI 总结',
    quickReply: '智能回复',
    sender: '发件人',
    recipient: '收件人',
    time: '时间',
    summary: '摘要',
    defaultSummary: '本次更新聚焦账号可见性、缓存清理和刷新过程中的邮件状态展示。',
    releaseTitle: '每周产品更新',
    releaseSubject: '每周发布说明',
    releaseSnippet: '账号设置现在展示同步健康状态、最近清理任务和当前缓存占用。',
    financeSender: '财务团队',
    financeSubject: '发票确认',
    financeSnippet: '请在周五前确认附件中的发票信息。',
    opsSender: '运维监控',
    opsSubject: '存储用量报告',
    opsSnippet: '磁盘缓存健康，附件缓存清理任务已完成。',
    today: '今天 09:42',
    yesterday: '昨天',
    monday: '周一',
    accounts: '邮箱账号',
    endpoint: '后端地址',
    refresh: '刷新',
    newAccount: '添加邮箱账号',
    email: '邮箱',
    displayName: '显示名称',
    provider: '服务商',
    password: '密码 / 授权码',
    imapHost: 'IMAP 主机',
    smtpHost: 'SMTP 主机',
    port: '端口',
    security: '安全协议',
    save: '保存',
    test: '测试',
    saved: '已保存',
    savedAccounts: '已保存账号',
    loading: '加载中',
    stored: '已保存密钥',
    noSecret: '未保存密钥',
    syncFolders: '同步文件夹',
    foldersSynced: '文件夹已同步',
    noFolders: '暂无文件夹',
    folder: '文件夹',
    requestFailed: '请求失败',
    online: '已连接',
    themeLight: '浅色',
    themeDark: '深色',
    language: '语言',
    chinese: '中文',
    english: 'English',
    logout: '退出登录',
    previewBadge: '当前为前端骨架数据',
    aiNote: 'AI 功能将按需调用外部 API，不会默认全量处理邮件。',
  },
  en: {
    appName: 'Mail Manager',
    appSubtitle: 'AI Mail Client',
    mail: 'Mail View',
    settings: 'Mail Accounts',
    dashboard: 'Dashboard',
    folders: 'Folders',
    aiTools: 'AI Assistant',
    inbox: 'Inbox',
    starred: 'Starred',
    sent: 'Sent',
    archive: 'Archive',
    trash: 'Trash',
    unread: 'unread',
    sync: 'Refresh',
    searchPlaceholder: 'Search mail…',
    loadedCount: '3 messages loaded',
    summarize: 'AI Summary',
    quickReply: 'Smart Reply',
    sender: 'From',
    recipient: 'To',
    time: 'Time',
    summary: 'Summary',
    defaultSummary: 'This release focuses on account visibility, cache cleanup, and clearer message states during refreshes.',
    releaseTitle: 'Weekly product update',
    releaseSubject: 'Weekly release notes',
    releaseSnippet: 'Account settings now show sync health, recent cleanup runs, and current cache footprint.',
    financeSender: 'Finance Team',
    financeSubject: 'Invoice review',
    financeSnippet: 'Please confirm the attached invoice before Friday.',
    opsSender: 'Ops Monitor',
    opsSubject: 'Storage usage report',
    opsSnippet: 'Disk cache is healthy. Attachment cache cleanup completed.',
    today: 'Today 09:42',
    yesterday: 'Yesterday',
    monday: 'Mon',
    accounts: 'Mail Accounts',
    endpoint: 'API endpoint',
    refresh: 'Refresh',
    newAccount: 'Add mail account',
    email: 'Email',
    displayName: 'Display name',
    provider: 'Provider',
    password: 'Password / app password',
    imapHost: 'IMAP host',
    smtpHost: 'SMTP host',
    port: 'Port',
    security: 'Security',
    save: 'Save',
    test: 'Test',
    saved: 'Saved',
    savedAccounts: 'Saved accounts',
    loading: 'Loading',
    stored: 'Secret stored',
    noSecret: 'No secret',
    syncFolders: 'Sync folders',
    foldersSynced: 'Folders synced',
    noFolders: 'No folders',
    folder: 'folder',
    requestFailed: 'Request failed',
    online: 'Connected',
    themeLight: 'Light',
    themeDark: 'Dark',
    language: 'Language',
    chinese: '中文',
    english: 'English',
    logout: 'Log out',
    previewBadge: 'Using skeleton preview data',
    aiNote: 'AI features will call external APIs on demand and will not process all mail by default.',
  },
};

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

const folderMeta = [
  { key: 'inbox', count: 12, icon: '📥' },
  { key: 'starred', count: 3, icon: '⭐' },
  { key: 'sent', count: 0, icon: '📤' },
  { key: 'archive', count: 48, icon: '🗄️' },
  { key: 'trash', count: 2, icon: '🗑️' },
];

const messageMeta = [
  { senderKey: 'releaseTitle', subjectKey: 'releaseSubject', snippetKey: 'releaseSnippet', timeKey: 'today', unread: true },
  { senderKey: 'financeSender', subjectKey: 'financeSubject', snippetKey: 'financeSnippet', timeKey: 'yesterday', unread: true },
  { senderKey: 'opsSender', subjectKey: 'opsSubject', snippetKey: 'opsSnippet', timeKey: 'monday', unread: false },
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

function initialLanguage(): Language {
  return localStorage.getItem('language') === 'en' ? 'en' : 'zh';
}

function initialTheme(): Theme {
  return localStorage.getItem('theme') === 'dark' ? 'dark' : 'light';
}

function App() {
  const [view, setView] = useState<View>('mail');
  const [language, setLanguageState] = useState<Language>(initialLanguage);
  const [theme, setThemeState] = useState<Theme>(initialTheme);
  const t = copy[language];

  const setLanguage = (next: Language) => {
    localStorage.setItem('language', next);
    setLanguageState(next);
  };

  const setTheme = (next: Theme) => {
    localStorage.setItem('theme', next);
    setThemeState(next);
  };

  return (
    <main className={theme === 'dark' ? 'dark' : ''}>
      <div className="min-h-screen bg-[#f4f6fb] text-[#1a1d2e] antialiased dark:bg-[#09090b] dark:text-[#e8ecf4]">
        <div className="fixed inset-0 -z-10 bg-[radial-gradient(ellipse_at_15%_5%,rgba(99,102,241,0.08),transparent_45%),radial-gradient(ellipse_at_85%_95%,rgba(167,139,250,0.08),transparent_45%)] dark:bg-[radial-gradient(ellipse_at_0%_0%,rgba(99,102,241,0.16),transparent_42%),radial-gradient(ellipse_at_90%_100%,rgba(167,139,250,0.08),transparent_52%)]" />
        <div className="flex min-h-screen">
          <aside className="hidden w-60 shrink-0 border-r border-black/5 bg-white/80 backdrop-blur-2xl dark:border-white/10 dark:bg-zinc-900/75 lg:flex lg:flex-col">
            <div className="flex h-16 items-center gap-3 border-b border-black/5 px-5 dark:border-white/10">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 text-lg text-white shadow-lg shadow-indigo-500/20">
                ✉️
              </div>
              <div className="min-w-0">
                <h1 className="truncate text-[15px] font-semibold tracking-[-0.02em]">{t.appName}</h1>
                <p className="truncate text-xs text-slate-500 dark:text-slate-400">{t.appSubtitle}</p>
              </div>
            </div>

            <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
              <SidebarButton active={view === 'mail'} icon="📬" label={t.mail} onClick={() => setView('mail')} />
              <SidebarButton active={view === 'accounts'} icon="👤" label={t.accounts} onClick={() => setView('accounts')} />
              <SidebarButton active={false} icon="📊" label={t.dashboard} onClick={() => setView('mail')} />
              <SidebarButton active={false} icon="🏷️" label={t.folders} onClick={() => setView('mail')} />
              <SidebarButton active={false} icon="✨" label={t.aiTools} onClick={() => setView('mail')} />
            </nav>

            <div className="border-t border-black/5 p-4 text-xs text-slate-500 dark:border-white/10 dark:text-slate-400">
              <div className="rounded-2xl border border-black/5 bg-white/60 p-3 dark:border-white/10 dark:bg-white/[0.03]">
                <p className="font-medium text-slate-700 dark:text-slate-200">{t.online}</p>
                <p className="mt-1 truncate">{API_BASE_URL}</p>
              </div>
              <button className="mt-3 flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left hover:bg-black/[0.03] dark:hover:bg-white/[0.05]" type="button">
                ↩ <span>{t.logout}</span>
              </button>
            </div>
          </aside>

          <section className="flex min-w-0 flex-1 flex-col">
            <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-black/5 bg-white/75 px-4 backdrop-blur-2xl dark:border-white/10 dark:bg-zinc-950/70 sm:px-6 lg:px-7">
              <div className="min-w-0">
                <div className="flex items-center gap-2 lg:hidden">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white">✉️</div>
                  <h1 className="truncate text-base font-semibold">{t.appName}</h1>
                </div>
                <h2 className="hidden text-base font-semibold tracking-[-0.02em] lg:block">{view === 'mail' ? t.mail : t.accounts}</h2>
              </div>
              <div className="flex items-center gap-2">
                <div className="hidden rounded-xl border border-black/5 bg-white/80 p-1 shadow-sm dark:border-white/10 dark:bg-white/[0.04] sm:flex">
                  <button
                    className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                      theme === 'light' ? 'bg-indigo-50 text-indigo-600 dark:bg-indigo-500/15 dark:text-indigo-300' : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
                    }`}
                    onClick={() => setTheme('light')}
                    type="button"
                  >
                    ☀️ {t.themeLight}
                  </button>
                  <button
                    className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                      theme === 'dark' ? 'bg-indigo-50 text-indigo-600 dark:bg-indigo-500/15 dark:text-indigo-300' : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
                    }`}
                    onClick={() => setTheme('dark')}
                    type="button"
                  >
                    🌙 {t.themeDark}
                  </button>
                </div>
                <div className="rounded-xl border border-black/5 bg-white/80 p-1 shadow-sm dark:border-white/10 dark:bg-white/[0.04]">
                  <button
                    className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                      language === 'zh' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
                    }`}
                    onClick={() => setLanguage('zh')}
                    type="button"
                  >
                    中文
                  </button>
                  <button
                    className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                      language === 'en' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
                    }`}
                    onClick={() => setLanguage('en')}
                    type="button"
                  >
                    EN
                  </button>
                </div>
              </div>
            </header>

            {view === 'mail' ? <MailView t={t} /> : <AccountsView t={t} />}
          </section>
        </div>
      </div>
    </main>
  );
}

function SidebarButton({ active, icon, label, onClick }: { active: boolean; icon: string; label: string; onClick: () => void }) {
  return (
    <button
      className={`group relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-medium transition ${
        active
          ? 'bg-indigo-500/10 text-indigo-600 dark:bg-indigo-500/15 dark:text-indigo-300'
          : 'text-slate-500 hover:bg-black/[0.03] hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/[0.05] dark:hover:text-white'
      }`}
      onClick={onClick}
      type="button"
    >
      {active ? <span className="absolute left-0 h-5 w-1 rounded-r-full bg-gradient-to-b from-indigo-500 to-violet-500" /> : null}
      <span className="ml-1 text-base">{icon}</span>
      <span>{label}</span>
    </button>
  );
}

function MailView({ t }: { t: Copy }) {
  const folders = folderMeta.map((folder) => ({ ...folder, name: t[folder.key] }));
  const messages = messageMeta.map((message) => ({
    sender: t[message.senderKey],
    subject: t[message.subjectKey],
    snippet: t[message.snippetKey],
    time: t[message.timeKey],
    unread: message.unread,
  }));

  return (
    <div className="flex min-h-0 flex-1 flex-col p-4 sm:p-5 lg:p-6">
      <div className="mb-3 flex flex-col gap-3 rounded-2xl border border-black/5 bg-white/80 p-3 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-white/[0.04] lg:flex-row lg:items-center">
        <select className="h-10 rounded-xl border border-black/10 bg-white px-3 text-sm outline-none focus:border-indigo-400 dark:border-white/10 dark:bg-zinc-950 dark:text-white">
          <option>local@example.invalid</option>
        </select>
        <select className="h-10 rounded-xl border border-black/10 bg-white px-3 text-sm outline-none focus:border-indigo-400 dark:border-white/10 dark:bg-zinc-950 dark:text-white">
          <option>{t.inbox}</option>
        </select>
        <button className="h-10 rounded-xl border border-black/10 bg-white px-4 text-sm font-medium hover:bg-slate-50 dark:border-white/10 dark:bg-white/[0.04] dark:hover:bg-white/[0.07]" type="button">
          {t.sync}
        </button>
        <input
          className="h-10 min-w-0 flex-1 rounded-xl border border-black/10 bg-white px-3 text-sm outline-none placeholder:text-slate-400 focus:border-indigo-400 dark:border-white/10 dark:bg-zinc-950 dark:text-white"
          placeholder={t.searchPlaceholder}
        />
        <span className="shrink-0 text-xs text-slate-500 dark:text-slate-400">{t.loadedCount}</span>
      </div>

      <div className="grid min-h-[660px] flex-1 overflow-hidden rounded-[22px] border border-black/10 bg-white/70 shadow-xl shadow-slate-200/50 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-900/60 dark:shadow-black/20 lg:grid-cols-[360px_minmax(0,1fr)]">
        <section className="min-h-0 border-b border-black/5 dark:border-white/10 lg:border-b-0 lg:border-r">
          <div className="border-b border-black/5 p-4 dark:border-white/10">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-lg font-semibold tracking-[-0.03em]">{t.inbox}</h1>
                <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">12 {t.unread}</p>
              </div>
              <span className="rounded-full bg-indigo-500/10 px-2.5 py-1 text-xs font-medium text-indigo-600 dark:text-indigo-300">{t.previewBadge}</span>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2">
              {folders.slice(0, 4).map((folder) => (
                <button
                  className="flex items-center justify-between rounded-xl border border-black/5 bg-white/70 px-3 py-2 text-sm hover:border-indigo-200 hover:bg-indigo-50/60 dark:border-white/10 dark:bg-white/[0.03] dark:hover:bg-indigo-500/10"
                  key={folder.key}
                  type="button"
                >
                  <span className="flex items-center gap-2"><span>{folder.icon}</span>{folder.name}</span>
                  <span className="text-xs text-slate-400">{folder.count}</span>
                </button>
              ))}
            </div>
          </div>
          <div className="max-h-[560px] overflow-y-auto">
            {messages.map((message, index) => (
              <article
                className={`relative cursor-pointer border-b border-black/5 p-4 transition dark:border-white/10 ${
                  index === 0
                    ? 'bg-indigo-500/[0.07] dark:bg-indigo-500/10'
                    : 'bg-transparent hover:bg-black/[0.025] dark:hover:bg-white/[0.04]'
                }`}
                key={message.subject}
              >
                {index === 0 ? <span className="absolute left-0 top-4 h-16 w-1 rounded-r-full bg-gradient-to-b from-indigo-500 to-violet-500" /> : null}
                <div className="flex items-start justify-between gap-3">
                  <h2 className="truncate text-sm font-semibold text-slate-900 dark:text-white">{message.sender}</h2>
                  <time className="shrink-0 text-xs text-slate-400">{message.time}</time>
                </div>
                <p className="mt-1 truncate text-sm font-medium text-slate-800 dark:text-slate-100">{message.subject}</p>
                <p className="mt-1 line-clamp-2 text-sm leading-5 text-slate-500 dark:text-slate-400">{message.snippet}</p>
                {message.unread ? <span className="mt-3 block h-2 w-2 rounded-full bg-indigo-500" /> : null}
              </article>
            ))}
          </div>
        </section>

        <section className="min-w-0 overflow-y-auto bg-white dark:bg-zinc-950/50">
          <article className="p-5 sm:p-6">
            <div className="border-b border-black/5 pb-4 dark:border-white/10">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <h2 className="text-2xl font-semibold tracking-[-0.04em] text-slate-950 dark:text-white">{t.releaseSubject}</h2>
                  <dl className="mt-4 grid gap-1 text-sm text-slate-500 dark:text-slate-400">
                    <div><dt className="inline font-medium text-slate-700 dark:text-slate-300">{t.sender}: </dt><dd className="inline">Product Updates &lt;noreply@example.invalid&gt;</dd></div>
                    <div><dt className="inline font-medium text-slate-700 dark:text-slate-300">{t.recipient}: </dt><dd className="inline">local@example.invalid</dd></div>
                    <div><dt className="inline font-medium text-slate-700 dark:text-slate-300">{t.time}: </dt><dd className="inline">{t.today}</dd></div>
                  </dl>
                </div>
                <div className="flex shrink-0 gap-2">
                  <button className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 hover:bg-indigo-500" type="button">
                    {t.summarize}
                  </button>
                  <button className="rounded-xl border border-black/10 bg-white px-4 py-2 text-sm font-semibold hover:bg-slate-50 dark:border-white/10 dark:bg-white/[0.04] dark:hover:bg-white/[0.07]" type="button">
                    {t.quickReply}
                  </button>
                </div>
              </div>
            </div>

            <div className="mt-4 overflow-hidden rounded-[20px] border border-black/5 bg-[#f8fafc] dark:border-white/10 dark:bg-black">
              <div className="mx-auto max-w-3xl px-6 py-8 text-left sm:px-8">
                <div className="mb-6 inline-flex rounded-2xl border border-black/10 bg-white px-4 py-2 text-sm font-semibold text-slate-900 shadow-sm dark:border-white/10 dark:bg-white dark:text-black">
                  AI Mail
                </div>
                <h3 className="max-w-2xl text-3xl font-semibold leading-tight tracking-[-0.04em] text-slate-950 dark:text-white sm:text-4xl">
                  {t.releaseSubject}
                </h3>
                <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600 dark:text-slate-300">{t.releaseSnippet}</p>
                <button className="mt-8 rounded-full bg-slate-950 px-6 py-3 text-sm font-semibold text-white shadow-lg hover:bg-slate-800 dark:bg-white dark:text-black dark:hover:bg-slate-200" type="button">
                  {t.summarize}
                </button>
                <div className="mt-10 rounded-[24px] border border-indigo-100 bg-gradient-to-br from-indigo-100 via-white to-violet-100 p-6 text-left shadow-inner dark:border-indigo-500/20 dark:from-indigo-950 dark:via-zinc-950 dark:to-violet-950">
                  <p className="text-sm font-semibold text-indigo-700 dark:text-indigo-300">{t.summary}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{t.defaultSummary}</p>
                  <p className="mt-4 rounded-2xl bg-white/75 p-4 text-xs leading-5 text-slate-500 dark:bg-white/[0.05] dark:text-slate-400">{t.aiNote}</p>
                </div>
              </div>
            </div>
          </article>
        </section>
      </div>
    </div>
  );
}

function AccountsView({ t }: { t: Copy }) {
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
    <section className="min-w-0 flex-1 p-4 sm:p-6 lg:p-8">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-[-0.04em]">{t.accounts}</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{t.endpoint}: {API_BASE_URL}</p>
        </div>
        <button
          className="rounded-xl border border-black/10 bg-white px-4 py-2 text-sm font-semibold shadow-sm hover:bg-slate-50 dark:border-white/10 dark:bg-white/[0.04] dark:hover:bg-white/[0.07]"
          onClick={() => void accountsQuery.refetch()}
          type="button"
        >
          {t.refresh}
        </button>
      </div>

      <div className="grid gap-5 xl:grid-cols-[420px_minmax(420px,1fr)]">
        <form
          className="rounded-[22px] border border-black/5 bg-white/80 p-5 shadow-xl shadow-slate-200/50 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-900/70 dark:shadow-black/20"
          onSubmit={(event) => {
            event.preventDefault();
            createAccount.mutate();
          }}
        >
          <h2 className="text-base font-semibold tracking-[-0.03em]">{t.newAccount}</h2>
          <div className="mt-5 grid gap-3">
            <TextField label={t.email} onChange={(email) => setForm((current) => ({ ...current, email }))} type="email" value={form.email} />
            <TextField label={t.displayName} onChange={(display_name) => setForm((current) => ({ ...current, display_name }))} value={form.display_name} />
            <TextField label={t.provider} onChange={(provider) => setForm((current) => ({ ...current, provider }))} value={form.provider} />
            <TextField label={t.password} onChange={(password) => setForm((current) => ({ ...current, password }))} type="password" value={form.password} />
            <div className="grid gap-3 sm:grid-cols-[1fr_96px_132px]">
              <TextField label={t.imapHost} onChange={(imap_host) => setForm((current) => ({ ...current, imap_host }))} value={form.imap_host} />
              <NumberField label={t.port} onChange={(imap_port) => setForm((current) => ({ ...current, imap_port }))} value={form.imap_port} />
              <SecurityField label={t.security} onChange={(imap_security) => setForm((current) => ({ ...current, imap_security }))} value={form.imap_security} />
            </div>
            <div className="grid gap-3 sm:grid-cols-[1fr_96px_132px]">
              <TextField label={t.smtpHost} onChange={(smtp_host) => setForm((current) => ({ ...current, smtp_host }))} value={form.smtp_host} />
              <NumberField label={t.port} onChange={(smtp_port) => setForm((current) => ({ ...current, smtp_port }))} value={form.smtp_port} />
              <SecurityField label={t.security} onChange={(smtp_security) => setForm((current) => ({ ...current, smtp_security }))} value={form.smtp_security} />
            </div>
          </div>
          <div className="mt-5 flex flex-wrap gap-2">
            <button className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60" disabled={createAccount.isPending} type="submit">
              {t.save}
            </button>
            <button className="rounded-xl border border-black/10 bg-white px-4 py-2 text-sm font-semibold hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-white/10 dark:bg-white/[0.04] dark:hover:bg-white/[0.07]" disabled={testDraftSettings.isPending} onClick={() => testDraftSettings.mutate()} type="button">
              {t.test}
            </button>
          </div>
          <StatusLine error={createAccount.error ?? testDraftSettings.error} report={formTest} text={createAccount.isSuccess ? t.saved : null} t={t} />
        </form>

        <div className="grid gap-5">
          <section className="overflow-hidden rounded-[22px] border border-black/5 bg-white/80 shadow-xl shadow-slate-200/50 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-900/70 dark:shadow-black/20">
            <div className="flex h-14 items-center justify-between border-b border-black/5 px-5 dark:border-white/10">
              <h2 className="text-sm font-semibold">{t.savedAccounts}</h2>
              <span className="rounded-full bg-indigo-500/10 px-2.5 py-1 text-xs font-medium text-indigo-600 dark:text-indigo-300">{accounts.length}</span>
            </div>
            {accountsQuery.isLoading ? <p className="p-5 text-sm text-slate-500">{t.loading}</p> : null}
            {accountsQuery.error ? <p className="p-5 text-sm text-red-600">{errorMessage(accountsQuery.error, t)}</p> : null}
            <div className="divide-y divide-black/5 dark:divide-white/10">
              {accounts.map((account) => (
                <button
                  className={`flex w-full items-center justify-between gap-3 px-5 py-4 text-left transition hover:bg-black/[0.025] focus:outline-none focus:ring-2 focus:ring-indigo-400/30 dark:hover:bg-white/[0.04] ${
                    account.id === activeAccountId ? 'bg-indigo-500/10 dark:bg-indigo-500/15' : ''
                  }`}
                  key={account.id}
                  onClick={() => {
                    setSelectedAccountId(account.id);
                    setSavedTest(null);
                  }}
                  type="button"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-semibold">{account.email}</span>
                    <span className="mt-1 block truncate text-xs text-slate-500 dark:text-slate-400">
                      {account.imap_host}:{account.imap_port} · {account.imap_security}
                    </span>
                  </span>
                  <span className="shrink-0 rounded-full border border-black/10 px-2.5 py-1 text-xs text-slate-500 dark:border-white/10 dark:text-slate-400">
                    {account.has_secret ? t.stored : t.noSecret}
                  </span>
                </button>
              ))}
            </div>
          </section>

          <section className="overflow-hidden rounded-[22px] border border-black/5 bg-white/80 shadow-xl shadow-slate-200/50 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-900/70 dark:shadow-black/20">
            <div className="flex min-h-14 flex-wrap items-center justify-between gap-2 border-b border-black/5 px-5 py-3 dark:border-white/10">
              <div className="min-w-0">
                <h2 className="truncate text-sm font-semibold">{activeAccount?.email ?? t.folders}</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">{foldersQuery.data?.length ?? 0} {t.folders}</p>
              </div>
              <div className="flex gap-2">
                <button className="rounded-xl border border-black/10 bg-white px-4 py-2 text-sm font-semibold hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-white/10 dark:bg-white/[0.04] dark:hover:bg-white/[0.07]" disabled={activeAccountId === null || testSavedSettings.isPending} onClick={() => activeAccountId !== null && testSavedSettings.mutate(activeAccountId)} type="button">
                  {t.test}
                </button>
                <button className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60" disabled={activeAccountId === null || syncFolders.isPending} onClick={() => activeAccountId !== null && syncFolders.mutate(activeAccountId)} type="button">
                  {t.syncFolders}
                </button>
              </div>
            </div>
            <StatusLine error={testSavedSettings.error ?? syncFolders.error} report={savedTest} text={syncFolders.isSuccess ? t.foldersSynced : null} t={t} />
            {foldersQuery.isLoading ? <p className="p-5 text-sm text-slate-500">{t.loading}</p> : null}
            {foldersQuery.error ? <p className="p-5 text-sm text-red-600">{errorMessage(foldersQuery.error, t)}</p> : null}
            <div className="divide-y divide-black/5 dark:divide-white/10">
              {(foldersQuery.data ?? []).map((folder) => (
                <div className="grid gap-1 px-5 py-4 sm:grid-cols-[160px_1fr_96px]" key={folder.id}>
                  <p className="truncate text-sm font-semibold">{folder.name}</p>
                  <p className="truncate text-sm text-slate-500 dark:text-slate-400">{folder.path}</p>
                  <p className="text-sm text-slate-400">{folder.role ?? t.folder}</p>
                </div>
              ))}
              {activeAccountId !== null && !foldersQuery.isLoading && (foldersQuery.data ?? []).length === 0 ? (
                <p className="p-5 text-sm text-slate-500">{t.noFolders}</p>
              ) : null}
            </div>
          </section>
        </div>
      </div>
    </section>
  );
}

function TextField({ label, onChange, type = 'text', value }: { label: string; onChange: (value: string) => void; type?: string; value: string }) {
  return (
    <label className="grid gap-1.5 text-xs font-semibold text-slate-500 dark:text-slate-400">
      <span>{label}</span>
      <input className="h-11 rounded-xl border border-black/10 bg-white px-3 text-sm text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-indigo-400 focus:ring-4 focus:ring-indigo-500/10 dark:border-white/10 dark:bg-zinc-950 dark:text-white" onChange={(event) => onChange(event.target.value)} type={type} value={value} />
    </label>
  );
}

function NumberField({ label, onChange, value }: { label: string; onChange: (value: number) => void; value: number }) {
  return (
    <label className="grid gap-1.5 text-xs font-semibold text-slate-500 dark:text-slate-400">
      <span>{label}</span>
      <input className="h-11 rounded-xl border border-black/10 bg-white px-3 text-sm text-slate-950 outline-none transition focus:border-indigo-400 focus:ring-4 focus:ring-indigo-500/10 dark:border-white/10 dark:bg-zinc-950 dark:text-white" min={1} max={65535} onChange={(event) => onChange(Number(event.target.value))} type="number" value={value} />
    </label>
  );
}

function SecurityField({ label, onChange, value }: { label: string; onChange: (value: AccountForm['imap_security']) => void; value: AccountForm['imap_security'] }) {
  return (
    <label className="grid gap-1.5 text-xs font-semibold text-slate-500 dark:text-slate-400">
      <span>{label}</span>
      <select className="h-11 rounded-xl border border-black/10 bg-white px-3 text-sm text-slate-950 outline-none transition focus:border-indigo-400 focus:ring-4 focus:ring-indigo-500/10 dark:border-white/10 dark:bg-zinc-950 dark:text-white" onChange={(event) => onChange(event.target.value as AccountForm['imap_security'])} value={value}>
        <option value="ssl">SSL</option>
        <option value="starttls">STARTTLS</option>
        <option value="none">None</option>
      </select>
    </label>
  );
}

function StatusLine({ error, report, text, t }: { error: Error | null; report: ConnectivityReport | null; text: string | null; t: Copy }) {
  if (error) {
    return <p className="px-5 py-3 text-sm text-red-600">{errorMessage(error, t)}</p>;
  }
  if (report) {
    return (
      <p className="px-5 py-3 text-sm text-slate-500 dark:text-slate-400">
        IMAP {report.imap.ok ? 'ok' : report.imap.error} · SMTP {report.smtp.ok ? 'ok' : report.smtp.error}
      </p>
    );
  }
  if (text) {
    return <p className="px-5 py-3 text-sm text-slate-500 dark:text-slate-400">{text}</p>;
  }
  return null;
}

function errorMessage(error: unknown, t: Copy) {
  return error instanceof Error ? error.message : t.requestFailed;
}

export default App;
