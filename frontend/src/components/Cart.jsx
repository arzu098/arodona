import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useWishlist } from '../context/WishlistContext';
import { useAuth } from '../context/AuthContext';
import Search from './Search';
function Cart() {
  const { cartItems, removeFromCart, updateQuantity, getCartTotal, getCartCount } = useCart();
  const { wishlistItems, addToWishlist } = useWishlist();
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [discountCode, setDiscountCode] = useState('');
  const [appliedDiscount, setAppliedDiscount] = useState(0);
  const [selectAll, setSelectAll] = useState(true);
  const [selectedItems, setSelectedItems] = useState(
    cartItems.reduce((acc, item) => ({ ...acc, [item.cartId]: true }), {})
  );
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const subtotal = cartItems
    .filter(item => selectedItems[item.cartId])
    .reduce((total, item) => {
      const price = typeof item.price === 'string' 
        ? parseFloat(item.price.replace(/[₹$,\s]/g, ''))
        : item.price;
      return total + (price * item.quantity);
    }, 0);
  const taxes = subtotal * 0.07; // 7% tax
  const deliveryFee = subtotal > 0 ? (subtotal > 5000 ? 0 : 50) : 0;
  const discount = (subtotal * appliedDiscount) / 100;
  const grandTotal = subtotal + taxes + deliveryFee - discount;
  const handleApplyDiscount = () => {
    if (discountCode === 'OFFER50') {
      setAppliedDiscount(50);
    } else if (discountCode === 'OFFER30') {
      setAppliedDiscount(30);
    } else if (discountCode === 'OFFER20') {
      setAppliedDiscount(20);
    } else {
      alert('Invalid discount code');
    }
  };
  const handleSelectAll = () => {
    const newValue = !selectAll;
    setSelectAll(newValue);
    const newSelected = {};
    cartItems.forEach(item => {
      newSelected[item.cartId] = newValue;
    });
    setSelectedItems(newSelected);
  };
  const handleSelectItem = (cartId) => {
    setSelectedItems(prev => ({
      ...prev,
      [cartId]: !prev[cartId]
    }));
  };

  const handleDeleteSelected = () => {
    cartItems.forEach(item => {
      if (selectedItems[item.cartId]) {
        removeFromCart(item.cartId);
      }
    });
    // Reset selection after deletion
    setSelectAll(false);
    setSelectedItems({});
  };

  const handleMoveToWishlist = async () => {
    // Get selected items
    const itemsToMove = cartItems.filter(item => selectedItems[item.cartId]);
    
    if (itemsToMove.length === 0) {
      alert('Please select items to move to wishlist');
      return;
    }

    // Add each selected item to wishlist and remove from cart
    for (const item of itemsToMove) {
      await addToWishlist({
        id: item.id,
        product_id: item.id,
        name: item.name,
        price: item.price,
        originalPrice: item.originalPrice,
        image: item.image,
        _rawPrice: typeof item.price === 'number' ? item.price : parseFloat(item.price.replace(/[₹$,\s]/g, ''))
      });
      removeFromCart(item.cartId);
    }

    // Reset selection after moving
    setSelectAll(false);
    setSelectedItems({});
  };

  const handleUserIconClick = () => {
    if (isAuthenticated && user) {
      switch (user.role) {
        case 'super_admin': navigate('/super-admin/dashboard'); break;
        case 'admin': navigate('/admin/dashboard'); break;
        case 'vendor': navigate('/vendor/dashboard'); break;
        case 'customer': navigate('/customer/dashboard'); break;
        default: navigate('/login');
      }
    } else {
      navigate('/login');
    }
  };

  return (
    <div className="min-h-screen bg-[#F4E7D0]">
      {/* Header */}
      <header className="bg-[#3E2F2A] text-white py-3 sm:py-4 px-4 sm:px-6 lg:px-[5%]">
        <div className="max-w-[1400px] mx-auto">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link to="/" className="flex items-center">
              <img 
                src="/Images/1000017875-removebg-preview 9.jpg" 
                alt="Soara" 
                className="w-14 h-14 sm:w-16 sm:h-16 md:w-20 md:h-20 object-contain" 
              />
            </Link>
            
            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-4 lg:gap-8">
              <Link to="/rings" className="hover:text-yellow-400 transition-colors text-xs lg:text-sm font-medium">RINGS</Link>
              <Link to="/earrings" className="hover:text-yellow-400 transition-colors text-xs lg:text-sm font-medium">EARRINGS</Link>
              <Link to="/bracelets" className="hover:text-yellow-400 transition-colors text-xs lg:text-sm font-medium">BRACELETS</Link>
              <Link to="/pendents" className="hover:text-yellow-400 transition-colors text-xs lg:text-sm font-medium">PENDENTS</Link>
              <Link to="/necklaces" className="hover:text-yellow-400 transition-colors text-xs lg:text-sm font-medium">NECKLACES</Link>
            </nav>

            {/* Icons */}
            <div className="flex items-center gap-3 sm:gap-4 md:gap-6 relative">
              <button 
                onClick={() => setIsSearchOpen(!isSearchOpen)}
                className="hover:text-yellow-400 transition-colors"
              >
                <svg width="18" height="18" className="sm:w-5 sm:h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8"></circle>
                  <path d="m21 21-4.35-4.35"></path>
                </svg>
              </button>
              <Search isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
              
              <Link to="/wishlist" className="hover:text-yellow-400 transition-colors relative">
                <svg width="18" height="18" className="sm:w-5 sm:h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                </svg>
                {wishlistItems.length > 0 && (
                  <span className="absolute -top-2 -right-2 bg-yellow-500 text-[#3E2F2A] text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                    {wishlistItems.length}
                  </span>
                )}
              </Link>
              
              <button 
                onClick={handleUserIconClick}
                className="hover:text-yellow-400 transition-colors bg-transparent border-none cursor-pointer"
                aria-label={isAuthenticated ? "Go to Dashboard" : "Login"}
              >
                <svg width="18" height="18" className="sm:w-5 sm:h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
              </button>
              
              <Link to="/cart" className="hover:text-yellow-400 transition-colors text-yellow-400 relative">
                <svg width="18" height="18" className="sm:w-5 sm:h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="9" cy="21" r="1"></circle>
                  <circle cx="20" cy="21" r="1"></circle>
                  <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
                </svg>
                {getCartCount() > 0 && (
                  <span className="absolute -top-2 -right-2 bg-yellow-500 text-[#3E2F2A] text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                    {getCartCount()}
                  </span>
                )}
              </Link>

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
            <div className="md:hidden bg-[#2d2219] mt-4 py-4 px-4 rounded">
              <nav className="flex flex-col gap-3">
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
            </div>
          )}
        </div>
      </header>

      {/* Cart Content */}
      <div className="px-4 sm:px-6 lg:px-[5%] py-8 sm:py-10 md:py-12">
        <div className="max-w-[1400px] mx-auto">
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-serif text-gray-900 mb-6 sm:mb-8">My Cart</h1>

          {cartItems.length === 0 ? (
            <div className="bg-white rounded-lg p-8 sm:p-12 text-center">
              <svg className="w-16 h-16 sm:w-20 sm:h-20 md:w-24 md:h-24 mx-auto mb-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <h2 className="text-xl sm:text-2xl font-serif text-gray-900 mb-2">Your cart is empty</h2>
              <p className="text-sm sm:text-base text-gray-600 mb-6">Add some beautiful jewelry to your cart!</p>
              <Link to="/" className="inline-block bg-[#3E2F2A] text-white px-6 sm:px-8 py-2.5 sm:py-3 text-sm rounded hover:bg-[#2d2219] transition-colors">
                Continue Shopping
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
              {/* Left - Cart Items */}
              <div className="lg:col-span-2">
                {/* Selection Header */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 gap-3">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={selectAll}
                      onChange={handleSelectAll}
                      className="w-4 h-4 rounded border-gray-400"
                    />
                    <span className="text-xs sm:text-sm font-medium text-gray-900">
                      {cartItems.filter(item => selectedItems[item.cartId]).length}/{cartItems.length} Items Selected
                    </span>
                  </label>

                  <div className="flex items-center gap-3 sm:gap-4">
                    <button 
                      onClick={handleDeleteSelected}
                      className="flex items-center gap-2 text-xs sm:text-sm text-gray-700 hover:text-red-600 transition-colors"
                    >
                      <svg width="14" height="14" className="sm:w-4 sm:h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                      </svg>
                      <span className="hidden sm:inline">Delete</span>
                    </button>
                    <button 
                      onClick={handleMoveToWishlist}
                      className="bg-white border border-gray-300 px-3 sm:px-4 py-1.5 sm:py-2 rounded text-xs sm:text-sm hover:bg-gray-50 transition-colors"
                    >
                      WISHLIST
                    </button>
                  </div>
                </div>

                {/* Cart Items */}
                <div className="space-y-3 sm:space-y-4">
                  {cartItems.map((item, index) => (
                    <div key={item.cartId || item.id || index} className="bg-white rounded-lg p-4 sm:p-6 shadow-sm">
                      <div className="flex gap-3 sm:gap-4">
                        <input 
                          type="checkbox"
                          checked={selectedItems[item.cartId] || false}
                          onChange={() => handleSelectItem(item.cartId)}
                          className="w-4 h-4 rounded border-gray-400 mt-1 flex-shrink-0"
                        />
                        
                        <img 
                          src={item.image} 
                          alt={item.name} 
                          className="w-20 h-20 sm:w-28 sm:h-28 md:w-32 md:h-32 object-contain bg-gray-50 rounded flex-shrink-0"
                        />

                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between mb-2 gap-2">
                            <div className="flex-1 min-w-0">
                              <h3 className="text-sm sm:text-base md:text-lg font-medium text-gray-900 mb-1 line-clamp-2">{item.name}</h3>
                              {item.originalPrice && (
                                <div className="flex items-center gap-2 sm:gap-4 text-xs sm:text-sm text-gray-600">
                                  <span className="line-through">
                                    {item.originalPrice >= 1000 
                                      ? `₹${item.originalPrice.toLocaleString('en-IN')}` 
                                      : `$${item.originalPrice.toFixed(2)}`}
                                  </span>
                                </div>
                              )}
                              <p className="text-xs sm:text-sm text-gray-600 mt-1">Color: {item.selectedColor || 'Silver'}</p>
                            </div>
                            <button 
                              onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                removeFromCart(item.cartId);
                              }}
                              className="text-gray-400 hover:text-red-600 transition-colors text-xl flex-shrink-0"
                              title="Remove item"
                            >
                              ✕
                            </button>
                          </div>

                          <div className="text-lg sm:text-xl font-bold text-gray-900 mb-3">
                            {typeof item.price === 'string' 
                              ? item.price 
                              : item.price 
                                ? (item.price >= 1000 
                                  ? `₹${item.price.toLocaleString('en-IN')}` 
                                  : `$${item.price.toFixed(2)}`)
                                : 'N/A'}
                          </div>

                          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                            <div className="flex items-center gap-2">
                              <svg width="14" height="14" className="sm:w-4 sm:h-4 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                <line x1="12" y1="8" x2="12" y2="16"></line>
                                <line x1="8" y1="12" x2="16" y2="12"></line>
                              </svg>
                              <span className="text-xs sm:text-sm text-gray-700">15 Days</span>
                              <span className="text-[10px] sm:text-xs text-gray-500">return available</span>
                            </div>

                            <div className="flex items-center gap-2 sm:gap-3">
                              <span className="text-xs sm:text-sm text-gray-700">Qty:</span>
                              <div className="flex items-center border border-gray-300 rounded">
                                <button 
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    if (item.quantity > 1) {
                                      updateQuantity(item.cartId, item.quantity - 1);
                                    }
                                  }}
                                  disabled={item.quantity <= 1}
                                  className="px-2 sm:px-3 py-1 hover:bg-gray-100 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                                  title="Decrease quantity"
                                >
                                  −
                                </button>
                                <span className="px-3 sm:px-4 py-1 border-x border-gray-300 text-sm min-w-[40px] text-center">{item.quantity || 1}</span>
                                <button 
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    updateQuantity(item.cartId, item.quantity + 1);
                                  }}
                                  className="px-2 sm:px-3 py-1 hover:bg-gray-100 transition-colors text-sm"
                                  title="Increase quantity"
                                >
                                  +
                                </button>
                              </div>
                            </div>
                          </div>

                          <div className="mt-3 flex items-center gap-2 text-xs sm:text-sm text-gray-600">
                            <svg width="14" height="14" className="sm:w-4 sm:h-4 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <rect x="1" y="3" width="15" height="13"></rect>
                              <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"></polygon>
                              <circle cx="5.5" cy="18.5" r="2.5"></circle>
                              <circle cx="18.5" cy="18.5" r="2.5"></circle>
                            </svg>
                            <span>Delivered by <strong className="whitespace-nowrap">Feb 25, 2025</strong></span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Right - Order Summary */}
              <div>
                <div className="bg-white rounded-lg p-4 sm:p-6 shadow-sm lg:sticky lg:top-4">
                  <h2 className="text-base sm:text-lg font-semibold text-gray-900 mb-4">Order Summary</h2>
                  
                  <div className="space-y-3 sm:space-y-4 mb-6">
                    <div className="flex justify-between text-sm sm:text-base text-gray-700">
                      <span>Subtotal</span>
                      <span className="font-medium">
                        {subtotal >= 1000 
                          ? `₹${subtotal.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` 
                          : `$${subtotal.toFixed(2)}`}
                      </span>
                    </div>

                    {/* Discount Code */}
                    <div className="border-t pt-4">
                      <label className="block text-xs sm:text-sm text-gray-700 mb-2">Enter Discount Code</label>
                      <div className="flex gap-2">
                        <input 
                          type="text" 
                          value={discountCode}
                          onChange={(e) => setDiscountCode(e.target.value.toUpperCase())}
                          placeholder="OFFER50"
                          className="flex-1 border border-gray-300 rounded px-3 py-2 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-[#3E2F2A]"
                        />
                        <button 
                          onClick={handleApplyDiscount}
                          className="bg-[#3E2F2A] text-white px-3 sm:px-4 py-2 rounded text-xs sm:text-sm hover:bg-[#2d2219] transition-colors whitespace-nowrap"
                        >
                          APPLY
                        </button>
                      </div>
                    </div>

                    <div className="flex justify-between text-sm sm:text-base text-gray-700">
                      <span>Taxes</span>
                      <span className="font-medium">
                        {taxes >= 1000 
                          ? `₹${taxes.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` 
                          : `$${taxes.toFixed(2)}`}
                      </span>
                    </div>

                    <div className="flex justify-between text-sm sm:text-base text-gray-700">
                      <span>Delivery Fee</span>
                      <span className="font-medium text-green-600">
                        {deliveryFee === 0 ? 'FREE' : `$${deliveryFee.toFixed(2)}`}
                      </span>
                    </div>
                  </div>

                  <div className="border-t pt-4 mb-6">
                    <div className="flex justify-between text-base sm:text-lg font-bold text-gray-900">
                      <span>Grand Total</span>
                      <span>
                        {grandTotal >= 1000 
                          ? `₹${grandTotal.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` 
                          : `$${grandTotal.toFixed(2)}`}
                      </span>
                    </div>
                  </div>

                  <Link 
                    to="/checkout"
                    className="block w-full bg-[#3E2F2A] text-white py-2.5 sm:py-3 rounded text-sm sm:text-base font-medium hover:bg-[#2d2219] transition-colors text-center"
                  >
                    CHECKOUT
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12 sm:mt-16">
        <div className="px-4 sm:px-6 lg:px-[5%] py-6 sm:py-8">
          <div className="max-w-[1400px] mx-auto">
            <div className="flex flex-col md:flex-row items-center justify-center md:justify-between gap-6 md:gap-8">
              <nav className="flex flex-wrap items-center justify-center gap-4 sm:gap-6 md:gap-8 order-2 md:order-1">
                <Link to="/rings" className="text-xs sm:text-sm text-gray-700 hover:text-gray-900 transition-colors">RINGS</Link>
                <Link to="/bracelets" className="text-xs sm:text-sm text-gray-700 hover:text-gray-900 transition-colors">BRACELETS</Link>
                <Link to="/about" className="text-xs sm:text-sm text-gray-700 hover:text-gray-900 transition-colors">ABOUT US</Link>
                <Link to="/contact" className="text-xs sm:text-sm text-gray-700 hover:text-gray-900 transition-colors">CONTACT US</Link>
              </nav>

              <img 
                src="/Images/1000017875-removebg-preview 9.jpg" 
                alt="Soara" 
                className="h-10 sm:h-12 md:h-14 object-contain order-1 md:order-2" 
              />

              <nav className="flex flex-wrap items-center justify-center gap-4 sm:gap-6 md:gap-8 order-3">
                <Link to="/terms" className="text-xs sm:text-sm text-gray-700 hover:text-gray-900 transition-colors">TERMS & CONDITIONS</Link>
                <Link to="/privacy" className="text-xs sm:text-sm text-gray-700 hover:text-gray-900 transition-colors">PRIVACY POLICY</Link>
              </nav>
            </div>
          </div>
        </div>

        <div className="bg-[#3E2F2A] text-white py-4 px-4 sm:px-6 lg:px-[5%]">
          <div className="max-w-[1400px] mx-auto">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <p className="text-xs sm:text-sm text-center sm:text-left">Copyright © 2025 Soara. All Rights Reserved.</p>
              <div className="flex items-center gap-2">
                <div className="w-8 h-5 sm:w-10 sm:h-6 bg-[#EB001B] rounded flex items-center justify-center text-white text-[10px] font-bold">M</div>
                <div className="w-8 h-5 sm:w-10 sm:h-6 bg-[#1434CB] rounded flex items-center justify-center text-white text-[10px] font-bold">V</div>
                <div className="w-8 h-5 sm:w-10 sm:h-6 bg-[#00579F] rounded flex items-center justify-center text-white text-[10px] font-bold">AE</div>
                <div className="w-8 h-5 sm:w-10 sm:h-6 bg-[#FF5F00] rounded flex items-center justify-center text-white text-[10px] font-bold">DC</div>
                <div className="w-8 h-5 sm:w-10 sm:h-6 bg-[#1A1F71] rounded flex items-center justify-center text-white text-[10px] font-bold">DS</div>
                <div className="w-8 h-5 sm:w-10 sm:h-6 bg-[#EB001B] rounded flex items-center justify-center text-white text-[10px] font-bold">MC</div>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Cart;
