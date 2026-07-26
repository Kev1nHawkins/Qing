export interface ApiResponse<T> { code: number; message: string; data: T }
export interface PageData<T> { total: number; items: T[]; page: number; pageSize: number }
export interface Entity { id: number; created_at?: string; updated_at?: string }
export interface Culture extends Entity { title: string; slug: string; category: string; summary: string; content: string; cover_image_url: string | null; source_title: string; source_url: string | null; status: string }
export interface Location extends Entity { name: string; address: string; description: string | null; latitude: string; longitude: string; image_url: string | null; culture_item_id: number | null }
export interface RouteTask extends Entity { route_id: number; culture_item_id: number | null; location_id: number; order_no: number; title: string; description: string; task_type: string; question: string | null; options: string[] | null; points: number; latitude: string | null; longitude: string | null; radius_meters: number }
export interface CultureRoute extends Entity { title: string; slug: string; summary: string; cover_image_url: string | null; duration_minutes: number; distance_km: string; status: string; tasks?: RouteTask[] }
export interface CreationTemplate extends Entity { name: string; code: string; description: string; prompt_template: string; options_schema: Record<string, string[]> | null; preview_url: string | null; status: string; culture_item_id: number | null }
export interface Creation extends Entity { user_id: number; template_id: number; culture_item_id: number | null; title: string; input_payload: Record<string, string>; output_url: string | null; description: string | null; status: 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILED'; error_message: string | null; retry_count: number }
export interface Post extends Entity { author_id: number; culture_item_id: number | null; creation_id: number | null; title: string; content: string; cover_image_url: string | null; status: string; like_count: number; comment_count: number; favorite_count: number }
export interface Comment extends Entity { post_id: number; user_id: number; parent_id: number | null; content: string; is_deleted: boolean }
export interface PointRecord extends Entity { amount: number; balance_after: number; reason_type: string; business_key?: string; description: string; created_at: string }
export interface Badge extends Entity { code: string; name: string; description: string; icon_url: string | null; rule_type: string; rule_value: number; is_active: boolean }
export interface UserBadge extends Entity { badge_id: number; awarded_at: string; reason: string }
export interface RouteProgressRecord { recordId: number; taskId: number; status: string; awardedPoints: number; completedAt: string | null; evidenceAssetId: number | null }
export interface RouteProgress {
  routeId: number
  started: boolean
  totalTasks: number
  completedTasks: number
  progressPercent: number
  completedTaskIds: number[]
  records: RouteProgressRecord[]
}
export interface TaskCompletePayload {
  answer?: string
  qr_code?: string
  latitude?: number
  longitude?: number
  file_asset_id?: number
}
export interface TaskSubmission { payload: TaskCompletePayload; photo?: File }
export interface TaskCompleteResult {
  recordId: number
  awardedPoints: number
  pointsTotal?: number
  alreadyCompleted: boolean
  distanceMeters?: number | null
}
export interface ShopCategory { code: string; name: string }
export interface ShopProduct {
  code: string
  name: string
  subtitle: string
  description: string
  category: string
  categoryLabel: string
  points: number
  delivery: string
  limit: 'ONCE' | 'REPEATABLE'
  badge: string
  symbol: string
  accent: string
}
export interface ShopRedeemResult {
  recordId: number
  productCode: string
  productName: string
  cost: number
  pointsTotal: number
  delivery: string
  alreadyRedeemed: boolean
}
export interface ShopRedemption {
  recordId: number
  redemptionId: string
  voucherCode: string
  productCode: string
  productName: string
  subtitle: string
  category: string
  categoryLabel: string
  symbol: string
  accent: string
  cost: number
  delivery: string
  redeemedAt: string
  fulfillment: 'DIGITAL' | 'PICKUP' | 'EXPERIENCE'
  status: 'AVAILABLE' | 'READY_FOR_PICKUP' | 'PENDING_CONFIRMATION'
  statusLabel: string
  actionLabel: string
  instruction: string
}
