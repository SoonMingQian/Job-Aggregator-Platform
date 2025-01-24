import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import ProfilePage from './pages/ProfilePage'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/" element={<div>Home Page</div>} />
      </Routes>
    </Router>
  )
}

export default App