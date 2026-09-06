import campusImage from '@/assets/culture/gzu-innovation.webp'

// Local assets keep the competition demo independent from external image CDNs.
export const visuals = {
  campus: campusImage,
  pavilion: campusImage,
  gate: campusImage,
  kapok: campusImage,
  opera: campusImage,
}
export function cultureVisual(category = '', index = 0) {
  const text = category.toLowerCase()
  if (text.includes('校园') || text.includes('广大')) return visuals.pavilion
  if (text.includes('粤剧') || text.includes('戏曲')) return visuals.opera
  return [visuals.kapok, visuals.campus, visuals.gate][index % 3]
}
