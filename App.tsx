// Design philosophy: Signal Atelier — Swiss editorial data design, ink-black surfaces, bone typography, signal teal accents, and paper-first interactions.
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { lazy, Suspense } from "react";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import { TimeframeProvider } from "./contexts/TimeframeContext";

const Home = lazy(() => import("./pages/Home"));
const SignalRoom = lazy(() => import("./pages/SignalRoom"));
const ResearchDesk = lazy(() => import("./pages/ResearchDesk"));
const Management = lazy(() => import("./pages/Management"));
const AuthenticatedAudit = lazy(() => import("./pages/AuthenticatedAudit"));
const AuditMatrix = lazy(() => import("./pages/AuditMatrix"));
const WorkbenchSurface = lazy(() => import("./pages/WorkbenchSurface"));

function RouteLoading() {
  return <main className="min-h-screen bg-[#080b0a] text-[#e9e7df] grid place-items-center" aria-live="polite"><span className="font-mono text-xs tracking-[0.16em] text-[#38c9c2]">LOADING OPERATOR SURFACE…</span></main>;
}

function Router() {
  // make sure to consider if you need authentication for certain routes
  return (
    <Switch>
      <Route path={"/"} component={Home} />
      <Route path={"/overview"} component={Home} />
      <Route path={"/signal-room"} component={SignalRoom} />
      <Route path="/research-desk" component={ResearchDesk} />
      <Route path="/management" component={Management} />
      <Route path="/authenticated-audit" component={AuthenticatedAudit} />
      <Route path="/audit-matrix" component={AuditMatrix} />
      <Route path="/workbench" component={WorkbenchSurface} />
      <Route path="/market-map" component={WorkbenchSurface} />
      <Route path="/risk-lab" component={WorkbenchSurface} />
      <Route path="/replay" component={WorkbenchSurface} />
      <Route path="/audit-log" component={WorkbenchSurface} />
      <Route path="/404" component={NotFound} />
      <Route component={NotFound} />
    </Switch>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="dark">
        <TooltipProvider>
          <TimeframeProvider>
            <Toaster />
            <Suspense fallback={<RouteLoading />}><Router /></Suspense>
          </TimeframeProvider>
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
