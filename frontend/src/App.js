import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
} from 'chart.js';
import { Bar, Pie, Line } from 'react-chartjs-2';
import './App.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Helper function to get auth token
const getAuthHeader = () => {
  const token = localStorage.getItem('auth_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// Login Component
const Login = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [showRegister, setShowRegister] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/auth/login`, credentials);
      localStorage.setItem('auth_token', response.data.access_token);
      localStorage.setItem('user_info', JSON.stringify(response.data.user));
      onLogin(response.data.user);
    } catch (error) {
      setError(error.response?.data?.detail || 'Invalid credentials');
    }
  };

  if (showRegister) {
    return <Register onBack={() => setShowRegister(false)} />;
  }

  if (showForgotPassword) {
    return <ForgotPassword onBack={() => setShowForgotPassword(false)} />;
  }

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">CLIENT SERVICES</h1>
          <p className="text-gray-600 mt-2">Local Data Collection Platform</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Username</label>
            <input
              type="text"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={credentials.username}
              onChange={(e) => setCredentials({...credentials, username: e.target.value})}
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Password</label>
            <input
              type="password"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={credentials.password}
              onChange={(e) => setCredentials({...credentials, password: e.target.value})}
              required
            />
          </div>
          
          {error && <div className="text-red-600 text-sm">{error}</div>}
          
          <button
            type="submit"
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Sign In
          </button>
        </form>

        <div className="mt-6 text-center space-y-2">
          <button
            onClick={() => setShowForgotPassword(true)}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            Forgot Password?
          </button>
          <div className="text-gray-500">|</div>
          <button
            onClick={() => setShowRegister(true)}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            New User? Register Here
          </button>
        </div>
      </div>
    </div>
  );
};
// Register Component
const Register = ({ onBack }) => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    email: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/auth/register`, {
        username: formData.username,
        password: formData.password,
        full_name: formData.full_name,
        email: formData.email
      });

      setSuccess(response.data.message);
      setFormData({
        username: '',
        password: '',
        confirmPassword: '',
        full_name: '',
        email: ''
      });
    } catch (error) {
      setError(error.response?.data?.detail || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Register</h1>
          <p className="text-gray-600 mt-2">Create a new account</p>
        </div>

        {success && (
          <div className="mb-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded">
            {success}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Username *</label>
            <input
              type="text"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={formData.username}
              onChange={(e) => setFormData({...formData, username: e.target.value})}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Full Name</label>
            <input
              type="text"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={formData.full_name}
              onChange={(e) => setFormData({...formData, full_name: e.target.value})}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Password *</label>
            <input
              type="password"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              minLength="6"
              required
            />
            <p className="text-xs text-gray-500 mt-1">Minimum 6 characters</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Confirm Password *</label>
            <input
              type="password"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
              required
            />
          </div>
          
          {error && <div className="text-red-600 text-sm">{error}</div>}
          
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {isLoading ? 'Registering...' : 'Register'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={onBack}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            ← Back to Login
          </button>
        </div>
      </div>
    </div>
  );
};

// Forgot Password Component
const ForgotPassword = ({ onBack }) => {
  const [step, setStep] = useState(1); // 1: enter username, 2: enter reset code
  const [formData, setFormData] = useState({
    username: '',
    reset_code: '',
    new_password: '',
    confirm_password: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleInitiateReset = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/auth/forgot-password`, {
        username: formData.username
      });

      setSuccess(`Reset code: ${response.data.reset_code}`);
      setStep(2);
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to initiate password reset');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCompleteReset = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (formData.new_password !== formData.confirm_password) {
      setError('Passwords do not match');
      return;
    }

    if (formData.new_password.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    setIsLoading(true);
    try {
      await axios.post(`${API}/auth/reset-password`, {
        username: formData.username,
        reset_code: formData.reset_code,
        new_password: formData.new_password
      });

      setSuccess('Password reset successfully! You can now login with your new password.');
      setTimeout(() => {
        onBack();
      }, 3000);
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to reset password');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Reset Password</h1>
          <p className="text-gray-600 mt-2">
            {step === 1 ? 'Enter your username' : 'Enter reset code and new password'}
          </p>
        </div>

        {success && (
          <div className="mb-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded">
            {success}
          </div>
        )}

        {step === 1 ? (
          <form onSubmit={handleInitiateReset} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Username</label>
              <input
                type="text"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
                required
              />
            </div>
            
            {error && <div className="text-red-600 text-sm">{error}</div>}
            
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {isLoading ? 'Generating Reset Code...' : 'Get Reset Code'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleCompleteReset} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Reset Code</label>
              <input
                type="text"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={formData.reset_code}
                onChange={(e) => setFormData({...formData, reset_code: e.target.value})}
                placeholder="Enter the 6-digit reset code"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">New Password</label>
              <input
                type="password"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={formData.new_password}
                onChange={(e) => setFormData({...formData, new_password: e.target.value})}
                minLength="6"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Confirm New Password</label>
              <input
                type="password"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={formData.confirm_password}
                onChange={(e) => setFormData({...formData, confirm_password: e.target.value})}
                required
              />
            </div>
            
            {error && <div className="text-red-600 text-sm">{error}</div>}
            
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {isLoading ? 'Resetting Password...' : 'Reset Password'}
            </button>
          </form>
        )}

        <div className="mt-6 text-center">
          <button
            onClick={onBack}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            ← Back to Login
          </button>
        </div>
      </div>
    </div>
  );
};

// Navigation Component
const Navigation = ({ user, activeTab, setActiveTab, onLogout }) => {
  const getAvailableTabs = () => {
    const allTabs = [
      { id: 'dashboard', label: 'Dashboard' },
      { id: 'users', label: 'Manage Users' },
      { id: 'roles', label: 'Manage Roles' },
      { id: 'locations', label: 'Manage Locations' },
      { id: 'templates', label: 'Manage Templates' },
      { id: 'reports', label: 'Reports' },
      { id: 'submit', label: 'Submit Data' },
      { id: 'statistics', label: 'Statistics' }
    ];

    // Filter tabs based on user permissions
    if (user.page_permissions && user.page_permissions.length > 0) {
      return allTabs.filter(tab => user.page_permissions.includes(tab.id));
    }

    // Fallback to role-based tabs if no permissions defined
    const roleTabs = {
      admin: ['dashboard', 'users', 'roles', 'locations', 'templates', 'reports', 'submit', 'statistics'],
      manager: ['dashboard', 'submit', 'reports'],
      data_entry: ['dashboard', 'submit'],
      statistician: ['dashboard', 'statistics', 'reports']
    };

    const userTabs = roleTabs[user.role] || ['dashboard'];
    return allTabs.filter(tab => userTabs.includes(tab.id));
  };

  const availableTabs = getAvailableTabs();

  return (
    <nav className="bg-blue-600 text-white p-4">
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-6">
          <h1 className="text-xl font-bold">CLIENT SERVICES</h1>
          <div className="flex space-x-4">
            {availableTabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3 py-2 rounded ${activeTab === tab.id ? 'bg-blue-800' : 'hover:bg-blue-700'}`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <span className="text-sm">
            {user.username} ({user.role})
            {user.assigned_location && ` - ${user.assigned_location}`}
          </span>
          <button
            onClick={onLogout}
            className="px-3 py-2 bg-red-600 hover:bg-red-700 rounded text-sm"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
};

// Dashboard Component
const Dashboard = ({ user }) => {
  const [stats, setStats] = useState({ submissions: 0, templates: 0, users: 0 });
  const [submissionsByLocation, setSubmissionsByLocation] = useState([]);
  const [missingReports, setMissingReports] = useState({ deadline: null, missing_locations: [], total_missing: 0 });
  const [deadline, setDeadline] = useState('');
  const [showDeadlineEdit, setShowDeadlineEdit] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState('');

  useEffect(() => {
    fetchStats();
    fetchSubmissionsByLocation();
    fetchMissingReports();
    fetchDeadline();
  }, [user.role, selectedMonth]);

  const fetchStats = async () => {
    try {
      const headers = getAuthHeader();
      const [submissionsRes, templatesRes] = await Promise.all([
        axios.get(`${API}/submissions`, { headers }),
        axios.get(`${API}/templates`, { headers })
      ]);
      
      let usersCount = 0;
      if (user.role === 'admin') {
        const usersRes = await axios.get(`${API}/users`, { headers });
        usersCount = usersRes.data.length;
      }
      
      setStats({
        submissions: submissionsRes.data.length,
        templates: templatesRes.data.length,
        users: usersCount
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchSubmissionsByLocation = async () => {
    try {
      const headers = getAuthHeader();
      const params = selectedMonth ? `?month_year=${selectedMonth}` : '';
      const response = await axios.get(`${API}/dashboard/submissions-by-location${params}`, { headers });
      setSubmissionsByLocation(response.data);
    } catch (error) {
      console.error('Error fetching submissions by location:', error);
    }
  };

  const fetchMissingReports = async () => {
    try {
      const headers = getAuthHeader();
      const response = await axios.get(`${API}/dashboard/missing-reports`, { headers });
      setMissingReports(response.data);
    } catch (error) {
      console.error('Error fetching missing reports:', error);
    }
  };

  const fetchDeadline = async () => {
    try {
      const headers = getAuthHeader();
      const response = await axios.get(`${API}/admin/settings/report_deadline`, { headers });
      if (response.data.setting_value) {
        setDeadline(response.data.setting_value.split('T')[0]); // Extract date part
      }
    } catch (error) {
      console.error('Error fetching deadline:', error);
    }
  };

  const updateDeadline = async () => {
    if (!deadline) {
      alert('Please select a deadline date');
      return;
    }

    try {
      const headers = getAuthHeader();
      const deadlineISO = new Date(deadline).toISOString();
      
      await axios.post(`${API}/admin/settings`, {
        setting_key: 'report_deadline',
        setting_value: deadlineISO,
        description: 'Deadline for monthly report submissions'
      }, { headers });

      alert('Deadline updated successfully!');
      setShowDeadlineEdit(false);
      fetchMissingReports();
    } catch (error) {
      alert('Error updating deadline: ' + (error.response?.data?.detail || error.message));
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'text-green-600';
      case 'reviewed': return 'text-blue-600';
      case 'rejected': return 'text-red-600';
      default: return 'text-yellow-600';
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Dashboard</h2>
        {user.role === 'admin' && (
          <div className="flex items-center space-x-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Filter by Month:</label>
              <input
                type="month"
                className="mt-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
              />
            </div>
            <button
              onClick={() => setShowDeadlineEdit(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
            >
              Set Report Deadline
            </button>
          </div>
        )}
      </div>
      
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-700">Total Submissions</h3>
          <p className="text-3xl font-bold text-blue-600">{stats.submissions}</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-700">Active Templates</h3>
          <p className="text-3xl font-bold text-green-600">{stats.templates}</p>
        </div>
        
        {user.role === 'admin' && (
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-700">Total Users</h3>
            <p className="text-3xl font-bold text-purple-600">{stats.users}</p>
          </div>
        )}
      </div>

      {/* Submissions by Location */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">
            Submissions by Location
            {selectedMonth && <span className="text-sm text-gray-500 ml-2">({selectedMonth})</span>}
          </h3>
          
          {submissionsByLocation.length === 0 ? (
            <p className="text-gray-500">No submissions found for the selected period.</p>
          ) : (
            <div className="space-y-4">
              {submissionsByLocation.map((locationData, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-4">
                  <div className="flex justify-between items-center">
                    <h4 className="font-semibold">{locationData.location}</h4>
                    <span className="text-lg font-bold text-blue-600">{locationData.submission_count}</span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2 mt-2 text-sm">
                    <div className="flex items-center text-green-600">
                      <span className="w-2 h-2 bg-green-600 rounded-full mr-2"></span>
                      {locationData.approved_count} Approved
                    </div>
                    <div className="flex items-center text-blue-600">
                      <span className="w-2 h-2 bg-blue-600 rounded-full mr-2"></span>
                      {locationData.reviewed_count} Reviewed
                    </div>
                    <div className="flex items-center text-yellow-600">
                      <span className="w-2 h-2 bg-yellow-600 rounded-full mr-2"></span>
                      {locationData.submitted_count} Submitted
                    </div>
                    <div className="flex items-center text-red-600">
                      <span className="w-2 h-2 bg-red-600 rounded-full mr-2"></span>
                      {locationData.rejected_count} Rejected
                    </div>
                  </div>
                  
                  {locationData.latest_submission && (
                    <p className="text-xs text-gray-500 mt-1">
                      Latest: {new Date(locationData.latest_submission).toLocaleDateString()}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Missing Reports */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Missing Reports</h3>
            {missingReports.deadline && (
              <span className="text-sm text-gray-500">
                Deadline: {new Date(missingReports.deadline).toLocaleDateString()}
              </span>
            )}
          </div>
          
          {!missingReports.deadline ? (
            <div className="text-center py-4">
              <p className="text-gray-500 mb-3">No deadline set</p>
              {user.role === 'admin' && (
                <button
                  onClick={() => setShowDeadlineEdit(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                >
                  Set Deadline
                </button>
              )}
            </div>
          ) : (
            <div>
              <div className="mb-4 p-3 bg-red-50 border-l-4 border-red-500">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-red-700">
                    {missingReports.total_missing} locations missing reports
                  </span>
                  {user.role === 'admin' && (
                    <button
                      onClick={() => setShowDeadlineEdit(true)}
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      Edit Deadline
                    </button>
                  )}
                </div>
              </div>
              
              {missingReports.missing_locations.length === 0 ? (
                <p className="text-green-600 text-center py-4">
                  ✓ All locations have submitted their reports!
                </p>
              ) : (
                <div className="space-y-2">
                  {missingReports.missing_locations.map((location) => (
                    <div key={location.id} className="flex items-center justify-between p-2 bg-red-50 rounded">
                      <div>
                        <span className="font-medium text-red-800">{location.name}</span>
                        {location.description && (
                          <p className="text-xs text-red-600">{location.description}</p>
                        )}
                      </div>
                      <span className="text-red-600">⚠️</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Deadline Edit Modal */}
      {showDeadlineEdit && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-semibold mb-4">Set Report Deadline</h3>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Deadline Date
                </label>
                <input
                  type="date"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  value={deadline}
                  onChange={(e) => setDeadline(e.target.value)}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Locations that haven't submitted reports after this date will be highlighted
                </p>
              </div>

              <div className="flex justify-end space-x-4">
                <button
                  onClick={() => setShowDeadlineEdit(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  onClick={updateDeadline}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Save Deadline
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Welcome, {user.username}!</h3>
        <p className="text-gray-600">
          You are logged in as a <strong>{user.role}</strong>.
          {user.assigned_location && ` You are assigned to ${user.assigned_location}.`}
        </p>
        <div className="mt-4 text-sm text-gray-500">
          <p>Use the navigation above to access your available features:</p>
          <ul className="list-disc list-inside mt-2">
            {user.role === 'admin' && (
              <>
                <li>Manage users, locations, and data collection templates</li>
                <li>View and export reports from all locations</li>
                <li>Submit data for any location</li>
                <li>Set report deadlines and monitor compliance</li>
              </>
            )}
            {user.role === 'manager' && (
              <>
                <li>Submit and review data for your assigned location</li>
                <li>Generate and export reports for your location</li>
                <li>Monitor submission deadlines</li>
              </>
            )}
            {user.role === 'data_entry' && (
              <>
                <li>Submit data for your assigned location</li>
                <li>View your submitted records</li>
              </>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
};

// Role Management Component (Admin only)
const RoleManagement = () => {
  const [roles, setRoles] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    permissions: []
  });

  const availablePermissions = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'users', label: 'Manage Users' },
    { id: 'roles', label: 'Manage Roles' },
    { id: 'locations', label: 'Manage Locations' },
    { id: 'templates', label: 'Manage Templates' },
    { id: 'reports', label: 'Reports' },
    { id: 'submit', label: 'Submit Data' },
    { id: 'statistics', label: 'Statistics' }
  ];

  useEffect(() => {
    fetchRoles();
  }, []);

  const fetchRoles = async () => {
    try {
      const response = await axios.get(`${API}/roles`, { headers: getAuthHeader() });
      setRoles(response.data || []);
    } catch (error) {
      console.error('Error fetching roles:', error);
    }
  };

  const fetchRoleForEdit = async (roleId) => {
    try {
      const response = await axios.get(`${API}/roles/${roleId}`, { headers: getAuthHeader() });
      const role = response.data;
      setFormData({
        name: role.name,
        display_name: role.display_name,
        description: role.description || '',
        permissions: role.permissions || []
      });
      setEditingRole(role);
      setShowForm(true);
    } catch (error) {
      alert('Error fetching role for editing: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingRole) {
        await axios.put(`${API}/roles/${editingRole.id}`, formData, { headers: getAuthHeader() });
        alert('Role updated successfully!');
      } else {
        await axios.post(`${API}/roles`, formData, { headers: getAuthHeader() });
        alert('Role created successfully!');
      }
      resetForm();
      fetchRoles();
    } catch (error) {
      alert(`Error ${editingRole ? 'updating' : 'creating'} role: ` + (error.response?.data?.detail || error.message));
    }
  };

  const resetForm = () => {
    setFormData({ name: '', display_name: '', description: '', permissions: [] });
    setShowForm(false);
    setEditingRole(null);
  };

  const handleEdit = (role) => {
    fetchRoleForEdit(role.id);
  };

  const handleDelete = async (roleId, roleName, isSystemRole) => {
    if (isSystemRole) {
      alert('System roles cannot be deleted as they are essential for system functionality');
      return;
    }

    if (window.confirm(`Are you sure you want to delete the role "${roleName}"?`)) {
      try {
        await axios.delete(`${API}/roles/${roleId}`, { headers: getAuthHeader() });
        alert('Role deleted successfully!');
        fetchRoles();
      } catch (error) {
        alert('Error deleting role: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  const handlePermissionChange = (permissionId, isChecked) => {
    if (isChecked) {
      setFormData({
        ...formData,
        permissions: [...formData.permissions, permissionId]
      });
    } else {
      setFormData({
        ...formData,
        permissions: formData.permissions.filter(p => p !== permissionId)
      });
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Role Management</h2>
        <button
          onClick={() => {
            resetForm();
            setShowForm(!showForm);
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          {showForm ? 'Cancel' : 'Create New Role'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h3 className="text-lg font-semibold mb-4">
            {editingRole ? `Edit Role: ${editingRole.display_name}` : 'Create New Role'}
            {editingRole?.is_system_role && (
              <span className="ml-2 px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded-full">
                System Role
              </span>
            )}
          </h3>
          {editingRole?.is_system_role && (
            <div className="mb-4 p-3 bg-orange-50 border-l-4 border-orange-400 text-orange-700">
              <p className="text-sm">
                <strong>Note:</strong> You are editing a system role. Changes will affect all users assigned to this role. 
                System roles cannot be deleted but can be modified to meet your organization's needs.
              </p>
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Role Name (ID)</label>
                <input
                  type="text"
                  className={`mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md ${
                    editingRole?.is_system_role ? 'bg-gray-100 cursor-not-allowed' : ''
                  }`}
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value.toLowerCase().replace(/\s+/g, '_')})}
                  placeholder="role_name"
                  disabled={editingRole?.is_system_role}
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  {editingRole?.is_system_role 
                    ? 'System role names cannot be changed to maintain system integrity'
                    : 'Lowercase letters, numbers, and underscores only'
                  }
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Display Name</label>
                <input
                  type="text"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                  value={formData.display_name}
                  onChange={(e) => setFormData({...formData, display_name: e.target.value})}
                  placeholder="Role Display Name"
                  required
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                rows="3"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="Describe the role and its purpose"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">Permissions</label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {availablePermissions.map(permission => (
                  <label key={permission.id} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300"
                      checked={formData.permissions.includes(permission.id)}
                      onChange={(e) => handlePermissionChange(permission.id, e.target.checked)}
                    />
                    <span className="text-sm text-gray-700">{permission.label}</span>
                  </label>
                ))}
              </div>
            </div>
            
            <div className="flex space-x-4">
              <button
                type="submit"
                className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                {editingRole ? 'Update Role' : 'Create Role'}
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="px-6 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <div className="overflow-x-auto">
          <table className="min-w-full table-auto">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Display Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Permissions</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {roles.map(role => (
                <tr key={role.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {role.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {role.display_name}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                    {role.description || 'No description'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    <div className="flex flex-wrap gap-1">
                      {role.permissions?.slice(0, 3).map(permission => (
                        <span key={permission} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                          {permission}
                        </span>
                      ))}
                      {role.permissions?.length > 3 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                          +{role.permissions.length - 3} more
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      role.is_system_role 
                        ? 'bg-red-100 text-red-800' 
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {role.is_system_role ? 'System' : 'Custom'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button
                      onClick={() => handleEdit(role)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(role.id, role.display_name, role.is_system_role)}
                      className={`${
                        role.is_system_role 
                          ? 'text-gray-400 cursor-not-allowed' 
                          : 'text-red-600 hover:text-red-900'
                      }`}
                      disabled={role.is_system_role}
                      title={role.is_system_role ? 'System roles cannot be deleted' : 'Delete role'}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Change Password Component (for all users)
const ChangePassword = ({ user }) => {
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [isChanging, setIsChanging] = useState(false);

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      alert('New passwords do not match');
      return;
    }

    if (passwordData.new_password.length < 6) {
      alert('Password must be at least 6 characters long');
      return;
    }

    if (passwordData.current_password === passwordData.new_password) {
      alert('New password must be different from current password');
      return;
    }

    setIsChanging(true);
    try {
      await axios.post(`${API}/users/change-password`, {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      }, { headers: getAuthHeader() });

      alert('Password changed successfully!');
      setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
    } catch (error) {
      alert('Error changing password: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsChanging(false);
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Change Password</h2>
      
      <div className="max-w-md bg-white p-6 rounded-lg shadow">
        <div className="mb-4 p-3 bg-blue-50 border-l-4 border-blue-400">
          <p className="text-sm text-blue-700">
            <strong>User:</strong> {user.username}<br/>
            <strong>Role:</strong> {user.role}
          </p>
        </div>

        <form onSubmit={handlePasswordChange} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Current Password</label>
            <input
              type="password"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              value={passwordData.current_password}
              onChange={(e) => setPasswordData({...passwordData, current_password: e.target.value})}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">New Password</label>
            <input
              type="password"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              value={passwordData.new_password}
              onChange={(e) => setPasswordData({...passwordData, new_password: e.target.value})}
              minLength="6"
              required
            />
            <p className="text-xs text-gray-500 mt-1">Minimum 6 characters</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Confirm New Password</label>
            <input
              type="password"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              value={passwordData.confirm_password}
              onChange={(e) => setPasswordData({...passwordData, confirm_password: e.target.value})}
              required
            />
          </div>

          <button
            type="submit"
            disabled={isChanging}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {isChanging ? 'Changing Password...' : 'Change Password'}
          </button>
        </form>
      </div>
    </div>
  );
};

// User Management Component (Admin only)
const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [pendingUsers, setPendingUsers] = useState([]);
  const [deletedUsers, setDeletedUsers] = useState([]);
  const [locations, setLocations] = useState([]);
  const [availableRoles, setAvailableRoles] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [showPasswordReset, setShowPasswordReset] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [resettingUser, setResettingUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [activeTab, setActiveTab] = useState('users'); // 'users', 'pending', or 'deleted'
  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    role: 'data_entry',
    assigned_location: '',
    page_permissions: []
  });

  const availablePermissions = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'users', label: 'Manage Users' },
    { id: 'roles', label: 'Manage Roles' },
    { id: 'locations', label: 'Manage Locations' },
    { id: 'templates', label: 'Manage Templates' },
    { id: 'reports', label: 'Reports' },
    { id: 'submit', label: 'Submit Data' },
    { id: 'statistics', label: 'Statistics' }
  ];

  const getDefaultPermissions = (role) => {
    // Try to find the role in available roles first
    const roleData = availableRoles.find(r => r.name === role);
    if (roleData) {
      return roleData.permissions || [];
    }

    // Fallback to hardcoded defaults
    const defaults = {
      admin: ['dashboard', 'users', 'roles', 'locations', 'templates', 'reports', 'submit', 'statistics'],
      manager: ['dashboard', 'submit', 'reports'],
      data_entry: ['dashboard', 'submit'],
      statistician: ['dashboard', 'statistics', 'reports']
    };
    return defaults[role] || [];
  };

  useEffect(() => {
    fetchUsers();
    fetchLocations();
    fetchAvailableRoles();
    fetchPendingUsers();
    fetchDeletedUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`, { headers: getAuthHeader() });
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchLocations = async () => {
    try {
      const response = await axios.get(`${API}/locations`, { headers: getAuthHeader() });
      setLocations(response.data);
    } catch (error) {
      console.error('Error fetching locations:', error);
    }
  };

  const fetchAvailableRoles = async () => {
    try {
      const response = await axios.get(`${API}/roles`, { headers: getAuthHeader() });
      setAvailableRoles(response.data || []);
    } catch (error) {
      console.error('Error fetching roles:', error);
      // Fallback to default roles
      setAvailableRoles([
        { name: 'admin', display_name: 'Administrator' },
        { name: 'manager', display_name: 'Service Hub Manager' },
        { name: 'data_entry', display_name: 'Data Entry Officer' },
        { name: 'statistician', display_name: 'Statistician' }
      ]);
    }
  };
  const fetchPendingUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/pending-users`, { headers: getAuthHeader() });
      setPendingUsers(response.data);
    } catch (error) {
      console.error('Error fetching pending users:', error);
    }
  };

  const fetchDeletedUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/deleted-users`, { headers: getAuthHeader() });
      setDeletedUsers(response.data);
    } catch (error) {
      console.error('Error fetching deleted users:', error);
    }
  };

  const handleApproveUser = async (userId, status, role = 'data_entry', location = '') => {
    try {
      await axios.post(`${API}/admin/approve-user`, {
        user_id: userId,
        status: status,
        role: role,
        assigned_location: location
      }, { headers: getAuthHeader() });
      
      alert(`User ${status} successfully!`);
      fetchPendingUsers();
      fetchUsers();
    } catch (error) {
      alert('Error processing user approval: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleRestoreUser = async (userId) => {
    if (!window.confirm('Are you sure you want to restore this user?')) {
      return;
    }

    try {
      await axios.post(`${API}/admin/restore-user/${userId}`, {}, { headers: getAuthHeader() });
      alert('User restored successfully!');
      fetchDeletedUsers();
      fetchUsers();
    } catch (error) {
      alert('Error restoring user: ' + (error.response?.data?.detail || error.message));
    }
  };

  const fetchUserForEdit = async (userId) => {
    try {
      const response = await axios.get(`${API}/users/${userId}`, { headers: getAuthHeader() });
      const user = response.data;
      setNewUser({
        username: user.username,
        password: '', // Don't prefill password for security
        role: user.role,
        assigned_location: user.assigned_location || '',
        page_permissions: user.page_permissions || getDefaultPermissions(user.role)
      });
      setEditingUser(user);
      setShowForm(true);
    } catch (error) {
      alert('Error fetching user for editing: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      if (editingUser) {
        // Update existing user
        const updateData = {
          username: newUser.username,
          role: newUser.role,
          assigned_location: newUser.assigned_location
        };
        
        // Only include password if it's provided
        if (newUser.password.trim()) {
          updateData.password = newUser.password;
        }
        
        await axios.put(`${API}/users/${editingUser.id}`, updateData, { headers: getAuthHeader() });
        alert('User updated successfully!');
      } else {
        // Create new user
        await axios.post(`${API}/users`, newUser, { headers: getAuthHeader() });
        alert('User created successfully!');
      }
      
      resetForm();
      fetchUsers();
    } catch (error) {
      alert(`Error ${editingUser ? 'updating' : 'creating'} user: ` + (error.response?.data?.detail || error.message));
    }
  };

  const resetForm = () => {
    setNewUser({ username: '', password: '', role: 'data_entry', assigned_location: '', page_permissions: [] });
    setShowForm(false);
    setEditingUser(null);
  };

  const resetPasswordForm = () => {
    setNewPassword('');
    setConfirmPassword('');
    setShowPasswordReset(false);
    setResettingUser(null);
  };

  const handleRoleChange = (newRole) => {
    setNewUser({
      ...newUser, 
      role: newRole,
      page_permissions: getDefaultPermissions(newRole)
    });
  };

  const handlePasswordReset = async (userId, username) => {
    const user = users.find(u => u.id === userId);
    setResettingUser(user);
    setShowPasswordReset(true);
  };

  const submitPasswordReset = async () => {
    if (!newPassword) {
      alert('Please enter a new password');
      return;
    }

    if (newPassword.length < 6) {
      alert('Password must be at least 6 characters long');
      return;
    }

    if (newPassword !== confirmPassword) {
      alert('Passwords do not match');
      return;
    }

    try {
      const response = await axios.post(
        `${API}/users/${resettingUser.id}/reset-password`,
        { new_password: newPassword },
        { headers: getAuthHeader() }
      );

      alert(`Password reset successfully for ${resettingUser.username}`);
      resetPasswordForm();
    } catch (error) {
      alert('Error resetting password: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = (user) => {
    fetchUserForEdit(user.id);
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await axios.delete(`${API}/users/${userId}`, { headers: getAuthHeader() });
        fetchUsers();
        fetchDeletedUsers(); // Refresh deleted users list
      } catch (error) {
        console.error('Error deleting user:', error);
        alert('Error deleting user: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">User Management</h2>
        <button
          onClick={() => {
            resetForm();
            setShowForm(!showForm);
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          {showForm ? 'Cancel' : 'Add New User'}
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('users')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'users'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Active Users ({users.length})
            </button>
            <button
              onClick={() => setActiveTab('pending')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'pending'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Pending Approval ({pendingUsers.length})
            </button>
            <button
              onClick={() => setActiveTab('deleted')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'deleted'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Deleted Users ({deletedUsers.length})
            </button>
          </nav>
        </div>
      </div>

      {showForm && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h3 className="text-lg font-semibold mb-4">
            {editingUser ? `Edit User: ${editingUser.username}` : 'Create New User'}
          </h3>
          <form onSubmit={handleCreateUser} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Username</label>
              <input
                type="text"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                value={newUser.username}
                onChange={(e) => setNewUser({...newUser, username: e.target.value})}
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Password {editingUser && <span className="text-sm text-gray-500">(leave blank to keep current)</span>}
              </label>
              <input
                type="password"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                value={newUser.password}
                onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                required={!editingUser}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Role</label>
              <select
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                value={newUser.role}
                onChange={(e) => handleRoleChange(e.target.value)}
              >
                {availableRoles.map(role => (
                  <option key={role.name} value={role.name}>{role.display_name}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Assigned Location</label>
              <select
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                value={newUser.assigned_location}
                onChange={(e) => setNewUser({...newUser, assigned_location: e.target.value})}
              >
                <option value="">Select Location</option>
                {locations.map(location => (
                  <option key={location.id} value={location.name}>{location.name}</option>
                ))}
              </select>
            </div>
            
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">Page Permissions</label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {availablePermissions.map(permission => (
                  <label key={permission.id} className="flex items-center">
                    <input
                      type="checkbox"
                      className="mr-2"
                      checked={newUser.page_permissions.includes(permission.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setNewUser({
                            ...newUser,
                            page_permissions: [...newUser.page_permissions, permission.id]
                          });
                        } else {
                          setNewUser({
                            ...newUser,
                            page_permissions: newUser.page_permissions.filter(p => p !== permission.id)
                          });
                        }
                      }}
                    />
                    <span className="text-sm">{permission.label}</span>
                  </label>
                ))}
              </div>
            </div>
            
            <div className="md:col-span-2 flex space-x-4">
              <button
                type="submit"
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                {editingUser ? 'Update User' : 'Create User'}
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Password Reset Modal */}
      {showPasswordReset && resettingUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Reset Password</h3>
                <button
                  onClick={resetPasswordForm}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              
              <div className="mb-4 p-3 bg-blue-50 border-l-4 border-blue-400">
                <p className="text-sm text-blue-700">
                  <strong>User:</strong> {resettingUser.username}<br/>
                  <strong>Role:</strong> {availableRoles.find(r => r.name === resettingUser.role)?.display_name || resettingUser.role}
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">New Password</label>
                  <input
                    type="password"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password"
                    minLength="6"
                  />
                  <p className="text-xs text-gray-500 mt-1">Minimum 6 characters</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Confirm Password</label>
                  <input
                    type="password"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm new password"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-4 mt-6">
                <button
                  onClick={resetPasswordForm}
                  className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  onClick={submitPasswordReset}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  Reset Password
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Content based on active tab */}
      {activeTab === 'users' && (
        <div className="bg-white rounded-lg shadow">
          <div className="overflow-x-auto">
            <table className="min-w-full table-auto">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Username</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Assigned Location</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {users.map(user => (
                  <tr key={user.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {user.username}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        user.role === 'admin' ? 'bg-red-100 text-red-800' :
                        user.role === 'manager' ? 'bg-blue-100 text-blue-800' :
                        user.role === 'statistician' ? 'bg-purple-100 text-purple-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {availableRoles.find(r => r.name === user.role)?.display_name || user.role}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.assigned_location || 'None'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <button
                        onClick={() => handleEdit(user)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handlePasswordReset(user.id, user.username)}
                        className="text-orange-600 hover:text-orange-900"
                      >
                        Reset Password
                      </button>
                      <button
                        onClick={() => handleDeleteUser(user.id)}
                        className="text-red-600 hover:text-red-900"
                        disabled={user.username === 'admin'}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pending Users Tab */}
      {activeTab === 'pending' && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">Users Pending Approval</h3>
            {pendingUsers.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No users pending approval</p>
              </div>
            ) : (
              <div className="space-y-4">
                {pendingUsers.map(user => (
                  <div key={user.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 className="text-lg font-medium text-gray-900">{user.username}</h4>
                        <div className="mt-2 space-y-1 text-sm text-gray-600">
                          <p><strong>Full Name:</strong> {user.full_name || 'Not provided'}</p>
                          <p><strong>Email:</strong> {user.email || 'Not provided'}</p>
                          <p><strong>Registered:</strong> {new Date(user.created_at).toLocaleString()}</p>
                          <p><strong>Status:</strong> 
                            <span className="ml-1 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">
                              Pending Approval
                            </span>
                          </p>
                        </div>
                      </div>
                      <div className="ml-4 flex-shrink-0">
                        <div className="space-y-3">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Assign Role</label>
                            <select
                              className="px-3 py-1 border border-gray-300 rounded text-sm"
                              id={`role-${user.id}`}
                              defaultValue="data_entry"
                            >
                              {availableRoles.map(role => (
                                <option key={role.name} value={role.name}>{role.display_name}</option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Assign Location</label>
                            <select
                              className="px-3 py-1 border border-gray-300 rounded text-sm"
                              id={`location-${user.id}`}
                            >
                              <option value="">Select Location</option>
                              {locations.map(location => (
                                <option key={location.id} value={location.name}>{location.name}</option>
                              ))}
                            </select>
                          </div>
                          <div className="flex space-x-2">
                            <button
                              onClick={() => {
                                const role = document.getElementById(`role-${user.id}`).value;
                                const location = document.getElementById(`location-${user.id}`).value;
                                handleApproveUser(user.id, 'approved', role, location);
                              }}
                              className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleApproveUser(user.id, 'rejected')}
                              className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                            >
                              Reject
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Deleted Users Tab */}
      {activeTab === 'deleted' && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">Deleted Users</h3>
            {deletedUsers.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No deleted users</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full table-auto">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Username</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Assigned Location</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Deleted Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Deleted By</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {deletedUsers.map(user => (
                      <tr key={user.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {user.username}
                          <span className="ml-2 px-2 py-1 bg-red-100 text-red-800 text-xs rounded">
                            Deleted
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            user.role === 'admin' ? 'bg-red-100 text-red-800' :
                            user.role === 'manager' ? 'bg-blue-100 text-blue-800' :
                            user.role === 'statistician' ? 'bg-purple-100 text-purple-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {availableRoles.find(r => r.name === user.role)?.display_name || user.role}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {user.assigned_location || 'None'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {user.deleted_at ? new Date(user.deleted_at).toLocaleString() : 'Unknown'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {user.deleted_by ? 
                            users.find(u => u.id === user.deleted_by)?.username || 'Unknown Admin' : 
                            'Unknown'
                          }
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                          <button
                            onClick={() => handleRestoreUser(user.id)}
                            className="text-green-600 hover:text-green-900"
                            disabled={user.username === 'admin'}
                            title={user.username === 'admin' ? 'Admin user cannot be restored' : 'Restore user'}
                          >
                            Restore
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Location Management Component (Admin only)
const LocationManagement = () => {
  const [locations, setLocations] = useState([]);
  const [deletedLocations, setDeletedLocations] = useState([]);
  const [activeTab, setActiveTab] = useState('active');
  const [showForm, setShowForm] = useState(false);
  const [editingLocation, setEditingLocation] = useState(null);
  const [formData, setFormData] = useState({ name: '', description: '' });

  useEffect(() => {
    fetchLocations();
    fetchDeletedLocations();
  }, []);

  const fetchLocations = async () => {
    try {
      const response = await axios.get(`${API}/locations`, { headers: getAuthHeader() });
      setLocations(response.data);
    } catch (error) {
      console.error('Error fetching locations:', error);
    }
  };

  const fetchDeletedLocations = async () => {
    try {
      const response = await axios.get(`${API}/locations/deleted`, { headers: getAuthHeader() });
      setDeletedLocations(response.data);
    } catch (error) {
      console.error('Error fetching deleted locations:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingLocation) {
        await axios.put(`${API}/locations/${editingLocation.id}`, formData, { headers: getAuthHeader() });
      } else {
        await axios.post(`${API}/locations`, formData, { headers: getAuthHeader() });
      }
      setFormData({ name: '', description: '' });
      setShowForm(false);
      setEditingLocation(null);
      fetchLocations();
    } catch (error) {
      alert('Error saving location: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = (location) => {
    setEditingLocation(location);
    setFormData({ name: location.name, description: location.description || '' });
    setShowForm(true);
  };

  const handleDelete = async (locationId) => {
    if (window.confirm('Are you sure you want to delete this location?')) {
      try {
        await axios.delete(`${API}/locations/${locationId}`, { headers: getAuthHeader() });
        fetchLocations();
        fetchDeletedLocations();
      } catch (error) {
        console.error('Error deleting location:', error);
      }
    }
  };

  const handleRestore = async (locationId) => {
    if (window.confirm('Are you sure you want to restore this location?')) {
      try {
        await axios.post(`${API}/locations/${locationId}/restore`, {}, { headers: getAuthHeader() });
        fetchLocations();
        fetchDeletedLocations();
        alert('Location restored successfully');
      } catch (error) {
        alert('Error restoring location: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Service Hub Locations</h2>
        <button
          onClick={() => {
            setShowForm(!showForm);
            setEditingLocation(null);
            setFormData({ name: '', description: '' });
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          {showForm ? 'Cancel' : 'Add New Location'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h3 className="text-lg font-semibold mb-4">
            {editingLocation ? 'Edit Location' : 'Create New Location'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Location Name</label>
              <input
                type="text"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                rows="3"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
              />
            </div>
            
            <button
              type="submit"
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              {editingLocation ? 'Update Location' : 'Create Location'}
            </button>
          </form>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('active')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'active'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Active Locations ({locations.length})
            </button>
            <button
              onClick={() => setActiveTab('deleted')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'deleted'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Deleted Locations ({deletedLocations.length})
            </button>
          </nav>
        </div>
      </div>

      {/* Active Locations Tab */}
      {activeTab === 'active' && (
        <div className="bg-white rounded-lg shadow">
          <div className="overflow-x-auto">
            <table className="min-w-full table-auto">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {locations.map(location => (
                  <tr key={location.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {location.name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {location.description || 'No description'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(location.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <button
                        onClick={() => handleEdit(location)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(location.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Deleted Locations Tab */}
      {activeTab === 'deleted' && (
        <div className="bg-white rounded-lg shadow">
          <div className="overflow-x-auto">
            <table className="min-w-full table-auto">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {deletedLocations.map(location => (
                  <tr key={location.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {location.name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {location.description || 'No description'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(location.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => handleRestore(location.id)}
                        className="text-green-600 hover:text-green-900"
                      >
                        Restore
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

// Template Management Component (Admin only)
const TemplateManagement = () => {
  const [templates, setTemplates] = useState([]);
  const [deletedTemplates, setDeletedTemplates] = useState([]);
  const [activeTab, setActiveTab] = useState('active');
  const [locations, setLocations] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    fields: [],
    assigned_locations: []
  });

  useEffect(() => {
    fetchTemplates();
    fetchDeletedTemplates();
    fetchLocations();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/templates`, { headers: getAuthHeader() });
      setTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  const fetchDeletedTemplates = async () => {
    try {
      const response = await axios.get(`${API}/templates/deleted`, { headers: getAuthHeader() });
      setDeletedTemplates(response.data);
    } catch (error) {
      console.error('Error fetching deleted templates:', error);
    }
  };

  const fetchLocations = async () => {
    try {
      const response = await axios.get(`${API}/locations`, { headers: getAuthHeader() });
      setLocations(response.data);
    } catch (error) {
      console.error('Error fetching locations:', error);
    }
  };

  const fetchTemplateForEdit = async (templateId) => {
    try {
      const response = await axios.get(`${API}/templates/${templateId}`, { headers: getAuthHeader() });
      const template = response.data;
      setFormData({
        name: template.name,
        description: template.description || '',
        fields: template.fields || [],
        assigned_locations: template.assigned_locations || []
      });
      setEditingTemplate(template);
      setShowForm(true);
    } catch (error) {
      alert('Error fetching template: ' + (error.response?.data?.detail || error.message));
    }
  };

  const addField = () => {
    setFormData({
      ...formData,
      fields: [...formData.fields, { name: '', type: 'text', label: '', required: false }]
    });
  };

  const updateField = (index, field) => {
    const newFields = [...formData.fields];
    newFields[index] = field;
    setFormData({ ...formData, fields: newFields });
  };

  const removeField = (index) => {
    const newFields = formData.fields.filter((_, i) => i !== index);
    setFormData({ ...formData, fields: newFields });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingTemplate) {
        await axios.put(`${API}/templates/${editingTemplate.id}`, formData, { headers: getAuthHeader() });
        alert('Template updated successfully!');
      } else {
        await axios.post(`${API}/templates`, formData, { headers: getAuthHeader() });
        alert('Template created successfully!');
      }
      resetForm();
      fetchTemplates();
    } catch (error) {
      alert(`Error ${editingTemplate ? 'updating' : 'creating'} template: ` + (error.response?.data?.detail || error.message));
    }
  };

  const resetForm = () => {
    setFormData({ name: '', description: '', fields: [], assigned_locations: [] });
    setShowForm(false);
    setEditingTemplate(null);
  };

  const handleEdit = (template) => {
    fetchTemplateForEdit(template.id);
  };

  const handleDelete = async (templateId) => {
    if (window.confirm('Are you sure you want to delete this template?')) {
      try {
        await axios.delete(`${API}/templates/${templateId}`, { headers: getAuthHeader() });
        fetchTemplates();
        fetchDeletedTemplates();
      } catch (error) {
        console.error('Error deleting template:', error);
      }
    }
  };

  const handleRestore = async (templateId) => {
    if (window.confirm('Are you sure you want to restore this template?')) {
      try {
        await axios.post(`${API}/templates/${templateId}/restore`, {}, { headers: getAuthHeader() });
        fetchTemplates();
        fetchDeletedTemplates();
        alert('Template restored successfully');
      } catch (error) {
        alert('Error restoring template: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Data Collection Templates</h2>
        <button
          onClick={() => {
            resetForm();
            setShowForm(!showForm);
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          {showForm ? 'Cancel' : 'Create New Template'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h3 className="text-lg font-semibold mb-4">
            {editingTemplate ? `Edit Template: ${editingTemplate.name}` : 'Create New Template'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Template Name</label>
                <input
                  type="text"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Assigned Locations</label>
                <select
                  multiple
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md h-20"
                  value={formData.assigned_locations}
                  onChange={(e) => setFormData({
                    ...formData,
                    assigned_locations: Array.from(e.target.selectedOptions, option => option.value)
                  })}
                >
                  {locations.map(location => (
                    <option key={location.id} value={location.name}>{location.name}</option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">Hold Ctrl/Cmd to select multiple</p>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                rows="2"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-4">
                <label className="block text-sm font-medium text-gray-700">Form Fields</label>
                <button
                  type="button"
                  onClick={addField}
                  className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                >
                  Add Field
                </button>
              </div>
              
              {formData.fields.map((field, index) => (
                <div key={index} className="border p-4 rounded mb-4 bg-gray-50">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Field Name</label>
                      <input
                        type="text"
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        value={field.name}
                        onChange={(e) => updateField(index, {...field, name: e.target.value})}
                        placeholder="field_name"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Label</label>
                      <input
                        type="text"
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        value={field.label}
                        onChange={(e) => updateField(index, {...field, label: e.target.value})}
                        placeholder="Display Label"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Type</label>
                      <select
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        value={field.type}
                        onChange={(e) => updateField(index, {...field, type: e.target.value})}
                      >
                        <option value="text">Text</option>
                        <option value="number">Number</option>
                        <option value="date">Date</option>
                        <option value="textarea">Textarea</option>
                        <option value="select">Dropdown</option>
                        <option value="file">File Upload</option>
                      </select>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          className="mr-2"
                          checked={field.required || false}
                          onChange={(e) => updateField(index, {...field, required: e.target.checked})}
                        />
                        <span className="text-sm text-gray-700">Required</span>
                      </label>
                      <button
                        type="button"
                        onClick={() => removeField(index)}
                        className="text-red-600 hover:text-red-900 text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                  
                  {field.type === 'select' && (
                    <div className="mt-3">
                      <label className="block text-sm font-medium text-gray-700">Options (comma-separated)</label>
                      <input
                        type="text"
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        value={field.options?.join(', ') || ''}
                        onChange={(e) => updateField(index, {
                          ...field, 
                          options: e.target.value.split(',').map(opt => opt.trim()).filter(opt => opt)
                        })}
                        placeholder="Option 1, Option 2, Option 3"
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            <div className="flex space-x-4">
              <button
                type="submit"
                className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                {editingTemplate ? 'Update Template' : 'Create Template'}
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="px-6 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <div className="overflow-x-auto">
          <table className="min-w-full table-auto">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fields</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Locations</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {templates.map(template => (
                <tr key={template.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {template.name}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {template.description || 'No description'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {template.fields.length} fields
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {template.assigned_locations.join(', ') || 'None'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(template.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button
                      onClick={() => handleEdit(template)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(template.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Data Submission Component
const DataSubmission = ({ user }) => {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [formData, setFormData] = useState({});
  const [monthYear, setMonthYear] = useState('');
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchTemplates();
    // Set current month/year as default
    const now = new Date();
    setMonthYear(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`);
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/templates`, { headers: getAuthHeader() });
      setTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  const handleFileUpload = async (file, fieldName) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API}/upload`, formData, {
        headers: {
          ...getAuthHeader(),
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setFormData(prev => ({
        ...prev,
        [fieldName]: response.data.filename
      }));
    } catch (error) {
      alert('Error uploading file: ' + (error.response?.data?.detail || error.message));
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const submissionData = {
        template_id: selectedTemplate.id,
        service_location: user.assigned_location || formData.service_location,
        month_year: monthYear,
        form_data: formData
      };

      await axios.post(`${API}/submissions`, submissionData, { headers: getAuthHeader() });
      alert('Data submitted successfully!');
      setFormData({});
      setSelectedTemplate(null);
    } catch (error) {
      alert('Error submitting data: ' + (error.response?.data?.detail || error.message));
    }
  };

  const renderFormField = (field) => {
    const commonProps = {
      className: "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md",
      value: formData[field.name] || '',
      onChange: (e) => setFormData({...formData, [field.name]: e.target.value}),
      required: field.required
    };

    switch (field.type) {
      case 'textarea':
        return <textarea {...commonProps} rows="3" />;
      case 'number':
        return <input type="number" {...commonProps} />;
      case 'date':
        return <input type="date" {...commonProps} />;
      case 'select':
        return (
          <select {...commonProps}>
            <option value="">Select an option</option>
            {field.options?.map((option, idx) => (
              <option key={idx} value={option}>{option}</option>
            ))}
          </select>
        );
      case 'file':
        return (
          <div>
            <input
              type="file"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              onChange={(e) => e.target.files[0] && handleFileUpload(e.target.files[0], field.name)}
              accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.csv"
            />
            {uploading && <p className="text-sm text-blue-600 mt-1">Uploading...</p>}
            {formData[field.name] && (
              <p className="text-sm text-green-600 mt-1">File uploaded: {formData[field.name]}</p>
            )}
          </div>
        );
      default:
        return <input type="text" {...commonProps} />;
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Submit Data</h2>

      {!selectedTemplate ? (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Select Template</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map(template => (
              <div
                key={template.id}
                className="border rounded-lg p-4 cursor-pointer hover:bg-gray-50"
                onClick={() => setSelectedTemplate(template)}
              >
                <h4 className="font-semibold">{template.name}</h4>
                <p className="text-sm text-gray-600 mt-2">{template.description}</p>
                <p className="text-xs text-gray-500 mt-2">{template.fields.length} fields</p>
              </div>
            ))}
          </div>
          {templates.length === 0 && (
            <p className="text-gray-500">No templates available for your location.</p>
          )}
        </div>
      ) : (
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold">{selectedTemplate.name}</h3>
            <button
              onClick={() => setSelectedTemplate(null)}
              className="px-3 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Back to Templates
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Month/Year</label>
                <input
                  type="month"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                  value={monthYear}
                  onChange={(e) => setMonthYear(e.target.value)}
                  required
                />
              </div>
              
              {user.role === 'admin' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Service Location</label>
                  <select
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                    value={formData.service_location || ''}
                    onChange={(e) => setFormData({...formData, service_location: e.target.value})}
                    required
                  >
                    <option value="">Select Location</option>
                    {selectedTemplate.assigned_locations.map(location => (
                      <option key={location} value={location}>{location}</option>
                    ))}
                  </select>
                </div>
              )}
              
              {user.assigned_location && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Service Location</label>
                  <input
                    type="text"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100"
                    value={user.assigned_location}
                    readOnly
                  />
                </div>
              )}
            </div>

            <div className="space-y-4">
              {selectedTemplate.fields.map((field, index) => (
                <div key={index}>
                  <label className="block text-sm font-medium text-gray-700">
                    {field.label}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  {renderFormField(field)}
                </div>
              ))}
            </div>

            <button
              type="submit"
              className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700"
              disabled={uploading}
            >
              Submit Data
            </button>
          </form>
        </div>
      )}
    </div>
  );
};

// Reports Component
const Reports = ({ user }) => {
  const [submissions, setSubmissions] = useState([]);
  const [locations, setLocations] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [editingSubmission, setEditingSubmission] = useState(null);
  const [editFormData, setEditFormData] = useState({});
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [activeEditTab, setActiveEditTab] = useState('edit'); // 'edit' or 'delete'
  const [deleteConfirmed, setDeleteConfirmed] = useState(false);
  const [summaryData, setSummaryData] = useState({
    byTemplate: {},
    byLocation: {},
    byMonth: {},
    byUser: {},
    byStatus: {},
    byDate: {}
  });
  const [activeView, setActiveView] = useState('summary'); // 'summary' or 'detailed'
  const [filters, setFilters] = useState({
    location: '',
    month_year: '',
    template_id: '',
    submitted_by: '',
    status: ''
  });

  useEffect(() => {
    fetchSubmissions();
    fetchLocations();
    fetchTemplates();
    fetchUsers();
  }, [filters]);

  useEffect(() => {
    generateSummaryData();
  }, [submissions]);

  const fetchSubmissions = async () => {
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const response = await axios.get(`${API}/submissions-detailed?${params}`, { headers: getAuthHeader() });
      setSubmissions(response.data || []);
    } catch (error) {
      console.error('Error fetching submissions:', error);
      // Fallback to regular submissions if detailed endpoint fails
      try {
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
          if (value) params.append(key, value);
        });
        const response = await axios.get(`${API}/submissions?${params}`, { headers: getAuthHeader() });
        const regularSubmissions = response.data || [];
        // Add username lookup for fallback
        for (let submission of regularSubmissions) {
          submission.submitted_by_username = 'Loading...';
        }
        setSubmissions(regularSubmissions);
      } catch (fallbackError) {
        console.error('Error fetching regular submissions:', fallbackError);
        setSubmissions([]);
      }
    }
  };

  const fetchLocations = async () => {
    try {
      const response = await axios.get(`${API}/locations`, { headers: getAuthHeader() });
      setLocations(response.data || []);
    } catch (error) {
      console.error('Error fetching locations:', error);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/templates`, { headers: getAuthHeader() });
      setTemplates(response.data || []);
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      if (user.role === 'admin') {
        const response = await axios.get(`${API}/users`, { headers: getAuthHeader() });
        setUsers(response.data || []);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const generateSummaryData = () => {
    const summary = {
      byTemplate: {},
      byLocation: {},
      byMonth: {},
      byUser: {},
      byStatus: {},
      byDate: {}
    };

    submissions.forEach(submission => {
      // By Template
      const templateName = getTemplateById(submission.template_id)?.name || 'Unknown Template';
      summary.byTemplate[templateName] = (summary.byTemplate[templateName] || 0) + 1;

      // By Location
      summary.byLocation[submission.service_location] = (summary.byLocation[submission.service_location] || 0) + 1;

      // By Month/Year
      summary.byMonth[submission.month_year] = (summary.byMonth[submission.month_year] || 0) + 1;

      // By User
      const username = submission.submitted_by_username || 'Unknown User';
      summary.byUser[username] = (summary.byUser[username] || 0) + 1;

      // By Status
      summary.byStatus[submission.status] = (summary.byStatus[submission.status] || 0) + 1;

      // By Date (submitted date)
      const submitDate = new Date(submission.submitted_at).toLocaleDateString();
      summary.byDate[submitDate] = (summary.byDate[submitDate] || 0) + 1;
    });

    setSummaryData(summary);
  };

  const fetchSubmissionDetail = async (submissionId) => {
    try {
      const response = await axios.get(`${API}/submissions/${submissionId}`, { headers: getAuthHeader() });
      setSelectedSubmission(response.data);
      setShowDetailModal(true);
    } catch (error) {
      alert('Error fetching submission details: ' + (error.response?.data?.detail || error.message));
    }
  };

  const startEditSubmission = async (submissionId) => {
    try {
      const response = await axios.get(`${API}/submissions/${submissionId}`, { headers: getAuthHeader() });
      setEditingSubmission(response.data);
      setEditFormData(response.data.form_data || {});
      setActiveEditTab('edit'); // Reset to edit tab
    } catch (error) {
      alert('Error fetching submission for editing: ' + (error.response?.data?.detail || error.message));
    }
  };

  const deleteSubmission = async () => {
    if (!editingSubmission) return;
    
    const confirmText = `Are you sure you want to delete this submission?\n\nDetails:\n- Template: ${getTemplateById(editingSubmission.template_id)?.name}\n- Location: ${editingSubmission.service_location}\n- Month/Year: ${editingSubmission.month_year}\n- Submitted by: ${editingSubmission.submitted_by_username || 'Unknown'}\n\nThis action cannot be undone.`;
    
    if (window.confirm(confirmText)) {
      try {
        const response = await axios.delete(`${API}/submissions/${editingSubmission.id}`, { headers: getAuthHeader() });
        alert('Submission deleted successfully!');
        setEditingSubmission(null);
        setEditFormData({});
        fetchSubmissions(); // Refresh the submissions list
      } catch (error) {
        alert('Error deleting submission: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  const saveSubmissionEdit = async () => {
    try {
      const updateData = {
        form_data: editFormData,
        month_year: editingSubmission.month_year,
        status: editingSubmission.status
      };

      await axios.put(`${API}/submissions/${editingSubmission.id}`, updateData, { headers: getAuthHeader() });
      alert('Submission updated successfully!');
      setEditingSubmission(null);
      setEditFormData({});
      fetchSubmissions();
    } catch (error) {
      alert('Error updating submission: ' + (error.response?.data?.detail || error.message));
    }
  };

  const cancelEdit = () => {
    setEditingSubmission(null);
    setEditFormData({});
  };

  const exportCSV = async () => {
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const response = await axios.get(`${API}/reports/csv?${params}`, {
        headers: getAuthHeader(),
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'report.csv');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Error exporting CSV:', error);
    }
  };

  const getTemplateById = (templateId) => {
    return templates.find(t => t.id === templateId);
  };

  const getUserById = (userId) => {
    return users.find(u => u.id === userId);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'text-green-600';
      case 'reviewed': return 'text-blue-600';
      case 'rejected': return 'text-red-600';
      default: return 'text-yellow-600';
    }
  };

  const getStatusBgColor = (status) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'reviewed': return 'bg-blue-100 text-blue-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-yellow-100 text-yellow-800';
    }
  };

  const renderSummaryCard = (title, data, colorClass = 'text-blue-600') => (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {Object.entries(data)
          .sort(([,a], [,b]) => b - a)
          .slice(0, 10)
          .map(([key, value]) => (
            <div key={key} className="flex justify-between items-center">
              <span className="text-sm text-gray-700 truncate pr-2" title={key}>
                {key.length > 20 ? key.substring(0, 20) + '...' : key}
              </span>
              <span className={`font-semibold ${colorClass}`}>{value}</span>
            </div>
          ))}
        {Object.keys(data).length === 0 && (
          <p className="text-gray-500 text-sm">No data available</p>
        )}
      </div>
    </div>
  );

  const renderEditFormField = (field, value) => {
    const commonProps = {
      className: "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm",
      value: value || '',
      onChange: (e) => setEditFormData({...editFormData, [field.name]: e.target.value})
    };

    switch (field.type) {
      case 'textarea':
        return <textarea {...commonProps} rows="3" />;
      case 'number':
        return <input type="number" {...commonProps} />;
      case 'date':
        return <input type="date" {...commonProps} />;
      case 'select':
        return (
          <select {...commonProps}>
            <option value="">Select an option</option>
            {field.options?.map((option, idx) => (
              <option key={idx} value={option}>{option}</option>
            ))}
          </select>
        );
      case 'file':
        return (
          <div>
            <p className="text-sm text-gray-600">Current file: {value || 'None'}</p>
            <input
              type="text"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              value={value || ''}
              onChange={(e) => setEditFormData({...editFormData, [field.name]: e.target.value})}
              placeholder="File name or path"
            />
          </div>
        );
      default:
        return <input type="text" {...commonProps} />;
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Reports</h2>
        <div className="flex space-x-4">
          <div className="flex bg-gray-200 rounded-lg p-1">
            <button
              onClick={() => setActiveView('summary')}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                activeView === 'summary' 
                  ? 'bg-white text-blue-600 shadow' 
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              Summary View
            </button>
            <button
              onClick={() => setActiveView('detailed')}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                activeView === 'detailed' 
                  ? 'bg-white text-blue-600 shadow' 
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              Detailed View
            </button>
          </div>
          <button
            onClick={exportCSV}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h3 className="text-lg font-semibold mb-4">Filters</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {user.role === 'admin' && (
            <div>
              <label className="block text-sm font-medium text-gray-700">Location</label>
              <select
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                value={filters.location}
                onChange={(e) => setFilters({...filters, location: e.target.value})}
              >
                <option value="">All Locations</option>
                {locations.map(location => (
                  <option key={location.id} value={location.name}>{location.name}</option>
                ))}
              </select>
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Month/Year</label>
            <input
              type="month"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              value={filters.month_year}
              onChange={(e) => setFilters({...filters, month_year: e.target.value})}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Template</label>
            <select
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              value={filters.template_id}
              onChange={(e) => setFilters({...filters, template_id: e.target.value})}
            >
              <option value="">All Templates</option>
              {templates.map(template => (
                <option key={template.id} value={template.id}>{template.name}</option>
              ))}
            </select>
          </div>

          {user.role === 'admin' && (
            <div>
              <label className="block text-sm font-medium text-gray-700">Submitted By</label>
              <select
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                value={filters.submitted_by}
                onChange={(e) => setFilters({...filters, submitted_by: e.target.value})}
              >
                <option value="">All Users</option>
                {users.map(user => (
                  <option key={user.id} value={user.id}>{user.username}</option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700">Status</label>
            <select
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
            >
              <option value="">All Status</option>
              <option value="submitted">Submitted</option>
              <option value="reviewed">Reviewed</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </div>
      </div>

      {/* Summary View */}
      {activeView === 'summary' && (
        <div>
          {/* Overall Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white p-4 rounded-lg shadow text-center">
              <h3 className="text-sm font-medium text-gray-700">Total Reports</h3>
              <p className="text-2xl font-bold text-blue-600">{submissions.length}</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow text-center">
              <h3 className="text-sm font-medium text-gray-700">Approved</h3>
              <p className="text-2xl font-bold text-green-600">
                {submissions.filter(s => s.status === 'approved').length}
              </p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow text-center">
              <h3 className="text-sm font-medium text-gray-700">Pending Review</h3>
              <p className="text-2xl font-bold text-yellow-600">
                {submissions.filter(s => s.status === 'submitted').length}
              </p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow text-center">
              <h3 className="text-sm font-medium text-gray-700">Rejected</h3>
              <p className="text-2xl font-bold text-red-600">
                {submissions.filter(s => s.status === 'rejected').length}
              </p>
            </div>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {renderSummaryCard('By Template', summaryData.byTemplate, 'text-purple-600')}
            {renderSummaryCard('By Location', summaryData.byLocation, 'text-blue-600')}
            {renderSummaryCard('By Month/Year', summaryData.byMonth, 'text-green-600')}
            {renderSummaryCard('By User', summaryData.byUser, 'text-orange-600')}
            {renderSummaryCard('By Status', summaryData.byStatus, 'text-red-600')}
            {renderSummaryCard('By Submission Date', summaryData.byDate, 'text-indigo-600')}
          </div>
        </div>
      )}

      {/* Edit Submission Modal with Tabs */}
      {editingSubmission && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Manage Submission</h3>
                <button
                  onClick={cancelEdit}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              
              {/* Tab Navigation */}
              <div className="flex mb-6 border-b border-gray-200">
                <button
                  onClick={() => setActiveEditTab('edit')}
                  className={`px-4 py-2 font-medium text-sm ${
                    activeEditTab === 'edit'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Edit Submission
                </button>
                {user.role === 'admin' && (
                  <button
                    onClick={() => setActiveEditTab('delete')}
                    className={`px-4 py-2 font-medium text-sm ${
                      activeEditTab === 'delete'
                        ? 'text-red-600 border-b-2 border-red-600'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Delete Submission
                  </button>
                )}
              </div>

              {/* Submission Info Header */}
              <div className="mb-4 p-4 bg-gray-50 rounded">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><strong>Template:</strong> {getTemplateById(editingSubmission.template_id)?.name}</div>
                  <div><strong>Location:</strong> {editingSubmission.service_location}</div>
                  <div><strong>Month/Year:</strong> {editingSubmission.month_year}</div>
                  <div><strong>Submitted By:</strong> {editingSubmission.submitted_by_username || 'Unknown'}</div>
                  <div><strong>Submitted At:</strong> {new Date(editingSubmission.submitted_at).toLocaleDateString()}</div>
                  <div>
                    <strong>Status:</strong> 
                    <select
                      className="ml-2 px-2 py-1 border border-gray-300 rounded text-sm"
                      value={editingSubmission.status}
                      onChange={(e) => setEditingSubmission({...editingSubmission, status: e.target.value})}
                      disabled={activeEditTab === 'delete'}
                    >
                      <option value="submitted">Submitted</option>
                      <option value="reviewed">Reviewed</option>
                      <option value="approved">Approved</option>
                      <option value="rejected">Rejected</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Edit Tab Content */}
              {activeEditTab === 'edit' && (
                <div>
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {getTemplateById(editingSubmission.template_id)?.fields.map((field, index) => (
                      <div key={index}>
                        <label className="block text-sm font-medium text-gray-700">
                          {field.label}
                          {field.required && <span className="text-red-500 ml-1">*</span>}
                        </label>
                        {renderEditFormField(field, editFormData[field.name])}
                      </div>
                    ))}
                  </div>

                  <div className="flex justify-end space-x-4 mt-6">
                    <button
                      onClick={cancelEdit}
                      className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={saveSubmissionEdit}
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Save Changes
                    </button>
                  </div>
                </div>
              )}

              {/* Delete Tab Content */}
              {activeEditTab === 'delete' && user.role === 'admin' && (
                <div>
                  <div className="space-y-6">
                    {/* Warning Message */}
                    <div className="p-4 bg-red-50 border-l-4 border-red-400 rounded">
                      <div className="flex">
                        <div className="flex-shrink-0">
                          <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <div className="ml-3">
                          <h3 className="text-sm font-medium text-red-800">
                            Warning: Permanent Deletion
                          </h3>
                          <div className="mt-2 text-sm text-red-700">
                            <p>
                              You are about to permanently delete this submission. This action cannot be undone.
                              All data associated with this submission will be lost forever.
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Submission Details for Confirmation */}
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-3">Submission Details to be Deleted:</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Submission ID:</span>
                          <span className="font-mono text-xs">{editingSubmission.id}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Template:</span>
                          <span>{getTemplateById(editingSubmission.template_id)?.name}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Location:</span>
                          <span>{editingSubmission.service_location}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Period:</span>
                          <span>{editingSubmission.month_year}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Submitted By:</span>
                          <span>{editingSubmission.submitted_by_username || 'Unknown User'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Submitted Date:</span>
                          <span>{new Date(editingSubmission.submitted_at).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Current Status:</span>
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            editingSubmission.status === 'approved' ? 'bg-green-100 text-green-800' :
                            editingSubmission.status === 'reviewed' ? 'bg-blue-100 text-blue-800' :
                            editingSubmission.status === 'rejected' ? 'bg-red-100 text-red-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {editingSubmission.status}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Form Fields:</span>
                          <span>{Object.keys(editingSubmission.form_data || {}).length} fields</span>
                        </div>
                        {editingSubmission.attachments && editingSubmission.attachments.length > 0 && (
                          <div className="flex justify-between">
                            <span className="text-gray-600">Attachments:</span>
                            <span>{editingSubmission.attachments.length} files</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Form Data Preview */}
                    {Object.keys(editingSubmission.form_data || {}).length > 0 && (
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                        <h4 className="font-medium text-gray-900 mb-3">Form Data Preview:</h4>
                        <div className="space-y-2 text-sm max-h-40 overflow-y-auto">
                          {Object.entries(editingSubmission.form_data || {}).map(([key, value]) => (
                            <div key={key} className="flex justify-between py-1 border-b border-gray-200 last:border-b-0">
                              <span className="text-gray-600 font-medium">{key}:</span>
                              <span className="text-gray-800 max-w-xs truncate" title={value}>
                                {value || '(empty)'}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Confirmation Checkbox */}
                    <div className="flex items-center space-x-3 p-4 bg-red-50 rounded-lg">
                      <input
                        type="checkbox"
                        id="confirmDelete"
                        className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                        onChange={(e) => setDeleteConfirmed(e.target.checked)}
                      />
                      <label htmlFor="confirmDelete" className="text-sm text-red-800">
                        I understand that this action is permanent and cannot be undone
                      </label>
                    </div>
                  </div>

                  <div className="flex justify-end space-x-4 mt-6">
                    <button
                      onClick={cancelEdit}
                      className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={deleteSubmission}
                      disabled={!deleteConfirmed}
                      className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Delete Submission
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Detail View Modal */}
      {showDetailModal && selectedSubmission && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Submission Details</h3>
                <button
                  onClick={() => setShowDetailModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded">
                  <div>
                    <strong>Template:</strong> {getTemplateById(selectedSubmission.template_id)?.name}
                  </div>
                  <div>
                    <strong>Location:</strong> {selectedSubmission.service_location}
                  </div>
                  <div>
                    <strong>Month/Year:</strong> {selectedSubmission.month_year}
                  </div>
                  <div>
                    <strong>Status:</strong> 
                    <span className={`ml-2 px-2 py-1 rounded-full text-xs ${getStatusBgColor(selectedSubmission.status)}`}>
                      {selectedSubmission.status}
                    </span>
                  </div>
                  <div>
                    <strong>Submitted:</strong> {new Date(selectedSubmission.submitted_at).toLocaleString()}
                  </div>
                  <div>
                    <strong>Submitted By:</strong> {selectedSubmission.submitted_by}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-3">Form Data:</h4>
                  <div className="space-y-3">
                    {getTemplateById(selectedSubmission.template_id)?.fields.map((field, index) => (
                      <div key={index} className="border-b pb-2">
                        <strong className="text-sm text-gray-700">{field.label}:</strong>
                        <div className="mt-1">
                          {field.type === 'file' ? (
                            selectedSubmission.form_data[field.name] ? (
                              <a 
                                href={`${API}/files/${selectedSubmission.form_data[field.name]}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:text-blue-800"
                              >
                                {selectedSubmission.form_data[field.name]}
                              </a>
                            ) : (
                              <span className="text-gray-500">No file uploaded</span>
                            )
                          ) : (
                            <span>{selectedSubmission.form_data[field.name] || 'No data'}</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex justify-end mt-6">
                <button
                  onClick={() => setShowDetailModal(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Detailed View */}
      {activeView === 'detailed' && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">All Submissions ({submissions.length})</h3>
            {submissions.length === 0 ? (
              <p className="text-gray-500">No submissions found.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full table-auto">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Template</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Month/Year</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Submitted By</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {submissions.map(submission => (
                      <tr key={submission.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {templates.find(t => t.id === submission.template_id)?.name || 'Unknown Template'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {submission.service_location}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {submission.month_year}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {submission.submitted_by_username || 'Unknown User'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(submission.submitted_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className={`px-2 py-1 rounded-full text-xs ${getStatusBgColor(submission.status)}`}>
                            {submission.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                          <button
                            onClick={() => fetchSubmissionDetail(submission.id)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            View
                          </button>
                          {user.role !== 'data_entry' && (
                            <button
                              onClick={() => startEditSubmission(submission.id)}
                              className="text-green-600 hover:text-green-900"
                            >
                              Edit
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Statistics Component
const Statistics = ({ user }) => {
  const [statisticsData, setStatisticsData] = useState(null);
  const [customFieldData, setCustomFieldData] = useState(null);
  const [options, setOptions] = useState({});
  const [customFields, setCustomFields] = useState([]);
  const [query, setQuery] = useState({
    date_from: '',
    date_to: '',
    locations: [],
    user_roles: [],
    templates: [],
    status: [],
    group_by: 'location',
    analyze_custom_fields: false,
    custom_field_name: '',
    custom_field_analysis_type: 'frequency'
  });
  const [loading, setLoading] = useState(false);
  const [showCustomFieldAnalysis, setShowCustomFieldAnalysis] = useState(false);

  useEffect(() => {
    fetchOptions();
    fetchCustomFields();
  }, []);

  const fetchOptions = async () => {
    try {
      const response = await axios.get(`${API}/statistics/options`, { headers: getAuthHeader() });
      setOptions(response.data);
    } catch (error) {
      console.error('Error fetching statistics options:', error);
    }
  };

  const fetchCustomFields = async () => {
    try {
      const response = await axios.get(`${API}/statistics/custom-fields`, { headers: getAuthHeader() });
      setCustomFields(response.data.custom_fields);
    } catch (error) {
      console.error('Error fetching custom fields:', error);
    }
  };

  const generateReport = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/statistics/generate`, query, { headers: getAuthHeader() });
      setStatisticsData(response.data);
    } catch (error) {
      alert('Error generating statistics: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const generateCustomFieldReport = async () => {
    if (!query.custom_field_name) {
      alert('Please select a custom field to analyze');
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/statistics/generate-custom-field`, query, { headers: getAuthHeader() });
      setCustomFieldData(response.data);
    } catch (error) {
      alert('Error generating custom field statistics: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const generatePDFReport = async () => {
    try {
      const queryString = encodeURIComponent(JSON.stringify(query));
      const response = await axios.get(`${API}/reports/pdf?report_type=statistics&query_params=${queryString}`, { 
        headers: getAuthHeader(),
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'statistics_report.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      alert('Error generating PDF report: ' + (error.response?.data?.detail || error.message));
    }
  };

  const getChartData = () => {
    if (!statisticsData || !statisticsData.data) return null;

    const labels = statisticsData.data.map(item => item.category || 'Unknown');
    const data = statisticsData.data.map(item => item.total_submissions);
    
    return {
      labels,
      datasets: [
        {
          label: 'Total Submissions',
          data,
          backgroundColor: [
            'rgba(54, 162, 235, 0.8)',
            'rgba(255, 99, 132, 0.8)',
            'rgba(255, 205, 86, 0.8)',
            'rgba(75, 192, 192, 0.8)',
            'rgba(153, 102, 255, 0.8)',
            'rgba(255, 159, 64, 0.8)',
          ],
          borderColor: [
            'rgba(54, 162, 235, 1)',
            'rgba(255, 99, 132, 1)',
            'rgba(255, 205, 86, 1)',
            'rgba(75, 192, 192, 1)',
            'rgba(153, 102, 255, 1)',
            'rgba(255, 159, 64, 1)',
          ],
          borderWidth: 1,
        },
      ],
    };
  };

  const getStatusChartData = () => {
    if (!statisticsData || !statisticsData.summary) return null;

    return {
      labels: ['Approved', 'Reviewed', 'Submitted', 'Rejected'],
      datasets: [
        {
          data: [
            statisticsData.summary.total_approved,
            statisticsData.summary.total_reviewed,
            statisticsData.summary.total_submitted,
            statisticsData.summary.total_rejected,
          ],
          backgroundColor: [
            'rgba(34, 197, 94, 0.8)',
            'rgba(59, 130, 246, 0.8)',
            'rgba(251, 191, 36, 0.8)',
            'rgba(239, 68, 68, 0.8)',
          ],
        },
      ],
    };
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: `Statistics by ${query.group_by}`,
      },
    },
  };

  const pieChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'right',
      },
      title: {
        display: true,
        text: 'Submission Status Distribution',
      },
    },
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Statistics</h2>

      {/* Filters */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h3 className="text-lg font-semibold mb-4">Generate Custom Report</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Date From</label>
            <input
              type="date"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              value={query.date_from}
              onChange={(e) => setQuery({...query, date_from: e.target.value})}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Date To</label>
            <input
              type="date"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              value={query.date_to}
              onChange={(e) => setQuery({...query, date_to: e.target.value})}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Group By</label>
            <select
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              value={query.group_by}
              onChange={(e) => setQuery({...query, group_by: e.target.value})}
            >
              {options.group_by_options?.map(option => (
                <option key={option.id} value={option.id}>{option.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Locations</label>
            <select
              multiple
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm h-24"
              value={query.locations}
              onChange={(e) => setQuery({
                ...query,
                locations: Array.from(e.target.selectedOptions, option => option.value)
              })}
            >
              {options.locations?.map(location => (
                <option key={location.id} value={location.name}>{location.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">User Roles</label>
            <select
              multiple
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm h-24"
              value={query.user_roles}
              onChange={(e) => setQuery({
                ...query,
                user_roles: Array.from(e.target.selectedOptions, option => option.value)
              })}
            >
              {options.user_roles?.map(role => (
                <option key={role} value={role}>{role}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Templates</label>
            <select
              multiple
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm h-24"
              value={query.templates}
              onChange={(e) => setQuery({
                ...query,
                templates: Array.from(e.target.selectedOptions, option => option.value)
              })}
            >
              {options.templates?.map(template => (
                <option key={template.id} value={template.id}>{template.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Status</label>
            <select
              multiple
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm h-24"
              value={query.status}
              onChange={(e) => setQuery({
                ...query,
                status: Array.from(e.target.selectedOptions, option => option.value)
              })}
            >
              {options.status_options?.map(status => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Custom Field Analysis Section */}
        <div className="mb-4">
          <div className="flex items-center mb-4">
            <input
              type="checkbox"
              id="customFieldAnalysis"
              checked={showCustomFieldAnalysis}
              onChange={(e) => {
                setShowCustomFieldAnalysis(e.target.checked);
                setQuery({...query, analyze_custom_fields: e.target.checked});
              }}
              className="mr-2"
            />
            <label htmlFor="customFieldAnalysis" className="text-sm font-medium text-gray-700">
              Enable Custom Field Analysis
            </label>
          </div>

          {showCustomFieldAnalysis && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
              <div>
                <label className="block text-sm font-medium text-gray-700">Custom Field</label>
                <select
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  value={query.custom_field_name}
                  onChange={(e) => setQuery({...query, custom_field_name: e.target.value})}
                >
                  <option value="">Select a field...</option>
                  {customFields.map(field => (
                    <option key={field.name} value={field.name}>
                      {field.label} ({field.type}) - {field.template}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Analysis Type</label>
                <select
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  value={query.custom_field_analysis_type}
                  onChange={(e) => setQuery({...query, custom_field_analysis_type: e.target.value})}
                >
                  <option value="frequency">Frequency Count</option>
                  <option value="numerical">Numerical Analysis</option>
                  <option value="trend">Trend Over Time</option>
                </select>
              </div>

              <div className="flex items-end">
                <button
                  onClick={generateCustomFieldReport}
                  disabled={loading || !query.custom_field_name}
                  className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
                >
                  {loading ? 'Analyzing...' : 'Analyze Field'}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="flex space-x-4">
          <button
            onClick={generateReport}
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Generating...' : 'Generate Report'}
          </button>
          
          <button
            onClick={generatePDFReport}
            disabled={!statisticsData}
            className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
          >
            Download PDF Report
          </button>
        </div>
      </div>

      {/* Custom Field Analysis Results */}
      {customFieldData && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h3 className="text-lg font-semibold mb-4">
            Custom Field Analysis: {customFieldData.field_name} ({customFieldData.analysis_type})
          </h3>
          
          {customFieldData.analysis_type === 'numerical' && customFieldData.results[0] && (
            <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-4">
              <div className="text-center">
                <div className="text-sm text-gray-600">Count</div>
                <div className="text-lg font-bold">{customFieldData.results[0].total_count}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-600">Average</div>
                <div className="text-lg font-bold">{customFieldData.results[0].average}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-600">Sum</div>
                <div className="text-lg font-bold">{customFieldData.results[0].sum}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-600">Min</div>
                <div className="text-lg font-bold">{customFieldData.results[0].min}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-600">Max</div>
                <div className="text-lg font-bold">{customFieldData.results[0].max}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-600">Std Dev</div>
                <div className="text-lg font-bold">{customFieldData.results[0].std_dev}</div>
              </div>
            </div>
          )}

          {customFieldData.analysis_type === 'frequency' && (
            <div className="overflow-x-auto">
              <table className="min-w-full table-auto">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Count</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Percentage</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {customFieldData.results.map((item, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {item.value || 'Empty'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {item.count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {item.percentage?.toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {customFieldData.analysis_type === 'trend' && (
            <div className="overflow-x-auto">
              <table className="min-w-full table-auto">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Month</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Submissions</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Values</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {customFieldData.results.map((item, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {item.month}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {item.total_submissions}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {item.values.map((val, i) => (
                          <span key={i} className="inline-block mr-2 mb-1 px-2 py-1 bg-blue-100 rounded">
                            {val.value}: {val.count}
                          </span>
                        ))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Results */}
      {statisticsData && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="bg-white p-4 rounded-lg shadow text-center">
              <h3 className="text-sm font-medium text-gray-700">Total Submissions</h3>
              <p className="text-2xl font-bold text-blue-600">{statisticsData.summary.total_submissions}</p>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow text-center">
              <h3 className="text-sm font-medium text-gray-700">Approved</h3>
              <p className="text-2xl font-bold text-green-600">{statisticsData.summary.total_approved}</p>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow text-center">
              <h3 className="text-sm font-medium text-gray-700">Reviewed</h3>
              <p className="text-2xl font-bold text-blue-600">{statisticsData.summary.total_reviewed}</p>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow text-center">
              <h3 className="text-sm font-medium text-gray-700">Pending</h3>
              <p className="text-2xl font-bold text-yellow-600">{statisticsData.summary.total_submitted}</p>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow text-center">
              <h3 className="text-sm font-medium text-gray-700">Approval Rate</h3>
              <p className="text-2xl font-bold text-purple-600">{statisticsData.summary.approval_rate}%</p>
            </div>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Submissions Distribution</h3>
              {getChartData() && <Bar data={getChartData()} options={chartOptions} />}
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Status Overview</h3>
              {getStatusChartData() && <Pie data={getStatusChartData()} options={pieChartOptions} />}
            </div>
          </div>

          {/* Data Table */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">Detailed Breakdown</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full table-auto">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        {query.group_by}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Approved</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reviewed</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Submitted</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rejected</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Users</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {statisticsData.data.map((item, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {item.category || 'Unknown'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.total_submissions}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                          {item.approved_count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600">
                          {item.reviewed_count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-yellow-600">
                          {item.submitted_count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                          {item.rejected_count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.unique_user_count}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Main App Component
function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('auth_token');
    const userInfo = localStorage.getItem('user_info');
    
    if (token && userInfo) {
      setUser(JSON.parse(userInfo));
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    setActiveTab('dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    setUser(null);
    setActiveTab('dashboard');
  };

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard user={user} />;
      case 'users':
        return <UserManagement />;
      case 'roles':
        return <RoleManagement />;
      case 'locations':
        return <LocationManagement />;
      case 'templates':
        return <TemplateManagement />;
      case 'submit':
        return <DataSubmission user={user} />;
      case 'reports':
        return <Reports user={user} />;
      case 'statistics':
        return <Statistics user={user} />;
      default:
        return <Dashboard user={user} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Navigation
        user={user}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onLogout={handleLogout}
      />
      <main>
        {renderContent()}
      </main>
    </div>
  );
}

export default App;