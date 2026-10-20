import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react"
import { ImagePlus, X } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Toaster } from "@/components/ui/sonner"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import {
  explainMatch,
  formatPrice,
  listProducts,
  searchProducts,
  type MatchExplanation,
  type MatchPoint,
  type Product,
  type Provider,
  type SearchHit,
} from "@/lib/api"

const CATEGORIES = [
  { id: "all", label: "Todas" },
  { id: "gafas", label: "Gafas" },
  { id: "armazones", label: "Armazones" },
] as const

type CategoryId = (typeof CATEGORIES)[number]["id"]

const LINKS = [
  { href: "https://www.youtube.com/@LeoBurbanoAI", label: "YouTube" },
  { href: "https://github.com/leonardoburbanov", label: "GitHub" },
  { href: "https://www.linkedin.com/in/leoburbano/", label: "LinkedIn" },
  { href: "https://www.instagram.com/leo.burbano.ai/", label: "Instagram" },
]

function isSearchHit(product: Product | SearchHit): product is SearchHit {
  return "score" in product
}

function projectIso(point: MatchPoint): { sx: number; sy: number } {
  const angle = Math.PI / 6
  return {
    sx: (point.x - point.z) * Math.cos(angle),
    sy: point.y + (point.x + point.z) * Math.sin(angle),
  }
}

function MatchPlot({ points, matched }: { points: MatchPoint[]; matched: "text" | "image" }) {
  const flat = points.map((point) => ({ point, ...projectIso(point) }))
  const xs = flat.map((item) => item.sx)
  const ys = flat.map((item) => item.sy)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  const spanX = maxX - minX || 1
  const spanY = maxY - minY || 1
  const placed = flat.map((item) => ({
    ...item,
    px: 28 + ((item.sx - minX) / spanX) * 264,
    py: 196 - ((item.sy - minY) / spanY) * 156,
  }))
  const query = placed.find((item) => item.point.role === "query")
  const winner = placed.find((item) => item.point.role === matched)

  return (
    <svg viewBox="0 0 320 220" className="mt-4 w-full" role="img" aria-label="Distancia entre la consulta y el embedding">
      <line x1="28" y1="188" x2="92" y2="188" className="stroke-muted-foreground" strokeWidth="1" />
      <line x1="28" y1="188" x2="28" y2="148" className="stroke-muted-foreground" strokeWidth="1" />
      <line x1="28" y1="188" x2="48" y2="204" className="stroke-muted-foreground" strokeWidth="1" />
      <text x="96" y="192" className="fill-muted-foreground text-[10px]">PC1</text>
      <text x="8" y="144" className="fill-muted-foreground text-[10px]">PC2</text>
      <text x="52" y="214" className="fill-muted-foreground text-[10px]">PC3</text>
      {query && winner && (
        <line x1={query.px} y1={query.py} x2={winner.px} y2={winner.py} className="stroke-primary" strokeWidth="1.5" />
      )}
      {placed.map((item) => {
        const role = item.point.role
        const isWinner = role === matched
        const radius = role === "catalog" ? 2.5 : isWinner || role === "query" ? 5 : 4
        const fill = role === "catalog" ? "var(--muted-foreground)" : isWinner || role === "query" ? "var(--primary)" : "var(--foreground)"
        return (
          <g key={`${role}-${item.point.label}`}>
            <circle cx={item.px} cy={item.py} r={radius} fill={fill} opacity={role === "catalog" ? 0.35 : 1} />
            {role !== "catalog" && (
              <text x={item.px + 8} y={item.py + 4} className="fill-foreground text-[11px]">
                {item.point.label}
              </text>
            )}
          </g>
        )
      })}
    </svg>
  )
}

