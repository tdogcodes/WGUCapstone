import { cn } from "@/lib/utils"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export interface ForecastRecord {
  product_id: number
  product_name: string
  category: string
  price: number
  units_sold_last_month: number
  current_stock: number
  predicted_demand: number
  recommendation: "increase" | "decrease" | "maintain"
  adjustment: number
}

function formatRecommendation(record: ForecastRecord) {
  switch (record.recommendation) {
    case "increase":
      return { text: `Increase by ${record.adjustment}`, color: "text-emerald-600" }
    case "decrease":
      return { text: `Decrease by ${Math.abs(record.adjustment)}`, color: "text-red-600" }
    default:
      return { text: "Maintain", color: "text-foreground" }
  }
}

export default function ProductCard({ product }: { product: ForecastRecord }) {
  const rec = formatRecommendation(product)

  return (
    <Card className="w-80">
      <CardHeader>
        <CardTitle>{product.product_name}</CardTitle>
        <CardDescription>{product.category}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        <Row label="Price" value={`$${product.price.toFixed(2)}`} />
        <Row label="Inventory" value={`${product.current_stock} units`} />
        <Row
          label="Predicted demand next month"
          value={`${Math.round(product.predicted_demand)} units`}
        />
        <Row label="Inventory recommendation" value={rec.text} valueClassName={rec.color} />
      </CardContent>
    </Card>
  )
}

function Row({
  label,
  value,
  valueClassName,
}: {
  label: string
  value: string
  valueClassName?: string
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-muted-foreground">{label}</span>
      <span className={cn("font-medium", valueClassName)}>{value}</span>
    </div>
  )
}