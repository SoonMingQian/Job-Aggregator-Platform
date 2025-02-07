import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Header from './components/Header';
import ProfilePage from './pages/ProfilePage'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import CompleteProfile from './pages/CompleteProfile'
import MainPage from './pages/MainPage'
import SearchResultPage from './pages/SearchResultPage'
import EditPersonalInfo from './pages/EditPersonalInfo';
import EditProfessional from './pages/EditProfessional';
import EditContact from './pages/EditContact';
import EditCV from './pages/EditCV';

function App() {
  return (
    <Router>
      <Header />
      <Routes>
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/complete-profile" element={<CompleteProfile />} />
        <Route path="/main" element={<MainPage />} />
        <Route path="/search" element={<SearchResultPage />} />
        <Route path="/edit-profile/personal-info" element={<EditPersonalInfo />} />
        <Route path="/edit-profile/professional" element={<EditProfessional />} />
        <Route path="/edit-profile/contact" element={<EditContact />} />
        <Route path="/edit-profile/cv" element={<EditCV />} />
      </Routes>
    </Router>
  )
}

export default App