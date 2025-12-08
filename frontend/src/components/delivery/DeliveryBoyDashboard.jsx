import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import ChatInterface from '../chat/ChatInterface';
import VendorDeliveryChatInterface from '../chat/VendorDeliveryChatInterface';

const DeliveryBoyDashboard = () => {
  const { user, logout } = useAuth();
  const [orders, setOrders] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [chatOrder, setChatOrder] = useState(null);
  const [vendorChatOrder, setVendorChatOrder] = useState(null);
  const [unreadCounts, setUnreadCounts] = useState({});
  const [vendorUnreadCounts, setVendorUnreadCounts] = useState({});
  const [totalUnreadCount, setTotalUnreadCount] = useState(0);
  const [showNotification, setShowNotification] = useState(false);
  const [notificationMessage, setNotificationMessage] = useState('');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    // Check if user has delivery_boy role before fetching data
    if (!user) {
      setLoading(false);
      return;
    }

    if (user.role !== 'delivery_boy') {
      console.error('Access denied: User is not a delivery boy', { userRole: user.role });
      setLoading(false);
      return;
    }

    fetchDashboardData();
    fetchUnreadCounts();
    fetchVendorUnreadCounts();
    
    // Set up interval to check for new messages
    const interval = setInterval(() => {
      fetchUnreadCounts();
      fetchVendorUnreadCounts();
    }, 10000); // Check every 10 seconds
    return () => clearInterval(interval);
  }, [user]);

  // Function to show notification
  const showMessageNotification = (message, type = 'customer') => {
    setNotificationMessage(message);
    setShowNotification(true);
    setTimeout(() => {
      setShowNotification(false);
    }, 5000); // Hide after 5 seconds
  };

  // Calculate total unread messages
  useEffect(() => {
    const customerTotal = Object.values(unreadCounts).reduce((sum, count) => sum + count, 0);
    const vendorTotal = Object.values(vendorUnreadCounts).reduce((sum, count) => sum + count, 0);
    const newTotal = customerTotal + vendorTotal;
    
    // Show notification if total increased
    if (newTotal > totalUnreadCount && totalUnreadCount > 0) {
      const increase = newTotal - totalUnreadCount;
      if (customerTotal > Object.values(unreadCounts).reduce((sum, count) => sum + count, 0)) {
        showMessageNotification(`+${increase} new customer message${increase > 1 ? 's' : ''}`);
      } else {
        showMessageNotification(`+${increase} new vendor message${increase > 1 ? 's' : ''}`);
      }
    }
    
    setTotalUnreadCount(newTotal);
  }, [unreadCounts, vendorUnreadCounts]);

  const fetchUnreadCounts = async () => {
    if (!orders || orders.length === 0) return;
    
    try {
      const counts = {};
      let hasChanges = false;
      
      for (const order of orders) {
        try {
          const response = await api.get(`/api/chat/messages/${order.id}`);
          const messages = response.data.messages || [];
          const unreadCount = messages.filter(msg => 
            msg.sender_type === 'customer' && 
            msg.status !== 'read'
          ).length;
          if (unreadCount > 0) {
            counts[order.id] = unreadCount;
          }
        } catch (error) {
          // Ignore errors for individual orders
        }
      }
      
      // Only update state if there are actual changes
      setUnreadCounts(prev => {
        const prevKeys = Object.keys(prev).sort();
        const newKeys = Object.keys(counts).sort();
        
        if (prevKeys.length !== newKeys.length || 
            !prevKeys.every((key, i) => key === newKeys[i] && prev[key] === counts[key])) {
          return counts;
        }
        return prev;
      });
    } catch (error) {
      console.error('Error fetching unread counts:', error);
    }
  };

  const fetchVendorUnreadCounts = async () => {
    if (!orders || orders.length === 0) return;
    
    try {
      const counts = {};
      
      for (const order of orders) {
        try {
          const response = await api.get(`/api/chat/vendor-delivery/messages/${order.id}`);
          const messages = response.data.messages || [];
          const unreadCount = messages.filter(msg => 
            msg.sender_type === 'vendor' && 
            msg.status !== 'read'
          ).length;
          if (unreadCount > 0) {
            counts[order.id] = unreadCount;
          }
        } catch (error) {
          // Ignore errors for individual orders
        }
      }
      
      // Only update state if there are actual changes
      setVendorUnreadCounts(prev => {
        const prevKeys = Object.keys(prev).sort();
        const newKeys = Object.keys(counts).sort();
        
        if (prevKeys.length !== newKeys.length || 
            !prevKeys.every((key, i) => key === newKeys[i] && prev[key] === counts[key])) {
          return counts;
        }
        return prev;
      });
    } catch (error) {
      console.error('Error fetching vendor unread counts:', error);
    }
  };

  const handleChatOpen = (order) => {
    setChatOrder(order);
    // Clear unread count for this order
    setUnreadCounts(prev => {
      const newCounts = { ...prev };
      delete newCounts[order.id];
      return newCounts;
    });
  };

  const handleVendorChatOpen = (order) => {
    setVendorChatOrder(order);
    // Clear unread count for this order
    setVendorUnreadCounts(prev => {
      const newCounts = { ...prev };
      delete newCounts[order.id];
      return newCounts;
    });
  };

  const handleChatClose = () => {
    setChatOrder(null);
    // Refresh unread counts after closing chat
    setTimeout(fetchUnreadCounts, 1000);
  };

  const handleVendorChatClose = () => {
    setVendorChatOrder(null);
    // Refresh unread counts after closing chat
    setTimeout(fetchVendorUnreadCounts, 1000);
  };

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch orders and stats
      const [ordersResponse, statsResponse] = await Promise.all([
        api.get('/api/delivery/my-orders'),
        api.get('/api/delivery/dashboard-stats')
      ]);
      
      setOrders(ordersResponse.data.orders || []);
      setStats(statsResponse.data || {});
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      
      // Check if it's a 404 error specifically
      if (error.status === 404) {
        console.log('No orders found or delivery API not available');
        setOrders([]);
        setStats({
          total_orders: 0,
          pending_orders: 0,
          in_transit: 0,
          completed_orders: 0
        });
      } else if (error.status === 401) {
        console.error('Authentication failed - redirecting to login');
        logout();
      } else {
        console.error('API Error:', error);
        alert(`Failed to fetch dashboard data: ${error.message || 'Unknown error'}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (orderId, newStatus) => {
    try {
      await api.patch(`/api/delivery/orders/${orderId}/status`, { status: newStatus });
      
      // Update local state
      setOrders(orders.map(order => 
        order.id === orderId ? { ...order, status: newStatus } : order
      ));
      
      // Refresh stats
      fetchDashboardData();
      alert('Order status updated successfully');
    } catch (error) {
      console.error('Error updating order status:', error);
      alert('Failed to update order status');
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      assigned: 'bg-yellow-100 text-yellow-800',
      processing: 'bg-blue-100 text-blue-800',
      confirmed: 'bg-purple-100 text-purple-800',
      shipped: 'bg-indigo-100 text-indigo-800',
      picked_up: 'bg-orange-100 text-orange-800',
      in_transit: 'bg-cyan-100 text-cyan-800',
      delivered: 'bg-green-100 text-green-800',
      delivery_failed: 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const filteredOrders = orders.filter(order => {
    if (filter === 'all') return true;
    if (filter === 'pending') return ['assigned', 'processing', 'confirmed'].includes(order.status);
    if (filter === 'in_transit') return ['picked_up', 'in_transit', 'shipped'].includes(order.status);
    if (filter === 'completed') return ['delivered'].includes(order.status);
    return order.status === filter;
  });

  const getOrderTotal = (order) => {
    return order.pricing?.grand_total || order.total || 0;
  };

  // Calculate dynamic stats from orders
  const calculateStats = () => {
    const totalOrders = orders.length;
    const pendingOrders = orders.filter(o => ['assigned', 'processing', 'confirmed'].includes(o.status)).length;
    const inTransitOrders = orders.filter(o => ['picked_up', 'in_transit', 'shipped'].includes(o.status)).length;
    const completedOrders = orders.filter(o => o.status === 'delivered').length;
    
    return {
      total_orders: totalOrders,
      pending_orders: pendingOrders,
      in_transit: inTransitOrders,
      completed_orders: completedOrders
    };
  };

  const dynamicStats = calculateStats();

  // Check if user is not authenticated
  if (!user) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-red-600 mb-4">Please log in to access the delivery dashboard</div>
          <button 
            onClick={() => window.location.href = '/login'}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  // Check if user has the correct role
  if (user.role !== 'delivery_boy') {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-red-600 mb-4">
            Access Denied: This page is only for delivery boys
          </div>
          <div className="text-gray-600 mb-4">
            Current role: {user.role || 'Unknown'}
          </div>
          <button 
            onClick={() => window.history.back()}
            className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

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
      <header className="bg-gradient-to-r from-yellow-500 to-amber-600 shadow-lg sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4 sm:py-6">
            <div className="flex items-center">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-white rounded-full flex items-center justify-center text-yellow-600 font-bold text-xl mr-3 shadow-md">
                🚚
              </div>
              <div>
                <h1 className="text-lg sm:text-xl md:text-2xl font-bold text-white">Delivery Dashboard</h1>
                <p className="text-xs sm:text-sm text-yellow-200 hidden sm:block font-medium">Welcome back, {user?.name || user?.first_name || 'Delivery Partner'}</p>
              </div>
            </div>
            
            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-6">
              <Link
                to="/delivery/orders"
                className="text-yellow-100 hover:text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-white hover:bg-opacity-10 transition-all"
              >
                All Orders
              </Link>
              <Link
                to="/delivery/profile"
                className="text-yellow-100 hover:text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-white hover:bg-opacity-10 transition-all"
              >
                Profile
              </Link>
              <Link
                to="/chat"
                className="text-yellow-100 hover:text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-white hover:bg-opacity-10 transition-all relative"
              >
                💬 Help/Chat
                {totalUnreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-bold">
                    {totalUnreadCount > 99 ? '99+' : `+${totalUnreadCount}`}
                  </span>
                )}
              </Link>
            </div>

            {/* Desktop User Info */}
            <div className="hidden md:flex items-center space-x-3 lg:space-x-4">
              <span className="text-xs lg:text-sm text-yellow-100">ID: {user?.id}</span>
              <span className="bg-white bg-opacity-20 text-white px-2 py-1 rounded-full text-xs font-medium border border-white border-opacity-30">
                DELIVERY PARTNER
              </span>
              <button
                onClick={logout}
                className="bg-red-500 text-white px-3 lg:px-4 py-2 rounded text-sm hover:bg-red-600 transition-colors shadow-md"
              >
                Logout
              </button>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 rounded-md text-yellow-100 hover:text-white hover:bg-white hover:bg-opacity-10"
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
            <div className="md:hidden border-t border-yellow-400 border-opacity-30 py-4 space-y-3">
              <Link
                to="/delivery/orders"
                className="block text-yellow-100 hover:text-white px-4 py-2 text-base font-medium hover:bg-white hover:bg-opacity-10 rounded mx-4"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                All Orders
              </Link>
              <Link
                to="/delivery/profile"
                className="block text-yellow-100 hover:text-white px-4 py-2 text-base font-medium hover:bg-white hover:bg-opacity-10 rounded mx-4"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Profile
              </Link>
              <Link
                to="/chat"
                className="block text-yellow-100 hover:text-white px-4 py-2 text-base font-medium hover:bg-white hover:bg-opacity-10 rounded mx-4 relative"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                💬 Help/Chat
                {totalUnreadCount > 0 && (
                  <span className="absolute top-1 right-6 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-bold">
                    {totalUnreadCount > 99 ? '99+' : `+${totalUnreadCount}`}
                  </span>
                )}
              </Link>
              <div className="border-t border-yellow-400 border-opacity-30 pt-3 mt-3">
                <div className="px-4 py-2 text-sm text-yellow-100">ID: {user?.id}</div>
                <button
                  onClick={() => {
                    logout();
                    setIsMobileMenuOpen(false);
                  }}
                  className="w-full text-left bg-red-500 text-white px-4 py-2 text-base font-medium hover:bg-red-600 mx-4 rounded"
                >
                  Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </header>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-bold">📦</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Orders</dt>
                    <dd className="text-lg font-medium text-gray-900">{dynamicStats.total_orders}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-amber-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-bold">⏳</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Pending</dt>
                    <dd className="text-lg font-medium text-gray-900">{dynamicStats.pending_orders}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-bold">🚛</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">In Transit</dt>
                    <dd className="text-lg font-medium text-gray-900">{dynamicStats.in_transit}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-bold">✅</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Completed</dt>
                    <dd className="text-lg font-medium text-gray-900">{dynamicStats.completed_orders}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Filter Buttons */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-lg ${
                filter === 'all'
                  ? 'bg-yellow-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              All Orders ({orders.length})
            </button>
            <button
              onClick={() => setFilter('pending')}
              className={`px-4 py-2 rounded-lg ${
                filter === 'pending'
                  ? 'bg-amber-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Pending ({orders.filter(o => ['assigned', 'processing', 'confirmed'].includes(o.status)).length})
            </button>
            <button
              onClick={() => setFilter('in_transit')}
              className={`px-4 py-2 rounded-lg ${
                filter === 'in_transit'
                  ? 'bg-orange-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              In Transit ({orders.filter(o => ['picked_up', 'in_transit', 'shipped'].includes(o.status)).length})
            </button>
            <button
              onClick={() => setFilter('completed')}
              className={`px-4 py-2 rounded-lg ${
                filter === 'completed'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Completed ({orders.filter(o => o.status === 'delivered').length})
            </button>
          </div>
        </div>

        {/* Orders List */}
        {filteredOrders.length === 0 ? (
          <div className="bg-white shadow rounded-lg p-12 text-center">
            <div className="w-24 h-24 mx-auto mb-4 text-gray-400 text-6xl">📦</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No orders found</h3>
            <p className="text-gray-600">
              {filter === 'all'
                ? 'You have no orders assigned yet'
                : `You have no ${filter} orders`}
            </p>
          </div>
        ) : (
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-2 sm:px-4 lg:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Order ID
                    </th>
                    <th className="px-2 sm:px-4 lg:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Customer
                    </th>
                    <th className="px-2 sm:px-4 lg:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden sm:table-cell">
                      Items
                    </th>
                    <th className="px-2 sm:px-4 lg:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="px-2 sm:px-4 lg:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-2 sm:px-4 lg:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredOrders.map((order) => (
                    <tr key={order.id} className="hover:bg-gray-50">
                      <td className="px-2 sm:px-4 lg:px-6 py-2 sm:py-4 whitespace-nowrap">
                        <div className="text-xs sm:text-sm font-medium text-gray-900 truncate max-w-[80px] sm:max-w-none">
                          {order.order_number || `#${order.id.substring(0, 8)}`}
                        </div>
                      </td>
                      <td className="px-2 sm:px-4 lg:px-6 py-2 sm:py-4 whitespace-nowrap">
                        <div className="text-xs sm:text-sm text-gray-500 truncate max-w-[100px] sm:max-w-none">
                          {order.customer_email || order.customer_id?.substring(0, 8) || 'N/A'}
                        </div>
                        <div className="text-xs text-gray-400 sm:hidden">
                          {order.items?.length || 0} items
                        </div>
                      </td>
                      <td className="px-2 sm:px-4 lg:px-6 py-2 sm:py-4 whitespace-nowrap text-xs sm:text-sm text-gray-500 hidden sm:table-cell">
                        {order.items?.length || 0} item(s)
                      </td>
                      <td className="px-2 sm:px-4 lg:px-6 py-2 sm:py-4 whitespace-nowrap text-xs sm:text-sm font-semibold text-gray-900">
                        ₹{getOrderTotal(order).toLocaleString()}
                      </td>
                      <td className="px-2 sm:px-4 lg:px-6 py-2 sm:py-4 whitespace-nowrap">
                        <span className={`px-1.5 sm:px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(order.status)}`}>
                          {order.status?.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-2 sm:px-4 lg:px-6 py-2 sm:py-4 whitespace-nowrap text-xs sm:text-sm">
                        <div className="flex gap-1 sm:gap-2 flex-wrap justify-center">
                          <button
                            onClick={() => setSelectedOrder(order)}
                            className="text-yellow-600 hover:text-yellow-800 bg-yellow-50 px-1 sm:px-2 py-1 rounded text-[10px] sm:text-xs"
                          >
                            <span className="sm:hidden">👁️</span>
                            <span className="hidden sm:inline">View</span>
                          </button>
                          
                          {/* Chat Button with Notification Badge */}
                          <div className="relative">
                            <button
                              onClick={() => handleChatOpen(order)}
                              className="text-purple-600 hover:text-purple-900 bg-purple-50 px-1 sm:px-2 py-1 rounded text-[10px] sm:text-xs flex items-center gap-0.5 sm:gap-1"
                              title="Chat with Customer"
                            >
                              <span className="hidden sm:inline">👥💬</span>
                              <span className="sm:hidden">👤</span>
                            </button>
                            {unreadCounts[order.id] && (
                              <span className="absolute -top-1 -right-1 sm:-top-2 sm:-right-2 bg-red-500 text-white text-[8px] sm:text-xs rounded-full h-3 w-3 sm:h-5 sm:w-5 flex items-center justify-center font-bold">
                                {unreadCounts[order.id] > 9 ? '9+' : unreadCounts[order.id]}
                              </span>
                            )}
                          </div>

                          {/* Vendor Chat Button with Notification Badge */}
                          <div className="relative">
                            <button
                              onClick={() => handleVendorChatOpen(order)}
                              className="text-green-600 hover:text-green-900 bg-green-50 px-1 sm:px-2 py-1 rounded text-[10px] sm:text-xs flex items-center gap-0.5 sm:gap-1"
                              title="Chat with Vendor for Pickup"
                            >
                              <span className="hidden sm:inline">🏢💬</span>
                              <span className="sm:hidden">🏢</span>
                            </button>
                            {vendorUnreadCounts[order.id] && (
                              <span className="absolute -top-1 -right-1 sm:-top-2 sm:-right-2 bg-red-500 text-white text-[8px] sm:text-xs rounded-full h-3 w-3 sm:h-5 sm:w-5 flex items-center justify-center font-bold">
                                {vendorUnreadCounts[order.id] > 9 ? '9+' : vendorUnreadCounts[order.id]}
                              </span>
                            )}
                          </div>
                          
                          {order.status === 'assigned' && (
                            <button
                              onClick={() => handleStatusUpdate(order.id, 'picked_up')}
                              className="text-orange-600 hover:text-orange-900 bg-orange-50 px-2 py-1 rounded text-xs"
                            >
                              Pick Up
                            </button>
                          )}
                          
                          {order.status === 'picked_up' && (
                            <button
                              onClick={() => handleStatusUpdate(order.id, 'in_transit')}
                              className="text-indigo-600 hover:text-indigo-900 bg-indigo-50 px-2 py-1 rounded text-xs"
                            >
                              In Transit
                            </button>
                          )}
                          
                          {(['picked_up', 'in_transit', 'shipped'].includes(order.status)) && (
                            <button
                              onClick={() => handleStatusUpdate(order.id, 'delivered')}
                              className="text-green-600 hover:text-green-900 bg-green-50 px-2 py-1 rounded text-xs"
                            >
                              Delivered
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Order Details Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Order Details</h2>
                <button
                  onClick={() => setSelectedOrder(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-6">
                {/* Order Info */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Order Number</p>
                      <p className="font-semibold">{selectedOrder.order_number || `#${selectedOrder.id?.substring(0, 8)}`}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Status</p>
                      <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(selectedOrder.status)}`}>
                        {selectedOrder.status?.toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Total Amount</p>
                      <p className="font-semibold text-lg">₹{getOrderTotal(selectedOrder).toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Items</p>
                      <p className="font-semibold">{selectedOrder.items?.length || 0} item(s)</p>
                    </div>
                  </div>
                </div>

                {/* Delivery Address */}
                {selectedOrder.shipping_address && (
                  <div className="bg-green-50 p-4 rounded-lg">
                    <h3 className="text-lg font-semibold mb-3 text-green-900">Delivery Address</h3>
                    <div className="space-y-2">
                      <p className="font-medium">
                        {selectedOrder.shipping_address.first_name} {selectedOrder.shipping_address.last_name}
                      </p>
                      <p className="text-gray-700">{selectedOrder.shipping_address.address_line1}</p>
                      {selectedOrder.shipping_address.address_line2 && (
                        <p className="text-gray-700">{selectedOrder.shipping_address.address_line2}</p>
                      )}
                      <p className="text-gray-700">
                        {selectedOrder.shipping_address.city}, {selectedOrder.shipping_address.state_province} {selectedOrder.shipping_address.postal_code}
                      </p>
                      {selectedOrder.shipping_address.phone && (
                        <p className="font-medium text-green-800">{selectedOrder.shipping_address.phone}</p>
                      )}
                    </div>
                  </div>
                )}

                {/* Order Items */}
                <div>
                  <h3 className="text-lg font-semibold mb-3">Order Items</h3>
                  <div className="space-y-2">
                    {selectedOrder.items?.map((item, index) => (
                      <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                        <div>
                          <p className="font-medium">{item.product_name || 'Unknown Product'}</p>
                          <p className="text-sm text-gray-600">Qty: {item.quantity}</p>
                        </div>
                        <p className="font-semibold">₹{(item.unit_price * item.quantity).toLocaleString()}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="flex gap-3 pt-4 border-t">
                  {selectedOrder.status === 'assigned' && (
                    <button
                      onClick={() => {
                        handleStatusUpdate(selectedOrder.id, 'picked_up');
                        setSelectedOrder(null);
                      }}
                      className="bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600"
                    >
                      Mark as Picked Up
                    </button>
                  )}
                  
                  {selectedOrder.status === 'picked_up' && (
                    <button
                      onClick={() => {
                        handleStatusUpdate(selectedOrder.id, 'in_transit');
                        setSelectedOrder(null);
                      }}
                      className="bg-amber-500 text-white px-4 py-2 rounded hover:bg-amber-600"
                    >
                      Mark In Transit
                    </button>
                  )}
                  
                  {(['picked_up', 'in_transit', 'shipped'].includes(selectedOrder.status)) && (
                    <button
                      onClick={() => {
                        handleStatusUpdate(selectedOrder.id, 'delivered');
                        setSelectedOrder(null);
                      }}
                      className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                    >
                      Mark as Delivered
                    </button>
                  )}
                  
                  <button
                    onClick={() => setSelectedOrder(null)}
                    className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Chat Interface Modal */}
      {chatOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-xs w-full h-[450px] flex flex-col">
            {/* Chat Header */}
            <div className="flex justify-between items-center p-3 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">
                Chat - Order #{chatOrder.order_number || chatOrder.id.substring(0, 8)}
              </h3>
              <button
                onClick={handleChatClose}
                className="text-gray-500 hover:text-gray-700 p-1"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Chat Content */}
            <div className="flex-1 overflow-hidden">
              <ChatInterface
                orderId={chatOrder.id}
                recipientId={chatOrder.customer_id}
                recipientName={chatOrder.customer_email || 'Customer'}
                onClose={handleChatClose}
                onUnreadCountChange={(count) => {
                  setUnreadCounts(prev => ({
                    ...prev,
                    [chatOrder.id]: count
                  }));
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Vendor Chat Interface Modal */}
      {vendorChatOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full h-[500px] flex flex-col">
            {/* Chat Header */}
            <div className="flex justify-between items-center p-3 border-b border-gray-200 bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-t-lg">
              <h3 className="text-lg font-semibold flex items-center">
                <span className="mr-2">🏭</span>
                Pickup Chat - Order #{vendorChatOrder.order_number || vendorChatOrder.id.substring(0, 8)}
              </h3>
              <button
                onClick={handleVendorChatClose}
                className="text-white hover:text-gray-200 p-1"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Chat Content */}
            <div className="flex-1 overflow-hidden">
              <VendorDeliveryChatInterface
                orderId={vendorChatOrder.id}
                recipientId={vendorChatOrder.vendor_id || vendorChatOrder.seller_id}
                recipientName={vendorChatOrder.vendor_name || 'Vendor'}
                onClose={handleVendorChatClose}
                onUnreadCountChange={(count) => {
                  setVendorUnreadCounts(prev => ({
                    ...prev,
                    [vendorChatOrder.id]: count
                  }));
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Notification Popup */}
      {showNotification && (
        <div className="fixed top-20 right-4 bg-white border border-gray-200 rounded-lg shadow-lg p-4 z-50 max-w-sm animate-bounce">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-bold">💬</span>
              </div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900">New Message!</p>
              <p className="text-sm text-gray-600">{notificationMessage}</p>
            </div>
            <div className="ml-auto">
              <button
                onClick={() => setShowNotification(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DeliveryBoyDashboard;