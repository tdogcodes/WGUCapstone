import { useQuery } from '@tanstack/react-query'
import { SERVERURL } from '../constants.js'

function App() {

  const {data, isPending} = useQuery({
    queryFn: async () => fetch(`${SERVERURL}/api/health`).then(res => res.json()),
    queryKey: ['health']
  })

  return (
    <div>
      <h1>Monorepo App</h1>
      <p>Status: {isPending ? "Loading..." : data.status}</p>
      <p>Backend says: {isPending ? "Loading..." : data.message}</p>
    </div>
  )
}

export default App