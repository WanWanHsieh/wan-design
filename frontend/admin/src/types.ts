export interface AdminUser {
  id: number
  email: string
  full_name: string
  is_active: boolean
  permissions: string[]
}

export interface ProductImage {
  id: number
  storage_key: string
  thumbnail_key: string | null
  alt_text: string | null
  sort_order: number
  is_primary: boolean
}

export interface AttributeValue {
  id: number
  attribute_definition_id: number
  value_text: string | null
  value_number: number | null
  value_boolean: boolean | null
}

export interface Product {
  id: number
  sku: string
  name: string
  slug: string
  description: string | null
  category_id: number | null
  base_price: number
  status: string
  custom_attributes: Record<string, string>
  track_stock: boolean
  stock_quantity: number
  is_featured: boolean
  sale_price: number | null
  sale_starts_at: string | null
  sale_ends_at: string | null
  is_on_sale: boolean
  effective_price: number
  images: ProductImage[]
  attribute_values: AttributeValue[]
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
  unit: string
  unit_cost: number
  price_addon: number
  quantity_on_hand: number
  origin: string | null
  fabric_type: string | null
  supplier: string | null
  notes: string | null
  status: string
  custom_attributes: Record<string, string>
  images: MaterialImage[]
}

export interface Permission {
  id: number
  code: string
  description: string | null
}

export interface Role {
  id: number
  name: string
  description: string | null
  permissions: Permission[]
}

export interface OrderItem {
  id: number
  product_id: number | null
  product_name_snapshot: string
  product_thumbnail: string | null
  product_image: string | null
  material_id: number | null
  material_name_snapshot: string
  material_thumbnail: string | null
  material_image: string | null
  unit_price: number
  quantity: number
  subtotal: number
  is_completed: boolean
}

export interface OrderListItem {
  id: number
  order_no: string
  customer_name: string
  phone: string
  shipping_method: string
  shipping_store_code: string | null
  shipping_address: string | null
  expected_delivery_date: string
  total_amount: number
  status: string
  notes: string | null
  created_at: string
  items: OrderItem[]
}

export type Order = OrderListItem
