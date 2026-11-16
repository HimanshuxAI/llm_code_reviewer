import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Nav from "./components/Nav";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Submit from "./pages/Submit";
import Results from "./pages/Results";
import History from "./pages/History";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-black text-white">
        <Nav />
        <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/submit"
              element={
                <ProtectedRoute>
                  <Submit />
                </ProtectedRoute>
              }
            />
            <Route
              path="/results/:id"
              element={
                <ProtectedRoute>
                  <Results />
                </ProtectedRoute>
              }
            />
            <Route
              path="/history"
              element={
                <ProtectedRoute>
                  <History />
                </ProtectedRoute>
              }
            />
            <Route path="/" element={<Navigate to="/submit" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
