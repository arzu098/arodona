import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
const AdminDashboard = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalVendors: 0,
    totalOrders: 0,
    totalRevenue: 0,
    pendingVendors: 0,
    pendingOrders: 0
  });
  const [recentUsers, setRecentUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Users management state
  const [users, setUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [usersPagination, setUsersPagination] = useState({ skip: 0, limit: 10, total: 0 });
  
  // Vendors management state
  const [vendors, setVendors] = useState([]);
  const [vendorsLoading, setVendorsLoading] = useState(false);
  const [vendorsPagination, setVendorsPagination] = useState({ skip: 0, limit: 10, total: 0 });
  
  // Audit logs state
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditLogsLoading, setAuditLogsLoading] = useState(false);
  const [auditLogsPagination, setAuditLogsPagination] = useState({ skip: 0, limit: 20, total: 0 });
  
  // Settings state
  const [settings, setSettings] = useState(null);
  const [settingsLoading, setSettingsLoading] = useState(false);
  
  // Create Vendor Form State
  const [createVendorForm, setCreateVendorForm] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    phone: '',
    business_name: '',
    business_type: 'jewelry'
  });
  const [createVendorLoading, setCreateVendorLoading] = useState(false);
  const [createVendorError, setCreateVendorError] = useState('');
  const [createVendorSuccess, setCreateVendorSuccess] = useState('');
  
  // Create User Form State
  const [createUserForm, setCreateUserForm] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    phone: '',
    role: 'customer'
  });
  const [createUserLoading, setCreateUserLoading] = useState(false);
  const [createUserError, setCreateUserError] = useState('');
  const [createUserSuccess, setCreateUserSuccess] = useState('');
  
  // Region Form State
  const [createRegionForm, setCreateRegionForm] = useState({
    code: '',
    name: '',
    country: '',
    currency: 'INR',
    timezone: 'Asia/Kolkata',
    tax_rate: 0
  });
  const [createRegionLoading, setCreateRegionLoading] = useState(false);
  const [createRegionError, setCreateRegionError] = useState('');
  const [createRegionSuccess, setCreateRegionSuccess] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  useEffect(() => {
    if (activeTab === 'manage-users') {
      fetchUsers();
    } else if (activeTab === 'manage-vendors') {
      fetchVendors();
    } else if (activeTab === 'audit-logs') {
      fetchAuditLogs();
    } else if (activeTab === 'settings') {
      fetchSettings();
    }
  }, [activeTab]);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      
      // Fetch dashboard stats
      const statsResponse = await fetch('http://localhost:5858/api/admin/dashboard-stats', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats({
          totalUsers: statsData.total_users || 0,
          totalVendors: statsData.total_vendors || 0,
          totalOrders: 0, // Will be implemented when order system is ready
          totalRevenue: 0, // Will be implemented when order system is ready
          pendingVendors: statsData.pending_vendor_approvals || 0,
          pendingOrders: 0 // Will be implemented when order system is ready
        });
        
        // Set recent users
        if (statsData.recent_users) {
          setRecentUsers(statsData.recent_users);
        }
      } else {
        console.error('Failed to fetch dashboard stats');
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async (skip = 0) => {
    setUsersLoading(true);
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`http://localhost:5858/api/admin/users?skip=${skip}&limit=${usersPagination.limit}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUsers(data.users || []);
        setUsersPagination(prev => ({ ...prev, skip, total: data.total || 0 }));
      }
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setUsersLoading(false);
    }
  };

  const fetchVendors = async (skip = 0) => {
    setVendorsLoading(true);
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`http://localhost:5858/api/admin/vendors?skip=${skip}&limit=${vendorsPagination.limit}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('Vendors response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Vendors data received:', data);
        console.log('Vendors array:', data.vendors);
        setVendors(data.vendors || []);
        setVendorsPagination(prev => ({ ...prev, skip, total: data.total || 0 }));
      } else {
        const errorData = await response.json();
        console.error('Error response:', errorData);
      }
    } catch (error) {
      console.error('Error fetching vendors:', error);
    } finally {
      setVendorsLoading(false);
    }
  };

  const fetchAuditLogs = async (skip = 0) => {
    setAuditLogsLoading(true);
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`http://localhost:5858/api/admin/audit-logs?skip=${skip}&limit=${auditLogsPagination.limit}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAuditLogs(data.logs || []);
        setAuditLogsPagination(prev => ({ ...prev, skip, total: data.total || 0 }));
      }
    } catch (error) {
      console.error('Error fetching audit logs:', error);
    } finally {
      setAuditLogsLoading(false);
    }
  };

  const fetchSettings = async () => {
    setSettingsLoading(true);
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch('http://localhost:5858/api/admin/settings', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      }
    } catch (error) {
      console.error('Error fetching settings:', error);
    } finally {
      setSettingsLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
  };

  // Create Vendor Handler
  const handleCreateVendor = async (e) => {
    e.preventDefault();
    setCreateVendorLoading(true);
    setCreateVendorError('');
    setCreateVendorSuccess('');

    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch('http://localhost:5858/api/admin/create-vendor', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(createVendorForm)
      });

      const data = await response.json();

      if (response.ok) {
        setCreateVendorSuccess(`Vendor account created successfully for ${createVendorForm.email}`);
        setCreateVendorForm({
          email: '',
          password: '',
          first_name: '',
          last_name: '',
          phone: '',
          business_name: '',
          business_type: 'jewelry'
        });
        fetchDashboardData();
      } else {
        setCreateVendorError(data.detail || 'Failed to create vendor account');
      }
    } catch (error) {
      console.error('Error creating vendor:', error);
      setCreateVendorError('An error occurred while creating vendor account');
    } finally {
      setCreateVendorLoading(false);
    }
  };

  // Create User Handler
  const handleCreateUser = async (e) => {
    e.preventDefault();
    setCreateUserLoading(true);
    setCreateUserError('');
    setCreateUserSuccess('');

    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch('http://localhost:5858/api/admin/users', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(createUserForm)
      });

      const data = await response.json();

      if (response.ok) {
        setCreateUserSuccess(`User account created successfully for ${createUserForm.email}`);
        setCreateUserForm({
          email: '',
          password: '',
          first_name: '',
          last_name: '',
          phone: '',
          role: 'customer'
        });
        fetchUsers();
      } else {
        setCreateUserError(data.detail || 'Failed to create user account');
      }
    } catch (error) {
      console.error('Error creating user:', error);
      setCreateUserError('An error occurred while creating user account');
    } finally {
      setCreateUserLoading(false);
    }
  };

  // Update User Handler
  const handleUpdateUser = async (userId, updateData) => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`http://localhost:5858/api/admin/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      });

      if (response.ok) {
        fetchUsers();
        alert('User updated successfully');
      } else {
        const data = await response.json();
        alert(data.detail || 'Failed to update user');
      }
    } catch (error) {
      console.error('Error updating user:', error);
      alert('An error occurred while updating user');
    }
  };
  // Approve/Reject Vendor Handler
  const handleVendorApproval = async (vendorId, approved, remarks = '') => {
    try {
      const token = localStorage.getItem('accessToken');
      const newStatus = approved ? 'approved' : 'rejected';
      const response = await fetch(`http://localhost:5858/api/admin/vendors/${vendorId}/status`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          new_status: newStatus,
          notes: remarks 
        })
      });

      if (response.ok) {
        fetchVendors();
        alert(`Vendor ${approved ? 'approved' : 'rejected'} successfully`);
      } else {
        const data = await response.json();
        alert(data.detail || 'Failed to update vendor status');
      }
    } catch (error) {
      console.error('Error updating vendor:', error);
      alert('An error occurred while updating vendor');
    }
  };

  // Moderate Content Handler
  const handleModerateContent = async (contentType, contentId, action, reason = '') => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`http://localhost:5858/api/admin/content/${contentType}/${contentId}/moderate`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action, reason })
      });

      if (response.ok) {
        alert('Content moderated successfully');
      } else {
        const data = await response.json();
        alert(data.detail || 'Failed to moderate content');
      }
    } catch (error) {
      console.error('Error moderating content:', error);
      alert('An error occurred while moderating content');
    }
  };
  // Create Region Handler
  const handleCreateRegion = async (e) => {
    e.preventDefault();
    setCreateRegionLoading(true);
    setCreateRegionError('');
    setCreateRegionSuccess('');
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch('http://localhost:5858/api/admin/regions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(createRegionForm)
      });

      const data = await response.json();

      if (response.ok) {
        setCreateRegionSuccess(`Region "${createRegionForm.name}" created successfully`);
        setCreateRegionForm({
          code: '',
          name: '',
          country: '',
          currency: 'INR',
          timezone: 'Asia/Kolkata',
          tax_rate: 0
        });
      } else {
        setCreateRegionError(data.detail || 'Failed to create region');
      }
    } catch (error) {
      console.error('Error creating region:', error);
      setCreateRegionError('An error occurred while creating region');
    } finally {
      setCreateRegionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl">Loading dashboard...</div>
      </div>
    );
  }
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-lg sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Top bar with logo, title, and user info */}
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <img 
                src="/Images/1000017875-removebg-preview 9.jpg" 
                alt="Admin Logo" 
                className="w-10 h-10 sm:w-12 sm:h-12 object-contain mr-2 sm:mr-3" 
              />
              <div>
                <h1 className="text-lg sm:text-xl md:text-2xl font-bold text-gray-900">Admin Dashboard</h1>
                <p className="text-xs sm:text-sm text-gray-600 hidden sm:block">Welcome back, {user?.first_name}</p>
              </div>
            </div>
            
            {/* Desktop user info and logout */}
            <div className="hidden md:flex items-center space-x-3 lg:space-x-4">
              <span className="text-xs lg:text-sm text-gray-600">ID: {user?.id}</span>
              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                ADMIN
              </span>
              <button
                onClick={handleLogout}
                className="bg-red-600 text-white px-3 lg:px-4 py-2 rounded text-sm hover:bg-red-700 transition-colors"
              >
                Logout
              </button>
            </div>

            {/* Mobile menu button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {isMobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>

          {/* Mobile Menu Dropdown */}
          {isMobileMenuOpen && (
            <div className="md:hidden border-t border-gray-200 py-3 space-y-2">
              {/* User info in mobile */}
              <div className="px-3 py-2 bg-gray-50 rounded-md">
                <p className="text-sm font-medium text-gray-900">{user?.first_name}</p>
                <p className="text-xs text-gray-600">ID: {user?.id}</p>
                <span className="inline-block mt-1 px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                  ADMIN
                </span>
              </div>
              
              {/* Navigation in mobile */}
              {[
                { id: 'overview', name: 'Overview' },
                { id: 'create-vendor', name: 'Create Vendor' },
                { id: 'create-user', name: 'Create User' },
                { id: 'manage-users', name: 'Manage Users' },
                { id: 'manage-vendors', name: 'Manage Vendors' },
                { id: 'audit-logs', name: 'Audit Logs' },
                { id: 'settings', name: 'Settings' },
                { id: 'regions', name: 'Regions' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id);
                    setIsMobileMenuOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium ${
                    activeTab === tab.id
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {tab.name}
                </button>
              ))}
              
              {/* Logout button in mobile */}
              <button
                onClick={handleLogout}
                className="w-full text-left px-3 py-2 rounded-md text-sm font-medium text-red-600 hover:bg-red-50"
              >
                Logout
              </button>
            </div>
          )}
          
          {/* Desktop Navigation Tabs */}
          <nav className="hidden md:block border-t border-gray-200 pt-3 pb-2">
            <div className="flex space-x-4 lg:space-x-8 overflow-x-auto scrollbar-hide">
              {[
                { id: 'overview', name: 'Overview' },
                { id: 'create-vendor', name: 'Create Vendor' },
                { id: 'create-user', name: 'Create User' },
                { id: 'manage-users', name: 'Manage Users' },
                { id: 'manage-vendors', name: 'Manage Vendors' },
                { id: 'audit-logs', name: 'Audit Logs' },
                { id: 'settings', name: 'Settings' },
                { id: 'regions', name: 'Regions' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-xs lg:text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.name}
                </button>
              ))}
            </div>
          </nav>
        </div>
      </header>

      <div className="max-w-7xl mx-auto py-4 sm:py-6 px-4 sm:px-6 lg:px-8">
        {activeTab === 'overview' && (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 xs:grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-3">
          {/* Total Users */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-3 sm:p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 sm:h-6 sm:w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                  </svg>
                </div>
                <div className="ml-3 sm:ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-xs sm:text-sm font-medium text-gray-500 truncate">Total Users</dt>
                    <dd className="text-base sm:text-lg font-medium text-gray-900">{stats.totalUsers}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Total Vendors */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-3 sm:p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 sm:h-6 sm:w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <div className="ml-3 sm:ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-xs sm:text-sm font-medium text-gray-500 truncate">Total Vendors</dt>
                    <dd className="text-base sm:text-lg font-medium text-gray-900">{stats.totalVendors}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Total Orders */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-3 sm:p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 sm:h-6 sm:w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                  </svg>
                </div>
                <div className="ml-3 sm:ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-xs sm:text-sm font-medium text-gray-500 truncate">Total Orders</dt>
                    <dd className="text-base sm:text-lg font-medium text-gray-900">{stats.totalOrders}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Pending Vendors */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-3 sm:p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 sm:h-6 sm:w-6 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-3 sm:ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-xs sm:text-sm font-medium text-gray-500 truncate">Pending Vendors</dt>
                    <dd className="text-base sm:text-lg font-medium text-gray-900">{stats.pendingVendors}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Total Revenue */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-3 sm:p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 sm:h-6 sm:w-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                </div>
                <div className="ml-3 sm:ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-xs sm:text-sm font-medium text-gray-500 truncate">Total Revenue</dt>
                    <dd className="text-base sm:text-lg font-medium text-gray-900">₹{stats.totalRevenue?.toLocaleString() || 0}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Pending Orders */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-3 sm:p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 sm:h-6 sm:w-6 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                </div>
                <div className="ml-3 sm:ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-xs sm:text-sm font-medium text-gray-500 truncate">Pending Orders</dt>
                    <dd className="text-base sm:text-lg font-medium text-gray-900">{stats.pendingOrders}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-6 sm:mt-8">
          <h3 className="text-base sm:text-lg font-medium text-gray-900 mb-3 sm:mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 gap-3 sm:gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Link 
              to="/admin/users" 
              className="bg-blue-50 p-3 sm:p-4 rounded-lg hover:bg-blue-100 transition-colors"
            >
              <div className="flex items-center">
                <svg className="h-5 w-5 sm:h-6 sm:w-6 text-blue-600 mr-2 sm:mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                </svg>
                <div>
                  <h4 className="text-sm sm:text-base font-medium text-gray-900">Manage Users</h4>
                  <p className="text-xs sm:text-sm text-gray-600">View and edit users</p>
                </div>
              </div>
            </Link>

            <Link 
              to="/admin/vendors" 
              className="bg-green-50 p-3 sm:p-4 rounded-lg hover:bg-green-100 transition-colors"
            >
              <div className="flex items-center">
                <svg className="h-5 w-5 sm:h-6 sm:w-6 text-green-600 mr-2 sm:mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                <div>
                  <h4 className="text-sm sm:text-base font-medium text-gray-900">Manage Vendors</h4>
                  <p className="text-xs sm:text-sm text-gray-600">Approve and manage vendors</p>
                </div>
              </div>
            </Link>

            <Link 
              to="/admin/orders" 
              className="bg-yellow-50 p-3 sm:p-4 rounded-lg hover:bg-yellow-100 transition-colors"
            >
              <div className="flex items-center">
                <svg className="h-5 w-5 sm:h-6 sm:w-6 text-yellow-600 mr-2 sm:mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
                <div>
                  <h4 className="text-sm sm:text-base font-medium text-gray-900">View Orders</h4>
                  <p className="text-xs sm:text-sm text-gray-600">Monitor all orders</p>
                </div>
              </div>
            </Link>

            <Link 
              to="/admin/settings" 
              className="bg-purple-50 p-3 sm:p-4 rounded-lg hover:bg-purple-100 transition-colors"
            >
              <div className="flex items-center">
                <svg className="h-5 w-5 sm:h-6 sm:w-6 text-purple-600 mr-2 sm:mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <div>
                  <h4 className="text-sm sm:text-base font-medium text-gray-900">Settings</h4>
                  <p className="text-xs sm:text-sm text-gray-600">Platform configuration</p>
                </div>
              </div>
            </Link>
          </div>
        </div>

        {/* Recent Users */}
        <div className="mt-6 sm:mt-8">
          <h3 className="text-base sm:text-lg font-medium text-gray-900 mb-3 sm:mb-4">Recent Users</h3>
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {recentUsers.map((user) => (
                <li key={user.id}>
                  <div className="px-3 sm:px-4 py-3 sm:py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-0">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-8 w-8 sm:h-10 sm:w-10">
                        <img className="h-8 w-8 sm:h-10 sm:w-10 rounded-full" src={user.avatar || '/default-avatar.png'} alt="" />
                      </div>
                      <div className="ml-3 sm:ml-4">
                        <div className="text-xs sm:text-sm font-medium text-gray-900">
                          {user.first_name} {user.last_name}
                        </div>
                        <div className="text-xs sm:text-sm text-gray-500 truncate max-w-[200px] sm:max-w-none">{user.email}</div>
                      </div>
                    </div>
                    <div className="text-xs sm:text-sm text-gray-900 ml-11 sm:ml-0">
                      Role: <span className="font-medium">{user.role}</span>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
            </div>
          </>
        )}

        {activeTab === 'create-vendor' && (
          <div>
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4 sm:mb-6">Create Vendor Account</h2>
            
            <div className="bg-white rounded-lg shadow p-4 sm:p-6 max-w-2xl">
              {createVendorSuccess && (
                <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded text-sm">
                  {createVendorSuccess}
                </div>
              )}
              
              {createVendorError && (
                <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">
                  {createVendorError}
                </div>
              )}

              <form onSubmit={handleCreateVendor} className="space-y-3 sm:space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      First Name
                    </label>
                    <input
                      type="text"
                      value={createVendorForm.first_name}
                      onChange={(e) => setCreateVendorForm(prev => ({
                        ...prev,
                        first_name: e.target.value
                      }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Last Name (Optional)
                    </label>
                    <input
                      type="text"
                      value={createVendorForm.last_name}
                      onChange={(e) => setCreateVendorForm(prev => ({
                        ...prev,
                        last_name: e.target.value
                      }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={createVendorForm.email}
                    onChange={(e) => setCreateVendorForm(prev => ({
                      ...prev,
                      email: e.target.value
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Phone Number (Optional)
                  </label>
                  <input
                    type="tel"
                    value={createVendorForm.phone}
                    onChange={(e) => setCreateVendorForm(prev => ({
                      ...prev,
                      phone: e.target.value
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Business Name
                  </label>
                  <input
                    type="text"
                    value={createVendorForm.business_name}
                    onChange={(e) => setCreateVendorForm(prev => ({
                      ...prev,
                      business_name: e.target.value
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter business name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Business Type
                  </label>
                  <select
                    value={createVendorForm.business_type}
                    onChange={(e) => setCreateVendorForm(prev => ({
                      ...prev,
                      business_type: e.target.value
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="jewelry">Jewelry</option>
                    <option value="accessories">Accessories</option>
                    <option value="luxury">Luxury Items</option>
                    <option value="custom">Custom Jewelry</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Password
                  </label>
                  <input
                    type="password"
                    value={createVendorForm.password}
                    onChange={(e) => setCreateVendorForm(prev => ({
                      ...prev,
                      password: e.target.value
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                    minLength="8"
                  />
                  <p className="text-xs text-gray-500 mt-1">Minimum 8 characters</p>
                </div>

                <button
                  type="submit"
                  disabled={createVendorLoading}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-md font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {createVendorLoading ? 'Creating Vendor...' : 'Create Vendor Account'}
                </button>
              </form>
            </div>
          </div>
        )}

        {activeTab === 'manage-users' && (
          <div>
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4 sm:mb-6">Manage Users</h2>
            <div className="bg-white rounded-lg shadow">
              {usersLoading ? (
                <div className="p-6 text-center text-sm sm:text-base">Loading users...</div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                          <th className="hidden md:table-cell px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                          <th className="px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                          <th className="px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                          <th className="px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {users.map((user) => (
                          <tr key={user.id}>
                            <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="flex-shrink-0 h-8 w-8 sm:h-10 sm:w-10">
                                  <img className="h-8 w-8 sm:h-10 sm:w-10 rounded-full" src={user.avatar || '/default-avatar.png'} alt="" />
                                </div>
                                <div className="ml-2 sm:ml-4">
                                  <div className="text-xs sm:text-sm font-medium text-gray-900">{user.first_name} {user.last_name}</div>
                                  <div className="md:hidden text-xs text-gray-500 truncate max-w-[120px]">{user.email}</div>
                                </div>
                              </div>
                            </td>
                            <td className="hidden md:table-cell px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                              <div className="text-xs sm:text-sm text-gray-900">{user.email}</div>
                            </td>
                            <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                              <span className={`px-2 inline-flex text-[10px] sm:text-xs leading-5 font-semibold rounded-full ${
                                user.role === 'vendor' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'
                              }`}>
                                {user.role}
                              </span>
                            </td>
                            <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                              <span className={`px-2 inline-flex text-[10px] sm:text-xs leading-5 font-semibold rounded-full ${
                                user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                {user.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                            <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap text-xs sm:text-sm font-medium">
                              <button
                                onClick={() => {
                                  const newStatus = !user.is_active;
                                  handleUpdateUser(user.id, { is_active: newStatus });
                                }}
                                className="text-indigo-600 hover:text-indigo-900"
                              >
                                {user.is_active ? 'Deactivate' : 'Activate'}
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Pagination */}
                  <div className="bg-white px-3 sm:px-4 py-3 flex items-center justify-between border-t border-gray-200">
                    <div className="flex-1 flex justify-between sm:hidden">
                      <button
                        onClick={() => fetchUsers(Math.max(0, usersPagination.skip - usersPagination.limit))}
                        disabled={usersPagination.skip === 0}
                        className="relative inline-flex items-center px-3 py-2 border border-gray-300 text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                      >
                        Previous
                      </button>
                      <button
                        onClick={() => fetchUsers(usersPagination.skip + usersPagination.limit)}
                        disabled={usersPagination.skip + usersPagination.limit >= usersPagination.total}
                        className="ml-3 relative inline-flex items-center px-3 py-2 border border-gray-300 text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                      >
                        Next
                      </button>
                    </div>
                    <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                      <div>
                        <p className="text-sm text-gray-700">
                          Showing <span className="font-medium">{usersPagination.skip + 1}</span> to{' '}
                          <span className="font-medium">
                            {Math.min(usersPagination.skip + usersPagination.limit, usersPagination.total)}
                          </span>{' '}
                          of <span className="font-medium">{usersPagination.total}</span> results
                        </p>
                      </div>
                      <div>
                        <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                          <button
                            onClick={() => fetchUsers(Math.max(0, usersPagination.skip - usersPagination.limit))}
                            disabled={usersPagination.skip === 0}
                            className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                          >
                            Previous
                          </button>
                          <button
                            onClick={() => fetchUsers(usersPagination.skip + usersPagination.limit)}
                            disabled={usersPagination.skip + usersPagination.limit >= usersPagination.total}
                            className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                          >
                            Next
                          </button>
                        </nav>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {activeTab === 'create-user' && (
          <div>
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4 sm:mb-6">Create User Account</h2>
            
            <div className="bg-white rounded-lg shadow p-4 sm:p-6 max-w-2xl">
              {createUserSuccess && (
                <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded text-sm">
                  {createUserSuccess}
                </div>
              )}
              
              {createUserError && (
                <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">
                  {createUserError}
                </div>
              )}

              <form onSubmit={handleCreateUser} className="space-y-3 sm:space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      First Name
                    </label>
                    <input
                      type="text"
                      value={createUserForm.first_name}
                      onChange={(e) => setCreateUserForm(prev => ({
                        ...prev,
                        first_name: e.target.value
                      }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Last Name (Optional)
                    </label>
                    <input
                      type="text"
                      value={createUserForm.last_name}
                      onChange={(e) => setCreateUserForm(prev => ({
                        ...prev,
                        last_name: e.target.value
                      }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={createUserForm.email}
                    onChange={(e) => setCreateUserForm(prev => ({
                      ...prev,
                      email: e.target.value
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Phone Number (Optional)
                  </label>
                  <input
                    type="tel"
                    value={createUserForm.phone}
                    onChange={(e) => setCreateUserForm(prev => ({
                      ...prev,
                      phone: e.target.value
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Role
                  </label>
                  <select
                    value={createUserForm.role}
                    onChange={(e) => setCreateUserForm(prev => ({
                      ...prev,
                      role: e.target.value
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="customer">Customer</option>
                    <option value="vendor">Vendor</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Password
                  </label>
                  <input
                    type="password"
                    value={createUserForm.password}
                    onChange={(e) => setCreateUserForm(prev => ({
                      ...prev,
                      password: e.target.value
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                    minLength="8"
                  />
                  <p className="text-xs text-gray-500 mt-1">Minimum 8 characters</p>
                </div>

                <button
                  type="submit"
                  disabled={createUserLoading}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-md font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {createUserLoading ? 'Creating User...' : 'Create User Account'}
                </button>
              </form>
            </div>
          </div>
        )}

        {activeTab === 'manage-vendors' && (
          <div>
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4 sm:mb-6">Manage Vendors</h2>
            <div className="bg-white rounded-lg shadow">
              {vendorsLoading ? (
                <div className="p-6 text-center text-sm sm:text-base">Loading vendors...</div>
              ) : vendors.length === 0 ? (
                <div className="p-6 text-center text-gray-500 text-sm sm:text-base">
                  No vendors found. Create a vendor account to see them here.
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vendor</th>
                          <th className="hidden lg:table-cell px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Business</th>
                          <th className="hidden md:table-cell px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                          <th className="px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                          <th className="px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {vendors.map((vendor) => (
                          <tr key={vendor.id}>
                            <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                              <div>
                                <div className="text-xs sm:text-sm font-medium text-gray-900">
                                  {vendor.first_name} {vendor.last_name}
                                </div>
                                <div className="md:hidden text-xs text-gray-500 truncate max-w-[120px]">{vendor.email}</div>
                                <div className="lg:hidden text-xs text-gray-500">{vendor.business_name || 'N/A'}</div>
                              </div>
                            </td>
                            <td className="hidden lg:table-cell px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                              <div className="text-xs sm:text-sm text-gray-900">{vendor.business_name || 'N/A'}</div>
                              <div className="text-xs text-gray-500">{vendor.business_type || 'N/A'}</div>
                            </td>
                            <td className="hidden md:table-cell px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                              <div className="text-xs sm:text-sm text-gray-900">{vendor.email}</div>
                            </td>
                            <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                              <span className={`px-2 inline-flex text-[10px] sm:text-xs leading-5 font-semibold rounded-full ${
                                vendor.status === 'active' 
                                  ? 'bg-green-100 text-green-800' 
                                  : vendor.status === 'inactive' 
                                    ? 'bg-red-100 text-red-800'
                                    : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {vendor.status === 'active' ? 'Active' : vendor.status === 'inactive' ? 'Inactive' : vendor.status || 'Pending'}
                              </span>
                              <div className="hidden sm:block text-xs text-gray-500 mt-1">
                                Business: <span className="font-medium">{vendor.business_status || 'pending'}</span>
                              </div>
                            </td>
                            <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap text-xs sm:text-sm font-medium">
                              {vendor.business_status === 'pending' || !vendor.business_status ? (
                                <div className="flex flex-col sm:flex-row gap-1 sm:gap-2">
                                  <button
                                    onClick={() => handleVendorApproval(vendor.id, true, 'Approved by admin')}
                                    className="text-green-600 hover:text-green-900"
                                  >
                                    Approve
                                  </button>
                                  <button
                                    onClick={() => handleVendorApproval(vendor.id, false, 'Rejected by admin')}
                                    className="text-red-600 hover:text-red-900"
                                  >
                                    Reject
                                  </button>
                                </div>
                              ) : vendor.status === 'active' ? (
                                <button
                                  onClick={() => {
                                    if (confirm('Deactivate this vendor?')) {
                                      handleVendorApproval(vendor.id, false, 'Deactivated by admin');
                                    }
                                  }}
                                  className="text-orange-600 hover:text-orange-900"
                                >
                                  Deactivate
                                </button>
                              ) : (
                                <button
                                  onClick={() => handleVendorApproval(vendor.id, true, 'Reactivated by admin')}
                                  className="text-green-600 hover:text-green-900"
                                >
                                  Activate
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Pagination */}
                  <div className="bg-white px-3 sm:px-4 py-3 flex items-center justify-between border-t border-gray-200">
                    <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                      <div>
                        <p className="text-sm text-gray-700">
                          Showing <span className="font-medium">{vendorsPagination.skip + 1}</span> to{' '}
                          <span className="font-medium">
                            {Math.min(vendorsPagination.skip + vendorsPagination.limit, vendorsPagination.total)}
                          </span>{' '}
                          of <span className="font-medium">{vendorsPagination.total}</span> results
                        </p>
                      </div>
                      <div>
                        <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                          <button
                            onClick={() => fetchVendors(Math.max(0, vendorsPagination.skip - vendorsPagination.limit))}
                            disabled={vendorsPagination.skip === 0}
                            className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                          >
                            Previous
                          </button>
                          <button
                            onClick={() => fetchVendors(vendorsPagination.skip + vendorsPagination.limit)}
                            disabled={vendorsPagination.skip + vendorsPagination.limit >= vendorsPagination.total}
                            className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                          >
                            Next
                          </button>
                        </nav>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {activeTab === 'audit-logs' && (
          <div>
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4 sm:mb-6">Audit Logs</h2>
            <div className="bg-white rounded-lg shadow">
              {auditLogsLoading ? (
                <div className="p-6 text-center text-sm sm:text-base">Loading audit logs...</div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                          <th className="px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                          <th className="hidden md:table-cell px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entity</th>
                          <th className="hidden lg:table-cell px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Performed By</th>
                          <th className="hidden xl:table-cell px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Details</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {auditLogs.map((log, index) => (
                          <tr key={index}>
                            <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap text-xs sm:text-sm text-gray-900">
                              {new Date(log.timestamp).toLocaleString('en-US', { 
                                month: 'short', 
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </td>
                            <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                              <span className="px-2 inline-flex text-[10px] sm:text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                                {log.action}
                              </span>
                            </td>
                            <td className="hidden md:table-cell px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap text-xs sm:text-sm text-gray-500">
                              {log.entity_type} ({log.entity_id})
                            </td>
                            <td className="hidden lg:table-cell px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap text-xs sm:text-sm text-gray-500">
                              {log.performed_by}
                            </td>
                            <td className="hidden xl:table-cell px-3 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm text-gray-500">
                              {JSON.stringify(log.changes || {}).substring(0, 50)}...
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Pagination */}
                  <div className="bg-white px-3 sm:px-4 py-3 flex items-center justify-between border-t border-gray-200">
                    <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                      <div>
                        <p className="text-sm text-gray-700">
                          Showing <span className="font-medium">{auditLogsPagination.skip + 1}</span> to{' '}
                          <span className="font-medium">
                            {Math.min(auditLogsPagination.skip + auditLogsPagination.limit, auditLogsPagination.total)}
                          </span>{' '}
                          of <span className="font-medium">{auditLogsPagination.total}</span> results
                        </p>
                      </div>
                      <div>
                        <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                          <button
                            onClick={() => fetchAuditLogs(Math.max(0, auditLogsPagination.skip - auditLogsPagination.limit))}
                            disabled={auditLogsPagination.skip === 0}
                            className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                          >
                            Previous
                          </button>
                          <button
                            onClick={() => fetchAuditLogs(auditLogsPagination.skip + auditLogsPagination.limit)}
                            disabled={auditLogsPagination.skip + auditLogsPagination.limit >= auditLogsPagination.total}
                            className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                          >
                            Next
                          </button>
                        </nav>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div>
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4 sm:mb-6">Platform Settings</h2>
            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
              {settingsLoading ? (
                <div className="text-center text-sm sm:text-base">Loading settings...</div>
              ) : settings ? (
                <div className="space-y-3 sm:space-y-4">
                  <h3 className="text-base sm:text-lg font-medium">Current Settings</h3>
                  <pre className="bg-gray-100 p-3 sm:p-4 rounded overflow-auto text-xs sm:text-sm">
                    {JSON.stringify(settings, null, 2)}
                  </pre>
                  <p className="text-xs sm:text-sm text-gray-500">Settings management interface coming soon...</p>
                </div>
              ) : (
                <p className="text-gray-600 text-sm sm:text-base">No settings available</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'regions' && (
          <div>
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4 sm:mb-6">Create Region</h2>
            
            <div className="bg-white rounded-lg shadow p-4 sm:p-6 max-w-2xl">
              {createRegionSuccess && (
                <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded text-sm">
                  {createRegionSuccess}
                </div>
              )}
              
              {createRegionError && (
                <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">
                  {createRegionError}
                </div>
              )}

              <form onSubmit={handleCreateRegion} className="space-y-3 sm:space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Region Code
                  </label>
                  <input
                    type="text"
                    value={createRegionForm.code}
                    onChange={(e) => setCreateRegionForm(prev => ({
                      ...prev,
                      code: e.target.value.toUpperCase()
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., IN, US, UK"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Region Name
                  </label>
                  <input
                    type="text"
                    value={createRegionForm.name}
                    onChange={(e) => setCreateRegionForm(prev => ({
                      ...prev,
                      name: e.target.value
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., India"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Country
                  </label>
                  <input
                    type="text"
                    value={createRegionForm.country}
                    onChange={(e) => setCreateRegionForm(prev => ({
                      ...prev,
                      country: e.target.value
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., India, United States"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Currency
                  </label>
                  <input
                    type="text"
                    value={createRegionForm.currency}
                    onChange={(e) => setCreateRegionForm(prev => ({
                      ...prev,
                      currency: e.target.value.toUpperCase()
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., INR, USD, GBP"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Timezone
                  </label>
                  <input
                    type="text"
                    value={createRegionForm.timezone}
                    onChange={(e) => setCreateRegionForm(prev => ({
                      ...prev,
                      timezone: e.target.value
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Asia/Kolkata"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tax Rate (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="100"
                    value={createRegionForm.tax_rate}
                    onChange={(e) => setCreateRegionForm(prev => ({
                      ...prev,
                      tax_rate: parseFloat(e.target.value)
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={createRegionLoading}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-md font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {createRegionLoading ? 'Creating Region...' : 'Create Region'}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;