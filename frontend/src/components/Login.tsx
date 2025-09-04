import React, { useState } from 'react';
import { auth } from '../services/api';
import './Login.css';

interface LoginProps {
  setIsAuthenticated: (value: boolean) => void;
}

const Login: React.FC<LoginProps> = ({ setIsAuthenticated }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    bankroll: 1000,
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        // Login
        const response = await auth.login(formData.username, formData.password);
        localStorage.setItem('token', response.data.access_token);
        setIsAuthenticated(true);
      } else {
        // Register
        await auth.register(formData);
        // Auto-login after registration
        const loginResponse = await auth.login(formData.username, formData.password);
        localStorage.setItem('token', loginResponse.data.access_token);
        setIsAuthenticated(true);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>🎯 Sean Picks</h1>
        <h2>{isLogin ? 'Login' : 'Register'}</h2>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <input
              type="email"
              placeholder="Email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
            />
          )}
          
          <input
            type="text"
            placeholder="Username"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            required
          />
          
          <input
            type="password"
            placeholder="Password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            required
          />
          
          {!isLogin && (
            <input
              type="number"
              placeholder="Starting Bankroll"
              value={formData.bankroll}
              onChange={(e) => setFormData({ ...formData, bankroll: Number(e.target.value) })}
              required
              min="100"
              step="100"
            />
          )}
          
          <button type="submit" disabled={loading}>
            {loading ? 'Loading...' : isLogin ? 'Login' : 'Register'}
          </button>
        </form>
        
        <p>
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <button 
            className="toggle-button"
            onClick={() => setIsLogin(!isLogin)}
            type="button"
          >
            {isLogin ? 'Register' : 'Login'}
          </button>
        </p>
      </div>
    </div>
  );
};

export default Login;