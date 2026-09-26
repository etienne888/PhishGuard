export function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
}

export function isStrongEnoughPassword(value: string): boolean {
  return value.length >= 12 && /[A-Z]/.test(value) && /[a-z]/.test(value) && /[0-9]/.test(value)
}
