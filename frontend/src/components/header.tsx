import { Link } from "@tanstack/react-router"; // 1. Use TanStack Link
import { cn } from "@/lib/utils";
import { Button } from "@base-ui/react/button";


export default function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-card/60 backdrop-blur-xl backdrop-saturate-150">
      <div className="mx-auto flex h-14 w-full max-w-7xl items-between justify-between gap-3 px-4 sm:px-6">
        <Link
          to="/"
          className="group flex shrink-0 items-center gap-2.5 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-ring/60"
        >
          <span className="text-xl font-bold tracking-tight">
            Analytics Dashboard
          </span>
        </Link>
        <nav aria-label="Primary" className="hidden items-center gap-1 md:flex">
          <Button
            className={cn(
              "relative rounded-full px-3.5 py-1.5 text-md font-medium b-1 bg-primary text-accent transition-colors duration-200 outline-none focus-visible:ring-2 focus-visible:ring-ring/60"
            )}
          >
            Tracy's Ecommerce Store
          </Button>
        </nav>
      </div>
    </header>
  );
}