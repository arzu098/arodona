import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useWishlist } from '../context/WishlistContext';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import Search from './Search';
import Footer from './Footer';
const Wishlist = () => {
  const { wishlistItems, removeFromWishlist, clearWishlist } = useWishlist();
    const { cartItems, addToCart, isInCart, getCartCount } = useCart();
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  // Safely format a price value (handles undefined/null/string)
  const formatPrice = (value) => {
    const n = Number(value);
    if (!Number.isFinite(n)) return '₹0.00';
    return n >= 1000 ? `₹${n.toFixed(2)}` : `$${n.toFixed(2)}`;
  };
  const handleAddToCart = async (item) => {
    // Add to cart
    addToCart({
      id: item.id,
      name: item.name,
      price: item.price,
      originalPrice: item.originalPrice,
      image: item.image,
      quantity: 1
    });
    
    // Remove from wishlist after adding to cart
    await removeFromWishlist(item.id || item.product_id || item._id);
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
                <svg width="20" height="20" className="sm:w-[22px] sm:h-[22px]" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2">
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
              <Link to="/cart" className="hover:text-yellow-400 transition-colors relative">
                <svg width="18" height="18" className="sm:w-5 sm:h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
                  <line x1="3" y1="6" x2="21" y2="6"></line>
                  <path d="M16 10a4 4 0 0 1-8 0"></path>
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

      {/* Wishlist Content */}
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-[5%] py-8 sm:py-10 md:py-12">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 sm:mb-8 gap-3">
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-serif text-gray-900">My Wishlist</h1>
          {wishlistItems.length > 0 && (
            <button 
              onClick={clearWishlist}
              className="text-xs sm:text-sm text-red-600 hover:text-red-700 font-medium underline"
            >
              Clear All
            </button>
          )}
        </div>

        {wishlistItems.length === 0 ? (
          <div className="text-center py-12 sm:py-16 md:py-20 px-4">
            <svg 
              className="mx-auto mb-4 text-gray-400" 
              width="60" 
              height="60"
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="1.5"
            >
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
            </svg>
            <h2 className="text-xl sm:text-2xl md:text-3xl font-serif text-gray-800 mb-2">Your wishlist is empty</h2>
            <p className="text-sm sm:text-base text-gray-600 mb-6">Save your favorite items to your wishlist</p>
            <Link 
              to="/" 
              className="inline-block bg-[#3E2F2A] text-white px-6 sm:px-8 py-2.5 sm:py-3 text-xs sm:text-sm font-medium hover:bg-[#2d2219] transition-colors rounded"
            >
              Continue Shopping
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 xs:grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-5 md:gap-6">
            {wishlistItems.map((item) => {
              // Handle both backend format (item.product) and guest format (flat item)
              const product = item.product || item;
              const productId = product.id || product._id || item.favorite_id;
              const productImage = product.images?.[0]?.url || product.image || '';
              const productName = product.name || 'Unnamed Product';
              const productPrice = product.price || 0;
              const productOriginalPrice = product.originalPrice || product.original_price;
              
              return (
                <div key={productId} className="bg-white rounded-lg overflow-hidden shadow-md hover:shadow-xl transition-all relative group">
                  <Link to={`/product/${productId}`} className="block">
                    <div className="w-full h-[200px] sm:h-[240px] md:h-[280px] flex items-center justify-center bg-white p-4 sm:p-6">
                      <img src={productImage} alt={productName} className="max-w-full max-h-full object-contain" />
                    </div>
                    <div className="px-3 sm:px-4 py-3 sm:py-4 text-center">
                      <h3 className="text-[10px] sm:text-xs uppercase tracking-wider text-gray-800 mb-2 font-medium line-clamp-2">{productName}</h3>
                      <div className="flex justify-center items-center gap-2 mb-3">
                        <span className="text-xs sm:text-sm font-semibold text-gray-900">
                          {formatPrice(productPrice)}
                        </span>
                        {(productOriginalPrice !== undefined && productOriginalPrice !== null) && (
                          <span className="text-xs sm:text-sm text-gray-400 line-through">
                            {formatPrice(productOriginalPrice)}
                          </span>
                        )}
                      </div>
                    </div>
                  </Link>
                  
                  <button
                    onClick={() => removeFromWishlist(productId)}
                    className="absolute top-2 sm:top-3 right-2 sm:right-3 bg-white border border-gray-300 w-7 h-7 sm:w-8 sm:h-8 rounded-sm flex items-center justify-center hover:bg-red-50 hover:border-red-300 hover:text-red-600 transition-all text-lg sm:text-xl"
                    title="Remove from wishlist"
                  >
                    ×
                  </button>

                  <button 
                    onClick={() => handleAddToCart({
                      id: productId,
                      name: productName,
                      price: productPrice,
                      image: productImage
                    })}
                    className="w-full bg-[#3E2F2A] text-white py-2 sm:py-2.5 text-[10px] sm:text-xs uppercase tracking-wider font-medium hover:bg-[#2d2219] transition-colors"
                  >
                    Add to Cart
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <Footer />
    </div>
  );
};

export default Wishlist;
