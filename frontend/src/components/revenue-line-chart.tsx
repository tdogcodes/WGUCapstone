import { useQuery } from '@tanstack/react-query'
import { CartesianGrid, Line, LineChart, YAxis } from 'recharts'
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

interface RevenueRow {
  year_month: string
  revenue: number
}

const LAST_MONTHS = 6

const CHART_CONFIG: ChartConfig = {
  revenue: {
    label: 'Revenue',
    color: 'var(--chart-2)',
  },
}

async function fetchRevenue(): Promise<RevenueRow[]> {
  const res = await fetch('/api/shop/revenue')
  if (!res.ok) {
    throw new Error(`Failed to fetch revenue: ${res.status}`)
  }
  return res.json()
}

export default function RevenueLineChart() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['revenue'],
    queryFn: fetchRevenue,
  })

  if (isLoading) {
    return <div className="flex justify-center p-6">Loading chart...</div>
  }

  if (isError) {
    return (
      <div className="flex justify-center p-6 text-red-600">
        Failed to load revenue.
      </div>
    )
  }

  if (!data?.length) {
    return null
  }

  const chartData = data.slice(-LAST_MONTHS)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Revenue over the last 6 months</CardTitle>
        <CardDescription>
          {chartData[0].year_month} - {chartData[chartData.length - 1].year_month}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={CHART_CONFIG} className="aspect-[4/3] w-full">
          <LineChart
            data={chartData}
            margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
          >
            <CartesianGrid vertical={false} />
            <YAxis
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              tick={{ fontSize: 12 }}
              tickFormatter={(value: number) => `${value.toLocaleString()}`}
            />
            <ChartTooltip
              cursor={false}
              content={
                <ChartTooltipContent
                  indicator="line"
                  formatter={(value, _name, _item, _index, payload) =>
                    `$${Number(value).toLocaleString()} - ${(payload as { year_month?: string } | undefined)?.year_month ?? ''}`
                  }
                />
              }
            />
            <Line
              dataKey="revenue"
              type="natural"
              stroke="var(--color-revenue)"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}