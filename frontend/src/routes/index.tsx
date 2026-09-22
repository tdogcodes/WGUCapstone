import { useQuery } from '@tanstack/react-query'
import { createFileRoute } from '@tanstack/react-router'

import ProductCard, { type ForecastRecord } from '@/components/product-card'
import RevenueLineChart from '@/components/revenue-line-chart'
import SalesByCategoryChart from '@/components/sales-by-category-chart'
import TopProductsBarChart from '@/components/top-products-bar-chart'

export const Route = createFileRoute('/')({
  component: Home,
})

async function fetchForecast(): Promise<ForecastRecord[]> {
  const res = await fetch('/api/forecast/product')
  if (!res.ok) {
    throw new Error(`Failed to fetch forecast: ${res.status}`)
  }
  return res.json()
}

function Home() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['forecast'],
    queryFn: fetchForecast,
  })

  if (isLoading) {
    return <div className="p-6">Loading products...</div>
  }

  if (isError) {
    return (
      <div className="p-6">
        <p className="text-red-600">Failed to load forecast data.</p>
        <p className="text-sm text-muted-foreground">{String(error)}</p>
      </div>
    )
  }

  return (
    <>
      <div className="grid gap-6 p-6 lg:grid-cols-3 mx-60 max-h-sm">
        <SalesByCategoryChart />
        <TopProductsBarChart />
        <RevenueLineChart />
      </div>
      <div className="flex justify-center flex-wrap gap-4 p-6 mx-16">
        {data?.map((product) => (
          <ProductCard key={product.product_id} product={product} />
        ))}
      </div>
    </>
  )
}

export default Home