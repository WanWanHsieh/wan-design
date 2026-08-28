export interface ProductVariant {
  id: number
  sku: string | null
  name: string
  price: number
  track_stock: boolean
  stock_quantity: number
  sort_order: number
  is_active: boolean
}

export interface ProductListItem {
  id: number
  sku: string
  name: string
  slug: string
  base_price: number
  status: string
  category_id: number | null
  track_stock: boolean
  stock_quantity: number
  is_featured: boolean
  requires_material: boolean
  has_reference_images: boolean
  sale_price: number | null
  sale_starts_at: string | null
  sale_ends_at: string | null
  is_on_sale: boolean
  effective_price: number
  has_variants: boolean
  variants: ProductVariant[]
  primary_image: string | null
  primary_thumbnail: string | null
}

export interface ProductImage {
  id: number
  storage_key: string
  thumbnail_key: string | null
  alt_text: string | null
  sort_order: number
  is_primary: boolean
  image_type: 'main' | 'reference'
}

export interface ProductDetail {
  id: number
  sku: string
  name: string
  slug: string
  description: string | null
  category_id: number | null
  base_price: number
  status: string
  custom_attributes: Record<string, unknown>
  track_stock: boolean
  stock_quantity: number
  requires_material: boolean
  sale_price: number | null
  sale_starts_at: string | null
  sale_ends_at: string | null
  is_on_sale: boolean
  effective_price: number
  has_variants: boolean
  variants: ProductVariant[]
  images: ProductImage[]
}

export interface MaterialImage {
  id: number
  storage_key: string
  thumbnail_key: string | null
  alt_text: string | null
  sort_order: number
  is_primary: boolean
  image_type: 'fabric' | 'showcase'
}

export interface Material {
  id: number
  code: string | null
  name: string
  price_addon: number
  origin: string | null
  fabric_type: string | null
  images: MaterialImage[]
}

export interface OrderItemResult {
  id: number
  product_name_snapshot: string
  product_thumbnail: string | null
  product_image: string | null
  variant_name_snapshot: string | null
  material_name_snapshot: string | null
  material_thumbnail: string | null
  material_image: string | null
  unit_price: number
  quantity: number
  subtotal: number
  is_completed: boolean
  custom_note: string | null
  extra_charge: number
}

export interface OrderResult {
  id: number
  order_no: string
  real_name: string | null
  contact_source: string | null
  customer_name: string
  phone: string
  shipping_method: string
  shipping_store_code: string | null
  shipping_address: string | null
  expected_delivery_date: string
  total_amount: number
  status: string
  notes: string | null
  adjustment_amount: number
  adjustment_note: string | null
  created_at: string
  items: OrderItemResult[]
}

export interface Announcement {
  message: string
  is_active: boolean
}

export interface Category {
  id: number
  name: string
  slug: string
  description: string | null
  parent_id: number | null
  sort_order: number
  is_active: boolean
}
