import { ref } from 'vue'

/**
 * Read the text of a screenshot (SMS, WhatsApp, email) in the browser with
 * Tesseract.js. The library and its French/English language data (~10 MB, then
 * cached by the browser) are only downloaded the first time it is used; the
 * image itself never leaves the device.
 */
export function useOcr() {
  const busy = ref(false)
  const progress = ref(0)

  async function readImage(file: File): Promise<string> {
    busy.value = true
    progress.value = 0
    try {
      const { createWorker } = await import('tesseract.js')
      const worker = await createWorker(['fra', 'eng'], 1, {
        logger: (m: { status: string; progress: number }) => {
          if (m.status === 'recognizing text') progress.value = Math.round(m.progress * 100)
        },
      })
      try {
        const { data } = await worker.recognize(file)
        return data.text.replace(/[ \t]+\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim()
      } finally {
        await worker.terminate()
      }
    } finally {
      busy.value = false
    }
  }

  return { busy, progress, readImage }
}
