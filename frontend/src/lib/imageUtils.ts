/**
 * Shared image utilities for resizing and processing uploaded images.
 * Used by both TripPlanner (terrain photos) and SearchPanel (product photos).
 */

// Max image dimensions before we resize (keeps payload reasonable)
export const MAX_IMAGE_DIMENSION = 2048
export const MAX_FILE_SIZE_MB = 50  // Generous limit — resizeImage() compresses to ~200KB-1MB output regardless

/**
 * Resize an image to fit within MAX_IMAGE_DIMENSION and return as base64 (no data URI prefix).
 */
export function resizeImage(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const img = new Image()
      img.onload = () => {
        let { width, height } = img
        // Scale down if needed
        if (width > MAX_IMAGE_DIMENSION || height > MAX_IMAGE_DIMENSION) {
          const ratio = Math.min(MAX_IMAGE_DIMENSION / width, MAX_IMAGE_DIMENSION / height)
          width = Math.round(width * ratio)
          height = Math.round(height * ratio)
        }
        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height
        const ctx = canvas.getContext('2d')!
        ctx.drawImage(img, 0, 0, width, height)
        // Return base64 without data URI prefix
        const dataUrl = canvas.toDataURL('image/jpeg', 0.85)
        resolve(dataUrl.split(',')[1])
      }
      img.onerror = reject
      img.src = e.target?.result as string
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}
