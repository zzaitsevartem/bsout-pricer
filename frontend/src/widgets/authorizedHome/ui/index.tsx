'use client';

import React from 'react';
import { useUnit } from 'effector-react';
import { $isAuth } from '@/shared/config/store';
import { useMe } from '@/models/user';
import { useTrackingUsage } from '@/models/tracking';
import { useUnreadNotificationCount } from '@/models/notification';
import { AuthorizedHero } from './AuthorizedHero';
import { TariffStrip } from './TariffStrip';
import { TrackingOverview } from './TrackingOverview';
import { QuickAccess } from './QuickAccess';
import { NotificationsFeed } from './NotificationsFeed';

export const AuthorizedHome: React.FC = () => {
  const isAuth = useUnit($isAuth);
  const { data: me } = useMe({ enabled: isAuth });
  const { data: usage } = useTrackingUsage({ enabled: isAuth });
  const { data: unread } = useUnreadNotificationCount({ enabled: isAuth });

  return (
    <>
      <AuthorizedHero me={me} used={usage?.used} unread={unread?.unread_count} />
      <TariffStrip />
      <TrackingOverview />
      <QuickAccess used={usage?.used} />
      <NotificationsFeed />
    </>
  );
};
