import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';

const SuperAdminAnalytics = () => {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(30); // days
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError('');
      const token = localStorage.getItem('accessToken');
      
      const response = await fetch(
        `http://localhost:5858/api/super-admin/analytics?days=${timeRange}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      } else {
        setError('Failed to fetch analytics');
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
      setError('An error occurred while fetching analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
          <p className="mt-4 text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  // Mock data for demonstration if API doesn't return data
  const mockAnalytics = {
    total_users: 1250,
    total_vendors: 85,
    total_orders: 3420,
    total_revenue: 5240000,
    active_users: 890,
    new_users_this_month: 145,
    orders_this_month: 420,
    revenue_this_month: 680000,
    top_products: [
      { name: 'Diamond Ring', sales: 145, revenue: 450000 },
      { name: 'Gold Necklace', sales: 98, revenue: 320000 },
      { name: 'Pearl Earrings', sales: 87, revenue: 180000 },
      { name: 'Silver Bracelet', sales: 65, revenue: 95000 },
      { name: 'Platinum Chain', sales: 52, revenue: 280000 }
    ],
    top_vendors: [
      { name: 'Luxury Jewels', orders: 245, revenue: 1200000 },
      { name: 'Royal Gems', orders: 198, revenue: 980000 },
      { name: 'Diamond Palace', orders: 156, revenue: 750000 },
      { name: 'Golden Touch', orders: 132, revenue: 620000 },
      { name: 'Silver Star', orders: 98, revenue: 450000 }
    ],
    user_growth: [
      { month: 'Jan', users: 950 },
      { month: 'Feb', users: 1020 },
      { month: 'Mar', users: 1100 },
      { month: 'Apr', users: 1180 },
      { month: 'May', users: 1250 }
    ],
    revenue_growth: [
      { month: 'Jan', revenue: 850000 },
      { month: 'Feb', revenue: 920000 },
      { month: 'Mar', revenue: 1100000 },
      { month: 'Apr', revenue: 1350000 },
      { month: 'May', revenue: 1520000 }
    ]
  };

  const data = analytics || mockAnalytics;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Platform Analytics</h2>
          <p className="text-sm text-gray-600 mt-1">
            Comprehensive insights and performance metrics
          </p>
        </div>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(parseInt(e.target.value))}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
          <option value={365}>Last year</option>
        </select>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm font-medium">Total Users</p>
              <p className="text-3xl font-bold mt-2">{data.total_users?.toLocaleString()}</p>
              <p className="text-blue-100 text-xs mt-2">+{data.new_users_this_month} this month</p>
            </div>
            <div className="bg-blue-400 bg-opacity-30 p-3 rounded-full">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-sm font-medium">Total Revenue</p>
              <p className="text-3xl font-bold mt-2">₹{(data.total_revenue / 1000).toFixed(0)}K</p>
              <p className="text-green-100 text-xs mt-2">₹{(data.revenue_this_month / 1000).toFixed(0)}K this month</p>
            </div>
            <div className="bg-green-400 bg-opacity-30 p-3 rounded-full">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-sm font-medium">Total Orders</p>
              <p className="text-3xl font-bold mt-2">{data.total_orders?.toLocaleString()}</p>
              <p className="text-purple-100 text-xs mt-2">+{data.orders_this_month} this month</p>
            </div>
            <div className="bg-purple-400 bg-opacity-30 p-3 rounded-full">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-100 text-sm font-medium">Total Vendors</p>
              <p className="text-3xl font-bold mt-2">{data.total_vendors}</p>
              <p className="text-orange-100 text-xs mt-2">{data.active_users} active users</p>
            </div>
            <div className="bg-orange-400 bg-opacity-30 p-3 rounded-full">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Growth Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">User Growth Trend</h3>
          <div className="space-y-3">
            {data.user_growth?.map((item, index) => (
              <div key={index} className="flex items-center gap-4">
                <span className="text-sm font-medium text-gray-600 w-12">{item.month}</span>
                <div className="flex-1 bg-gray-200 rounded-full h-6">
                  <div
                    className="bg-blue-600 h-6 rounded-full flex items-center justify-end pr-2"
                    style={{ width: `${(item.users / data.total_users) * 100}%` }}
                  >
                    <span className="text-xs text-white font-medium">{item.users}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Revenue Growth Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue Growth Trend</h3>
          <div className="space-y-3">
            {data.revenue_growth?.map((item, index) => (
              <div key={index} className="flex items-center gap-4">
                <span className="text-sm font-medium text-gray-600 w-12">{item.month}</span>
                <div className="flex-1 bg-gray-200 rounded-full h-6">
                  <div
                    className="bg-green-600 h-6 rounded-full flex items-center justify-end pr-2"
                    style={{ width: `${(item.revenue / Math.max(...data.revenue_growth.map(r => r.revenue))) * 100}%` }}
                  >
                    <span className="text-xs text-white font-medium">₹{(item.revenue / 1000).toFixed(0)}K</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Products and Vendors */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Products */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 bg-gradient-to-r from-purple-500 to-purple-600 text-white">
            <h3 className="text-lg font-semibold">Top Selling Products</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {data.top_products?.map((product, index) => (
                <div key={index} className="flex items-center justify-between pb-4 border-b border-gray-200 last:border-0">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-10 h-10 bg-purple-100 text-purple-600 rounded-full font-bold">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{product.name}</p>
                      <p className="text-sm text-gray-500">{product.sales} sales</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">₹{(product.revenue / 1000).toFixed(0)}K</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Top Vendors */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white">
            <h3 className="text-lg font-semibold">Top Performing Vendors</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {data.top_vendors?.map((vendor, index) => (
                <div key={index} className="flex items-center justify-between pb-4 border-b border-gray-200 last:border-0">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-10 h-10 bg-blue-100 text-blue-600 rounded-full font-bold">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{vendor.name}</p>
                      <p className="text-sm text-gray-500">{vendor.orders} orders</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">₹{(vendor.revenue / 1000).toFixed(0)}K</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-6">Performance Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-2">Conversion Rate</p>
            <p className="text-3xl font-bold text-green-600">12.5%</p>
            <p className="text-xs text-gray-500 mt-2">+2.3% from last month</p>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-2">Average Order Value</p>
            <p className="text-3xl font-bold text-blue-600">₹15,325</p>
            <p className="text-xs text-gray-500 mt-2">+₹1,250 from last month</p>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-2">Customer Retention</p>
            <p className="text-3xl font-bold text-purple-600">68%</p>
            <p className="text-xs text-gray-500 mt-2">+5% from last month</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SuperAdminAnalytics;
