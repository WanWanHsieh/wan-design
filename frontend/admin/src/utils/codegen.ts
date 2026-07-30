const UNAMBIGUOUS_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

function randomToken(length: number): string {
  let result = ''
  for (let i = 0; i < length; i++) {
    result += UNAMBIGUOUS_CHARS[Math.floor(Math.random() * UNAMBIGUOUS_CHARS.length)]
  }
  return result
}

export function generateSku(prefix: string): string {
  return `${prefix}-${randomToken(6)}`
}

export function generateSlug(prefix: string): string {
  return `${prefix}-${randomToken(6).toLowerCase()}`
}
