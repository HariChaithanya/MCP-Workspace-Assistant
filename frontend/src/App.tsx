function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 px-6 py-4">
        <h1 className="text-xl font-semibold tracking-tight">
          MCP Workspace Assistant
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Local AI assistant for developers — Step 1 scaffold
        </p>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-16 text-center">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-10 shadow-xl">
          <p className="text-lg text-slate-300">
            React + TypeScript + Tailwind frontend is running.
          </p>
          <p className="mt-4 text-sm text-slate-500">
            Connect the FastAPI backend at{" "}
            <code className="rounded bg-slate-800 px-2 py-0.5 text-slate-300">
              /health
            </code>{" "}
            in the next steps.
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;
