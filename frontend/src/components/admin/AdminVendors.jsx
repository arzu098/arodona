import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const AdminVendors = () => {
  const { user } = useAuth();
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    search: ''
  });
  const [pagination, setPagination] = useState({
    skip: 0,
    limit: 10,
    total: 0
  });

  useEffect(() => {
    fetchVendors();
  }, [filters, pagination.skip, pagination.limit]);

  const fetchVendors = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('accessToken');
      
      const params = new URLSearchParams({
        skip: pagination.skip.toString(),
        limit: pagination.limit.toString()
      });
      
      if (filters.status) params.append('status', filters.status);
      
      const response = await fetch(`http://localhost:5858/api/admin/vendors?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setVendors(data.vendors || []);
        setPagination(prev => ({
          ...prev,
          total: data.total || 0
        }));
      } else {
        setError('Failed to fetch vendors');
      }
    } catch (error) {
      console.error('Error fetching vendors:', error);
      setError('Error loading vendors');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveVendor = async (vendorId, approved, remarks = '') => {
    try {
      setError('');
      setSuccess('');
      const token = localStorage.getItem('accessToken');
      
      const response = await fetch(`http://localhost:5858/api/admin/vendors/${vendorId}/approve`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          approved, 
          remarks: remarks || (approved ? 'Approved by admin' : 'Rejected by admin')
        })
      });

      if (response.ok) {
        setSuccess(`Vendor ${approved ? 'approved' : 'rejected'} successfully`);
        fetchVendors(); // Refresh the list
      } else {
        const data = await response.json();
        setError(data.detail || `Failed to ${approved ? 'approve' : 'reject'} vendor`);
      }
    } catch (error) {
      console.error('Error updating vendor status:', error);
      setError('Error updating vendor status');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const totalPages = Math.ceil(pagination.total / pagination.limit);
  const currentPage = Math.floor(pagination.skip / pagination.limit) + 1;

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Link to="/admin/dashboard" className="text-blue-600 hover:text-blue-800 mr-4">
                ← Back to Dashboard
              </Link>
              <h1 className="text-2xl font-bold text-gray-900">Vendor Management</h1>
            </div>
            <div className="text-sm text-gray-600">
              Admin: {user?.first_name} {user?.last_name}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Filters */}
        <div className="bg-white rounded-lg shadow mb-6 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Status</option>
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search
              </label>
              <input
                type="text"
                placeholder="Search by name, email, or business..."
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Messages */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        
        {success && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
            {success}
          </div>
        )}

        {/* Vendors Table */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Vendors ({pagination.total})
              </h3>
            </div>

            {loading ? (
              <div className="text-center py-8">
                <div className="text-gray-500">Loading vendors...</div>
              </div>
            ) : vendors.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-gray-500">No vendors found</div>
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Vendor
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Contact
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Business
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Registered
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {vendors.map((vendor) => (
                        <tr key={vendor.id}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="flex-shrink-0 h-10 w-10">
                                <img 
                                  className="h-10 w-10 rounded-full" 
                                  src={vendor.avatar || '/default-avatar.png'} 
                                  alt=""
                                />
                              </div>
                              <div className="ml-4">
                                <div className="text-sm font-medium text-gray-900">
                                  {vendor.first_name} {vendor.last_name}
                                </div>
                                <div className="text-sm text-gray-500">
                                  ID: {vendor.id}
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">{vendor.email}</div>
                            <div className="text-sm text-gray-500">{vendor.phone || 'No phone'}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">
                              {vendor.business_name || 'Not specified'}
                            </div>
                            <div className="text-sm text-gray-500">
                              {vendor.business_description || 'No description'}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(vendor.status || 'pending')}`}>
                              {vendor.status || 'pending'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatDate(vendor.created_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              {(!vendor.status || vendor.status === 'pending') && (
                                <>
                                  <button
                                    onClick={() => handleApproveVendor(vendor.id, true)}
                                    className="text-green-600 hover:text-green-900 px-3 py-1 bg-green-100 hover:bg-green-200 rounded text-xs"
                                  >
                                    Approve
                                  </button>
                                  <button
                                    onClick={() => handleApproveVendor(vendor.id, false)}
                                    className="text-red-600 hover:text-red-900 px-3 py-1 bg-red-100 hover:bg-red-200 rounded text-xs"
                                  >
                                    Reject
                                  </button>
                                </>
                              )}
                              {vendor.status === 'approved' && (
                                <button
                                  onClick={() => handleApproveVendor(vendor.id, false, 'Suspended by admin')}
                                  className="text-red-600 hover:text-red-900 px-3 py-1 bg-red-100 hover:bg-red-200 rounded text-xs"
                                >
                                  Suspend
                                </button>
                              )}
                              {vendor.status === 'rejected' && (
                                <button
                                  onClick={() => handleApproveVendor(vendor.id, true, 'Reinstated by admin')}
                                  className="text-green-600 hover:text-green-900 px-3 py-1 bg-green-100 hover:bg-green-200 rounded text-xs"
                                >
                                  Reinstate
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6 mt-4">
                  <div className="flex-1 flex justify-between sm:hidden">
                    <button
                      onClick={() => setPagination(prev => ({ ...prev, skip: Math.max(0, prev.skip - prev.limit) }))}
                      disabled={pagination.skip === 0}
                      className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setPagination(prev => ({ ...prev, skip: prev.skip + prev.limit }))}
                      disabled={pagination.skip + pagination.limit >= pagination.total}
                      className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                  <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm text-gray-700">
                        Showing <span className="font-medium">{pagination.skip + 1}</span> to{' '}
                        <span className="font-medium">
                          {Math.min(pagination.skip + pagination.limit, pagination.total)}
                        </span>{' '}
                        of <span className="font-medium">{pagination.total}</span> results
                      </p>
                    </div>
                    <div>
                      <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                        <button
                          onClick={() => setPagination(prev => ({ ...prev, skip: Math.max(0, prev.skip - prev.limit) }))}
                          disabled={pagination.skip === 0}
                          className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                        >
                          Previous
                        </button>
                        <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                          Page {currentPage} of {totalPages}
                        </span>
                        <button
                          onClick={() => setPagination(prev => ({ ...prev, skip: prev.skip + prev.limit }))}
                          disabled={pagination.skip + pagination.limit >= pagination.total}
                          className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
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
      </div>
    </div>
  );
};

export default AdminVendors;