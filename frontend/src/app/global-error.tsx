'use client';

import { useEffect } from 'react';

// Заменяет root layout целиком, поэтому не может опираться на стили из
// layout.tsx и на Header/Footer — они могут быть причиной падения.
// Стили заданы инлайном: страница обязана читаться даже когда layout сломан.
const styles = `
  *, *::before, *::after { box-sizing: border-box; }
  body {
    margin: 0;
    background: #FAF9F5;
    color: #141413;
    font-family: 'DM Sans', 'Raleway', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.5;
  }
  .wrap { max-width: 1200px; margin: 0 auto; padding: 64px 24px; }
  .eyebrow {
    margin: 0 0 8px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em;
    color: #87867F;
  }
  h1 { margin: 0 0 16px; font-size: 40px; font-weight: 600; line-height: 1.15; }
  p { margin: 0 0 16px; font-size: 16px; color: #3D3D3A; max-width: 720px; }
  .hint { font-size: 15px; color: #5E5D59; }
  .actions { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 32px; }
  .btn {
    display: inline-block; padding: 8px 16px; border: 1px solid #141413; border-radius: 999px;
    font-size: 14px; text-decoration: none; cursor: pointer; background: #141413; color: #FAF9F5;
  }
  .btn-secondary { background: transparent; color: #141413; }
  code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
`;

export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <html lang="ru">
      <body>
        <style dangerouslySetInnerHTML={{ __html: styles }} />
        <div className="wrap">
          <p className="eyebrow">Ошибка 500</p>
          <h1>Сайт не удалось загрузить</h1>
          <p>Сбой произошёл на верхнем уровне приложения — перезагрузите страницу.</p>
          <p className="hint">
            Если не помогло, сообщите нам:{' '}
            <a href="mailto:support@bscout.ru">support@bscout.ru</a>
          </p>
          <div className="actions">
            <button type="button" className="btn" onClick={reset}>
              Попробовать снова
            </button>
            <a className="btn btn-secondary" href="/">
              На главную
            </a>
          </div>
        </div>
      </body>
    </html>
  );
}
