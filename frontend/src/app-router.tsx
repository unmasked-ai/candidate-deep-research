import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import App from './App'
import HomePage from './pages/home'

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/app" element={<App />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

