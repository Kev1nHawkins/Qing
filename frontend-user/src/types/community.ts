export interface CommunityPost {
  id: number
  author_id: number
  author_name?: string | null
  author_avatar_url?: string | null
  culture_item_id?: number | null
  culture_item_title?: string | null
  creation_id?: number | null
  creation_title?: string | null
  creation_preview_url?: string | null
  title: string
  content: string
  cover_image_url?: string | null
  status: string
  like_count: number
  comment_count: number
  favorite_count: number
  tags: string[]
  created_at: string
  updated_at: string
}

export interface CommunityComment {
  id: number
  post_id: number
  user_id: number
  author_name?: string | null
  author_avatar_url?: string | null
  parent_id?: number | null
  content: string
  is_deleted: boolean
  created_at: string
  updated_at: string
}

export interface CultureOption {
  id: number
  title: string
}

export interface CreationOption {
  id: number
  title: string
  status: string
  output_url?: string | null
}

export interface PublishPostPayload {
  title: string
  content: string
  culture_item_id: number | null
  creation_id: number | null
  cover_image_url: string | null
  tags: string[]
}
