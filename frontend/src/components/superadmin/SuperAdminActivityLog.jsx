import React, { useState, useEffect } from 'react';

const SuperAdminActivityLog = () => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [filters, setFilters] = useState({
    activity_type: '',
    start_date: '',
    end_date: '',
    search: ''
  });
  
  const [pagination, setPagination] = useState({
    skip: 0,
    limit: 50,
    total: 0
  });

  useEffect(() => {
    fetchActivityLog();
  }, [pagination.skip, pagination.limit, filters]);

  // Reset pagination when filters change
  useEffect(() => {
    setPagination(prev => ({ ...prev, skip: 0 }));
  }, [filters.activity_type, filters.start_date, filters.end_date, filters.search]);

  const fetchActivityLog = async () => {
    try {
      setLoading(true);
      setError('');
      const token = localStorage.getItem('accessToken');
      
      const params = new URLSearchParams({
        skip: pagination.skip.toString(),
        limit: pagination.limit.toString(),
      });
      
      if (filters.activity_type) params.append('activity_type', filters.activity_type);
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (filters.search) params.append('search', filters.search);

      const response = await fetch(
        `http://localhost:5858/api/super-admin/activity-log?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setActivities(data.activities || []);
        setPagination(prev => ({ ...prev, total: data.total || 0 }));
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to fetch activity log');
      }
    } catch (error) {
      console.error('Error fetching activity log:', error);
      setError('An error occurred while fetching activity log');
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = () => {
    // Create CSV headers
    const headers = ['Date & Time', 'Activity Type', 'Actor', 'Actor Email', 'Actor Role', 'Target Name', 'Target Email', 'Business Name', 'Business Type', 'Approval Status', 'Details'];
    
    // Create CSV rows
    const rows = activities.map(activity => [
      new Date(activity.created_at).toLocaleString(),
      activity.activity_type,
      activity.actor_name || activity.actor_email || 'System',
      activity.actor_email || '',
      activity.actor_role || '',
      activity.target_name || activity.target_email || 'N/A',
      activity.target_email || '',
      activity.vendor_details?.business_name || '',
      activity.vendor_details?.business_type || '',
      activity.vendor_details?.approval_status || '',
      activity.description || ''
    ]);
    
    // Combine headers and rows
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');
    
    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `activity_log_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case 'vendor_created':
        return '➕';
      case 'vendor_updated':
        return '✏️';
      case 'vendor_deleted':
        return '🗑️';
      case 'vendor_approved':
        return '✅';
      case 'vendor_rejected':
        return '❌';
      case 'admin_created':
        return '👤➕';
      case 'admin_deleted':
        return '👤🗑️';
      default:
        return '📝';
    }
  };

  const getActivityColor = (type) => {
    switch (type) {
      case 'vendor_created':
      case 'admin_created':
      case 'vendor_approved':
        return 'bg-green-100 text-green-800';
      case 'vendor_updated':
        return 'bg-blue-100 text-blue-800';
      case 'vendor_deleted':
      case 'admin_deleted':
      case 'vendor_rejected':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Activity Log</h2>
          <p className="text-sm text-gray-600 mt-1">
            Track all vendor and admin creation, updates, and deletions
          </p>
        </div>
        <button
          onClick={exportToCSV}
          disabled={activities.length === 0}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Export CSV
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Activity Type
            </label>
            <select
              value={filters.activity_type}
              onChange={(e) => setFilters(prev => ({ ...prev, activity_type: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="">All Activities</option>
              <option value="vendor_created">Vendor Created</option>
              <option value="vendor_updated">Vendor Updated</option>
              <option value="vendor_deleted">Vendor Deleted</option>
              <option value="vendor_approved">Vendor Approved</option>
              <option value="vendor_rejected">Vendor Rejected</option>
              <option value="admin_created">Admin Created</option>
              <option value="admin_deleted">Admin Deleted</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <input
              type="text"
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
              placeholder="Search by name or email..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) => setFilters(prev => ({ ...prev, start_date: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) => setFilters(prev => ({ ...prev, end_date: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
        </div>
        
        {(filters.activity_type || filters.search || filters.start_date || filters.end_date) && (
          <button
            onClick={() => setFilters({ activity_type: '', search: '', start_date: '', end_date: '' })}
            className="text-sm text-purple-600 hover:text-purple-700 font-medium"
          >
            Clear all filters
          </button>
        )}
      </div>

      {/* Stats Card */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg shadow-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold mb-1">Total Activities</h3>
            <p className="text-3xl font-bold">{pagination.total}</p>
          </div>
          <div className="bg-white bg-opacity-20 p-4 rounded-full">
            <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
        </div>
      </div>

      {/* Activity Log Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
            <p className="mt-4 text-gray-600">Loading activity log...</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date & Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Activity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Performed By
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Target
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Details
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {activities.map((activity, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(activity.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1 px-3 py-1 text-xs font-medium rounded-full ${getActivityColor(activity.activity_type)}`}>
                          <span>{getActivityIcon(activity.activity_type)}</span>
                          {activity.activity_type.replace(/_/g, ' ').toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {activity.actor_name || 'System'}
                        </div>
                        <div className="text-xs text-gray-500">
                          {activity.actor_email || ''}
                        </div>
                        {activity.actor_role && (
                          <div className="text-xs text-purple-600 font-medium mt-1">
                            {activity.actor_role === 'admin' ? '👨‍💼 Admin' : 
                             activity.actor_role === 'super_admin' ? '⭐ Super Admin' : 
                             activity.actor_role}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {activity.target_name || 'N/A'}
                        </div>
                        <div className="text-xs text-gray-500">
                          {activity.target_email || ''}
                        </div>
                        {activity.vendor_details && (
                          <div className="mt-2 space-y-1">
                            <div className="text-xs">
                              <span className="font-semibold text-gray-700">Business:</span>{' '}
                              <span className="text-gray-600">{activity.vendor_details.business_name}</span>
                            </div>
                            <div className="text-xs">
                              <span className="font-semibold text-gray-700">Type:</span>{' '}
                              <span className="text-gray-600">{activity.vendor_details.business_type}</span>
                            </div>
                            <div className="text-xs">
                              <span className="font-semibold text-gray-700">Status:</span>{' '}
                              <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                                activity.vendor_details.approval_status === 'approved' ? 'bg-green-100 text-green-800' :
                                activity.vendor_details.approval_status === 'rejected' ? 'bg-red-100 text-red-800' :
                                'bg-yellow-100 text-yellow-800'
                              }`}>
                                {activity.vendor_details.approval_status}
                              </span>
                            </div>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-700 max-w-md">
                          {activity.description || 'No additional details'}
                        </div>
                        {activity.vendor_details?.business_description && (
                          <div className="mt-2 text-xs text-gray-500 italic">
                            "{activity.vendor_details.business_description.substring(0, 100)}
                            {activity.vendor_details.business_description.length > 100 ? '...' : ''}"
                          </div>
                        )}
                        {activity.vendor_details?.contact_phone && (
                          <div className="mt-1 text-xs text-gray-600">
                            📞 {activity.vendor_details.contact_phone}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {activities.length === 0 && (
                <div className="text-center py-12">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No activity found</h3>
                  <p className="mt-1 text-sm text-gray-500">No activities match your current filters.</p>
                </div>
              )}
            </div>

            {/* Pagination */}
            {pagination.total > 0 && (
              <div className="bg-gray-50 px-6 py-3 flex items-center justify-between border-t border-gray-200">
                <div className="text-sm text-gray-700">
                  Showing {pagination.skip + 1} to {Math.min(pagination.skip + pagination.limit, pagination.total)} of {pagination.total} activities
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPagination(prev => ({ ...prev, skip: Math.max(0, prev.skip - prev.limit) }))}
                    disabled={pagination.skip === 0}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPagination(prev => ({ ...prev, skip: prev.skip + prev.limit }))}
                    disabled={pagination.skip + pagination.limit >= pagination.total}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default SuperAdminActivityLog;
