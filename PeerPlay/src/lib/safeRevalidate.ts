import { revalidatePath } from 'next/cache'

export function safeRevalidatePath(path: string) {
  try {
    revalidatePath(path)
  } catch {
    // Ignored in non-request contexts (CLI tests, background workers)
  }
}
