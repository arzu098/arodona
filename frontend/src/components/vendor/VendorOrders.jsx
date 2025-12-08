import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import vendorService from '../../services/vendorService';
import api from '../../services/api';
import VendorDeliveryChatInterface from '../chat/VendorDeliveryChatInterface';
import VendorCustomerChatInterface from '../chat/VendorCustomerChatInterface';

const VendorOrders = () => {
  const { user, logout } = useAuth();
  const [orders, setOrders] = useState([]);
  const [vendorProfile, setVendorProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, pending, processing, shipped, completed
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [deliveryBoys, setDeliveryBoys] = useState([]);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [selectedDeliveryBoy, setSelectedDeliveryBoy] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [expectedDeliveryDate, setExpectedDeliveryDate] = useState('');
  const [showChatModal, setShowChatModal] = useState(false);
  const [chatOrderId, setChatOrderId] = useState(null);
  const [showCustomerChatModal, setShowCustomerChatModal] = useState(false);
  const [customerChatOrderId, setCustomerChatOrderId] = useState(null);
  const [chatUnreadCounts, setChatUnreadCounts] = useState({}); // Track unread counts per order

  useEffect(() => {
    fetchVendorData();
  }, []);

  // Auto-refresh effect
  useEffect(() => {
    let interval;
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchVendorData();
        setLastRefresh(new Date());
      }, 30000); // Refresh every 30 seconds
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  // Handle unread count updates from chat components
  const handleUnreadCountChange = (orderId, chatType, count) => {
    setChatUnreadCounts(prev => ({
      ...prev,
      [`${orderId}-${chatType}`]: count
    }));
  };

  // Reset unread count when chat is opened
  const handleOpenDeliveryChat = (orderId) => {
    const order = orders.find(o => o.id === orderId);
    
    // Debug log to see what fields are available - ALWAYS LOG
    console.log('🔍 DEBUGGING: Order delivery fields for order', orderId, ':', {
      assigned_delivery_boy: order?.assigned_delivery_boy,
      delivery_boy_id: order?.delivery_boy_id,
      delivery_boy_name: order?.delivery_boy_name,
      delivery_partner: order?.delivery_partner,
      deliveryBoyId: order?.deliveryBoyId,
      delivery_boy: order?.delivery_boy,
      isAssignedByHelper: isDeliveryBoyAssigned(order),
      full_order_keys: order ? Object.keys(order) : 'no order found'
    });
    
    // Since chat is working when we click OK, delivery boy IS assigned
    // The detection logic needs to be more lenient or the field names are different
    console.log('✅ Opening delivery chat for order:', orderId);
    
    setChatOrderId(orderId);
    setShowChatModal(true);
    // Reset unread count immediately
    setChatUnreadCounts(prev => ({
      ...prev,
      [`${orderId}-delivery`]: 0
    }));
  };

  const handleOpenCustomerChat = (orderId) => {
    setCustomerChatOrderId(orderId);
    setShowCustomerChatModal(true);
    // Reset unread count immediately
    setChatUnreadCounts(prev => ({
      ...prev,
      [`${orderId}-customer`]: 0
    }));
  };

  const fetchVendorData = async () => {
    try {
      // Get vendor profile
      console.log('Fetching vendor profile...');
      const vendor = await vendorService.getMyProfile();
      console.log('Vendor profile:', vendor);
      setVendorProfile(vendor);

      // Fetch orders for this vendor
      console.log('Fetching vendor orders for vendor ID:', vendor.id);
      const ordersData = await vendorService.getVendorOrders(vendor.id, { limit: 100 });
      console.log('Raw orders response:', ordersData);
      
      // Handle both array and object responses
      let ordersList = [];
      if (Array.isArray(ordersData)) {
        ordersList = ordersData;
      } else if (ordersData.orders && Array.isArray(ordersData.orders)) {
        ordersList = ordersData.orders;
      } else if (ordersData.data && Array.isArray(ordersData.data)) {
        ordersList = ordersData.data;
      }
      
      console.log('Processed orders list:', ordersList);
      
      // Debug: Log delivery-related fields and pricing for each order
      ordersList.forEach((order, index) => {
        console.log(`Order ${index + 1} full details:`, {
          id: order.id,
          order_number: order.order_number,
          // Delivery fields
          assigned_delivery_boy: order.assigned_delivery_boy,
          delivery_boy_id: order.delivery_boy_id,
          delivery_boy_name: order.delivery_boy_name,
          delivery_partner: order.delivery_partner,
          deliveryBoyId: order.deliveryBoyId,
          delivery_boy: order.delivery_boy,
          isAssigned: isDeliveryBoyAssigned(order),
          // Pricing fields
          items_count: order.items?.length || 0,
          items_exist: !!order.items,
          total: order.total,
          totals: order.totals,
          pricing: order.pricing,
          grand_total: order.grand_total,
          amount: order.amount,
          calculated_total: getOrderTotal(order),
          // Full items array preview
          items_preview: order.items?.slice(0, 2).map(item => ({
            product_name: item.product_name,
            quantity: item.quantity,
            unit_price: item.unit_price,
            line_total: item.line_total
          })) || []
        });
      });
      
      setOrders(ordersList);
      
      // Fetch delivery boys for this vendor
      const deliveryBoysResponse = await api.get(`/api/delivery/get_all`);
      setDeliveryBoys(deliveryBoysResponse.data || []);
      
      console.log(`Successfully loaded ${ordersList.length} orders for vendor`);
    } catch (error) {
      console.error('Error fetching vendor data:', error);
      console.error('Error details:', error.response?.data || error.message);
      
      // Set empty data on error to show proper "no orders" message
      setOrders([]);
      setVendorProfile(null);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateOrderStatus = async (orderId, newStatus) => {
    try {
      console.log(`Updating order ${orderId} status to ${newStatus}`); // Debug log
      const response = await api.patch(`/api/orders/${orderId}`, { status: newStatus });
      console.log('Status update response:', response.data); // Debug log
      
      // Refresh the order data to get updated information
      await fetchVendorData();
      setLastRefresh(new Date());
      
      alert('Order status updated successfully');
    } catch (error) {
      console.error('Error updating order status:', error);
      alert(`Failed to update order status: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleAssignDeliveryBoy = async () => {
    if (!selectedDeliveryBoy || !selectedOrder) {
      alert('Please select a delivery boy');
      return;
    }

    try {
      console.log(`Assigning delivery boy ${selectedDeliveryBoy} to order ${selectedOrder.id}`); // Debug log
      
      // First assign the delivery boy
      const assignResponse = await api.patch(`/api/orders/${selectedOrder.id}/assign-delivery`, {
        delivery_boy_id: selectedDeliveryBoy
      });
      console.log('Delivery assignment response:', assignResponse.data); // Debug log
      
      // If expected delivery date is set, update it too
      if (expectedDeliveryDate) {
        console.log(`Setting expected delivery date ${expectedDeliveryDate} for order ${selectedOrder.id}`);
        await api.patch(`/api/orders/${selectedOrder.id}`, {
          expected_delivery: expectedDeliveryDate
        });
      }
      
      // Refresh the order data to get updated information with delivery boy details
      await fetchVendorData();
      setLastRefresh(new Date());
      
      setShowAssignModal(false);
      setSelectedDeliveryBoy('');
      setExpectedDeliveryDate('');
      setSelectedOrder(null); // Close the modal
      alert(`Delivery boy assigned successfully${expectedDeliveryDate ? ' with expected delivery date' : ''}`);
    } catch (error) {
      console.error('Error assigning delivery boy:', error);
      alert(`Failed to assign delivery boy: ${error.response?.data?.detail || error.message}`);
    }
  };



  const fetchOrderDetails = async (orderId) => {
    try {
      const response = await api.get(`/api/orders/${orderId}`);
      console.log('Order details response:', response.data); // Debug log
      return response.data;
    } catch (error) {
      console.error('Error fetching order details:', error);
      return null;
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      confirmed: 'bg-blue-100 text-blue-800',
      processing: 'bg-purple-100 text-purple-800',
      shipped: 'bg-indigo-100 text-indigo-800',
      picked_up: 'bg-orange-100 text-orange-800',
      out_for_delivery: 'bg-cyan-100 text-cyan-800',
      delivered: 'bg-green-100 text-green-800',
      delivery_failed: 'bg-red-100 text-red-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
      returned: 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status) => {
    const icons = {
      pending: '⏳',
      confirmed: '✅',
      processing: '⚙️',
      shipped: '🚚',
      picked_up: '📦',
      out_for_delivery: '🛵',
      delivered: '✅',
      delivery_failed: '❌',
      completed: '🎉',
      cancelled: '❌',
      returned: '↩️',
    };
    return icons[status] || '📋';
  };

  const getStatusCounts = () => {
    return {
      pending: orders.filter(o => o.status === 'pending').length,
      processing: orders.filter(o => o.status === 'processing').length,
      shipped: orders.filter(o => o.status === 'shipped').length,
      delivered: orders.filter(o => o.status === 'delivered').length,
      completed: orders.filter(o => o.status === 'completed').length,
      cancelled: orders.filter(o => o.status === 'cancelled').length,
      assigned: orders.filter(o => o.assigned_delivery_boy || o.status === 'assigned').length,
      total: orders.length
    };
  };

  const statusCounts = getStatusCounts();

  const filteredOrders = orders.filter(order => {
    if (filter === 'all') return true;
    if (filter === 'assigned') return order.assigned_delivery_boy || order.status === 'assigned';
    return order.status === filter;
  });

  const getOrderTotal = (order) => {
    // Check multiple possible total fields
    const total = order.totals?.total || 
                  order.total || 
                  order.pricing?.grand_total || 
                  order.grand_total ||
                  order.amount ||
                  order.total_amount ||
                  order.order_total ||
                  0;
    
    // If still 0, calculate from items
    if (total === 0 && order.items && Array.isArray(order.items) && order.items.length > 0) {
      const calculatedTotal = order.items.reduce((sum, item) => {
        const itemTotal = item.line_total || 
                         item.total || 
                         (item.quantity * item.unit_price) || 
                         (item.quantity * item.price) ||
                         0;
        return sum + itemTotal;
      }, 0);
      console.log(`💰 Calculated total for order ${order.id?.substring(0, 8)}: ₹${calculatedTotal} from ${order.items.length} items`);
      return calculatedTotal;
    }
    
    return total;
  };

  const getItemsCount = (order) => {
    return order.items?.length || order.item_count || 0;
  };

  // Helper function to check if delivery boy is assigned
  const isDeliveryBoyAssigned = (order) => {
    if (!order) return false;
    
    // Check multiple possible field variations
    const deliveryFields = [
      order.assigned_delivery_boy,
      order.delivery_boy_id,
      order.delivery_boy_name,
      order.delivery_partner,
      order.deliveryBoyId,
      order.delivery_boy,
      order.assignedDeliveryBoy,
      order.deliveryBoy,
      order.deliveryBoyName,
      order.delivery_assigned,
      order.assigned_to,
      order.courier_id,
      order.driver_id,
      order.delivery_agent_id,
      order.delivery_agent_name
    ];
    
    // Return true if any field has a truthy value
    const hasDeliveryAssignment = deliveryFields.some(field => 
      field && 
      field !== '' && 
      field !== null && 
      field !== undefined &&
      field !== 'null' &&
      field !== 'undefined'
    );
    
    console.log('🔍 isDeliveryBoyAssigned check:', {
      orderId: order.id?.substring(0, 8),
      hasDeliveryAssignment,
      checkedFields: deliveryFields.map((field, index) => ({
        fieldName: ['assigned_delivery_boy', 'delivery_boy_id', 'delivery_boy_name', 'delivery_partner', 'deliveryBoyId', 'delivery_boy', 'assignedDeliveryBoy', 'deliveryBoy', 'deliveryBoyName', 'delivery_assigned', 'assigned_to', 'courier_id', 'driver_id', 'delivery_agent_id', 'delivery_agent_name'][index],
        value: field,
        truthy: !!field
      }))
    });
    
    return hasDeliveryAssignment;
  };

  // Helper function to get delivery boy display name
  const getDeliveryBoyName = (order) => {
    return order?.delivery_boy_name || 
           order?.delivery_partner || 
           order?.deliveryBoyName ||
           'Delivery Boy';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl">Loading orders...</div>
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
                <h1 className="text-2xl font-bold text-gray-900">Order Management</h1>
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
        {/* Status Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4 mb-6">
          <div className="bg-white shadow rounded-lg p-4 text-center hover:shadow-md transition-shadow cursor-pointer" onClick={() => setFilter('all')}>
            <div className="text-2xl mb-2">📊</div>
            <div className="text-2xl font-bold text-gray-900">{statusCounts.total}</div>
            <div className="text-xs text-gray-600">Total Orders</div>
          </div>
          
          <div className="bg-white shadow rounded-lg p-4 text-center hover:shadow-md transition-shadow cursor-pointer" onClick={() => setFilter('pending')}>
            <div className="text-2xl mb-2">⏳</div>
            <div className="text-2xl font-bold text-yellow-600">{statusCounts.pending}</div>
            <div className="text-xs text-gray-600">Pending</div>
          </div>
          
          <div className="bg-white shadow rounded-lg p-4 text-center hover:shadow-md transition-shadow cursor-pointer" onClick={() => setFilter('processing')}>
            <div className="text-2xl mb-2">⚙️</div>
            <div className="text-2xl font-bold text-purple-600">{statusCounts.processing}</div>
            <div className="text-xs text-gray-600">Processing</div>
          </div>
          
          <div className="bg-white shadow rounded-lg p-4 text-center hover:shadow-md transition-shadow cursor-pointer" onClick={() => setFilter('shipped')}>
            <div className="text-2xl mb-2">🚚</div>
            <div className="text-2xl font-bold text-indigo-600">{statusCounts.shipped}</div>
            <div className="text-xs text-gray-600">Shipped</div>
          </div>
          
          <div className="bg-white shadow rounded-lg p-4 text-center hover:shadow-md transition-shadow cursor-pointer" onClick={() => setFilter('delivered')}>
            <div className="text-2xl mb-2">✅</div>
            <div className="text-2xl font-bold text-green-600">{statusCounts.delivered}</div>
            <div className="text-xs text-gray-600">Delivered</div>
          </div>
          
          <div className="bg-white shadow rounded-lg p-4 text-center hover:shadow-md transition-shadow cursor-pointer" onClick={() => setFilter('completed')}>
            <div className="text-2xl mb-2">🎉</div>
            <div className="text-2xl font-bold text-green-600">{statusCounts.completed}</div>
            <div className="text-xs text-gray-600">Completed</div>
          </div>
          
          <div className="bg-white shadow rounded-lg p-4 text-center hover:shadow-md transition-shadow cursor-pointer" onClick={() => setFilter('assigned')}>
            <div className="text-2xl mb-2">👤</div>
            <div className="text-2xl font-bold text-purple-600">{statusCounts.assigned}</div>
            <div className="text-xs text-gray-600">Assigned</div>
          </div>
          
          <div className="bg-white shadow rounded-lg p-4 text-center hover:shadow-md transition-shadow cursor-pointer" onClick={() => setFilter('cancelled')}>
            <div className="text-2xl mb-2">❌</div>
            <div className="text-2xl font-bold text-red-600">{statusCounts.cancelled}</div>
            <div className="text-xs text-gray-600">Cancelled</div>
          </div>
        </div>

        {/* Auto-refresh Controls */}
        <div className="bg-white shadow rounded-lg p-4 mb-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="autoRefresh"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <label htmlFor="autoRefresh" className="text-sm text-gray-700">
                  Auto-refresh (30s)
                </label>
              </div>
              <button
                onClick={() => {
                  fetchVendorData();
                  setLastRefresh(new Date());
                }}
                className="bg-blue-100 text-blue-700 px-3 py-1 rounded-lg hover:bg-blue-200 transition-colors text-sm flex items-center gap-1"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh Now
              </button>
            </div>
            <div className="text-xs text-gray-500">
              Last updated: {lastRefresh.toLocaleTimeString()}
            </div>
          </div>
        </div>

        {/* Filter Buttons */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
                filter === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              📊 All ({statusCounts.total})
            </button>
            <button
              onClick={() => setFilter('pending')}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
                filter === 'pending'
                  ? 'bg-yellow-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              ⏳ Pending ({statusCounts.pending})
            </button>
            <button
              onClick={() => setFilter('processing')}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
                filter === 'processing'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              ⚙️ Processing ({statusCounts.processing})
            </button>
            <button
              onClick={() => setFilter('shipped')}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
                filter === 'shipped'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              🚚 Shipped ({statusCounts.shipped})
            </button>
            <button
              onClick={() => setFilter('assigned')}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
                filter === 'assigned'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              👤 Assigned ({statusCounts.assigned})
            </button>
            <button
              onClick={() => setFilter('completed')}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
                filter === 'completed'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              🎉 Completed ({statusCounts.completed})
            </button>
          </div>
        </div>

        {/* Orders List */}
        {filteredOrders.length === 0 ? (
          <div className="bg-white shadow rounded-lg p-12 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No orders found</h3>
            <p className="text-gray-600">
              {filter === 'all'
                ? 'You have no orders yet'
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
                    <th className="px-2 sm:px-4 lg:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden md:table-cell">
                      Date
                    </th>
                    <th className="px-2 sm:px-4 lg:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden sm:table-cell">
                      Items
                    </th>
                    <th className="px-2 sm:px-4 lg:px-6 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total
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
                        <div className="text-xs text-gray-500 md:hidden">
                          {new Date(order.created_at).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-2 sm:px-4 lg:px-6 py-2 sm:py-4 whitespace-nowrap text-xs sm:text-sm text-gray-500 hidden md:table-cell">
                        {new Date(order.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-2 sm:px-4 lg:px-6 py-2 sm:py-4 whitespace-nowrap text-xs sm:text-sm text-gray-500 hidden sm:table-cell">
                        {getItemsCount(order)} item(s)
                      </td>
                      <td className="px-2 sm:px-4 lg:px-6 py-2 sm:py-4 whitespace-nowrap">
                        <div className="text-xs sm:text-sm font-semibold text-gray-900">
                          ₹{getOrderTotal(order).toLocaleString()}
                        </div>
                        <div className="text-xs text-gray-500 sm:hidden">
                          {getItemsCount(order)} items
                        </div>
                      </td>
                      <td className="px-2 sm:px-4 lg:px-6 py-2 sm:py-4 whitespace-nowrap">
                        <div className="flex flex-col gap-1">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(order.status)} flex items-center gap-1`}>
                            <span className="hidden sm:inline">{getStatusIcon(order.status)}</span>
                            <span className="text-xs">{order.status?.toUpperCase()}</span>
                          </span>
                          {isDeliveryBoyAssigned(order) && (
                            <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 hidden sm:inline-block">
                              👤 ASSIGNED
                            </span>
                          )}
                          {getDeliveryBoyName(order) !== 'Delivery Boy' && (
                            <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              🚚 {getDeliveryBoyName(order)}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-2 sm:px-4 lg:px-6 py-2 sm:py-4 whitespace-nowrap text-xs sm:text-sm">
                        <div className="flex gap-1 sm:gap-2 flex-wrap justify-center">
                          <button
                            onClick={async () => {
                              const fullOrderDetails = await fetchOrderDetails(order.id);
                              if (fullOrderDetails) {
                                setSelectedOrder(fullOrderDetails);
                              } else {
                                setSelectedOrder(order);
                              }
                            }}
                            className="text-blue-600 hover:text-blue-900 bg-blue-50 px-1 sm:px-2 py-1 rounded text-[10px] sm:text-xs flex items-center gap-0.5 sm:gap-1"
                          >
                            <svg className="w-2.5 h-2.5 sm:w-3 sm:h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                            <span className="hidden sm:inline">View</span>
                          </button>
                          
                          {/* Pickup Button - Available for shipped orders */}
                          {['shipped', 'out_for_delivery'].includes(order.status) && (
                            <button
                              onClick={() => handleUpdateOrderStatus(order.id, 'delivered')}
                              className="text-green-600 hover:text-green-900 bg-green-50 px-1 sm:px-2 py-1 rounded text-[10px] sm:text-xs flex items-center gap-0.5 sm:gap-1"
                              title="Mark as picked up/delivered"
                            >
                              <svg className="w-2.5 h-2.5 sm:w-3 sm:h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              <span className="hidden sm:inline">Pickup</span>
                            </button>
                          )}
                          
                          {/* Delivery Chat Button - Always available */}
                          <button
                            onClick={() => handleOpenDeliveryChat(order.id)}
                            className="text-purple-600 hover:text-purple-900 bg-purple-50 px-1 sm:px-2 py-1 rounded text-[10px] sm:text-xs flex items-center gap-0.5 sm:gap-1 relative"
                            title="Chat with delivery boy"
                          >
                            <svg className="w-2.5 h-2.5 sm:w-3 sm:h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                            </svg>
                            <span className="hidden sm:inline">
                              Delivery
                            </span>
                            <span className="sm:hidden">🚚</span>
                            {/* Unread badge */}
                            {chatUnreadCounts[`${order.id}-delivery`] > 0 && (
                              <span className="absolute -top-1 -right-1 sm:-top-2 sm:-right-2 bg-red-500 text-white text-[8px] sm:text-xs rounded-full h-3 w-3 sm:h-5 sm:w-5 flex items-center justify-center font-bold">
                                {chatUnreadCounts[`${order.id}-delivery`]}
                              </span>
                            )}
                            {/* Delivery boy is assigned - no warning needed */}
                          </button>
                          
                          {/* Customer Chat Button - Always available for order communication */}
                          <button
                            onClick={() => handleOpenCustomerChat(order.id)}
                            className="text-blue-600 hover:text-blue-900 bg-blue-50 px-1 sm:px-2 py-1 rounded text-[10px] sm:text-xs flex items-center gap-0.5 sm:gap-1 relative"
                            title="Chat with customer"
                          >
                            <svg className="w-2.5 h-2.5 sm:w-3 sm:h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a2 2 0 01-2-2v-6a2 2 0 012-2h8z" />
                            </svg>
                            <span className="hidden sm:inline">Customer</span>
                            <span className="sm:hidden">👤</span>
                            {/* Unread badge */}
                            {chatUnreadCounts[`${order.id}-customer`] > 0 && (
                              <span className="absolute -top-1 -right-1 sm:-top-2 sm:-right-2 bg-red-500 text-white text-[8px] sm:text-xs rounded-full h-3 w-3 sm:h-5 sm:w-5 flex items-center justify-center font-bold">
                                {chatUnreadCounts[`${order.id}-customer`]}
                              </span>
                            )}
                          </button>
                          
                          {!isDeliveryBoyAssigned(order) && !['completed', 'cancelled', 'delivered', 'returned'].includes(order.status) && (
                            <button
                              onClick={() => {
                                setSelectedOrder(order);
                                setExpectedDeliveryDate(order.expected_delivery ? new Date(order.expected_delivery).toISOString().split('T')[0] : '');
                                setShowAssignModal(true);
                              }}
                              className="text-purple-600 hover:text-purple-900 bg-purple-50 px-2 py-1 rounded text-xs"
                            >
                              Assign
                            </button>
                          )}
                          
                          {order.status === 'pending' && (
                            <button
                              onClick={() => handleUpdateOrderStatus(order.id, 'processing')}
                              className="text-green-600 hover:text-green-900 bg-green-50 px-2 py-1 rounded text-xs"
                            >
                              Accept
                            </button>
                          )}
                          
                          {order.status === 'processing' && isDeliveryBoyAssigned(order) && (
                            <button
                              onClick={() => handleUpdateOrderStatus(order.id, 'shipped')}
                              className="text-indigo-600 hover:text-indigo-900 bg-indigo-50 px-2 py-1 rounded text-xs"
                            >
                              Ship
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
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
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
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Order Number</p>
                      <p className="font-semibold">{selectedOrder.order_number || `#${selectedOrder.id?.substring(0, 8)}`}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Date</p>
                      <p className="font-semibold">{new Date(selectedOrder.created_at).toLocaleDateString()}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Status</p>
                      <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(selectedOrder.status)} flex items-center gap-1`}>
                        <span>{getStatusIcon(selectedOrder.status)}</span>
                        {selectedOrder.status?.toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Total Amount</p>
                      <p className="font-semibold text-lg">₹{(selectedOrder.pricing?.grand_total || getOrderTotal(selectedOrder)).toLocaleString()}</p>
                    </div>
                  </div>
                </div>

                {/* Customer Information */}
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3 text-blue-900">Customer Information</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Customer ID</p>
                      <p className="font-medium">{selectedOrder.customer_id}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Email</p>
                      <p className="font-medium">{selectedOrder.customer_email || 'Not provided'}</p>
                    </div>
                  </div>
                </div>

                {/* Delivery Address */}
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3 text-green-900">Delivery Address</h3>
                  {selectedOrder.shipping_address ? (
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
                      <p className="text-gray-700">{selectedOrder.shipping_address.country_code}</p>
                      {selectedOrder.shipping_address.phone && (
                        <p className="font-medium text-green-800">📞 {selectedOrder.shipping_address.phone}</p>
                      )}
                      {selectedOrder.shipping_address.email && (
                        <p className="font-medium text-green-800">📧 {selectedOrder.shipping_address.email}</p>
                      )}
                    </div>
                  ) : (
                    <p className="text-gray-600">No shipping address provided</p>
                  )}
                </div>

                {/* Payment Information */}
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3 text-yellow-900">Payment Information</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Payment Method</p>
                      <p className="font-medium">{selectedOrder.payment_details?.method || 'Not specified'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Payment Status</p>
                      <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                        selectedOrder.payment_status === 'completed' ? 'bg-green-100 text-green-800' : 
                        selectedOrder.payment_status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {selectedOrder.payment_status?.toUpperCase() || 'PENDING'}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Amount</p>
                      <p className="font-semibold">₹{(selectedOrder.payment_details?.amount || selectedOrder.pricing?.grand_total || 0).toLocaleString()}</p>
                    </div>
                  </div>
                </div>

                {/* Order Items */}
                <div>
                  <h3 className="text-lg font-semibold mb-3">Order Items</h3>
                  <div className="bg-white border rounded-lg overflow-hidden">
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vendor</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unit Price</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {selectedOrder.items?.map((item, index) => (
                            <tr key={index}>
                              <td className="px-4 py-4 whitespace-nowrap">
                                <div className="flex items-center">
                                  {item.product_image && (
                                    <img className="h-10 w-10 rounded-full mr-3" src={item.product_image} alt={item.product_name} />
                                  )}
                                  <div>
                                    <div className="text-sm font-medium text-gray-900">{item.product_name || 'Product'}</div>
                                    <div className="text-xs text-gray-500">ID: {item.product_id}</div>
                                  </div>
                                </div>
                              </td>
                              <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                                {item.vendor_name || vendorProfile?.business_name || '-'}
                              </td>
                              <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                                {item.quantity}
                              </td>
                              <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                                ₹{item.unit_price?.toLocaleString() || 0}
                              </td>
                              <td className="px-4 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                                ₹{item.line_total?.toLocaleString() || (item.quantity * item.unit_price).toLocaleString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                {/* Delivery Information */}
                {(selectedOrder.assigned_delivery_boy || selectedOrder.delivery_boy_name) && (
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <h3 className="text-lg font-semibold mb-3 text-purple-900">Delivery Information</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Delivery Boy:</span>
                          <span className="font-medium">{selectedOrder.delivery_boy_name || 'Not Assigned'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Phone:</span>
                          <span className="font-medium">
                            {selectedOrder.delivery_boy_phone ? (
                              <a href={`tel:${selectedOrder.delivery_boy_phone}`} className="text-blue-600 hover:text-blue-800">
                                {selectedOrder.delivery_boy_phone}
                              </a>
                            ) : 'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Delivery Partner:</span>
                          <span className="font-medium">{selectedOrder.delivery_partner || 'Not Assigned'}</span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Assignment ID:</span>
                          <span className="font-medium text-xs">{selectedOrder.assigned_delivery_boy || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Expected Delivery:</span>
                          <span className="font-medium">
                            {selectedOrder.expected_delivery ? (
                              <span className="flex items-center gap-1">
                                📅 {new Date(selectedOrder.expected_delivery).toLocaleDateString('en-US', {
                                  weekday: 'short',
                                  year: 'numeric',
                                  month: 'short',
                                  day: 'numeric'
                                })}
                              </span>
                            ) : (
                              <span className="text-orange-600">Not Set</span>
                            )}
                          </span>
                        </div>

                      </div>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-3 pt-4 border-t flex-wrap">
                  {selectedOrder.status === 'pending' && (
                    <button
                      onClick={() => {
                        handleUpdateOrderStatus(selectedOrder.id, 'processing');
                        setSelectedOrder(null);
                      }}
                      className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                    >
                      Accept Order
                    </button>
                  )}
                  
                  {(selectedOrder.status === 'processing' || selectedOrder.status === 'confirmed') && !selectedOrder.assigned_delivery_boy && (
                    <button
                      onClick={() => {
                        setExpectedDeliveryDate(selectedOrder.expected_delivery ? new Date(selectedOrder.expected_delivery).toISOString().split('T')[0] : '');
                        setShowAssignModal(true);
                      }}
                      className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
                    >
                      Assign Delivery Boy
                    </button>
                  )}
                  
                  {selectedOrder.status === 'processing' && selectedOrder.assigned_delivery_boy && (
                    <button
                      onClick={() => {
                        handleUpdateOrderStatus(selectedOrder.id, 'shipped');
                        setSelectedOrder(null);
                      }}
                      className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
                    >
                      Mark as Shipped
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

      {/* Assign Delivery Boy Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Assign Delivery Boy</h3>
                <button
                  onClick={() => {
                    setShowAssignModal(false);
                    setSelectedDeliveryBoy('');
                    setExpectedDeliveryDate('');
                  }}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Delivery Boy
                  </label>
                  <select
                    value={selectedDeliveryBoy}
                    onChange={(e) => setSelectedDeliveryBoy(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="">Choose a delivery boy...</option>
                    {deliveryBoys.map((boy) => (
                      <option key={boy.id} value={boy.id}>
                        {boy.name} - {boy.phone}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="border-t pt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                    📅 Expected Delivery Date
                    <span className="text-xs text-gray-500">(Optional)</span>
                  </label>
                  <input
                    type="date"
                    value={expectedDeliveryDate}
                    onChange={(e) => setExpectedDeliveryDate(e.target.value)}
                    min={new Date().toISOString().split('T')[0]} // Minimum date is today
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Set when the order should be delivered</p>
                </div>

                {selectedOrder && (
                  <div className="bg-purple-50 p-3 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Order: <span className="font-medium">{selectedOrder.order_number || `#${selectedOrder.id?.substring(0, 8)}`}</span></p>
                    <p className="text-sm text-gray-600">Status: <span className="font-medium capitalize">{selectedOrder.status}</span></p>
                  </div>
                )}

                <div className="flex gap-3 pt-4">
                  <button
                    onClick={handleAssignDeliveryBoy}
                    className="flex-1 bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 flex items-center justify-center gap-1"
                    disabled={!selectedDeliveryBoy}
                  >
                    👤 Assign {expectedDeliveryDate && '📅'}
                  </button>
                  <button
                    onClick={() => {
                      setShowAssignModal(false);
                      setSelectedDeliveryBoy('');
                      setExpectedDeliveryDate('');
                    }}
                    className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Chat Modal */}
      {showChatModal && chatOrderId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 sm:p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-sm sm:max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
            <div className="p-3 sm:p-4 bg-gray-50 border-b border-gray-200 flex justify-between items-center flex-shrink-0">
              <div>
                <h3 className="text-base sm:text-lg font-semibold text-gray-900">Chat with Delivery Boy</h3>
                <p className="text-xs sm:text-sm text-gray-600">Order #{chatOrderId.substring(0, 8)}</p>
                {(() => {
                  const currentOrder = orders.find(order => order.id === chatOrderId);
                  const deliveryBoyName = getDeliveryBoyName(currentOrder);
                  if (deliveryBoyName) {
                    return <p className="text-xs text-green-600">✅ 🚚 {deliveryBoyName}</p>;
                  } else {
                    return <p className="text-xs text-blue-600">🚚 Delivery Boy Assigned</p>;
                  }
                })()}
              </div>
              <button
                onClick={() => {
                  setShowChatModal(false);
                  setChatOrderId(null);
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              <VendorDeliveryChatInterface 
                orderId={chatOrderId}
                recipientId={(() => {
                  const currentOrder = orders.find(order => order.id === chatOrderId);
                  return currentOrder?.assigned_delivery_boy || 
                         currentOrder?.delivery_boy_id || 
                         currentOrder?.deliveryBoyId || 
                         'unknown';
                })()}
                recipientName={(() => {
                  const currentOrder = orders.find(order => order.id === chatOrderId);
                  return getDeliveryBoyName(currentOrder);
                })()}
                onClose={() => {
                  setShowChatModal(false);
                  setChatOrderId(null);
                }}
                onUnreadCountChange={(count) => handleUnreadCountChange(chatOrderId, 'delivery', count)}
              />
            </div>
          </div>
        </div>
      )}

      {/* Customer Chat Modal */}
      {showCustomerChatModal && customerChatOrderId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="p-4 bg-gray-50 border-b border-gray-200 flex justify-between items-center flex-shrink-0">
              <div>
                <h3 className="text-base sm:text-lg font-semibold text-gray-900">Chat with Customer</h3>
                <p className="text-xs sm:text-sm text-gray-600">Order #{customerChatOrderId.substring(0, 8)}</p>
                {(() => {
                  const currentOrder = orders.find(order => order.id === customerChatOrderId);
                  return currentOrder?.customer_name ? (
                    <p className="text-xs text-gray-500">👤 {currentOrder.customer_name}</p>
                  ) : null;
                })()}
              </div>
              <button
                onClick={() => {
                  setShowCustomerChatModal(false);
                  setCustomerChatOrderId(null);
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              <VendorCustomerChatInterface 
                orderId={customerChatOrderId}
                recipientId={(() => {
                  const currentOrder = orders.find(order => order.id === customerChatOrderId);
                  return currentOrder?.customer_id;
                })()}
                recipientName={(() => {
                  const currentOrder = orders.find(order => order.id === customerChatOrderId);
                  return currentOrder?.customer_name || 'Customer';
                })()}
                onClose={() => {
                  setShowCustomerChatModal(false);
                  setCustomerChatOrderId(null);
                }}
                onUnreadCountChange={(count) => handleUnreadCountChange(customerChatOrderId, 'customer', count)}
              />
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default VendorOrders;
