import { BrowserRouter, Routes, Route } from 'react-router-dom'

import Home from './pages/Home.jsx'
import Privacy from './pages/Privacy.jsx'
import Terms from './pages/Terms.jsx'
import Start from './pages/Start.jsx'
import Auth from './pages/Auth.jsx'
import NotFound from './pages/NotFound.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/privacy-policy" element={<Privacy />} />
        <Route path="/terms-of-service" element={<Terms />} />
        {/* local stand-ins for app.fourmula.ai, which renders client-side only */}
        <Route path="/start" element={<Start />} />
        <Route path="/auth" element={<Auth />} />
        {/* the original serves its 404 page for any unknown path */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  )
}
