import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import SuperAdminUsers from '../superadmin/SuperAdminUsers';
import SuperAdminVendors from '../superadmin/SuperAdminVendors';
import SuperAdminAdmins from '../superadmin/SuperAdminAdmins';
import SuperAdminSettings from '../superadmin/SuperAdminSettings';
import SuperAdminAnalytics from '../superadmin/SuperAdminAnalytics';
import SuperAdminActivityLog from '../superadmin/SuperAdminActivityLog';

const SuperAdminDashboard = () => {
  const { user, logout } = useAuth();
  
  // Get initial tab from URL hash or default to 'overview'
  const getInitialTab = () => {
    const hash = window.location.hash.replace('#', '');
    const validTabs = ['overview', 'users', 'vendors', 'admins', 'analytics', 'activity-log', 'settings'];
    return validTabs.includes(hash) ? hash : 'overview';
  };
  
  const [activeTab, setActiveTab] = useState(getInitialTab);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [loading, setLoading] = useState(false);

  // Update URL hash when tab changes
  const handleTabChange = (newTab) => {
    setActiveTab(newTab);
    window.location.hash = newTab;
  };

  // Listen for hash changes (browser back/forward)
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      const validTabs = ['overview', 'users', 'vendors', 'admins', 'analytics', 'activity-log', 'settings'];
      if (validTabs.includes(hash)) {
        setActiveTab(hash);
      }
    };
    
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Fetch dashboard stats
  const fetchDashboardStats = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('accessToken');
      const response = await fetch('http://localhost:5858/api/super-admin/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setDashboardStats(data);
      } else {
        console.error('Failed to fetch dashboard stats');
      }
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'overview') {
      fetchDashboardStats();
    }
  }, [activeTab]);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-14 sm:h-16">
            <div className="flex items-center">
              <h1 className="text-lg sm:text-xl md:text-2xl font-bold text-gray-900">Super Admin Dashboard</h1>
              <span className="ml-2 sm:ml-3 px-2 py-1 bg-purple-100 text-purple-800 text-[10px] sm:text-xs font-medium rounded">
                SUPER ADMIN
              </span>
            </div>
            
            {/* Desktop user info and logout */}
            <div className="hidden md:flex items-center space-x-3 lg:space-x-4">
              <span className="text-xs lg:text-sm text-gray-700">
                Welcome, {user?.first_name} {user?.last_name}
              </span>
              <button
                onClick={logout}
                className="bg-red-600 text-white px-3 lg:px-4 py-2 rounded-md text-xs lg:text-sm font-medium hover:bg-red-700"
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
                <p className="text-sm font-medium text-gray-900">
                  {user?.first_name} {user?.last_name}
                </p>
                <span className="inline-block mt-1 px-2 py-1 bg-purple-100 text-purple-800 text-xs font-medium rounded">
                  SUPER ADMIN
                </span>
              </div>
              
              {/* Navigation in mobile */}
              {[
                { id: 'overview', name: 'Overview', icon: '📊' },
                { id: 'users', name: 'Users', icon: '👥' },
                { id: 'vendors', name: 'Vendors', icon: '🏪' },
                { id: 'admins', name: 'Admins', icon: '👨‍💼' },
                { id: 'analytics', name: 'Analytics', icon: '📈' },
                { id: 'activity-log', name: 'Activity Log', icon: '📋' },
                { id: 'settings', name: 'Settings', icon: '⚙️' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => {
                    handleTabChange(tab.id);
                    setIsMobileMenuOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium flex items-center gap-2 ${
                    activeTab === tab.id
                      ? 'bg-purple-50 text-purple-600'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <span>{tab.icon}</span>
                  {tab.name}
                </button>
              ))}
              
              {/* Logout button in mobile */}
              <button
                onClick={logout}
                className="w-full text-left px-3 py-2 rounded-md text-sm font-medium text-red-600 hover:bg-red-50"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Navigation Tabs - Desktop only */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4 sm:mt-6">
        <nav className="hidden md:flex space-x-4 lg:space-x-8 overflow-x-auto">
          {[
            { id: 'overview', name: 'Overview', icon: '📊' },
            { id: 'users', name: 'Users', icon: '👥' },
            { id: 'vendors', name: 'Vendors', icon: '🏪' },
            { id: 'admins', name: 'Admins', icon: '👨‍💼' },
            { id: 'analytics', name: 'Analytics', icon: '📈' },
            { id: 'activity-log', name: 'Activity Log', icon: '📋' },
            { id: 'settings', name: 'Settings', icon: '⚙️' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-xs lg:text-sm flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span>{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
        {activeTab === 'overview' && (
          <div>
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4 sm:mb-6">System Overview</h2>
            
            {/* Stats Grid */}
            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                <p className="mt-4 text-gray-600">Loading dashboard...</p>
              </div>
            ) : dashboardStats ? (
              <>
                <div className="grid grid-cols-2 gap-3 sm:gap-6 lg:grid-cols-4 mb-6 sm:mb-8">
                  <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-4 sm:p-6 rounded-lg shadow-lg text-white">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-xs sm:text-sm font-medium opacity-90">Total Users</h3>
                        <p className="text-xl sm:text-2xl font-bold mt-1">{dashboardStats.total_users}</p>
                      </div>
                      <svg className="w-8 h-8 sm:w-10 sm:h-10 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                      </svg>
                    </div>
                  </div>
                  <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-4 sm:p-6 rounded-lg shadow-lg text-white">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-xs sm:text-sm font-medium opacity-90">Admins</h3>
                        <p className="text-xl sm:text-2xl font-bold mt-1">{dashboardStats.admins}</p>
                      </div>
                      <svg className="w-8 h-8 sm:w-10 sm:h-10 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                    </div>
                  </div>
                  <div className="bg-gradient-to-br from-green-500 to-green-600 p-4 sm:p-6 rounded-lg shadow-lg text-white">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-xs sm:text-sm font-medium opacity-90">Vendors</h3>
                        <p className="text-xl sm:text-2xl font-bold mt-1">{dashboardStats.vendors}</p>
                      </div>
                      <svg className="w-8 h-8 sm:w-10 sm:h-10 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                    </div>
                  </div>
                  <div className="bg-gradient-to-br from-orange-500 to-orange-600 p-4 sm:p-6 rounded-lg shadow-lg text-white">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-xs sm:text-sm font-medium opacity-90">Customers</h3>
                        <p className="text-xl sm:text-2xl font-bold mt-1">{dashboardStats.customers}</p>
                      </div>
                      <svg className="w-8 h-8 sm:w-10 sm:h-10 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                  </div>
                </div>

                {/* Recent Users */}
                {dashboardStats.recent_users && (
                  <div className="bg-white rounded-lg shadow">
                    <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-gray-200">
                      <h3 className="text-base sm:text-lg font-medium text-gray-900">Recent User Registrations</h3>
                    </div>
                    <div className="p-3 sm:p-6">
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                User
                              </th>
                              <th className="px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Role
                              </th>
                              <th className="hidden sm:table-cell px-3 sm:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Registered
                              </th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {dashboardStats.recent_users.map((user, index) => (
                              <tr key={index}>
                                <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                                  <div>
                                    <div className="text-xs sm:text-sm font-medium text-gray-900">
                                      {user.first_name} {user.last_name}
                                    </div>
                                    <div className="text-xs text-gray-500 truncate max-w-[150px] sm:max-w-none">{user.email}</div>
                                  </div>
                                </td>
                                <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                                  <span className={`inline-flex px-2 py-1 text-[10px] sm:text-xs font-medium rounded-full ${
                                    user.role === 'admin' ? 'bg-purple-100 text-purple-800' :
                                    user.role === 'vendor' ? 'bg-blue-100 text-blue-800' :
                                    'bg-green-100 text-green-800'
                                  }`}>
                                    {user.role}
                                  </span>
                                </td>
                                <td className="hidden sm:table-cell px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap text-xs sm:text-sm text-gray-500">
                                  {new Date(user.created_at).toLocaleDateString('en-US', {
                                    year: 'numeric',
                                    month: 'short',
                                    day: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <p className="text-gray-500">No dashboard data available</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'users' && <SuperAdminUsers />}
        {activeTab === 'vendors' && <SuperAdminVendors />}
        {activeTab === 'admins' && <SuperAdminAdmins />}
        {activeTab === 'analytics' && <SuperAdminAnalytics />}
        {activeTab === 'activity-log' && <SuperAdminActivityLog />}
        {activeTab === 'settings' && <SuperAdminSettings />}
      </div>
    </div>
  );
};

export default SuperAdminDashboard;