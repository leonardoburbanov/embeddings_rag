export type Provider = "gemini" | "cohere"

export type Product = {
  id: string
  name: string
  category: string
  price: number
  description: string
  image_url: string
}

export type SearchHit = Product & {
  score: number
}

export type MatchRole = "query" | "text" | "image" | "catalog"

export type MatchPoint = {
  label: string
  x: number
  y: number
  z: number
  role: MatchRole
}

export type MatchExplanation = {
  matched: "text" | "image"
  text_score: number
  image_score: number
  points: MatchPoint[]
}

const priceFormat = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
})

export function formatPrice(price: number): string {
  return priceFormat.format(price)
}

export async function listProducts(): Promise<Product[]> {
  const response = await fetch("/api/products")
  if (!response.ok) {
    throw new Error("No se pudo cargar el catálogo.")
  }
  return response.json() as Promise<Product[]>
}

export async function searchProducts(input: {
  provider: Provider
  query: string
  image: File | null
}): Promise<SearchHit[]> {
  const body = new FormData()
  body.set("provider", input.provider)
  if (input.query.trim()) {
    body.set("query", input.query.trim())
  }
  if (input.image) {
    body.set("image", input.image)
  }
  const response = await fetch("/api/search", { method: "POST", body })
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null
    throw new Error(payload?.detail ?? "La búsqueda no se pudo completar.")
  }
  return response.json() as Promise<SearchHit[]>
}

export async function explainMatch(input: {
  productId: string
  provider: Provider
  query: string
  image: File | null
}): Promise<MatchExplanation> {
  const body = new FormData()
  body.set("provider", input.provider)
  if (input.query.trim()) {
    body.set("query", input.query.trim())
  }
  if (input.image) {
    body.set("image", input.image)
  }
  const response = await fetch(`/api/products/${input.productId}/match`, { method: "POST", body })
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null
    throw new Error(payload?.detail ?? "No se pudo explicar el match.")
  }
  return response.json() as Promise<MatchExplanation>
}
