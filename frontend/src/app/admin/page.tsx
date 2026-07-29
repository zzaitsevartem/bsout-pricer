'use client';

import { ProtectedRoute } from '@/shared/ui/ProtectedRoute';
import { Header } from '@/widgets/Header/ui/Header';
import { AdminSidebar } from '@/widgets/AdminSidebar/ui/AdminSidebar';
import { AdminDashboard } from '@/widgets/AdminDashboard/ui/AdminDashboard';

function AdminContent() {
  return (
    <>
      <Header adminBadge />
      <div className="flex min-h-[calc(100vh-64px)]">
        <AdminSidebar />
        <AdminDashboard />
      </div>
    </>
  );
}

export default function AdminPage() {
  return (
    <ProtectedRoute>
      <AdminContent />
    </ProtectedRoute>
  );
}
