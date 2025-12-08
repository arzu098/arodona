import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';

const DeliveryOrders = () => {
  const { user, logout } = useAuth();
  const [searchParams] = useSearchParams();
  const orderIdFromUrl = searchParams.get('order_id');
  
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('active'); // active, completed, all
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [showOtpModal, setShowOtpModal] = useState(false);
  const [otp, setOtp] = useState('');
  const [signature, setSignature] = useState('');

  useEffect(() => {
    fetchOrders();
  }, [filter]);

  useEffect(() => {
    if (orderIdFromUrl && orders.length > 0) {
      const order = orders.find(o => o.id === orderIdFromUrl);
      if (order) setSelectedOrder(order);
    }
  }, [orderIdFromUrl, orders]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      // Use the correct delivery API endpoint
      const response = await api.get('/api/delivery/my-orders');
      
      // Debug: log the orders data
      console.log('Fetched orders:', response.data.orders);
      // Transform the data to match expected format
      const transformedOrders = (response.data.orders || []).map(order => ({
        id: order.id || order._id,
        order_number: order.order_number,
        customer_id: order.customer_id,
        customer_email: order.customer_email,
        customer_name: order.shipping_address?.first_name + ' ' + order.shipping_address?.last_name || 'N/A',
        customer_phone: order.shipping_address?.phone || 'N/A',
        delivery_address: formatAddress(order.shipping_address),
        pickup_address: 'Adorona Store', // Default pickup location
        payment_type: order.payment_details?.method || 'cod',
        amount: order.pricing?.grand_total || order.total || 0,
        status: mapOrderStatus(order.status),
        pickup_status: getPickupStatus(order.status),
        delivery_status: getDeliveryStatus(order.status),
        created_at: order.created_at,
        pickup_time: order.pickup_time,
        delivery_time: order.delivery_time,
        estimated_delivery: order.estimated_delivery,
        items: order.items || [],
        distance: 'Calculating...', // Can be calculated later
        delivery_instructions: order.delivery_instructions || 'Standard delivery'
      }));
      setOrders(transformedOrders);
    } catch (error) {
      console.error('Error fetching orders:', error);
      setOrders([]); // Empty array instead of mock data
    } finally {
      setLoading(false);
    }
  };

  // Helper functions to format data
  const formatAddress = (address) => {
    if (!address) return 'Address not provided';
    
    const parts = [
      address.address_line1,
      address.address_line2,
      address.city,
      address.state_province,
      address.postal_code
    ].filter(Boolean);
    
    return parts.join(', ');
  };

  const mapOrderStatus = (status) => {
    const statusMap = {
      'assigned': 'accepted',
      'picked_up': 'picked_up',
      'in_transit': 'out_for_delivery',
      'shipped': 'out_for_delivery',
      'delivered': 'delivered',
      'delivery_failed': 'cancelled'
    };
    return statusMap[status] || status;
  };

  const getPickupStatus = (status) => {
    return ['picked_up', 'in_transit', 'shipped', 'delivered'].includes(status) ? 'completed' : 'pending';
  };

  const getDeliveryStatus = (status) => {
    if (status === 'delivered') return 'completed';
    if (['in_transit', 'shipped'].includes(status)) return 'out_for_delivery';
    return 'pending';
  };

  // Memoize filtered orders to prevent unnecessary re-renders
  const filteredOrders = useMemo(() => {
    return orders.filter(order => {
      if (filter === 'active') {
        return ['accepted', 'picked_up', 'out_for_delivery'].includes(order.status);
      } else if (filter === 'completed') {
        return ['delivered'].includes(order.status);
      }
      return true; // 'all' filter shows everything
    });
  }, [orders, filter]);

  const updateOrderStatus = useCallback(async (orderId, newStatus) => {
    try {
      // Map frontend status to backend status
      const backendStatusMap = {
        'accepted': 'assigned',
        'picked_up': 'picked_up', 
        'out_for_delivery': 'in_transit',
        'delivered': 'delivered'
      };
      
      const backendStatus = backendStatusMap[newStatus] || newStatus;
      
      // Use correct delivery API endpoint
      await api.patch(`/api/delivery/orders/${orderId}/status`, {
        status: backendStatus
      });
      
      // Update local state optimistically
      setOrders(prevOrders => prevOrders.map(order => 
        order.id === orderId 
          ? { 
              ...order, 
              status: newStatus,
              pickup_status: newStatus === 'picked_up' ? 'completed' : order.pickup_status,
              delivery_status: newStatus === 'delivered' ? 'completed' : 
                              newStatus === 'out_for_delivery' ? 'out_for_delivery' : order.delivery_status,
              pickup_time: newStatus === 'picked_up' ? new Date().toISOString() : order.pickup_time,
              delivery_time: newStatus === 'delivered' ? new Date().toISOString() : order.delivery_time
            }
          : order
      ));
      
      setShowStatusModal(false);
      setShowOtpModal(false);
      setOtp('');
      setSignature('');
      alert('Status updated successfully!');
    } catch (error) {
      console.error('Error updating status:', error);
      alert('Failed to update status. Please try again.');
    }
  }, []);

  const handleStatusUpdate = (order, newStatus) => {
    setSelectedOrder(order);
    if (newStatus === 'delivered') {
      setShowOtpModal(true);
    } else {
      updateOrderStatus(order.id, newStatus);
    }
  };

  const handleDeliveryConfirm = () => {
    if (otp.length >= 4 || signature.length > 0) {
      updateOrderStatus(selectedOrder.id, 'delivered');
    } else {
      alert('Please enter OTP or take signature.');
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'accepted': return 'bg-blue-100 text-blue-800';
      case 'picked_up': return 'bg-yellow-100 text-yellow-800';
      case 'out_for_delivery': return 'bg-orange-100 text-orange-800';
      case 'delivered': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status) => {
    switch (status?.toLowerCase()) {
      case 'accepted': return 'Accepted';
      case 'picked_up': return 'Picked Up';
      case 'out_for_delivery': return 'Out for Delivery';
      case 'delivered': return 'Delivered';
      case 'cancelled': return 'Cancelled';
      default: return 'Unknown Status';
    }
  };

  const getPaymentText = (paymentType) => {
    return paymentType?.toLowerCase() === 'cod' ? 'COD (Cash on Delivery)' : 'Prepaid (Already Paid)';
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return 'Not Available';
    return new Date(timestamp).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const openMaps = (address) => {
    const encodedAddress = encodeURIComponent(address);
    window.open(`https://www.google.com/maps/search/?api=1&query=${encodedAddress}`, '_blank');
  };

  if (loading && orders.length === 0) {
    return (
      <div className="min-h-screen bg-[#F4E7D0] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#3E2F2A] mx-auto mb-4"></div>
          <p className="text-xl text-[#3E2F2A]">Loading your orders...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F4E7D0]">
      {/* Header */}
      <header className="bg-[#3E2F2A] text-white py-4 px-6 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link 
              to="/delivery/dashboard" 
              className="text-yellow-400 hover:text-yellow-300 transition-colors"
            >
              ← Back
            </Link>
            <div>
              <h1 className="text-xl font-bold">Pickup and Delivery List</h1>
              <p className="text-yellow-400 text-sm">Order Management</p>
            </div>
          </div>
          
          {/* Mobile menu button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden text-white hover:text-yellow-400"
          >
            ☰
          </button>

          {/* Desktop menu */}
          <nav className="hidden md:flex space-x-6">
            <Link to="/delivery/dashboard" className="hover:text-yellow-400 transition-colors">
              Dashboard
            </Link>
            
           
            <button onClick={logout} className="hover:text-yellow-400 transition-colors">
              Logout
            </button>
          </nav>
        </div>

        {/* Mobile menu */}
        {isMobileMenuOpen && (
          <nav className="md:hidden mt-4 space-y-2">
            <Link to="/delivery/dashboard" className="block py-2 hover:text-yellow-400 transition-colors">
              Dashboard
            </Link>
           
            <Link to="/delivery/map" className="block py-2 hover:text-yellow-400 transition-colors">
              Map/Navigation
            </Link>
            <button onClick={logout} className="block py-2 hover:text-yellow-400 transition-colors w-full text-left">
              Logout
            </button>
          </nav>
        )}
      </header>

      <div className="p-6">
        {/* Filter Tabs */}
        <div className="bg-white rounded-lg shadow-md mb-6 overflow-hidden">
          <div className="flex flex-wrap">
            <button
              onClick={() => setFilter('active')}
              disabled={loading}
              className={`px-6 py-3 font-medium transition-colors disabled:opacity-50 ${
                filter === 'active' 
                  ? 'bg-[#3E2F2A] text-white' 
                  : 'bg-white text-[#3E2F2A] hover:bg-gray-50'
              }`}
            >
              Active Orders ({filteredOrders.filter(o => ['accepted', 'picked_up', 'out_for_delivery'].includes(o.status)).length})
            </button>
            <button
              onClick={() => setFilter('completed')}
              disabled={loading}
              className={`px-6 py-3 font-medium transition-colors disabled:opacity-50 ${
                filter === 'completed' 
                  ? 'bg-[#3E2F2A] text-white' 
                  : 'bg-white text-[#3E2F2A] hover:bg-gray-50'
              }`}
            >
              Completed Orders ({filteredOrders.filter(o => o.status === 'delivered').length})
            </button>
            <button
              onClick={() => setFilter('all')}
              disabled={loading}
              className={`px-6 py-3 font-medium transition-colors disabled:opacity-50 ${
                filter === 'all' 
                  ? 'bg-[#3E2F2A] text-white' 
                  : 'bg-white text-[#3E2F2A] hover:bg-gray-50'
              }`}
            >
              All Orders ({orders.length})
            </button>
          </div>
        </div>

        {/* Orders List */}
        {filteredOrders.length > 0 ? (
          <div className="space-y-6">
            {filteredOrders.slice(0, 10).map((order) => (
              <div key={order.id} className="bg-white rounded-lg shadow-md overflow-hidden">
                {/* Order Header */}
                <div className="bg-gray-50 px-6 py-4 border-b">
                  <div className="flex flex-col md:flex-row md:items-center justify-between space-y-2 md:space-y-0">
                    <div className="flex items-center space-x-4">
                      <h3 className="text-lg font-bold text-[#3E2F2A]">
                        Order ID: {order.id}
                      </h3>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(order.status)}`}>
                        {getStatusText(order.status)}
                      </span>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <span>Distance: {order.distance}</span>
                      <span>Amount: ₹{order.amount}</span>
                    </div>
                  </div>
                </div>

                <div className="p-6">
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Customer Info */}
                    <div className="bg-blue-50 rounded-lg p-4">
                      <h4 className="font-semibold text-[#3E2F2A] mb-3 flex items-center">
                        <span className="mr-2">👤</span>
                        Customer Information
                      </h4>
                      <div className="space-y-2 text-sm">
                        <p><strong>Name:</strong> {order.customer_name}</p>
                        <p><strong>Phone:</strong> 
                          <a 
                            href={`tel:${order.customer_phone}`}
                            className="text-blue-600 hover:text-blue-800 ml-2"
                          >
                            {order.customer_phone}
                          </a>
                        </p>
                        <p><strong>Payment:</strong> {getPaymentText(order.payment_type)}</p>
                        {order.payment_type === 'cod' && (
                          <p className="text-orange-600 font-medium">💰 Collect: ₹{order.amount}</p>
                        )}
                      </div>
                    </div>

                    {/* Pickup Info */}
                    <div className="bg-yellow-50 rounded-lg p-4">
                      <h4 className="font-semibold text-[#3E2F2A] mb-3 flex items-center">
                        <span className="mr-2">📦</span>
                        about Pickup Details
                      </h4>
                      <div className="space-y-2 text-sm">
                        <p><strong>place:</strong> {order.pickup_address}</p>
                        <p><strong>condition:</strong> 
                          <span className={`ml-2 px-2 py-1 rounded text-xs ${
                            order.pickup_status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {order.pickup_status === 'completed' ? 'pickup' : 'pending'}
                          </span>
                        </p>
                        {order.pickup_time && (
                          <p><strong><time datetime={order.pickup_time}></time>:</strong> {formatTime(order.pickup_time)}</p>
                        )}
                        <button 
                          onClick={() => openMaps(order.pickup_address)}
                          className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700 transition-colors w-full"
                        >
                          Pickup Navigation
                        </button>
                      </div>
                    </div>

                    {/* Delivery Info */}
                    <div className="bg-green-50 rounded-lg p-4">
                      <h4 className="font-semibold text-[#3E2F2A] mb-3 flex items-center">
                        <span className="mr-2">🏠</span>
                        Delivery Details
                      </h4>
                      <div className="space-y-2 text-sm">
                        <p><strong>Address:</strong> {order.delivery_address}</p>
                        <p><strong>Status:</strong> 
                          <span className={`ml-2 px-2 py-1 rounded text-xs ${
                            order.delivery_status === 'completed' ? 'bg-green-100 text-green-800' : 
                            order.delivery_status === 'out_for_delivery' ? 'bg-orange-100 text-orange-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {order.delivery_status === 'completed' ? 'completed' : 
                             order.delivery_status === 'out_for_delivery' ? 'out for delivery' : 'pending'}
                          </span>
                        </p>
                        {order.delivery_time && (
                          <p><strong>Time:</strong> {formatTime(order.delivery_time)}</p>
                        )}
                        {order.delivery_instructions && (
                          <p><strong>Instructions:</strong> {order.delivery_instructions}</p>
                        )}
                        <button 
                          onClick={() => openMaps(order.delivery_address)}
                          className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 transition-colors w-full"
                        >
                          Delivery Navigation
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Order Items */}
                  <div className="mt-6 bg-gray-50 rounded-lg p-4">
                    <h4 className="font-semibold text-[#3E2F2A] mb-3">Order Items</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {order.items.map((item, index) => (
                        <div key={index} className="flex justify-between items-center text-sm bg-white p-2 rounded">
                          <span>{item.name} x {item.quantity}</span>
                          <span className="font-medium">₹{item.price}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="mt-6 pt-4 border-t">
                    <div className="flex flex-wrap gap-3 justify-center">
                      {order.status === 'accepted' && (
                        <button
                          onClick={() => handleStatusUpdate(order, 'picked_up')}
                          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          📦 Pickup Complete
                        </button>
                      )}
                      
                      {order.status === 'picked_up' && (
                        <button
                          onClick={() => handleStatusUpdate(order, 'out_for_delivery')}
                          className="bg-orange-600 text-white px-6 py-2 rounded-lg hover:bg-orange-700 transition-colors"
                        >
                          🚚 Out for Delivery
                        </button>
                      )}
                      
                      {order.status === 'out_for_delivery' && (
                        <button
                          onClick={() => handleStatusUpdate(order, 'delivered')}
                          className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors"
                        >
                          Delivery Complete
                          <span role="img" aria-label="check mark"> ✅</span>
                        </button>
                      )}

                      <button
                        onClick={() => window.open(`tel:${order.customer_phone}`)}
                        className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
                      >
                        📞 call 
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <div className="text-6xl mb-4">📦</div>
            <h3 className="text-xl font-semibold text-[#3E2F2A] mb-2">No Orders Found</h3>
            <p className="text-gray-600 mb-4">
              {filter === 'active' ? 'You have no active orders yet.' :
               filter === 'completed' ? 'You have no completed orders yet.' :
               'You have no orders yet.'}
            </p>
            <button
              onClick={fetchOrders}
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Refreshing...
                </span>
              ) : (
                'Refresh Orders'
              )}
            </button>
          </div>
        )}
      </div>

      {/* OTP/Signature Modal for Delivery Confirmation */}
      {showOtpModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-[#3E2F2A] mb-4">Delivery Confirmation</h3>
            <p className="text-gray-600 mb-4">
              Order ID: <strong>{selectedOrder?.id}</strong>
            </p>
            <p className="text-gray-600 mb-4">
              plz enter OTP received from customer or get their signature to confirm delivery.:
            </p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  OTP ()
                </label>
                <input
                  type="text"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  placeholder="OTP entered by Customer"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  maxLength="6"
                />
              </div>
              
              <div className="text-center text-gray-500"></div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                 <Digital>Digital Signature</Digital>
                </label>
                <textarea
                  value={signature}
                  onChange={(e) => setSignature(e.target.value)}
                  placeholder="Customer Name or Signature"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows="3"
                />
              </div>
            </div>
            
            <div className="flex space-x-4 mt-6">
              <button
                onClick={() => setShowOtpModal(false)}
                className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400 transition-colors"
              >
               <Reject>Reject</Reject>
              </button>
              <button
                onClick={handleDeliveryConfirm}
                className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
              >
                <Confirm>Confirm</Confirm>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DeliveryOrders;