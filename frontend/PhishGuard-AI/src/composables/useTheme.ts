import { computed, ref } from 'vue'

const STORAGE_KEY = 'pg-theme'

function initialDark(): boolean {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) return stored === 'dark'
  } catch { /* storage blocked: fall back to the OS setting */ }
  return typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches
}

// Module-level state: every toggle in the app (Navbar, admin header) shares it
const isDark = ref(initialDark())

function apply(dark: boolean) {
  document.documentElement.classList.toggle('dark', dark)
  document.documentElement.style.colorScheme = dark ? 'dark' : 'light'
}
if (typeof document !== 'undefined') apply(isDark.value)

export function useTheme() {
  function setDark(dark: boolean) {
    isDark.value = dark
    apply(dark)
    try { localStorage.setItem(STORAGE_KEY, dark ? 'dark' : 'light') } catch { /* not persisted */ }
  }
  return {
    isDark: computed(() => isDark.value),
    setDark,
    toggleTheme: () => setDark(!isDark.value),
  }
}
