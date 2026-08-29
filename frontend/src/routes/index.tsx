import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'

export const Route = createFileRoute('/')({
  component: Home,
})

function Home() {
  const { data, isPending } = useQuery({
    queryFn: () => fetch('http://localhost:8000/api/health').then(res => res.json()),
    queryKey: ['health']
  })

  return (
    <div>
      <h1 className=''>Monorepo App</h1>
      <Button>BUTTON BRUH</Button>
      <p>Status: {isPending ? "Loading..." : data.status}</p>
      <p>Backend says: {isPending ? "Loading..." : data.message}</p>
    </div>
  )
}

export default Home