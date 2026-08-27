// Vercel Edge Middleware: serves a small pre-rendered HTML with per-page
// og:title/description/image to link-preview crawlers (Facebook, LINE, etc.)
// for /products/:slug and /materials/:id, since those bots don't execute the
// SPA's JavaScript and would otherwise only see the static site-wide tags in
// index.html. Real browsers are untouched and keep loading the normal SPA.

export const config = {
  matcher: ['/products/:slug*', '/materials/:id*'],
}

const BOT_UA_PATTERN =
  /facebookexternalhit|facebot|twitterbot|linkedinbot|slackbot|telegrambot|whatsapp|discordbot|pinterest|redditbot|skypeuripreview|vkshare|line|applebot/i

const API_BASE = 'https://wan-design-backend.onrender.com'
const UPLOADS_BASE = 'https://pub-7d8992ec79004455bb975d4ecd25dd6d.r2.dev'
const SITE_ORIGIN = 'https://wan-design-storefront-sable.vercel.app'
const FALLBACK_IMAGE = `${SITE_ORIGIN}/logo.png`
const SITE_NAME = "Wan's Design 丸藝手作坊"

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => {
    switch (char) {
      case '&':
        return '&amp;'
      case '<':
        return '&lt;'
      case '>':
        return '&gt;'
      case '"':
        return '&quot;'
      default:
        return '&#39;'
    }
  })
}

function renderHtml(options: { title: string; description: string; image: string; url: string }): string {
  const title = escapeHtml(options.title)
  const description = escapeHtml(options.description)
  const image = escapeHtml(options.image)
  const url = escapeHtml(options.url)
  return `<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="${escapeHtml(SITE_NAME)}" />
<meta property="og:title" content="${title}" />
<meta property="og:description" content="${description}" />
<meta property="og:image" content="${image}" />
<meta property="og:url" content="${url}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="${title}" />
<meta name="twitter:description" content="${description}" />
<meta name="twitter:image" content="${image}" />
<title>${title}</title>
</head>
<body></body>
</html>`
}

function htmlResponse(html: string): Response {
  return new Response(html, {
    status: 200,
    headers: { 'content-type': 'text/html; charset=utf-8' },
  })
}

export default async function middleware(request: Request): Promise<Response | undefined> {
  const userAgent = request.headers.get('user-agent') ?? ''
  if (!BOT_UA_PATTERN.test(userAgent)) return undefined

  const url = new URL(request.url)
  const productMatch = url.pathname.match(/^\/products\/([^/]+)\/?$/)
  const materialMatch = url.pathname.match(/^\/materials\/(\d+)\/?$/)

  try {
    if (productMatch) {
      const res = await fetch(`${API_BASE}/api/v1/storefront/products/${productMatch[1]}`)
      if (!res.ok) return undefined
      const product = await res.json()
      const primaryImage =
        product.images?.find((img: { is_primary: boolean }) => img.is_primary) ?? product.images?.[0]
      const image = primaryImage ? `${UPLOADS_BASE}/${primaryImage.storage_key}` : FALLBACK_IMAGE
      const description: string =
        (product.description as string | null)?.slice(0, 100) || '手作客製化商品,可自選布料花色。'
      return htmlResponse(
        renderHtml({
          title: `${product.name} - ${SITE_NAME}`,
          description,
          image,
          url: `${SITE_ORIGIN}${url.pathname}`,
        }),
      )
    }

    if (materialMatch) {
      const res = await fetch(`${API_BASE}/api/v1/storefront/materials/${materialMatch[1]}`)
      if (!res.ok) return undefined
      const material = await res.json()
      const primaryImage =
        material.images?.find((img: { is_primary: boolean }) => img.is_primary) ?? material.images?.[0]
      const image = primaryImage ? `${UPLOADS_BASE}/${primaryImage.storage_key}` : FALLBACK_IMAGE
      const title = material.code ? `${material.code} ${material.name}` : material.name
      return htmlResponse(
        renderHtml({
          title: `${title} - ${SITE_NAME}`,
          description: '手作布料花色參考,歡迎點入官網選購。',
          image,
          url: `${SITE_ORIGIN}${url.pathname}`,
        }),
      )
    }
  } catch {
    return undefined
  }

  return undefined
}
