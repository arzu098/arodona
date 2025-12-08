import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import VendorDeliveryChat from './chat/VendorDeliveryChat';

const VendorDashboard = () => {
  const { user, logout } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [vendorProfile, setVendorProfile] = useState(null);
  const [dashboardData, setDashboardData] = useState({
    totalProducts: 0,
    totalOrders: 0,
    totalRevenue: 0,
    pendingOrders: 0,
    rating: 0,
    fulfillmentRate: 0
  });
  const [recentOrders, setRecentOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showOrderDetails, setShowOrderDetails] = useState(false);
  
  // Delivery assignment states
  const [showDeliveryAssignModal, setShowDeliveryAssignModal] = useState(false);
  const [availableDeliveryBoys, setAvailableDeliveryBoys] = useState([]);
  const [selectedDeliveryBoy, setSelectedDeliveryBoy] = useState('');
  const [assigningDelivery, setAssigningDelivery] = useState(false);
  
  // Delivery Staff Management States
  const [deliveryStaff, setDeliveryStaff] = useState([]);
  const [showAddDeliveryForm, setShowAddDeliveryForm] = useState(false);
  const [showVendorDeliveryChat, setShowVendorDeliveryChat] = useState(false);
  const [newDeliveryBoy, setNewDeliveryBoy] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    vehicle_type: '',
    address: ''
  });

  useEffect(() => {
    fetchVendorData();
  }, []);

  const fetchVendorData = async () => {
    try {
      // Get vendor profile by user - try the my-application endpoint first
      let vendor = null;
      try {
        const vendorResponse = await api.get(`/api/vendors/my-application`);
        vendor = vendorResponse.data;
      } catch (err) {
        // If my-application fails, try the list endpoint
        console.warn('Failed to get vendor application, trying list endpoint:', err);
        try {
          const vendorResponse = await api.get(`/api/vendors?user_id=${user.id}`);
          vendor = vendorResponse.data.vendors?.[0];
        } catch (listErr) {
          console.error('Failed to get vendor from list:', listErr);
        }
      }
      
      if (vendor) {
        setVendorProfile(vendor);
        
        // Fetch dashboard data
        try {
          const dashboardResponse = await api.get(`/api/vendors/${vendor.id}/dashboard`);
          setDashboardData(dashboardResponse.data);
        } catch (dashErr) {
          console.error('Error fetching dashboard data:', dashErr);
          // Set default dashboard data if fetch fails
          setDashboardData({
            totalProducts: 0,
            totalOrders: 0,
            totalRevenue: 0,
            pendingOrders: 0,
            rating: 0,
            fulfillmentRate: 0
          });
        }

        // Fetch recent orders
        try {
          const ordersResponse = await api.get(`/api/orders/vendor/orders?per_page=5`);
          setRecentOrders(ordersResponse.data.orders || []);
          
          // Update dashboard stats with order counts
          if (ordersResponse.data.orders) {
            const totalOrders = ordersResponse.data.total || ordersResponse.data.orders.length;
            const pendingCount = ordersResponse.data.orders.filter(order => 
              order.status === 'pending' || order.status === 'confirmed'
            ).length;
            
            setDashboardData(prev => ({
              ...prev,
              totalOrders: totalOrders,
              pendingOrders: pendingCount
            }));
          }
        } catch (ordersErr) {
          console.error('Error fetching orders:', ordersErr);
          setRecentOrders([]);
        }

        // Fetch delivery staff from API
        await fetchDeliveryStaff();
      }
    } catch (error) {
      console.error('Error fetching vendor data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
  };

  // Delivery Staff Management Functions (API Integrated)
  const fetchDeliveryStaff = async () => {
    try {
      console.log('🔄 Fetching delivery staff...');
      const response = await api.get('/api/delivery/get_all');
      console.log('✅ Delivery staff fetched:', response.data);
      setDeliveryStaff(response.data || []);
    } catch (error) {
      console.error('❌ Failed to fetch delivery staff:', error);
      setDeliveryStaff([]);
    }
  };

  const fetchOrderDetails = async (orderId) => {
    try {
      console.log('🔄 Fetching order details for:', orderId);
      
      // Try multiple endpoints to get order details
      let response;
      let orderData;
      
      try {
        // First try the general orders endpoint
        response = await api.get(`/api/orders/${orderId}`);
        orderData = response.data;
        console.log('✅ Order details fetched from /api/orders:', orderData);
      } catch (firstError) {
        console.warn('⚠️ Failed to fetch from /api/orders, trying vendor-specific endpoint:', firstError.message);
        
        // Fallback: try vendor-specific endpoint if we have vendor profile
        if (vendorProfile?.id) {
          try {
            const vendorOrdersResponse = await api.get(`/api/vendors/${vendorProfile.id}/orders`, {
              params: { limit: 100 }
            });
            const vendorOrders = vendorOrdersResponse.data?.orders || [];
            orderData = vendorOrders.find(order => order.id === orderId || order._id === orderId);
            
            if (orderData) {
              console.log('✅ Order details found in vendor orders:', orderData);
            } else {
              throw new Error('Order not found in vendor orders');
            }
          } catch (secondError) {
            console.error('❌ Failed to fetch from vendor endpoint too:', secondError.message);
            throw new Error(`Failed to fetch order details from both endpoints: ${firstError.message}, ${secondError.message}`);
          }
        } else {
          throw firstError;
        }
      }
      
      if (orderData) {
        // Ensure the order has an id field
        if (!orderData.id && orderData._id) {
          orderData.id = orderData._id;
        }
        
        setSelectedOrder(orderData);
        setShowOrderDetails(true);
        console.log('✅ Order details set successfully');
      } else {
        throw new Error('No order data received');
      }
    } catch (error) {
      console.error('❌ Error fetching order details:', error);
      console.error('Error details:', error.response?.data || error.message);
      
      // More specific error messages
      let errorMessage = 'Failed to fetch order details';
      if (error.response?.status === 403) {
        errorMessage = 'You do not have permission to view this order';
      } else if (error.response?.status === 404) {
        errorMessage = 'Order not found';
      } else if (error.message) {
        errorMessage = `Failed to fetch order details: ${error.message}`;
      }
      
      alert(errorMessage);
    }
  };

  // Fetch available delivery boys for assignment
  const fetchAvailableDeliveryBoys = async () => {
    try {
      console.log('🔄 Fetching available delivery boys...');
      const response = await api.get('/api/delivery/get_all');
      console.log('✅ Delivery boys fetched:', response.data);
      setAvailableDeliveryBoys(response.data || []);
    } catch (error) {
      console.error('❌ Failed to fetch delivery boys:', error);
      alert('Failed to load delivery boys');
    }
  };

  // Open delivery assignment modal
  const handleOpenDeliveryAssignment = () => {
    setShowDeliveryAssignModal(true);
    setSelectedDeliveryBoy('');
    fetchAvailableDeliveryBoys();
  };

  // Assign delivery boy to order
  const handleAssignDeliveryBoy = async () => {
    if (!selectedDeliveryBoy) {
      alert('Please select a delivery boy');
      return;
    }

    try {
      setAssigningDelivery(true);
      console.log('🚚 Assigning delivery boy:', selectedDeliveryBoy, 'to order:', selectedOrder.id);
      
      const response = await api.post(
        `/api/orders/${selectedOrder.id}/assign-delivery?delivery_boy_id=${selectedDeliveryBoy}`
      );
      
      console.log('✅ Delivery boy assigned:', response.data);
      alert('Delivery boy assigned successfully!');
      
      // Refresh order details
      await fetchOrderDetails(selectedOrder.id);
      
      // Close modal
      setShowDeliveryAssignModal(false);
      setSelectedDeliveryBoy('');
    } catch (error) {
      console.error('❌ Failed to assign delivery boy:', error);
      alert(error.response?.data?.detail || 'Failed to assign delivery boy');
    } finally {
      setAssigningDelivery(false);
    }
  };

  const handleAddDeliveryBoy = async (e) => {
    e.preventDefault();
    
    try {
      console.log('🚀 Creating delivery boy:', newDeliveryBoy);
      
      // Call the POST API to create delivery boy
      const response = await api.post('/api/delivery/', newDeliveryBoy);
      
      console.log('✅ Delivery boy created successfully:', response.data);
      
      // Add to local state
      setDeliveryStaff([...deliveryStaff, response.data]);
      
      // Reset form
      setNewDeliveryBoy({
        name: '',
        email: '',
        phone: '',
        password: '',
        vehicle_type: '',
        address: ''
      });
      
      setShowAddDeliveryForm(false);
      alert('Delivery boy added successfully!');
      
      // Refresh the list to make sure we have latest data
      await fetchDeliveryStaff();
      
    } catch (error) {
      console.error('❌ Failed to add delivery boy:', error);
      
      // Handle specific error messages
      if (error.response?.data?.detail) {
        alert(`Failed to add delivery boy: ${error.response.data.detail}`);
      } else {
        alert('Failed to add delivery boy. Please try again.');
      }
    }
  };

  const handleDeleteDeliveryBoy = async (staffId) => {
    if (window.confirm('Are you sure you want to delete this delivery boy?')) {
      try {
        console.log('🗑️ Deleting delivery boy with ID:', staffId);
        
        // Call the DELETE API endpoint
        await api.delete(`/api/delivery/${staffId}`);
        
        // Remove from local state after successful API call
        setDeliveryStaff(deliveryStaff.filter(staff => staff.id !== staffId));
        alert('Delivery boy deleted successfully!');
        console.log('✅ Delivery boy deleted from database');
        
      } catch (error) {
        console.error('❌ Failed to delete delivery boy:', error);
        if (error.response && error.response.status === 404) {
          alert('Delivery boy not found. It may have already been deleted.');
          // Still remove from local state if not found
          setDeliveryStaff(deliveryStaff.filter(staff => staff.id !== staffId));
        } else {
          alert('Failed to delete delivery boy. Please try again.');
        }
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl">Loading vendor dashboard...</div>
      </div>
    );
  }

  if (!vendorProfile) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-8 bg-white rounded-lg shadow-lg">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Vendor Profile Not Found</h2>
          <p className="text-gray-600 mb-6">
            You need to complete your vendor registration to access this dashboard.
            If you've already registered, please ensure you're logged in with the correct account.
          </p>
          <div className="space-y-3">
            <Link 
              to="/vendor/register" 
              className="block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Complete Vendor Registration
            </Link>
            <button
              onClick={handleLogout}
              className="block w-full bg-gray-200 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Logout and Try Different Account
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-lg sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4 sm:py-6">
            <div className="flex items-center">
              <img src="/Images/1000017875-removebg-preview 9.jpg" alt="Vendor Logo" className="w-10 h-10 sm:w-12 sm:h-12 object-contain mr-2 sm:mr-3" />
              <div>
                <h1 className="text-lg sm:text-xl md:text-2xl font-bold text-gray-900">Vendor Dashboard</h1>
                <p className="text-xs sm:text-sm text-gray-600 hidden sm:block">Welcome back, {user?.first_name} | {vendorProfile.business_name}</p>
              </div>
            </div>
            
            {/* Desktop User Info */}
            <div className="hidden md:flex items-center space-x-3 lg:space-x-4">
              <span className="text-xs lg:text-sm text-gray-600">ID: {user?.id}</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                vendorProfile.status === 'approved' ? 'bg-green-100 text-green-800' :
                vendorProfile.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {vendorProfile.status?.toUpperCase()}
              </span>
              <button
                onClick={handleLogout}
                className="bg-red-600 text-white px-3 lg:px-4 py-2 rounded text-sm hover:bg-red-700 transition-colors"
              >
                Logout
              </button>
            </div>

            {/* Mobile Menu Button */}
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
                <p className="text-xs text-gray-600">{vendorProfile.business_name}</p>
                <p className="text-xs text-gray-600 mt-1">ID: {user?.id}</p>
                <span className={`inline-block mt-2 px-2 py-1 rounded-full text-xs font-medium ${
                  vendorProfile.status === 'approved' ? 'bg-green-100 text-green-800' :
                  vendorProfile.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {vendorProfile.status?.toUpperCase()}
                </span>
              </div>
              
              {/* Logout button in mobile */}
              <button
                onClick={handleLogout}
                className="w-full text-left px-3 py-2 rounded-md text-sm font-medium text-red-600 hover:bg-red-50"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </header>

      <div className="max-w-7xl mx-auto py-4 sm:py-6 px-4 sm:px-6 lg:px-8">
        {/* Status Alert */}
        {vendorProfile.status === 'pending' && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 sm:p-4 mb-4 sm:mb-6">
            <div className="flex">
              <svg className="h-5 w-5 text-yellow-400 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div>
                <h3 className="text-xs sm:text-sm font-medium text-yellow-800">Vendor Application Under Review</h3>
                <p className="text-xs sm:text-sm text-yellow-700 mt-1">Your vendor application is currently being reviewed by our team. You'll be notified once it's approved.</p>
              </div>
            </div>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 xs:grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-3">
          {/* Total Products */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Products</dt>
                    <dd className="text-lg font-medium text-gray-900">{dashboardData.totalProducts}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Total Orders */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Orders</dt>
                    <dd className="text-lg font-medium text-gray-900">{dashboardData.totalOrders}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Total Revenue */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Revenue</dt>
                    <dd className="text-lg font-medium text-gray-900">₹{dashboardData.totalRevenue?.toLocaleString() || 0}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Pending Orders */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Pending Orders</dt>
                    <dd className="text-lg font-medium text-gray-900">{dashboardData.pendingOrders}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Rating */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Rating</dt>
                    <dd className="text-lg font-medium text-gray-900">{dashboardData.rating?.toFixed(1) || 'N/A'}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Fulfillment Rate */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Fulfillment Rate</dt>
                    <dd className="text-lg font-medium text-gray-900">{dashboardData.fulfillmentRate?.toFixed(1) || 0}%</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Link 
              to="/vendor/products" 
              className="bg-blue-50 p-4 rounded-lg hover:bg-blue-100 transition-colors"
            >
              <div className="flex items-center">
                <svg className="h-6 w-6 text-blue-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
                <div>
                  <h4 className="font-medium text-gray-900">Manage Products</h4>
                  <p className="text-sm text-gray-600">Add and edit products</p>
                </div>
              </div>
            </Link>

            <Link 
              to="/vendor/orders" 
              className="bg-green-50 p-4 rounded-lg hover:bg-green-100 transition-colors"
            >
              <div className="flex items-center">
                <svg className="h-6 w-6 text-green-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
                <div>
                  <h4 className="font-medium text-gray-900">View Orders</h4>
                  <p className="text-sm text-gray-600">Process customer orders</p>
                </div>
              </div>
            </Link>

            <Link 
              to="/vendor/profile" 
              className="bg-yellow-50 p-4 rounded-lg hover:bg-yellow-100 transition-colors"
            >
              <div className="flex items-center">
                <svg className="h-6 w-6 text-yellow-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                <div>
                  <h4 className="font-medium text-gray-900">Store Profile</h4>
                  <p className="text-sm text-gray-600">Update store information</p>
                </div>
              </div>
            </Link>

            <Link 
              to="/vendor/analytics" 
              className="bg-purple-50 p-4 rounded-lg hover:bg-purple-100 transition-colors"
            >
              <div className="flex items-center">
                <svg className="h-6 w-6 text-purple-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <div>
                  <h4 className="font-medium text-gray-900">Analytics</h4>
                  <p className="text-sm text-gray-600">View performance metrics</p>
                </div>
              </div>
            </Link>
          </div>
        </div>

        {/* Manage Delivery Staff */}
        <div className="mt-8">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-medium text-gray-900">Manage Delivery Staff</h3>
            <button
              onClick={() => setShowAddDeliveryForm(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Delivery Boy
            </button>
          </div>

          {/* Delivery Staff List */}
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            {deliveryStaff.length > 0 ? (
              <ul className="divide-y divide-gray-200">
                {deliveryStaff.map((staff) => (
                  <li key={staff.id}>
                    <div className="px-4 py-4 flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                            <svg className="h-6 w-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">{staff.name}</div>
                          <div className="text-sm text-gray-500">{staff.email}</div>
                          <div className="text-sm text-gray-500">{staff.phone}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900">{staff.vehicle_type}</div>
                        <div className="text-sm text-gray-500 mb-2">{staff.address}</div>
                        <button
                          onClick={() => handleDeleteDeliveryBoy(staff.id)}
                          className="bg-red-600 text-white px-3 py-1 rounded text-xs hover:bg-red-700 transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="px-4 py-8 text-center">
                <svg className="h-12 w-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <p className="text-gray-500 text-sm">No delivery staff added yet.</p>
                <p className="text-gray-400 text-xs mt-1">Click "Add Delivery Boy" to get started.</p>
              </div>
            )}
          </div>
        </div>

        {/* Add Delivery Boy Modal */}
        {showAddDeliveryForm && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" onClick={() => setShowAddDeliveryForm(false)}>
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white" onClick={(e) => e.stopPropagation()}>
              <div className="mt-3">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Add New Delivery Boy</h3>
                  <button
                    onClick={() => setShowAddDeliveryForm(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                
                <form onSubmit={handleAddDeliveryBoy} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                    <input
                      type="text"
                      required
                      value={newDeliveryBoy.name}
                      onChange={(e) => setNewDeliveryBoy({...newDeliveryBoy, name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter delivery boy name"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <input
                      type="email"
                      required
                      value={newDeliveryBoy.email}
                      onChange={(e) => setNewDeliveryBoy({...newDeliveryBoy, email: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter email address"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
                    <input
                      type="tel"
                      required
                      value={newDeliveryBoy.phone}
                      onChange={(e) => setNewDeliveryBoy({...newDeliveryBoy, phone: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter phone number"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                    <input
                      type="password"
                      required
                      value={newDeliveryBoy.password}
                      onChange={(e) => setNewDeliveryBoy({...newDeliveryBoy, password: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter password"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Vehicle Type</label>
                    <select
                      required
                      value={newDeliveryBoy.vehicle_type}
                      onChange={(e) => setNewDeliveryBoy({...newDeliveryBoy, vehicle_type: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select vehicle type</option>
                      <option value="bicycle">Bicycle</option>
                      <option value="motorcycle">Motorcycle</option>
                      <option value="scooter">Scooter</option>
                      <option value="car">Car</option>
                      <option value="van">Van</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
                    <textarea
                      required
                      value={newDeliveryBoy.address}
                      onChange={(e) => setNewDeliveryBoy({...newDeliveryBoy, address: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter address"
                      rows="3"
                    />
                  </div>
                  
                  <div className="flex justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={() => setShowAddDeliveryForm(false)}
                      className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
                    >
                      Add Delivery Boy
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Recent Orders */}
        {recentOrders.length > 0 && (
          <div className="mt-8">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Orders</h3>
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {recentOrders.map((order) => (
                  <li key={order.id}>
                    <div 
                      className="px-4 py-4 flex items-center justify-between hover:bg-gray-50 cursor-pointer transition-colors duration-150"
                      onClick={() => fetchOrderDetails(order.id)}
                    >
                      <div className="flex items-center">
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            Order #{order.order_number || order.id}
                          </div>
                          <div className="text-sm text-gray-500">
                            {new Date(order.created_at).toLocaleDateString()}
                          </div>
                        
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900">
                          ₹{order.total_amount || order.total || 0}
                        </div>
                        <div className={`text-sm ${
                          order.status === 'completed' || order.status === 'fulfilled' ? 'text-green-600' :
                          order.status === 'pending' || order.status === 'pending_payment' ? 'text-yellow-600' :
                          order.status === 'cancelled' ? 'text-red-600' :
                          'text-gray-600'
                        }`}>
                          {order.status}
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Order Details Modal */}
        {showOrderDetails && selectedOrder && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b">
                <h2 className="text-xl font-semibold text-gray-900">
                  Order Details - #{selectedOrder.order_number || selectedOrder.id}
                </h2>
                <button
                  onClick={() => {
                    setShowOrderDetails(false);
                    setSelectedOrder(null);
                  }}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              {/* Order Information */}
              <div className="p-6 space-y-6">
                {/* Basic Order Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Order Information</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Order ID:</span>
                        <span className="font-medium">{selectedOrder.id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Order Number:</span>
                        <span className="font-medium">{selectedOrder.order_number}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Status:</span>
                        <span className={`px-2 py-1 rounded text-sm ${
                          selectedOrder.status === 'completed' || selectedOrder.status === 'fulfilled' ? 'bg-green-100 text-green-800' :
                          selectedOrder.status === 'pending' || selectedOrder.status === 'pending_payment' ? 'bg-yellow-100 text-yellow-800' :
                          selectedOrder.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {selectedOrder.status}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Payment Status:</span>
                        <span className="font-medium">{selectedOrder.payment_status || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Created At:</span>
                        <span className="font-medium">
                          {new Date(selectedOrder.created_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Customer Information</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Customer ID:</span>
                        <span className="font-medium">{selectedOrder.customer_id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Email:</span>
                        <span className="font-medium">{selectedOrder.customer_email || 'N/A'}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Vendor Information */}
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Vendor Information</h3>
                  <div className="space-y-3">
                    {selectedOrder.vendor_orders && Object.keys(selectedOrder.vendor_orders).length > 0 ? (
                      Object.keys(selectedOrder.vendor_orders).map((vendorId, index) => {
                        // Get vendor name from first item
                        const vendorItem = selectedOrder.items?.find(item => item.vendor_id === vendorId);
                        return (
                          <div key={vendorId} className="bg-white p-3 rounded border">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              <div>
                                <div className="flex justify-between mb-1">
                                  <span className="text-gray-600 text-sm">Vendor ID:</span>
                                  <span className="font-mono text-sm font-medium">{vendorId}</span>
                                </div>
                                {vendorItem?.vendor_name && (
                                  <div className="flex justify-between">
                                    <span className="text-gray-600 text-sm">Vendor Name:</span>
                                    <span className="font-medium">{vendorItem.vendor_name}</span>
                                  </div>
                                )}
                              </div>
                              <div>
                                <div className="flex justify-between">
                                  <span className="text-gray-600 text-sm">Items Count:</span>
                                  <span className="font-medium">{selectedOrder.vendor_orders[vendorId]?.length || 0}</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      // Fallback for orders without vendor_orders structure
                      <div className="bg-white p-3 rounded border">
                        <div className="text-sm text-gray-600">
                          Vendor information available in individual items below
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Order Items */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Order Items</h3>
                  <div className="border rounded-lg overflow-hidden">
                    <div className="bg-gray-50 px-4 py-3 border-b">
                      <div className="grid grid-cols-12 gap-4 text-sm font-medium text-gray-900">
                        <div className="col-span-6">Product</div>
                        <div className="col-span-2 text-center">Quantity</div>
                        <div className="col-span-2 text-right">Unit Price</div>
                        <div className="col-span-2 text-right">Total</div>
                      </div>
                    </div>
                    <div className="divide-y divide-gray-200">
                      {selectedOrder.items && selectedOrder.items.map((item, index) => (
                        <div key={index} className="px-4 py-4">
                          <div className="grid grid-cols-12 gap-4 items-center">
                            <div className="col-span-6">
                              <div className="flex items-center space-x-3">
                                {item.product_image && (
                                  <img
                                    src={item.product_image}
                                    alt={item.product_name}
                                    className="w-12 h-12 object-cover rounded"
                                  />
                                )}
                                <div>
                                  <div className="font-medium text-gray-900">{item.product_name}</div>
                                  <div className="text-sm text-gray-500">SKU: {item.product_sku || 'N/A'}</div>
                                  <div className="text-sm text-blue-600 font-medium">
                                    Vendor: {item.vendor_name} ({item.vendor_id})
                                  </div>
                                  {item.customization?.size && (
                                    <div className="text-sm text-gray-500">Size: {item.customization.size}</div>
                                  )}
                                </div>
                              </div>
                            </div>
                            <div className="col-span-2 text-center">
                              <span className="font-medium">{item.quantity}</span>
                            </div>
                            <div className="col-span-2 text-right">
                              <span className="font-medium">₹{item.unit_price}</span>
                            </div>
                            <div className="col-span-2 text-right">
                              <span className="font-medium">₹{item.line_total}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Pricing Summary */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Order Summary</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Subtotal:</span>
                      <span className="font-medium">₹{selectedOrder.pricing?.subtotal || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Tax:</span>
                      <span className="font-medium">₹{selectedOrder.pricing?.tax_amount || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Shipping:</span>
                      <span className="font-medium">₹{selectedOrder.pricing?.shipping_cost || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Discount:</span>
                      <span className="font-medium text-red-600">-₹{selectedOrder.pricing?.discount_amount || 0}</span>
                    </div>
                    <hr className="my-2" />
                    <div className="flex justify-between text-lg font-semibold">
                      <span>Total:</span>
                      <span>₹{selectedOrder.pricing?.grand_total || selectedOrder.total_amount || 0}</span>
                    </div>
                  </div>
                </div>

                {/* Delivery Assignment Status */}
                {selectedOrder.delivery_assignment && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h3 className="text-lg font-medium text-green-900 mb-3 flex items-center gap-2">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Delivery Assignment
                    </h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Delivery Boy:</span>
                        <p className="font-medium text-gray-900">{selectedOrder.delivery_assignment.delivery_boy_name}</p>
                      </div>
                      <div>
                        <span className="text-gray-600">Phone:</span>
                        <p className="font-medium text-gray-900">{selectedOrder.delivery_assignment.delivery_boy_phone}</p>
                      </div>
                      <div>
                        <span className="text-gray-600">Vehicle:</span>
                        <p className="font-medium text-gray-900">{selectedOrder.delivery_assignment.delivery_boy_vehicle || 'N/A'}</p>
                      </div>
                      <div>
                        <span className="text-gray-600">Assigned At:</span>
                        <p className="font-medium text-gray-900">
                          {new Date(selectedOrder.delivery_assignment.assigned_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Addresses */}
                {(selectedOrder.shipping_address || selectedOrder.billing_address) && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {selectedOrder.shipping_address && (
                      <div>
                        <h3 className="text-lg font-medium text-gray-900 mb-3">Shipping Address</h3>
                        <div className="bg-gray-50 p-3 rounded text-sm">
                          <p className="font-medium">
                            {selectedOrder.shipping_address.first_name} {selectedOrder.shipping_address.last_name}
                          </p>
                          <p>{selectedOrder.shipping_address.address_line1}</p>
                          {selectedOrder.shipping_address.address_line2 && (
                            <p>{selectedOrder.shipping_address.address_line2}</p>
                          )}
                          <p>
                            {selectedOrder.shipping_address.city}, {selectedOrder.shipping_address.state_province} {selectedOrder.shipping_address.postal_code}
                          </p>
                          <p>{selectedOrder.shipping_address.country_code}</p>
                          <p>Phone: {selectedOrder.shipping_address.phone}</p>
                        </div>
                      </div>
                    )}

                    {selectedOrder.billing_address && (
                      <div>
                        <h3 className="text-lg font-medium text-gray-900 mb-3">Billing Address</h3>
                        <div className="bg-gray-50 p-3 rounded text-sm">
                          <p className="font-medium">
                            {selectedOrder.billing_address.first_name} {selectedOrder.billing_address.last_name}
                          </p>
                          <p>{selectedOrder.billing_address.address_line1}</p>
                          {selectedOrder.billing_address.address_line2 && (
                            <p>{selectedOrder.billing_address.address_line2}</p>
                          )}
                          <p>
                            {selectedOrder.billing_address.city}, {selectedOrder.billing_address.state_province} {selectedOrder.billing_address.postal_code}
                          </p>
                          <p>{selectedOrder.billing_address.country_code}</p>
                          <p>Phone: {selectedOrder.billing_address.phone}</p>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
               <button
              onClick={() => setShowVendorDeliveryChat(true)}
              className="bg-indigo-50 p-4 rounded-lg hover:bg-indigo-100 transition-colors text-left w-full"
            >
              <div className="flex items-center">
                <div className="flex items-center mr-3">
                  <span className="text-lg">🏭</span>
                  <span className="mx-1">💬</span>
                  <span className="text-lg">🚚</span>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">Pickup Chat</h4>
                  <p className="text-sm text-gray-600">Coordinate with delivery partners</p>
                </div>
              </div>
            </button>
              {/* Modal Actions */}
              <div className="flex justify-between space-x-3 p-6 border-t bg-gray-50">
                <button
                  onClick={handleOpenDeliveryAssignment}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  Assign Delivery Boy
                </button>
                
                <div className="flex space-x-3">
                  <button
                    onClick={() => {
                      setShowOrderDetails(false);
                      setSelectedOrder(null);
                    }}
                    className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    Close
                  </button>
                  <button
                    onClick={() => {
                      // You can add print functionality here
                      window.print();
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    Print Order
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Delivery Boy Assignment Modal */}
        {showDeliveryAssignModal && selectedOrder && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b">
                <h2 className="text-xl font-semibold text-gray-900">
                  Assign Delivery Boy
                </h2>
                <button
                  onClick={() => setShowDeliveryAssignModal(false)}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-6">
                <p className="text-sm text-gray-600 mb-4">
                  Order: <span className="font-medium">#{selectedOrder.order_number || selectedOrder.id}</span>
                </p>

                {/* Show current assignment if exists */}
                {selectedOrder.delivery_assignment && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                    <p className="text-sm font-medium text-blue-900 mb-2">Currently Assigned To:</p>
                    <p className="text-sm text-blue-800">
                      <strong>{selectedOrder.delivery_assignment.delivery_boy_name}</strong>
                    </p>
                    <p className="text-xs text-blue-600">
                      Phone: {selectedOrder.delivery_assignment.delivery_boy_phone}
                    </p>
                    <p className="text-xs text-blue-600">
                      Vehicle: {selectedOrder.delivery_assignment.delivery_boy_vehicle || 'N/A'}
                    </p>
                  </div>
                )}

                {/* Delivery Boy Selection */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Delivery Boy
                  </label>
                  <select
                    value={selectedDeliveryBoy}
                    onChange={(e) => setSelectedDeliveryBoy(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                  >
                    <option value="">Choose a delivery boy...</option>
                    {availableDeliveryBoys.map((boy) => (
                      <option key={boy.id} value={boy.id}>
                        {boy.name} - {boy.phone} ({boy.vehicle_type || 'No vehicle'})
                      </option>
                    ))}
                  </select>
                </div>

                {availableDeliveryBoys.length === 0 && (
                  <p className="text-sm text-red-600 mb-4">
                    No delivery boys available. Please add delivery staff first.
                  </p>
                )}
              </div>

              {/* Modal Actions */}
              <div className="flex justify-end space-x-3 p-6 border-t bg-gray-50">
                <button
                  onClick={() => setShowDeliveryAssignModal(false)}
                  className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAssignDeliveryBoy}
                  disabled={!selectedDeliveryBoy || assigningDelivery}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {assigningDelivery ? 'Assigning...' : 'Assign'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Vendor-Delivery Chat Modal */}
        {showVendorDeliveryChat && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full h-[80vh] flex flex-col">
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-t-lg">
                <h2 className="text-xl font-semibold flex items-center">
                  <span className="mx-2">💬</span>
                  <span className="mr-2">🚚</span>
                </h2>
                <button
                  onClick={() => setShowVendorDeliveryChat(false)}
                  className="text-white hover:text-gray-200 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              {/* Modal Content */}
              <div className="flex-1 p-6 overflow-hidden">
                <VendorDeliveryChat />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VendorDashboard;