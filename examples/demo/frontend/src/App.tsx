import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Sidebar } from "./components";
import { Dashboard, Prices, Forecasts, Historical } from "./pages";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 30000,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div 
          className="min-h-screen flex"
          style={{ backgroundColor: 'var(--bg-primary)' }}
        >
          <Sidebar />
          <main className="flex-1 ml-56">
            <div className="p-6">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/prices" element={<Prices />} />
                <Route path="/forecasts" element={<Forecasts />} />
                <Route path="/historical" element={<Historical />} />
              </Routes>
            </div>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
