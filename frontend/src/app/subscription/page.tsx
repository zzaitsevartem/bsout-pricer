'use client';

import { ProtectedRoute } from '@/shared/ui/ProtectedRoute';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { AccountSidebar } from '@/widgets/AccountSidebar/ui/AccountSidebar';
import { SubscriptionManager } from '@/widgets/SubscriptionManager/ui/SubscriptionManager';

function SubscriptionContent() {
  return (
    <>
      <Header />
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-[264px_1fr] gap-8 py-8 min-h-[calc(100vh-64px)] max-md:grid-cols-1">
          <AccountSidebar active="subscription" />
          <SubscriptionManager />
        </div>
      </div>
      <Footer />
    </>
  );
}

export default function SubscriptionPage() {
  return (
    <ProtectedRoute>
      <SubscriptionContent />
    </ProtectedRoute>
  );
}
