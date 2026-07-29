'use client';

function StatCard({ value, label, change, up }: { value: string; label: string; change: string; up: boolean }) {
  return (
    <div className="p-5 border border-border-light rounded-[24px] bg-ivory-elevated">
      <div className="text-[32px] font-bold text-slate leading-none mb-1">{value}</div>
      <div className="text-[14px] text-body-subtle">{label}</div>
      <p className={`text-[12px] mt-1 mb-0 ${up ? 'text-olive' : 'text-body-subtle'}`}>{change}</p>
    </div>
  );
}

function UsersTable() {
  const rows = [
    { id: '#142', name: 'Иван Петров', email: 'ivan@example.com', tariff: 'Базовый', status: 'Активен', date: '01.06.2026', tariffBadge: 'brand', statusBadge: 'success' },
    { id: '#141', name: 'Анна Смирнова', email: 'anna@example.com', tariff: 'Продвинутый', status: 'Активен', date: '30.05.2026', tariffBadge: 'dark', statusBadge: 'success' },
    { id: '#140', name: 'Олег Кузнецов', email: 'oleg@example.com', tariff: 'Пробный', status: 'Истекает', date: '28.05.2026', tariffBadge: 'default', statusBadge: 'warning' },
    { id: '#139', name: 'Мария Иванова', email: 'maria@example.com', tariff: 'Базовый', status: 'Заблокирован', date: '25.05.2026', tariffBadge: 'brand', statusBadge: 'danger' },
  ];

  const badgeStyle = (type: string) => {
    switch (type) {
      case 'dark': return 'bg-slate text-ivory border-slate';
      case 'brand': return 'bg-ivory-elevated border-[#3D3D3A] text-[#0A0A0A]';
      default: return 'bg-ivory border-border-default text-slate';
    }
  };

  const statusStyle = (type: string) => {
    switch (type) {
      case 'success': return 'bg-[#EDF1E5] border-[#C7D2B0] text-[#4F5C36]';
      case 'warning': return 'bg-[#F4EBD7] border-[#E5D29B] text-[#4A3A12]';
      case 'danger': return 'bg-[#F8E5DD] border-[#E8B6A1] text-[#8E3F22]';
      default: return '';
    }
  };

  return (
    <div className="overflow-x-auto border border-slate bg-ivory mb-8">
      <table className="w-full border-collapse text-[15px]">
        <thead>
          <tr className="bg-ivory-elevated border-b border-slate">
            {['ID', 'Имя', 'Email', 'Тариф', 'Статус', 'Дата регистрации'].map((h) => (
              <th key={h} className="font-montserrat text-[14px] font-medium uppercase tracking-[0.04em] text-body-muted text-left px-4 py-3 whitespace-nowrap">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td className="px-4 py-[14px] border-b border-border-light-subtle font-montserrat text-[14px] text-body">{row.id}</td>
              <td className="px-4 py-[14px] border-b border-border-light-subtle font-semibold text-body">{row.name}</td>
              <td className="px-4 py-[14px] border-b border-border-light-subtle text-body">{row.email}</td>
              <td className="px-4 py-[14px] border-b border-border-light-subtle">
                <span className={`inline-flex items-center text-xs px-2 py-0.5 border ${badgeStyle(row.tariffBadge)}`}>{row.tariff}</span>
              </td>
              <td className="px-4 py-[14px] border-b border-border-light-subtle">
                <span className={`inline-flex items-center text-xs px-2 py-0.5 border ${statusStyle(row.statusBadge)}`}>{row.status}</span>
              </td>
              <td className="px-4 py-[14px] border-b border-border-light-subtle text-[14px] text-body-subtle">{row.date}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ParsersTable() {
  const rows = [
    { store: 'ТГСМ', status: 'Работает', items: '3 421', updated: '12.06.2026 14:30', ok: true },
    { store: 'Профи', status: 'Работает', items: '2 890', updated: '12.06.2026 14:15', ok: true },
    { store: 'Либерти', status: 'Ошибка', items: '1 567', updated: '11.06.2026 23:00', ok: false },
    { store: 'ГринСпарк', status: 'Работает', items: '2 115', updated: '12.06.2026 12:00', ok: true },
    { store: 'Дивизион', status: 'Не активен', items: '2 854', updated: '10.06.2026 18:00', ok: false },
  ];

  const statusStyle = (status: string) => {
    switch (status) {
      case 'Работает': return 'bg-[#EDF1E5] border-[#C7D2B0] text-[#4F5C36]';
      case 'Ошибка': return 'bg-[#F8E5DD] border-[#E8B6A1] text-[#8E3F22]';
      default: return 'bg-[#F4EBD7] border-[#E5D29B] text-[#4A3A12]';
    }
  };

  return (
    <div className="overflow-x-auto border border-slate bg-ivory">
      <table className="w-full border-collapse text-[15px]">
        <thead>
          <tr className="bg-ivory-elevated border-b border-slate">
            {['Магазин', 'Статус', 'Товаров', 'Последнее обновление', 'Действия'].map((h) => (
              <th key={h} className="font-montserrat text-[14px] font-medium uppercase tracking-[0.04em] text-body-muted text-left px-4 py-3 whitespace-nowrap">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.store}>
              <td className="px-4 py-[14px] border-b border-border-light-subtle font-semibold text-body">{row.store}</td>
              <td className="px-4 py-[14px] border-b border-border-light-subtle">
                <span className={`inline-flex items-center text-xs px-2 py-0.5 border ${statusStyle(row.status)}`}>{row.status}</span>
              </td>
              <td className="px-4 py-[14px] border-b border-border-light-subtle text-body">{row.items}</td>
              <td className="px-4 py-[14px] border-b border-border-light-subtle text-[14px] text-body-subtle">{row.updated}</td>
              <td className="px-4 py-[14px] border-b border-border-light-subtle">
                <button className="btn-ghost btn-sm">Запустить</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function AdminDashboard() {
  const stats = [
    { value: '248', label: 'Пользователей', change: '+12 за неделю', up: true },
    { value: '156', label: 'Активных подписок', change: '+8 за неделю', up: true },
    { value: '12 847', label: 'Товаров в базе', change: '+342 за сегодня', up: false },
    { value: '5', label: 'Активных парсеров', change: 'Все работают', up: true },
  ];

  return (
    <main className="flex-1 p-8 overflow-x-hidden max-lg:p-6 max-md:p-4">
      <div className="flex justify-between items-center mb-8 flex-wrap gap-4">
        <div>
          <h2 className="text-[40px] font-semibold text-slate mb-1">Дашборд</h2>
          <p className="text-[15px] text-body-subtle mb-0">Сводка по системе за последние 30 дней</p>
        </div>
        <div className="flex gap-3">
          <button className="btn-secondary btn-sm">Экспорт</button>
          <button className="btn-primary btn-sm">Обновить</button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-8 max-lg:grid-cols-2 max-[480px]:grid-cols-1">
        {stats.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </div>

      <div className="flex justify-between items-center mb-4">
        <h3 className="text-2xl font-semibold text-slate mb-0">Последние пользователи</h3>
        <a href="#" className="btn-arrow">Все пользователи</a>
      </div>

      <UsersTable />

      <div className="flex justify-between items-center mb-4">
        <h3 className="text-2xl font-semibold text-slate mb-0">Парсеры</h3>
        <button className="btn-primary btn-sm">Запустить все</button>
      </div>

      <ParsersTable />
    </main>
  );
}
