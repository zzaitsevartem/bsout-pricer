'use client';

import React from 'react';
import { useIsFetching, useQueryClient } from '@tanstack/react-query';
import { Header } from '@/widgets/Header/ui/Header';
import { RequireAdmin } from '@/widgets/RequireAdmin/ui/RequireAdmin';
import { AdminSidebar } from '@/app/admin/_components/AdminSidebar';
import { StatsCards } from '@/app/admin/_components/StatsCards';
import { UsersTable } from '@/app/admin/_components/UsersTable';
import { ParsersTable } from '@/app/admin/_components/ParsersTable';

function AdminDashboard() {
  const queryClient = useQueryClient();
  const fetching = useIsFetching({ queryKey: ['admin'] });

  return (
    <div className="flex min-h-[calc(100vh-64px)]">
      <AdminSidebar />

      <main id="dashboard" className="flex-1 p-8 overflow-x-hidden max-lg:p-6 max-md:p-4">
        <div className="flex justify-between items-center mb-8 flex-wrap gap-4">
          <div>
            <h2 className="text-[40px] font-semibold text-slate mb-1" style={{ marginBottom: '4px' }}>Дашборд</h2>
            <p className="text-[15px] text-body-subtle mb-0">Сводка по системе</p>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => queryClient.invalidateQueries({ queryKey: ['admin'] })}
              disabled={fetching > 0}
              className="btn-primary btn-sm disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {fetching > 0 ? 'Обновление…' : 'Обновить'}
            </button>
          </div>
        </div>

        <StatsCards />
        <UsersTable />
        <ParsersTable />
      </main>
    </div>
  );
}

export default function AdminPage() {
  return (
    <>
      <Header />

      <RequireAdmin>
        <AdminDashboard />
      </RequireAdmin>
    </>
  );
}
