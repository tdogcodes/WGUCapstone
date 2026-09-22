import { useQuery } from '@tanstack/react-query'
import { Cell, Pie, PieChart } from 'recharts'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart'

interface SalesByCategoryRow {
  year_month: string
  category: string
  units_sold: number
  revenue: number
}

const PALETTE = [
  'var(--chart-1)',
  'var(--chart-2)',
  'var(--chart-3)',
  'var(--chart-4)',
  'var(--chart-5)',
  '#84cc16',
  '#a78bfa',
  '#f472b6',
  '#38bdf8',
]

const slugify = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-')

async function fetchSalesByCategory(): Promise<SalesByCategoryRow[]> {
  const res = await fetch('/api/shop/sales-by-category')
  if (!res.ok) {
    throw new Error(`Failed to fetch sales by category: ${res.status}`)
  }
  return res.json()
}

export default function SalesByCategoryChart() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['sales-by-category'],
    queryFn: fetchSalesByCategory,
  })

  if (isLoading) {
    return <div className="flex justify-center p-6">Loading chart...</div>
  }

  if (isError) {
    return (
      <div className="flex justify-center p-6 text-red-600">
        Failed to load sales by category.
      </div>
    )
  }

  if (!data?.length) {
    return null
  }

  const latestMonth = data.reduce(
    (max, row) => (row.year_month > max ? row.year_month : max),
    data[0].year_month
  )
  const monthRows = data.filter((row) => row.year_month === latestMonth)

  const totals = new Map<string, number>()
  for (const row of monthRows) {
    totals.set(row.category, (totals.get(row.category) ?? 0) + row.units_sold)
  }

  const chartData = [...totals.entries()]
    .map(([category, units_sold]) => ({ category, units_sold }))
    .sort((a, b) => b.units_sold - a.units_sold)

  const config: ChartConfig = Object.fromEntries(
    chartData.map((entry, index) => [
      slugify(entry.category),
      { label: entry.category, color: PALETTE[index % PALETTE.length] },
    ])
  )

return (
    <Card>
      <CardHeader>
        <CardTitle>Sales by Category</CardTitle>
        <CardDescription>{latestMonth}</CardDescription>
      </CardHeader>
        <CardContent>
          <ChartContainer
            config={config}
            className="mx-auto aspect-square max-h-[260px]"
          >
            <PieChart>
              <ChartTooltip
                cursor={false}
                content={<ChartTooltipContent nameKey="category" />}
              />
              <Pie
                data={chartData}
                dataKey="units_sold"
                nameKey="category"
                innerRadius={60}
                strokeWidth={4}
              >
                {chartData.map((entry) => (
                  <Cell
                    key={entry.category}
                    fill={config[slugify(entry.category)].color}
                  />
                ))}
              </Pie>
            </PieChart>
          </ChartContainer>
        </CardContent>
      </Card>
  )
}