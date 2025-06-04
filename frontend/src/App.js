import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/auth/login`, credentials);
      localStorage.setItem('auth_token', response.data.access_token);
      localStorage.setItem('user_info', JSON.stringify(response.data.user));
      onLogin(response.data.user);
    } catch (error) {
      setError('Invalid credentials');
    }
  };

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
        
        <div className="mt-4 text-sm text-gray-600 text-center">
          <p>Default Admin: admin / admin123</p>
        </div>
      </div>
    </div>
  );
};

// Navigation Component
const Navigation = ({ user, activeTab, setActiveTab, onLogout }) => {
  const tabs = {
    admin: [
      { id: 'dashboard', label: 'Dashboard' },
      { id: 'users', label: 'Manage Users' },
      { id: 'locations', label: 'Manage Locations' },
      { id: 'templates', label: 'Manage Templates' },
      { id: 'reports', label: 'Reports' },
      { id: 'submit', label: 'Submit Data' }
    ],
    manager: [
      { id: 'dashboard', label: 'Dashboard' },
      { id: 'submit', label: 'Submit Data' },
      { id: 'reports', label: 'Reports' }
    ],
    data_entry: [
      { id: 'dashboard', label: 'Dashboard' },
      { id: 'submit', label: 'Submit Data' }
    ]
  };

  return (
    <nav className="bg-blue-600 text-white p-4">
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-6">
          <h1 className="text-xl font-bold">CLIENT SERVICES</h1>
          <div className="flex space-x-4">
            {tabs[user.role]?.map(tab => (
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
                  
                  <div className="grid grid-cols-4 gap-2 mt-2 text-sm">
                    <div className="text-green-600">
                      ✓ {locationData.approved_count} approved
                    </div>
                    <div className="text-blue-600">
                      ◉ {locationData.reviewed_count} reviewed
                    </div>
                    <div className="text-yellow-600">
                      ● {locationData.submitted_count} submitted
                    </div>
                    <div className="text-red-600">
                      ✗ {locationData.rejected_count} rejected
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
                  Set Deadline
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

// User Management Component (Admin only)
const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [locations, setLocations] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    role: 'data_entry',
    assigned_location: ''
  });

  useEffect(() => {
    fetchUsers();
    fetchLocations();
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

  const fetchUserForEdit = async (userId) => {
    try {
      const response = await axios.get(`${API}/users/${userId}`, { headers: getAuthHeader() });
      const user = response.data;
      setNewUser({
        username: user.username,
        password: '', // Don't prefill password for security
        role: user.role,
        assigned_location: user.assigned_location || ''
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
    setNewUser({ username: '', password: '', role: 'data_entry', assigned_location: '' });
    setShowForm(false);
    setEditingUser(null);
  };

  const handleEdit = (user) => {
    fetchUserForEdit(user.id);
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await axios.delete(`${API}/users/${userId}`, { headers: getAuthHeader() });
        fetchUsers();
      } catch (error) {
        console.error('Error deleting user:', error);
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
                onChange={(e) => setNewUser({...newUser, role: e.target.value})}
              >
                <option value="data_entry">Data Entry Officer</option>
                <option value="manager">Service Hub Manager</option>
                <option value="admin">Administrator</option>
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
                      'bg-green-100 text-green-800'
                    }`}>
                      {user.role}
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
    </div>
  );
};

// Location Management Component (Admin only)
const LocationManagement = () => {
  const [locations, setLocations] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingLocation, setEditingLocation] = useState(null);
  const [formData, setFormData] = useState({ name: '', description: '' });

  useEffect(() => {
    fetchLocations();
  }, []);

  const fetchLocations = async () => {
    try {
      const response = await axios.get(`${API}/locations`, { headers: getAuthHeader() });
      setLocations(response.data);
    } catch (error) {
      console.error('Error fetching locations:', error);
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
      } catch (error) {
        console.error('Error deleting location:', error);
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
    </div>
  );
};

// Template Management Component (Admin only)
const TemplateManagement = () => {
  const [templates, setTemplates] = useState([]);
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
      } catch (error) {
        console.error('Error deleting template:', error);
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
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [editingSubmission, setEditingSubmission] = useState(null);
  const [editFormData, setEditFormData] = useState({});
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [filters, setFilters] = useState({
    location: '',
    month_year: '',
    template_id: ''
  });

  useEffect(() => {
    fetchSubmissions();
    fetchLocations();
    fetchTemplates();
  }, [filters]);

  const fetchSubmissions = async () => {
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const response = await axios.get(`${API}/submissions?${params}`, { headers: getAuthHeader() });
      setSubmissions(response.data);
    } catch (error) {
      console.error('Error fetching submissions:', error);
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

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/templates`, { headers: getAuthHeader() });
      setTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
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
    } catch (error) {
      alert('Error fetching submission for editing: ' + (error.response?.data?.detail || error.message));
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
        <button
          onClick={exportCSV}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h3 className="text-lg font-semibold mb-4">Filters</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {user.role === 'admin' && (
            <div>
              <label className="block text-sm font-medium text-gray-700">Location</label>
              <select
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
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
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              value={filters.month_year}
              onChange={(e) => setFilters({...filters, month_year: e.target.value})}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Template</label>
            <select
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              value={filters.template_id}
              onChange={(e) => setFilters({...filters, template_id: e.target.value})}
            >
              <option value="">All Templates</option>
              {templates.map(template => (
                <option key={template.id} value={template.id}>{template.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Edit Submission Modal */}
      {editingSubmission && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Edit Submission</h3>
                <button
                  onClick={cancelEdit}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              
              <div className="mb-4 p-4 bg-gray-50 rounded">
                <p><strong>Template:</strong> {getTemplateById(editingSubmission.template_id)?.name}</p>
                <p><strong>Location:</strong> {editingSubmission.service_location}</p>
                <p><strong>Month/Year:</strong> {editingSubmission.month_year}</p>
                <p><strong>Status:</strong> 
                  <select
                    className="ml-2 px-2 py-1 border border-gray-300 rounded text-sm"
                    value={editingSubmission.status}
                    onChange={(e) => setEditingSubmission({...editingSubmission, status: e.target.value})}
                  >
                    <option value="submitted">Submitted</option>
                    <option value="reviewed">Reviewed</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                  </select>
                </p>
              </div>

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
                    <span className={`ml-2 px-2 py-1 rounded-full text-xs ${
                      selectedSubmission.status === 'approved' ? 'bg-green-100 text-green-800' :
                      selectedSubmission.status === 'reviewed' ? 'bg-blue-100 text-blue-800' :
                      selectedSubmission.status === 'rejected' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
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

      {/* Results */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Submissions ({submissions.length})</h3>
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
                    <tr key={submission.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {templates.find(t => t.id === submission.template_id)?.name || submission.template_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {submission.service_location}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {submission.month_year}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {submission.submitted_by}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(submission.submitted_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          submission.status === 'approved' ? 'bg-green-100 text-green-800' :
                          submission.status === 'reviewed' ? 'bg-blue-100 text-blue-800' :
                          submission.status === 'rejected' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
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
      case 'locations':
        return <LocationManagement />;
      case 'templates':
        return <TemplateManagement />;
      case 'submit':
        return <DataSubmission user={user} />;
      case 'reports':
        return <Reports user={user} />;
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