export default function App() {
  const [provider, setProvider] = useState<Provider>("gemini")
  const [query, setQuery] = useState("")
  const [image, setImage] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [category, setCategory] = useState<CategoryId>("all")
  const [items, setItems] = useState<Array<Product | SearchHit>>([])
  const [searching, setSearching] = useState(false)
  const [loading, setLoading] = useState(true)
  const [catalogEmpty, setCatalogEmpty] = useState(false)
  const [matchProduct, setMatchProduct] = useState<SearchHit | null>(null)
  const [match, setMatch] = useState<MatchExplanation | null>(null)
  const [matchLoading, setMatchLoading] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)
  const activeSearch = useRef<{ query: string; image: File | null } | null>(null)

  useEffect(() => {
    let cancelled = false
    listProducts()
      .then((products) => {
        if (cancelled) return
        setItems(products)
        setCatalogEmpty(products.length === 0)
      })
      .catch((error: Error) => {
        if (!cancelled) toast.error(error.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  async function loadCatalog() {
    setLoading(true)
    setSearching(false)
    activeSearch.current = null
    setMatchProduct(null)
    setMatch(null)
    try {
      const products = await listProducts()
      setItems(products)
      setCatalogEmpty(products.length === 0)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo cargar el catálogo.")
    } finally {
      setLoading(false)
    }
  }

  async function runSearch(nextProvider: Provider, nextQuery: string, nextImage: File | null) {
    setLoading(true)
    setSearching(true)
    setMatchProduct(null)
    setMatch(null)
    activeSearch.current = { query: nextQuery, image: nextImage }
    try {
      const hits = await searchProducts({
        provider: nextProvider,
        query: nextQuery,
        image: nextImage,
      })
      setItems(hits)
      setCatalogEmpty(false)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "La búsqueda no se pudo completar.")
    } finally {
      setLoading(false)
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!query.trim() && !image) {
      void loadCatalog()
      return
    }
    void runSearch(provider, query, image)
  }

  function onProviderChange(value: string) {
    if (value !== "gemini" && value !== "cohere") return
    setProvider(value)
    const current = activeSearch.current
    if (current) void runSearch(value, current.query, current.image)
  }

  function onImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null
    setImage(file)
    setPreviewUrl((current) => {
      if (current) URL.revokeObjectURL(current)
      return file ? URL.createObjectURL(file) : null
    })
  }

  function clearImage() {
    setImage(null)
    setPreviewUrl((current) => {
      if (current) URL.revokeObjectURL(current)
      return null
    })
    if (fileRef.current) fileRef.current.value = ""
  }

  function closeMatch() {
    setMatchProduct(null)
    setMatch(null)
    setMatchLoading(false)
  }

  async function openMatch(product: SearchHit) {
    const current = activeSearch.current
    if (!current) return
    setMatchProduct(product)
    setMatch(null)
    setMatchLoading(true)
    try {
      const explanation = await explainMatch({
        productId: product.id,
        provider,
        query: current.query,
        image: current.image,
      })
      setMatch(explanation)
    } catch (error) {
      closeMatch()
      toast.error(error instanceof Error ? error.message : "No se pudo explicar el match.")
    } finally {
      setMatchLoading(false)
    }
  }

  const visible = items.filter((item) => category === "all" || item.category === category)

  return (
    <div className="min-h-svh">
      <Toaster />
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-6xl flex-wrap items-end justify-between gap-6 px-5 py-6">
          <div>
            <p className="font-display text-5xl leading-none tracking-[-0.03em] text-foreground">Lente AI</p>
            <p className="mt-3 max-w-md text-sm text-muted-foreground">
              El mostrador de gafas. Busca con una frase o con una foto.
            </p>
          </div>
          <div>
            <span className="sr-only">Proveedor de embeddings</span>
            <ToggleGroup
              type="single"
              value={provider}
              onValueChange={onProviderChange}
              variant="outline"
              size="sm"
              spacing={0}
              aria-label="Proveedor de embeddings"
            >
              <ToggleGroupItem value="gemini">Gemini</ToggleGroupItem>
              <ToggleGroupItem value="cohere">Cohere</ToggleGroupItem>
            </ToggleGroup>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 py-8">
        <form onSubmit={onSubmit} className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <label className="sr-only" htmlFor="query">
            Buscar gafas
          </label>
          <Input
            id="query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Gafas redondas, carey, para correr..."
            className="h-11 bg-card px-3"
          />
          <div className="flex items-center gap-2">
            <input
              ref={fileRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              className="sr-only"
              onChange={onImage}
            />
            <Button type="button" variant="outline" className="h-11 bg-card" onClick={() => fileRef.current?.click()}>
              <ImagePlus />
              Imagen
            </Button>
            <Button type="submit" className="h-11" disabled={loading}>
              Buscar
            </Button>
          </div>
        </form>

        {previewUrl && (
          <div className="mt-3 flex items-center gap-3">
            <img src={previewUrl} alt="Imagen de búsqueda" className="size-14 object-cover" />
            <Button type="button" variant="ghost" size="sm" onClick={clearImage}>
              <X />
              Quitar imagen
            </Button>
          </div>
        )}

        <div className="mt-6 flex flex-wrap gap-2" role="group" aria-label="Categoría">
          {CATEGORIES.map((item) => {
            const selected = category === item.id
            return (
              <button
                key={item.id}
                type="button"
                aria-pressed={selected}
                onClick={() => setCategory(item.id)}
                className={
                  selected
                    ? "rounded-full bg-primary px-3 py-1 text-sm text-primary-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                    : "rounded-full bg-card px-3 py-1 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                }
              >
                {item.label}
              </button>
            )
          })}
          {searching && (
            <button type="button" className="px-2 py-1 text-sm text-muted-foreground underline-offset-4 hover:underline" onClick={() => void loadCatalog()}>
              Ver todo el mostrador
            </button>
          )}
        </div>

        {loading ? (
          <div className="mt-8 grid grid-cols-2 gap-x-5 gap-y-10 md:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: 8 }, (_, index) => (
              <div key={index}>
                <Skeleton className="aspect-[4/5] w-full" />
                <Skeleton className="mt-3 h-6 w-2/3" />
              </div>
            ))}
          </div>
        ) : visible.length === 0 ? (
          <p className="mt-16 max-w-md text-lg">
            {catalogEmpty
              ? "El mostrador está vacío. Carga los productos con el notebook de este episodio."
              : searching
                ? "Nada coincide con esa búsqueda."
                : "No hay modelos en esta categoría."}
          </p>
        ) : (
          <ul className="mt-8 grid grid-cols-2 gap-x-5 gap-y-10 md:grid-cols-3 lg:grid-cols-4">
            {visible.map((product) => {
              const hit = searching && isSearchHit(product)
              const body = (
                <>
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="aspect-[4/5] w-full bg-card object-cover"
                  />
                  {searching && isSearchHit(product) && (
                    <div className="mt-2">
                      <div className="h-px w-full bg-border" aria-hidden="true">
                        <div
                          className="h-px bg-primary"
                          style={{ width: `${Math.round(Math.min(product.score, 1) * 100)}%` }}
                        />
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {Math.round(product.score * 100)} de similitud
                      </p>
                    </div>
                  )}
                  <div className="mt-3 flex items-baseline justify-between gap-3">
                    <h2 className="font-display text-lg leading-tight tracking-[-0.02em]">{product.name}</h2>
                    <p className="text-sm tabular-nums">{formatPrice(product.price)}</p>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">{product.description}</p>
                </>
              )
              return (
              <li key={product.id}>
                <article>
                  {hit ? (
                    <button
                      type="button"
                      className="block w-full text-left"
                      onClick={() => {
                        if (isSearchHit(product)) void openMatch(product)
                      }}
                    >
                      {body}
                    </button>
                  ) : (
                    body
                  )}
                </article>
              </li>
              )
            })}
          </ul>
        )}
      </main>

      {matchProduct && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-foreground/40 p-4 sm:items-center"
          onClick={closeMatch}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="match-title"
            className="max-h-[90svh] w-full max-w-lg overflow-auto bg-background p-5"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4">
              <h2 id="match-title" className="font-display text-2xl leading-tight">
                {matchProduct.name}
              </h2>
              <Button type="button" variant="ghost" size="sm" onClick={closeMatch}>
                <X />
                Cerrar
              </Button>
            </div>
            {matchLoading || !match ? (
              <p className="mt-6 text-sm text-muted-foreground">Calculando la proyección...</p>
            ) : (
              <>
                <p className="mt-4 text-lg">
                  {match.matched === "text" ? "Hizo match con el texto." : "Hizo match con la imagen."}
                </p>
                <p className="mt-2 text-sm text-muted-foreground">
                  Texto {Math.round(match.text_score * 100)} · Imagen {Math.round(match.image_score * 100)}
                </p>
                <MatchPlot points={match.points} matched={match.matched} />
              </>
            )}
          </div>
        </div>
      )}

      <footer className="mx-auto flex max-w-6xl flex-wrap gap-x-5 gap-y-2 px-5 py-10 text-sm text-muted-foreground">
        {LINKS.map((link) => (
          <a key={link.href} href={link.href} target="_blank" rel="noreferrer" className="underline-offset-4 hover:text-foreground hover:underline">
            {link.label}
          </a>
        ))}
      </footer>
    </div>
  )
}
