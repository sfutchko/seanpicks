import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

// Import components
import Dashboard from './components/Dashboard';
import BetTracker from './components/BetTracker';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/tracker" element={<BetTracker />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;