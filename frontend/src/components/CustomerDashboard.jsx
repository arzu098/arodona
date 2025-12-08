import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { useWishlist } from '../context/WishlistContext';
import ordersService from '../services/ordersService';
import ChatList from './chat/ChatList';
import ChatInterface from './chat/ChatInterface';
import VendorCustomerChatInterface from './chat/VendorCustomerChatInterface';

const CustomerDashboard = () => {
  const { user, logout } = useAuth();
  const { cartItems, getCartCount } = useCart();
  const { wishlistItems } = useWishlist();
  const [activeTab, setActiveTab] = useState('dashboard'); // dashboard, orders, profile, chat
  const [customerData, setCustomerData] = useState({
    totalOrders: 0,
    totalSpent: 0,
    wishlistItems: 0,
    cartItems: 0
  });
  const [recentOrders, setRecentOrders] = useState([]);
  const [favoriteProducts, setFavoriteProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  // Modal state for order details
  const [selectedOrderId, setSelectedOrderId] = useState(null);
  const [selectedOrderDetails, setSelectedOrderDetails] = useState(null);
  const [orderDetailsLoading, setOrderDetailsLoading] = useState(false);
  const [orderDetailsError, setOrderDetailsError] = useState(null);
  const [refreshInterval, setRefreshInterval] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
  const [showChatModal, setShowChatModal] = useState(false);
  const [chatOrderId, setChatOrderId] = useState(null);
  const [chatType, setChatType] = useState('delivery'); // 'delivery' or 'vendor'
  const [chatUnreadCounts, setChatUnreadCounts] = useState({}); // Track unread counts per order
  
  // Handler to open modal and fetch order details
  const handleOrderClick = async (orderId) => {
    setSelectedOrderId(orderId);
    setOrderDetailsLoading(true);
    setOrderDetailsError(null);
    setSelectedOrderDetails(null);
    try {
      const order = await ordersService.getOrderById(orderId);
      setSelectedOrderDetails(order);
    } catch (err) {
      setOrderDetailsError('Failed to fetch order details.');
    } finally {
      setOrderDetailsLoading(false);
    }
  };

  // Handler to close modal
  const handleCloseOrderModal = () => {
    setSelectedOrderId(null);
    setSelectedOrderDetails(null);
    setOrderDetailsError(null);
    setOrderDetailsLoading(false);
  };

  // Handler to open chat
  const handleOpenChat = async (orderId, type = 'delivery') => {
    try {
      // Reset unread count immediately when opening chat
      setChatUnreadCounts(prev => ({
        ...prev,
        [`${orderId}-${type}`]: 0
      }));
      
      setChatOrderId(orderId);
      setChatType(type);
      setShowChatModal(true);
      
      // If we don't have order details yet, fetch them for chat context
      if (!selectedOrderDetails || (selectedOrderDetails.id || selectedOrderDetails._id) !== orderId) {
        const order = await ordersService.getOrderById(orderId);
        setSelectedOrderDetails(order);
      }
    } catch (error) {
      console.error('Error opening chat:', error);
      // Still open chat even if we can't fetch details
      setChatOrderId(orderId);
      setChatType(type);
      setShowChatModal(true);
    }
  };

  // Handler to close chat
  const handleCloseChat = () => {
    setShowChatModal(false);
    setChatOrderId(null);
  };

  // Handle unread count updates from chat components
  const handleUnreadCountChange = (orderId, chatType, count) => {
    setChatUnreadCounts(prev => ({
      ...prev,
      [`${orderId}-${chatType}`]: count
    }));
  };

  // Reset unread count when chat is opened
  const handleOpenChatWithReset = (orderId, type = 'delivery') => {
    // Reset unread count immediately
    setChatUnreadCounts(prev => ({
      ...prev,
      [`${orderId}-${type}`]: 0
    }));
    // Then open the chat
    handleOpenChat(orderId, type);
  };

  useEffect(() => {
    fetchCustomerData();
  }, [cartItems, wishlistItems, activeTab]);

  // Auto-refresh orders every 30 seconds when on orders tab
  useEffect(() => {
    if (activeTab === 'orders' && autoRefreshEnabled) {
      // Start auto-refresh
      const interval = setInterval(() => {
        fetchCustomerData();
        setLastRefresh(new Date());
      }, 30000); // Refresh every 30 seconds
      setRefreshInterval(interval);
      
      return () => {
        if (interval) {
          clearInterval(interval);
        }
      };
    } else {
      // Stop auto-refresh when not on orders tab or disabled
      if (refreshInterval) {
        clearInterval(refreshInterval);
        setRefreshInterval(null);
      }
    }
  }, [activeTab, autoRefreshEnabled]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [refreshInterval]);

  const fetchCustomerData = async () => {
    try {
      // Fetch customer orders using orders service
      const ordersData = await ordersService.getMyOrders({ limit: 50 });
      const orders = ordersData.orders || [];
      
      // For dashboard tab, show only recent 5 orders
      if (activeTab === 'dashboard') {
        setRecentOrders(orders.slice(0, 5));
      } else {
        // For orders tab, show all orders
        setRecentOrders(orders);
      }

      // Calculate total spent
      const totalSpent = orders.reduce((sum, order) => sum + (order.total || 0), 0);
      
      // Use wishlist items from context (already fetched)
      setFavoriteProducts(wishlistItems.slice(0, 4)); // Get 4 favorite products

      setCustomerData({
        totalOrders: orders.length,
        totalSpent: totalSpent,
        wishlistItems: wishlistItems.length,
        cartItems: getCartCount()
      });

    } catch (error) {
      console.error('Error fetching customer data:', error);
      console.error('Error details:', error.response?.data);
      
      // Set default data on error
      setCustomerData({
        totalOrders: 0,
        totalSpent: 0,
        wishlistItems: wishlistItems.length,
        cartItems: getCartCount()
      });
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
  };

  const handleManualRefresh = async () => {
    await fetchCustomerData();
    setLastRefresh(new Date());
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center px-4">
        <div className="text-base sm:text-lg md:text-xl">Loading your dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header/Navbar */}
      <header className="bg-[#3E2F2A] text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-3 sm:py-4">
            {/* Logo and Brand */}
            <Link to="/" className="flex items-center flex-shrink-0">
              <img 
                src="/Images/1000017875-removebg-preview 9.jpg" 
                alt="Soara Logo" 
                className="w-12 h-12 sm:w-14 sm:h-14 md:w-16 md:h-16 object-contain"
              />
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-4 lg:gap-6">
              <Link to="/" className="hover:text-yellow-400 transition-colors text-xs lg:text-sm font-medium">HOME</Link>
              <Link to="/rings" className="hover:text-yellow-400 transition-colors text-xs lg:text-sm font-medium">RINGS</Link>
              <Link to="/earrings" className="hover:text-yellow-400 transition-colors text-xs lg:text-sm font-medium">EARRINGS</Link>
              <Link to="/bracelets" className="hover:text-yellow-400 transition-colors text-xs lg:text-sm font-medium">BRACELETS</Link>
              <Link to="/pendents" className="hover:text-yellow-400 transition-colors text-xs lg:text-sm font-medium">PENDENTS</Link>
              <Link to="/necklaces" className="hover:text-yellow-400 transition-colors text-xs lg:text-sm font-medium">NECKLACES</Link>
            </nav>

            {/* Right Side Icons */}
            <div className="flex items-center gap-3 sm:gap-4 md:gap-5">
              {/* User Info - Desktop Only */}
              <div className="hidden lg:flex items-center gap-2 text-xs">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span className="truncate max-w-[100px]">{user?.first_name}</span>
              </div>

              {/* Wishlist */}
              <Link to="/wishlist" className="hover:text-yellow-400 transition-colors relative hidden sm:block">
                <svg width="20" height="20" className="sm:w-[22px] sm:h-[22px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                </svg>
                {customerData.wishlistItems > 0 && (
                  <span className="absolute -top-2 -right-2 bg-yellow-500 text-[#3E2F2A] text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                    {customerData.wishlistItems}
                  </span>
                )}
              </Link>

              {/* Cart */}
              <Link to="/cart" className="hover:text-yellow-400 transition-colors relative">
                <svg width="20" height="20" className="sm:w-[22px] sm:h-[22px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
                  <line x1="3" y1="6" x2="21" y2="6"></line>
                  <path d="M16 10a4 4 0 0 1-8 0"></path>
                </svg>
                {customerData.cartItems > 0 && (
                  <span className="absolute -top-2 -right-2 bg-yellow-500 text-[#3E2F2A] text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                    {customerData.cartItems}
                  </span>
                )}
              </Link>

              {/* Logout Button - Desktop */}
              <button
                onClick={handleLogout}
                className="hidden sm:block bg-red-600 text-white px-3 sm:px-4 py-1.5 sm:py-2 rounded text-xs sm:text-sm hover:bg-red-700 transition-colors whitespace-nowrap"
              >
                Logout
              </button>

              {/* Mobile Menu Button */}
              <button 
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="md:hidden hover:text-yellow-400 transition-colors"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 6h16M4 12h16M4 18h16"></path>
                </svg>
              </button>
            </div>
          </div>

          {/* Mobile Menu Dropdown */}
          {isMobileMenuOpen && (
            <div className="md:hidden bg-[#2d2219] mt-2 mb-3 py-4 px-4 rounded">
              {/* User Info - Mobile */}
              <div className="flex items-center gap-2 text-sm mb-4 pb-3 border-b border-gray-600">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <div>
                  <p className="font-medium">{user?.first_name}</p>
                  <p className="text-xs text-gray-400">ID: {user?.id?.slice(0, 8)}...</p>
                </div>
              </div>

              <nav className="flex flex-col gap-3 mb-4">
                <Link 
                  to="/" 
                  className="text-white hover:text-yellow-400 transition-colors text-sm font-medium py-2"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  HOME
                </Link>
                <Link 
                  to="/rings" 
                  className="text-white hover:text-yellow-400 transition-colors text-sm font-medium py-2"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  RINGS
                </Link>
                <Link 
                  to="/earrings" 
                  className="text-white hover:text-yellow-400 transition-colors text-sm font-medium py-2"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  EARRINGS
                </Link>
                <Link 
                  to="/bracelets" 
                  className="text-white hover:text-yellow-400 transition-colors text-sm font-medium py-2"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  BRACELETS
                </Link>
                <Link 
                  to="/pendents" 
                  className="text-white hover:text-yellow-400 transition-colors text-sm font-medium py-2"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  PENDENTS
                </Link>
                <Link 
                  to="/necklaces" 
                  className="text-white hover:text-yellow-400 transition-colors text-sm font-medium py-2"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  NECKLACES
                </Link>
              </nav>

              {/* Mobile Wishlist Link */}
              <Link 
                to="/wishlist"
                className="flex items-center gap-2 text-white hover:text-yellow-400 transition-colors text-sm font-medium py-2 border-t border-gray-600 pt-3 sm:hidden"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                </svg>
                WISHLIST ({customerData.wishlistItems})
              </Link>

              {/* Mobile Logout Button */}
              <button
                onClick={() => {
                  handleLogout();
                  setIsMobileMenuOpen(false);
                }}
                className="w-full sm:hidden bg-red-600 text-white px-4 py-2 rounded text-sm hover:bg-red-700 transition-colors mt-3"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </header>

      <div className="max-w-7xl mx-auto py-4 sm:py-6 px-4 sm:px-6 lg:px-8">
        {/* Welcome Message */}
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg shadow-lg p-4 sm:p-6 mb-6 sm:mb-8 text-white">
          <h2 className="text-xl sm:text-2xl font-bold mb-2">Welcome to Soara Jewelry</h2>
          <p className="text-sm sm:text-base text-purple-100 mb-3 sm:mb-0">Discover exquisite jewelry pieces crafted just for you. Explore our latest collections and find your perfect style.</p>
          <Link 
            to="/shop" 
            className="inline-block mt-3 sm:mt-4 bg-white text-purple-600 px-4 sm:px-6 py-2 rounded-lg text-sm sm:text-base font-medium hover:bg-gray-100 transition-colors"
          >
            Shop Now
          </Link>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4 mb-6 sm:mb-8">
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
                    <dd className="text-base sm:text-lg font-medium text-gray-900">{customerData.totalOrders}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Total Spent */}
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
                    <dt className="text-xs sm:text-sm font-medium text-gray-500 truncate">Total Spent</dt>
                    <dd className="text-base sm:text-lg font-medium text-gray-900">₹{customerData.totalSpent?.toLocaleString() || 0}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Wishlist Items */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-3 sm:p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 sm:h-6 sm:w-6 text-pink-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                </div>
                <div className="ml-3 sm:ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-xs sm:text-sm font-medium text-gray-500 truncate">Wishlist Items</dt>
                    <dd className="text-base sm:text-lg font-medium text-gray-900">{customerData.wishlistItems}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Cart Items */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-3 sm:p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 sm:h-6 sm:w-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2.5 2.5M7 13l2.5 2.5" />
                  </svg>
                </div>
                <div className="ml-3 sm:ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-xs sm:text-sm font-medium text-gray-500 truncate">Cart Items</dt>
                    <dd className="text-base sm:text-lg font-medium text-gray-900">{customerData.cartItems}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mb-6 sm:mb-8">
          <h3 className="text-base sm:text-lg font-medium text-gray-900 mb-3 sm:mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 gap-3 sm:gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Link 
              to="/shop" 
              className="bg-blue-50 p-3 sm:p-4 rounded-lg hover:bg-blue-100 transition-colors"
            >
              <div className="flex items-center">
                <svg className="h-5 w-5 sm:h-6 sm:w-6 text-blue-600 mr-2 sm:mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <div className="min-w-0">
                  <h4 className="font-medium text-gray-900 text-sm sm:text-base truncate">Browse Jewelry</h4>
                  <p className="text-xs sm:text-sm text-gray-600 truncate">Explore our collections</p>
                </div>
              </div>
            </Link>

            <button 
              onClick={() => setActiveTab('orders')}
              className="bg-green-50 p-3 sm:p-4 rounded-lg hover:bg-green-100 transition-colors text-left"
            >
              <div className="flex items-center">
                <svg className="h-5 w-5 sm:h-6 sm:w-6 text-green-600 mr-2 sm:mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <div className="min-w-0">
                  <h4 className="font-medium text-gray-900 text-sm sm:text-base truncate">My Orders</h4>
                  <p className="text-xs sm:text-sm text-gray-600 truncate">Track your purchases</p>
                </div>
              </div>
            </button>

            <Link 
              to="/wishlist" 
              className="bg-pink-50 p-3 sm:p-4 rounded-lg hover:bg-pink-100 transition-colors"
            >
              <div className="flex items-center">
                <svg className="h-5 w-5 sm:h-6 sm:w-6 text-pink-600 mr-2 sm:mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
                <div className="min-w-0">
                  <h4 className="font-medium text-gray-900 text-sm sm:text-base truncate">Wishlist</h4>
                  <p className="text-xs sm:text-sm text-gray-600 truncate">View saved items</p>
                </div>
              </div>
            </Link>

            <button 
              onClick={() => setActiveTab('profile')}
              className="bg-purple-50 p-3 sm:p-4 rounded-lg hover:bg-purple-100 transition-colors text-left"
            >
              <div className="flex items-center">
                <svg className="h-5 w-5 sm:h-6 sm:w-6 text-purple-600 mr-2 sm:mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <div className="min-w-0">
                  <h4 className="font-medium text-gray-900 text-sm sm:text-base truncate">Profile</h4>
                  <p className="text-xs sm:text-sm text-gray-600 truncate">Update your information</p>
                </div>
              </div>
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`${
                activeTab === 'dashboard'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('orders')}
              className={`${
                activeTab === 'orders'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              All Orders
            </button>
            <button
              onClick={() => setActiveTab('profile')}
              className={`${
                activeTab === 'profile'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Profile
            </button>
          </nav>
        </div>

        {/* Dashboard Tab Content */}
        {activeTab === 'dashboard' && (
          <>
        {/* Recent Orders */}
        <div className="mb-6 sm:mb-8">
          <div className="flex justify-between items-center mb-3 sm:mb-4">
            <h3 className="text-base sm:text-lg font-medium text-gray-900">Recent Orders</h3>
            {recentOrders.length > 0 && (
              <button 
                onClick={() => setActiveTab('orders')} 
                className="text-blue-600 hover:text-blue-800 text-xs sm:text-sm font-medium"
              >
                View All Orders
              </button>
            )}
          </div>
          
          {recentOrders.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-4 sm:p-6 text-center">
              <svg className="h-10 w-10 sm:h-12 sm:w-12 text-gray-400 mx-auto mb-3 sm:mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
              <h4 className="text-base sm:text-lg font-medium text-gray-900 mb-2">No orders yet</h4>
              <p className="text-sm sm:text-base text-gray-600 mb-3 sm:mb-4">Start shopping to see your orders here!</p>
              <Link 
                to="/" 
                className="inline-block bg-blue-600 text-white px-4 py-2 text-sm rounded hover:bg-blue-700 transition-colors"
              >
                Start Shopping
              </Link>
            </div>
          ) : (
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {recentOrders.map((order, index) => (
                  <li key={order.id || order._id || `order-${index}`}>
                    <button
                      type="button"
                      className="block w-full text-left hover:bg-gray-50 focus:outline-none"
                      onClick={() => handleOrderClick(order.id || order._id)}
                    >
                      <div className="px-3 sm:px-4 py-3 sm:py-4 flex items-center justify-between">
                        <div className="flex items-center min-w-0 flex-1">
                          <div className="flex-shrink-0 h-8 w-8 sm:h-10 sm:w-10">
                            <div className="h-8 w-8 sm:h-10 sm:w-10 rounded-full bg-gray-300 flex items-center justify-center">
                              <svg className="h-4 w-4 sm:h-5 sm:w-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                              </svg>
                            </div>
                          </div>
                          <div className="ml-3 sm:ml-4 min-w-0 flex-1">
                            <div className="text-xs sm:text-sm font-medium text-gray-900 truncate">
                              Order #{order.id?.slice(-8)}
                            </div>
                            <div className="text-xs sm:text-sm text-gray-500">
                              {new Date(order.created_at).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                        <div className="text-right ml-2 flex-shrink-0">
                          <div className="text-xs sm:text-sm font-medium text-gray-900">₹{order.total?.toLocaleString()}</div>
                          <div className={`text-xs sm:text-sm ${
                            order.status === 'delivered' ? 'text-green-600' :
                            order.status === 'shipped' ? 'text-blue-600' :
                            order.status === 'processing' ? 'text-yellow-600' :
                            'text-gray-600'
                          }`}>
                            {order.status?.charAt(0).toUpperCase() + order.status?.slice(1)}
                          </div>
                        </div>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Favorite Products */}
        {favoriteProducts.length > 0 && (
          <div>
            <div className="flex justify-between items-center mb-3 sm:mb-4">
              <h3 className="text-base sm:text-lg font-medium text-gray-900">Your Favorites</h3>
              <Link to="/wishlist" className="text-blue-600 hover:text-blue-800 text-xs sm:text-sm font-medium">
                View All Favorites
              </Link>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:gap-4 md:gap-6 md:grid-cols-3 lg:grid-cols-4">
              {favoriteProducts.map((product, index) => (
                <div key={product.id || product._id || product.product_id || `product-${index}`} className="bg-white rounded-lg shadow overflow-hidden">
                  <div className="aspect-w-1 aspect-h-1 w-full">
                    <img
                      className="w-full h-32 sm:h-40 md:h-48 object-cover"
                      src={product.image || product.product?.images?.[0]?.url || '/placeholder-product.jpg'}
                      alt={product.name || product.product?.name}
                    />
                  </div>
                  <div className="p-3 sm:p-4">
                    <h4 className="text-xs sm:text-sm font-medium text-gray-900 truncate">{product.name || product.product?.name}</h4>
                    <p className="text-xs sm:text-sm text-gray-600 mt-1">₹{(product.price || product.product?.price)?.toLocaleString()}</p>
                    <Link
                      to={`/products/${product.id || product._id || product.product_id}`}
                      className="mt-2 w-full bg-blue-600 text-white text-xs sm:text-sm py-1.5 sm:py-2 px-3 sm:px-4 rounded hover:bg-blue-700 transition-colors block text-center"
                    >
                      View Product
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
          </>
        )}

        {/* All Orders Tab Content */}
        {activeTab === 'orders' && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-medium text-gray-900">All Orders</h3>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">
                    Last updated: {lastRefresh.toLocaleTimeString()}
                  </span>
                  {autoRefreshEnabled && refreshInterval && (
                    <span className="flex items-center gap-1 text-xs text-green-600">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      Auto-refresh ON
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setAutoRefreshEnabled(!autoRefreshEnabled)}
                    className={`px-2 py-1 text-xs rounded transition-colors ${
                      autoRefreshEnabled 
                        ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                    title={autoRefreshEnabled ? 'Disable auto-refresh' : 'Enable auto-refresh'}
                  >
                    {autoRefreshEnabled ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
                  </button>
                  <button
                    onClick={handleManualRefresh}
                    className="flex items-center gap-2 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                    disabled={loading}
                  >
                    <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    {loading ? 'Refreshing...' : 'Refresh'}
                  </button>
                </div>
              </div>
            </div>
            {recentOrders.length === 0 ? (
              <div className="text-center py-12">
                <svg className="h-12 w-12 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
                <h4 className="text-lg font-medium text-gray-900 mb-2">No orders yet</h4>
                <p className="text-gray-600 mb-4">Start shopping to see your orders here!</p>
                <Link 
                  to="/" 
                  className="inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
                >
                  Start Shopping
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {recentOrders.map((order, index) => (
                  <button
                    key={order.id || order._id || `order-${index}`}
                    type="button"
                    className="w-full text-left border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer focus:outline-none"
                    onClick={() => handleOrderClick(order.id || order._id)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="font-medium text-gray-900">Order #{order.id?.slice(-8) || order._id?.slice(-8)}</h4>
                        <p className="text-sm text-gray-500">{new Date(order.created_at).toLocaleDateString()}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-gray-900">₹{order.total?.toLocaleString()}</p>
                        <span className={`inline-block px-2 py-1 text-xs rounded ${
                          order.status === 'delivered' ? 'bg-green-100 text-green-800' :
                          order.status === 'shipped' || order.status === 'picked_up' ? 'bg-blue-100 text-blue-800' :
                          order.status === 'in_transit' || order.status === 'out_for_delivery' ? 'bg-orange-100 text-orange-800' :
                          order.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                          order.status === 'delivery_failed' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {order.status === 'picked_up' ? 'Picked Up' :
                           order.status === 'in_transit' ? 'In Transit' :
                           order.status === 'out_for_delivery' ? 'Out for Delivery' :
                           order.status === 'delivery_failed' ? 'Delivery Failed' :
                           order.status?.charAt(0).toUpperCase() + order.status?.slice(1)}
                        </span>
                      </div>
                    </div>
                    {order.items && order.items.length > 0 && (
                      <div className="mt-2 text-sm text-gray-600">
                        {order.items.length} item{order.items.length > 1 ? 's' : ''}
                      </div>
                    )}
                  </button>
                ))}
                    {/* Order Details Modal/Card */}
                    {selectedOrderId && (
                      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
                        <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-0 relative animate-fadeIn">
                          {/* Header with Chat Icon and Close Button */}
                          <div className="flex justify-between items-center p-4 border-b border-gray-200">
                            <div className="flex items-center gap-3">
                              <h2 className="text-lg font-semibold text-gray-800">ORDER DETAILS</h2>
                            </div>
                            <div className="flex items-center gap-2">
                              {/* Chat with Delivery Boy */}
                              <button
                                onClick={() => handleOpenChat(selectedOrderId, 'delivery')}
                                className="text-purple-500 hover:text-purple-600 transition-colors p-1 relative"
                                title="Chat with Delivery Boy"
                              >
                                <svg 
                                  className="w-5 h-5" 
                                  fill="none" 
                                  stroke="currentColor" 
                                  viewBox="0 0 24 24"
                                >
                                  <path 
                                    strokeLinecap="round" 
                                    strokeLinejoin="round" 
                                    strokeWidth={2} 
                                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a9.863 9.863 0 01-4.906-1.287l-3.094 1.046a.75.75 0 01-.96-.96l1.046-3.093A9.863 9.863 0 014 12c0-4.418 3.582-8 8-8s8 3.582 8 8z" 
                                  />
                                </svg>
                                {/* Unread badge */}
                                {chatUnreadCounts[`${selectedOrderId}-delivery`] > 0 && (
                                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center">
                                    {chatUnreadCounts[`${selectedOrderId}-delivery`]}
                                  </span>
                                )}
                              </button>
                              
                              {/* Chat with Vendor */}
                              <button
                                onClick={() => handleOpenChatWithReset(selectedOrderId, 'vendor')}
                                className="text-blue-500 hover:text-blue-600 transition-colors p-1 flex items-center gap-1 relative"
                                title="Chat with Vendor"
                              >
                                <svg 
                                  className="w-5 h-5" 
                                  fill="none" 
                                  stroke="currentColor" 
                                  viewBox="0 0 24 24"
                                >
                                  <path 
                                    strokeLinecap="round" 
                                    strokeLinejoin="round" 
                                    strokeWidth={2} 
                                    d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a2 2 0 01-2-2v-6a2 2 0 012-2h8z" 
                                  />
                                </svg>
                                <span className="text-xs text-blue-600">Vendor</span>
                                {/* Unread badge */}
                                {chatUnreadCounts[`${selectedOrderId}-vendor`] > 0 && (
                                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center">
                                    {chatUnreadCounts[`${selectedOrderId}-vendor`]}
                                  </span>
                                )}
                              </button>
                              {/* Close Button */}
                              <button
                                className="text-gray-500 hover:text-gray-700 text-xl font-bold"
                                onClick={handleCloseOrderModal}
                                aria-label="Close"
                              >
                                &times;
                              </button>
                            </div>
                          </div>
                          {orderDetailsLoading ? (
                            <div className="py-12 text-center text-lg">Loading order details...</div>
                          ) : orderDetailsError ? (
                            <div className="py-12 text-center text-red-600">{orderDetailsError}</div>
                          ) : selectedOrderDetails ? (
                            <div className="p-5 sm:p-7">
                              <div className="mb-2 text-xs text-gray-500 font-mono">Order ID: #{selectedOrderDetails.order_number || selectedOrderDetails.id?.slice(-8) || selectedOrderDetails._id?.slice(-8)}</div>
                              <h3 className="text-xl font-bold mb-1 text-green-700 flex items-center gap-2">
                                {selectedOrderDetails.status === 'out_for_delivery' ? (
                                  <>
                                    Your Order is Out for Delivery! <span role="img" aria-label="truck">🚚</span>
                                  </>
                                ) : selectedOrderDetails.status === 'delivered' ? (
                                  <>
                                    Your Order is Delivered! <span role="img" aria-label="check">✅</span>
                                  </>
                                ) : selectedOrderDetails.status === 'shipped' ? (
                                  <>Your Order is Shipped!</>
                                ) : selectedOrderDetails.status === 'picked_up' ? (
                                  <>
                                    Your Order has been Picked Up! <span role="img" aria-label="package">📦</span>
                                  </>
                                ) : selectedOrderDetails.status === 'in_transit' ? (
                                  <>
                                    Your Order is In Transit! <span role="img" aria-label="truck">🚛</span>
                                  </>
                                ) : selectedOrderDetails.status === 'delivery_failed' ? (
                                  <>
                                    Delivery Failed - Will Retry <span role="img" aria-label="warning">⚠️</span>
                                  </>
                                ) : selectedOrderDetails.status === 'processing' ? (
                                  <>Your Order is Processing...</>
                                ) : (
                                  <>Order Status: {selectedOrderDetails.status?.toUpperCase()}</>
                                )}
                              </h3>
                              <div className="text-sm text-gray-700 mb-4">
                                Expected Delivery: {selectedOrderDetails.expected_delivery ? new Date(selectedOrderDetails.expected_delivery).toLocaleString() : 'N/A'}
                              </div>
                              {/* Stepper UI */}
                              <div className="flex items-center justify-between mb-6">
                                {['Order Confirmed', 'Shipped/Picked Up', 'In Transit', 'Delivered'].map((step, idx) => {
                                  const statusMap = ['processing', 'shipped', 'in_transit', 'delivered'];
                                  // Handle alternate statuses
                                  let currentIdx = statusMap.indexOf(selectedOrderDetails.status);
                                  if (currentIdx === -1) {
                                    // Map delivery boy statuses to stepper steps
                                    if (selectedOrderDetails.status === 'picked_up') currentIdx = 1;
                                    if (selectedOrderDetails.status === 'out_for_delivery') currentIdx = 2;
                                    if (selectedOrderDetails.status === 'delivery_failed') currentIdx = 2;
                                  }
                                  const isCompleted = idx <= currentIdx;
                                  return (
                                    <React.Fragment key={step}>
                                      <div className="flex flex-col items-center">
                                        <div className={`rounded-full w-7 h-7 flex items-center justify-center border-2 ${isCompleted ? 'bg-green-500 border-green-500 text-white' : 'bg-white border-gray-300 text-gray-400'}`}>
                                          {isCompleted ? <span>&#10003;</span> : <span className="w-2 h-2 bg-gray-300 rounded-full block"></span>}
                                        </div>
                                        <div className={`text-xs mt-1 ${isCompleted ? 'text-green-700 font-semibold' : 'text-gray-400'}`}>{step}</div>
                                      </div>
                                      {idx < 3 && (
                                        <div className={`flex-1 h-1 ${idx < currentIdx ? 'bg-green-500' : 'bg-gray-200'}`}></div>
                                      )}
                                    </React.Fragment>
                                  );
                                })}
                              </div>
                              {/* Status in progress */}
                              <div className="flex items-center gap-2 mb-4">
                                <span className="inline-block text-green-600">
                                  <svg width="22" height="22" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#22c55e" strokeWidth="2"/><path d="M9 12l2 2 4-4" stroke="#22c55e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                                </span>
                                <span className="text-base font-medium">
                                  {selectedOrderDetails.status === 'out_for_delivery' ? 'Out for Delivery (In Progress)' :
                                   selectedOrderDetails.status === 'picked_up' ? 'Picked Up by Delivery Partner' :
                                   selectedOrderDetails.status === 'in_transit' ? 'In Transit to Your Location' :
                                   selectedOrderDetails.status === 'delivery_failed' ? 'Delivery Failed - Will Retry Soon' :
                                   selectedOrderDetails.status?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                </span>
                              </div>
                              {/* Delivery Partner Info */}
                              <div className="bg-gray-50 rounded-lg p-4 mb-2">
                                <div className="text-sm mb-1"><span className="font-semibold">Delivery Partner:</span> {selectedOrderDetails.delivery_partner || 'YourCo Logistics'}</div>
                                <div className="text-sm mb-1"><span className="font-semibold">Delivery Boy:</span> {selectedOrderDetails.delivery_boy_name || 'N/A'}</div>
                                <div className="flex gap-2 mt-2">
                                  {selectedOrderDetails.delivery_boy_phone && (
                                    <a href={`tel:${selectedOrderDetails.delivery_boy_phone}`} className="flex-1 bg-blue-100 text-blue-700 px-3 py-2 rounded flex items-center justify-center gap-2 font-medium hover:bg-blue-200">
                                      <svg width="18" height="18" fill="none" viewBox="0 0 24 24"><path d="M22 16.92v3a2 2 0 0 1-2.18 2A19.72 19.72 0 0 1 3.09 5.18 2 2 0 0 1 5 3h3a2 2 0 0 1 2 1.72c.13.96.37 1.89.72 2.78a2 2 0 0 1-.45 2.11l-1.27 1.27a16 16 0 0 0 6.29 6.29l1.27-1.27a2 2 0 0 1 2.11-.45c.89.35 1.82.59 2.78.72A2 2 0 0 1 22 16.92z" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                                      Call Delivery Boy
                                    </a>
                                  )}
                                  {selectedOrderDetails.delivery_boy_id && (
                                    <button 
                                      onClick={() => handleOpenChatWithReset(selectedOrderDetails.id, 'delivery')}
                                      className="flex-1 bg-green-100 text-green-700 px-2 sm:px-3 py-2 rounded flex items-center justify-center gap-1 sm:gap-2 font-medium hover:bg-green-200 relative text-xs sm:text-sm"
                                    >
                                      <svg width="16" height="16" className="sm:w-[18px] sm:h-[18px]" fill="none" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="#059669" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                                      <span className="hidden sm:inline">Chat with Delivery Boy</span>
                                      <span className="sm:hidden">🚚 Chat</span>
                                      {/* Unread badge */}
                                      {chatUnreadCounts[`${selectedOrderDetails.id}-delivery`] > 0 && (
                                        <span className="absolute -top-1 -right-1 sm:-top-2 sm:-right-2 bg-red-500 text-white text-[8px] sm:text-xs rounded-full h-3 w-3 sm:h-5 sm:w-5 flex items-center justify-center font-bold">
                                          {chatUnreadCounts[`${selectedOrderDetails.id}-delivery`]}
                                        </span>
                                      )}
                                    </button>
                                  )}
                                  
                                  {/* Chat with Vendor Button */}
                                  <button 
                                    onClick={() => handleOpenChatWithReset(selectedOrderDetails.id, 'vendor')}
                                    className="flex-1 bg-blue-100 text-blue-700 px-2 sm:px-3 py-2 rounded flex items-center justify-center gap-1 sm:gap-2 font-medium hover:bg-blue-200 relative text-xs sm:text-sm"
                                  >
                                    <svg width="16" height="16" className="sm:w-[18px] sm:h-[18px]" fill="none" viewBox="0 0 24 24"><path d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a2 2 0 01-2-2v-6a2 2 0 012-2h8z" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                                    <span className="hidden sm:inline">Chat with Vendor</span>
                                    <span className="sm:hidden">🏪 Chat</span>
                                    {/* Unread badge */}
                                    {chatUnreadCounts[`${selectedOrderDetails.id}-vendor`] > 0 && (
                                      <span className="absolute -top-1 -right-1 sm:-top-2 sm:-right-2 bg-red-500 text-white text-[8px] sm:text-xs rounded-full h-3 w-3 sm:h-5 sm:w-5 flex items-center justify-center font-bold">
                                        {chatUnreadCounts[`${selectedOrderDetails.id}-vendor`]}
                                      </span>
                                    )}
                                  </button>
                                  {/* <button className="flex-1 bg-blue-600 text-white px-3 py-2 rounded font-medium hover:bg-blue-700 flex items-center justify-center gap-2">
                                    <svg width="18" height="18" fill="none" viewBox="0 0 24 24"><path d="M21 21l-6-6m2-5a7 7 0 1 0-14 0 7 7 0 0 0 14 0z" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                                    View Tracking Map
                                  </button> */}
                                </div>
                              </div>
                              {/* Order Items and Address */}
                              <div className="mb-2 mt-4">
                                <span className="font-medium">Total:</span> ₹{selectedOrderDetails.total?.toLocaleString()}
                              </div>
                              <div className="mb-2">
                                <span className="font-medium">Delivery Address:</span> {selectedOrderDetails.address || selectedOrderDetails.delivery_address || 'N/A'}
                              </div>
                              <div className="mb-2">
                                <span className="font-medium">Payment Method:</span> {selectedOrderDetails.payment_method || 'N/A'}
                              </div>
                              <div className="mb-2">
                                <span className="font-medium">Items:</span>
                                <ul className="list-disc ml-5 mt-1">
                                  {selectedOrderDetails.items?.map((item, idx) => (
                                    <li key={idx}>
                                      {item.name} x{item.quantity} - ₹{item.price?.toLocaleString()}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                              <button
                                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 w-full"
                                onClick={() => handleOrderClick(selectedOrderId)}
                                disabled={orderDetailsLoading}
                              >
                                Refresh Status
                              </button>
                            </div>
                          ) : null}
                        </div>
                      </div>
                    )}
              </div>
            )}
          </div>
        )}

        {/* Profile Tab Content */}
        {activeTab === 'profile' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-medium text-gray-900 mb-6">Profile Information</h3>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                  <input 
                    type="text" 
                    value={user?.first_name || ''} 
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                  <input 
                    type="text" 
                    value={user?.last_name || ''} 
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input 
                  type="email" 
                  value={user?.email || ''} 
                  readOnly
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input 
                  type="text" 
                  value={user?.phone || 'Not provided'} 
                  readOnly
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Account Type</label>
                <input 
                  type="text" 
                  value={user?.role?.charAt(0).toUpperCase() + user?.role?.slice(1) || 'Customer'} 
                  readOnly
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                />
              </div>
              <div className="pt-4 border-t border-gray-200">
                <h4 className="text-lg font-medium text-gray-900 mb-4">Account Statistics</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-600">Total Orders</p>
                    <p className="text-2xl font-bold text-blue-600">{customerData.totalOrders}</p>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-600">Total Spent</p>
                    <p className="text-2xl font-bold text-green-600">₹{customerData.totalSpent.toLocaleString()}</p>
                  </div>
                  <div className="bg-pink-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-600">Wishlist Items</p>
                    <p className="text-2xl font-bold text-pink-600">{customerData.wishlistItems}</p>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-600">Cart Items</p>
                    <p className="text-2xl font-bold text-purple-600">{customerData.cartItems}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Chat Modal */}
        {showChatModal && chatOrderId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white rounded-lg shadow-lg w-full max-w-2xl h-5/6 flex flex-col">
              <div className="flex items-center justify-between p-4 border-b">
                <h3 className="text-lg font-medium text-gray-900">
                  Chat with {chatType === 'vendor' ? 'Vendor' : 'Delivery Boy'} - Order #{(selectedOrderDetails?.order_number || selectedOrderDetails?.id?.slice(-8) || chatOrderId?.slice(-8))}
                </h3>
                <button
                  onClick={handleCloseChat}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="flex-1 overflow-hidden">
                {chatType === 'vendor' ? (
                  <VendorCustomerChatInterface 
                    orderId={chatOrderId}
                    recipientId={selectedOrderDetails?.vendor_id || selectedOrderDetails?.seller_id}
                    recipientName={selectedOrderDetails?.vendor_name || selectedOrderDetails?.seller_name || 'Vendor'}
                    onClose={handleCloseChat}
                    onUnreadCountChange={(count) => handleUnreadCountChange(chatOrderId, 'vendor', count)}
                  />
                ) : (
                  <ChatInterface 
                    orderId={chatOrderId}
                    recipientId={selectedOrderDetails?.delivery_boy_id}
                    recipientName={selectedOrderDetails?.delivery_boy_name || 'Delivery Boy'}
                    onUnreadCountChange={(count) => handleUnreadCountChange(chatOrderId, 'delivery', count)}
                  />
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CustomerDashboard;
