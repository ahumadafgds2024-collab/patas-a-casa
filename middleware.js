import { next } from '@vercel/functions';

export const config = {
  matcher: '/mi-cuenta/',
  runtime: 'nodejs',
};

export default function middleware(request) {
  const url = new URL(request.url);
  const code = String(url.searchParams.get('activar') || '')
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '')
    .slice(0, 12);

  if (code) {
    const target = new URL('/mi-cuenta/shared-activate.html', request.url);
    target.searchParams.set('tag', code);
    return Response.redirect(target, 302);
  }

  return next();
}
