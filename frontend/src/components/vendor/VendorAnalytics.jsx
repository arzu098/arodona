import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import vendorService from '../../services/vendorService';

const VendorAnalytics = () => {
  const { user, logout } = useAuth();
  const [vendorProfile, setVendorProfile] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(30); // days

  useEffect(() => {
    fetchVendorData();
  }, [timeRange]);

  const fetchVendorData = async () => {
    try {
      // Get vendor profile
      const vendor = await vendorService.getMyProfile();
      setVendorProfile(vendor);

      // Fetch analytics
      const analyticsData = await vendorService.getMyAnalytics({ days: timeRange });
      setAnalytics(analyticsData);
    } catch (error) {
      console.error('Error fetching vendor analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <img src="/Images/1000017875-removebg-preview 9.jpg" alt="Vendor Logo" className="w-12 h-12 object-contain mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Analytics & Insights</h1>
                <p className="text-sm text-gray-600">{vendorProfile?.business_name}</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                to="/vendor/dashboard"
                className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300 transition-colors"
              >
                ← Back to Dashboard
              </Link>
              <button
                onClick={logout}
                className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Time Range Selector */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Time Period</h2>
            <div className="flex gap-2">
              <button
                onClick={() => setTimeRange(7)}
                className={`px-4 py-2 rounded-lg ${
                  timeRange === 7
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Last 7 Days
              </button>
              <button
                onClick={() => setTimeRange(30)}
                className={`px-4 py-2 rounded-lg ${
                  timeRange === 30
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Last 30 Days
              </button>
              <button
                onClick={() => setTimeRange(90)}
                className={`px-4 py-2 rounded-lg ${
                  timeRange === 90
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Last 90 Days
              </button>
              <button
                onClick={() => setTimeRange(365)}
                className={`px-4 py-2 rounded-lg ${
                  timeRange === 365
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Last Year
              </button>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Sales</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  ₹{analytics?.total_sales?.toLocaleString() || 0}
                </p>
              </div>
              <div className="p-3 bg-green-100 rounded-full">
                <svg className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
            </div>
            <p className="text-sm text-green-600 mt-4">
              {analytics?.sales_growth > 0 ? '+' : ''}{analytics?.sales_growth?.toFixed(1) || 0}% from previous period
            </p>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Orders</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {analytics?.total_orders || 0}
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-full">
                <svg className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
              </div>
            </div>
            <p className="text-sm text-blue-600 mt-4">
              {analytics?.orders_growth > 0 ? '+' : ''}{analytics?.orders_growth?.toFixed(1) || 0}% from previous period
            </p>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Order Value</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  ₹{analytics?.avg_order_value?.toLocaleString() || 0}
                </p>
              </div>
              <div className="p-3 bg-purple-100 rounded-full">
                <svg className="h-8 w-8 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
            <p className="text-sm text-gray-500 mt-4">
              Average value per order
            </p>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Products Sold</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {analytics?.products_sold || 0}
                </p>
              </div>
              <div className="p-3 bg-yellow-100 rounded-full">
                <svg className="h-8 w-8 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </div>
            </div>
            <p className="text-sm text-gray-500 mt-4">
              Total units sold
            </p>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Sales Chart */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Sales Trend</h3>
            <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
              <div className="text-center text-gray-500">
                <svg className="mx-auto h-12 w-12 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p>Chart visualization will be implemented here</p>
                <p className="text-sm">Using a charting library like Chart.js or Recharts</p>
              </div>
            </div>
          </div>

          {/* Orders Chart */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Order Status Distribution</h3>
            <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
              <div className="text-center text-gray-500">
                <svg className="mx-auto h-12 w-12 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
                </svg>
                <p>Pie chart visualization will be implemented here</p>
              </div>
            </div>
          </div>
        </div>

        {/* Top Products */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Top Selling Products</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Product</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Units Sold</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Revenue</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Avg Rating</th>
                </tr>
              </thead>
              <tbody>
                {analytics?.top_products?.length > 0 ? (
                  analytics.top_products.map((product, index) => (
                    <tr key={index} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm">{product.name}</td>
                      <td className="py-3 px-4 text-sm">{product.units_sold}</td>
                      <td className="py-3 px-4 text-sm font-semibold">₹{product.revenue?.toLocaleString()}</td>
                      <td className="py-3 px-4 text-sm">
                        <span className="text-yellow-500">★</span> {product.avg_rating?.toFixed(1) || 'N/A'}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="4" className="py-8 text-center text-gray-500">
                      No product data available for this period
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Customer Satisfaction</h3>
            <div className="text-center">
              <div className="text-4xl font-bold text-yellow-500 mb-2">
                {analytics?.avg_rating?.toFixed(1) || 'N/A'}
              </div>
              <div className="text-yellow-500 text-2xl mb-2">★★★★★</div>
              <p className="text-sm text-gray-600">Average Product Rating</p>
              <p className="text-xs text-gray-500 mt-2">
                Based on {analytics?.total_reviews || 0} reviews
              </p>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Fulfillment Rate</h3>
            <div className="text-center">
              <div className="text-4xl font-bold text-green-600 mb-2">
                {analytics?.fulfillment_rate?.toFixed(1) || 0}%
              </div>
              <p className="text-sm text-gray-600 mb-4">Orders Completed Successfully</p>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full"
                  style={{ width: `${analytics?.fulfillment_rate || 0}%` }}
                ></div>
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Response Time</h3>
            <div className="text-center">
              <div className="text-4xl font-bold text-blue-600 mb-2">
                {analytics?.avg_response_time || '< 24'}
              </div>
              <p className="text-sm text-gray-600">Hours (Average)</p>
              <p className="text-xs text-gray-500 mt-4">
                Time to process orders
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VendorAnalytics;
