import { useQuery } from '@tanstack/react-query'
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from 'recharts'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart'

interface TopProductRow {
  product_id: number
  name: string
  category: string
  units_sold: number
  revenue: number
}

interface TopProductsResponse {
  year_month: string
  products: TopProductRow[]
}

const CHART_CONFIG: ChartConfig = {
  units_sold: {
    label: 'Units Sold',
    color: 'var(--chart-1)',
  },
}

async function fetchTopProducts(): Promise<TopProductsResponse> {
  const res = await fetch('/api/shop/top-products')
  if (!res.ok) {
    throw new Error(`Failed to fetch top products: ${res.status}`)
  }
  return res.json()
}

export default function TopProductsBarChart() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['top-products'],
    queryFn: fetchTopProducts,
  })

  if (isLoading) {
    return <div className="flex justify-center p-6">Loading chart...</div>
  }

  if (isError) {
    return (
      <div className="flex justify-center p-6 text-red-600">
        Failed to load top products.
      </div>
    )
  }

  if (!data?.products.length) {
    return null
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Products</CardTitle>
        <CardDescription>Best sellers in {data.year_month}</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={CHART_CONFIG} className="aspect-[4/3] w-full">
          <BarChart data={data.products} layout="vertical" margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
            <CartesianGrid horizontal={false} />
            <XAxis type="number" tickLine={false} axisLine={false} />
            <YAxis
              type="category"
              dataKey="name"
              tickLine={false}
              axisLine={false}
              width={120}
              tick={{ fontSize: 12 }}
            />
            <ChartTooltip
              cursor={false}
              content={<ChartTooltipContent nameKey="name" />}
            />
            <Bar
              dataKey="units_sold"
              fill="var(--color-units_sold)"
              radius={4}
              barSize={24}
            />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}