import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useWishlist } from '../context/WishlistContext';
import { useAuth } from '../context/AuthContext';
import productService from '../services/productService';
import { formatProduct } from '../utils/imageUtils';
import Search from './Search';
import Footer from './Footer';

const Necklaces = () => {
  const { addToCart, cartItems, isInCart, getCartCount, getItemQuantity, updateQuantity, removeFromCart } = useCart();
  const { addToWishlist, removeFromWishlist, isInWishlist, wishlistItems } = useWishlist();
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [sortBy, setSortBy] = useState('Popularity');
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [necklaces, setNecklaces] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    const fetchNecklaces = async () => {
      try {
        setIsLoading(true);
        const response = await productService.getProductsByCategory('necklaces', { limit: 50 });
        const products = response.products || response.items || [];
        setNecklaces(products.map(formatProduct));
      } catch (error) {
        console.error('Error fetching necklaces:', error);
        setNecklaces([]);
      } finally {
        setIsLoading(false);
      }
    };
    fetchNecklaces();
  }, []);
  
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
    <div className="min-h-screen bg-[#fceec6]">
      {/* Header */}
      <header className="bg-[#3E2F2A] text-white px-4 sm:px-6 lg:px-[5%] py-4 sm:py-5">
        <div className="max-w-[1400px] mx-auto flex justify-between items-center">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 sm:gap-3 cursor-pointer">
            <img src="/Images/1000017875-removebg-preview 9.jpg" alt="Soara Logo" className="w-14 h-14 sm:w-16 sm:h-16 md:w-20 md:h-20 object-contain" />
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex gap-6 lg:gap-11 uppercase text-[11px] lg:text-[13px] tracking-wider font-light">
            <Link to="/rings" className="hover:text-yellow-500 transition-colors">RINGS</Link>
            <Link to="/earrings" className="hover:text-yellow-500 transition-colors">EARRINGS</Link>
            <Link to="/bracelets" className="hover:text-yellow-500 transition-colors">BRACELETS</Link>
            <Link to="/pendents" className="hover:text-yellow-500 transition-colors">PENDENTS</Link>
            <Link to="/necklaces" className="hover:text-yellow-500 transition-colors border-b-2 border-yellow-500 pb-1">NECKLACES</Link>
          </nav>
          {/* Icons */}
          <div className="flex gap-3 sm:gap-4 lg:gap-5 items-center relative">
            <button 
              onClick={() => setIsSearchOpen(!isSearchOpen)}
              className="hover:text-yellow-500 transition-colors"
            >
              <svg className="w-4 h-4 sm:w-[18px] sm:h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
              </svg>
            </button>
            <Search isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
            <Link to="/wishlist" className="hover:text-yellow-500 transition-colors relative">
              <svg className="w-4 h-4 sm:w-5 sm:h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
              </svg>
              {wishlistItems.length > 0 && (
                <span className="absolute -top-2 -right-2 bg-yellow-500 text-[#3E2F2A] text-[10px] sm:text-xs font-bold rounded-full w-4 h-4 sm:w-5 sm:h-5 flex items-center justify-center">
                  {wishlistItems.length}
                </span>
              )}
            </Link>
            <button 
              onClick={handleUserIconClick}
              className="hover:text-yellow-500 transition-colors hidden sm:block bg-transparent border-none cursor-pointer"
              aria-label={isAuthenticated ? "Go to Dashboard" : "Login"}
            >
              <svg className="w-4 h-4 sm:w-[18px] sm:h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
            </button>
            <Link to="/cart" className="hover:text-yellow-500 transition-colors relative">
              <svg className="w-4 h-4 sm:w-[18px] sm:h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <path d="M16 10a4 4 0 0 1-8 0"></path>
              </svg>
              {getCartCount() > 0 && (
                <span className="absolute -top-2 -right-2 bg-yellow-500 text-[#3E2F2A] text-[10px] sm:text-xs font-bold rounded-full w-4 h-4 sm:w-5 sm:h-5 flex items-center justify-center">
                  {getCartCount()}
                </span>
              )}
            </Link>
            
            {/* Mobile Menu Button */}
            <button 
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden hover:text-yellow-500 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden bg-[#2d2219] mt-4 py-4 px-4 rounded">
            <nav className="flex flex-col gap-3">
              <Link to="/rings" className="text-white hover:text-yellow-500 transition-colors pb-2 uppercase text-sm tracking-wider">RINGS</Link>
              <Link to="/earrings" className="text-white hover:text-yellow-500 transition-colors pb-2 uppercase text-sm tracking-wider">EARRINGS</Link>
              <Link to="/bracelets" className="text-white hover:text-yellow-500 transition-colors pb-2 uppercase text-sm tracking-wider">BRACELETS</Link>
              <Link to="/pendents" className="text-white hover:text-yellow-500 transition-colors pb-2 uppercase text-sm tracking-wider">PENDENTS</Link>
              <Link to="/necklaces" className="text-white hover:text-yellow-500 transition-colors border-b-2 border-yellow-500 pb-2 uppercase text-sm tracking-wider">NECKLACES</Link>
            </nav>
          </div>
        )}
      </header>

      {/* Hero Section */}
      <section className="px-4 sm:px-6 lg:px-[5%] py-8 sm:py-10 lg:py-12 text-center bg-[#fceec6]">
        <div className="max-w-[700px] mx-auto">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-serif font-normal text-gray-900 mb-2 sm:mb-3">Necklaces</h1>
          <p className="text-xs sm:text-sm text-gray-800 leading-relaxed px-4">
            Statement pieces that capture attention — our necklaces are crafted to adorn your neckline with sophistication and charm.
          </p>
        </div>
      </section>
      {/* Filter Section */}
      <section className="px-4 sm:px-6 lg:px-[5%] py-3 sm:py-4 bg-[#fceec6]">
        <div className="max-w-[1400px] mx-auto flex flex-wrap justify-center items-center gap-4 sm:gap-6 lg:gap-8 py-2 sm:py-3">
          <div className="flex items-center gap-2 sm:gap-3">
            <span className="text-[10px] sm:text-xs text-gray-800 uppercase tracking-wider font-medium">SORT BY:</span>
            <select 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-transparent border-none text-[10px] sm:text-xs text-gray-900 font-semibold cursor-pointer outline-none uppercase"
            >
              <option value="Popularity">Popularity</option>
              <option value="Price: Low to High">Price: Low to High</option>
              <option value="Price: High to Low">Price: High to Low</option>
              <option value="Newest">Newest</option>
            </select>
          </div>
          <button className="text-[10px] sm:text-xs text-gray-800 uppercase tracking-wider font-medium hover:text-gray-900 transition-colors">Type</button>
          <button className="text-[10px] sm:text-xs text-gray-800 uppercase tracking-wider font-medium hover:text-gray-900 transition-colors">Gemstone</button>
          <button className="text-[10px] sm:text-xs text-gray-800 uppercase tracking-wider font-medium hover:text-gray-900 transition-colors">Price</button>
        </div>
      </section>
      {/* Products Grid */}
      <section className="px-4 sm:px-6 lg:px-[5%] py-8 sm:py-10 lg:py-12 bg-[#fceec6]">
        <div className="max-w-[1400px] mx-auto grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 sm:gap-5">
          {isLoading ? (
            <div className="col-span-full text-center py-12"><p className="text-gray-600">Loading necklaces...</p></div>
          ) : necklaces.length === 0 ? (
            <div className="col-span-full text-center py-12"><p className="text-gray-600">No necklaces available at the moment</p></div>
          ) : (
            necklaces.map((necklace) => (
            <div key={necklace.id} className="bg-white rounded-sm overflow-hidden hover:shadow-lg transition-all relative group">
              <Link to={`/product/${necklace.id}`} className="block cursor-pointer">
                <div className="w-full h-[280px] flex items-center justify-center bg-white p-8">
                  <img src={necklace.image} alt={necklace.name} className="max-w-full max-h-full object-contain" />
                </div>
                <div className="px-4 py-3 text-center bg-white">
                  <h3 className="text-xs uppercase tracking-wider text-gray-800 mb-1.5 font-medium">{necklace.name}</h3>
                  {necklace.brand && (
                    <p className="text-xs text-gray-500 mb-1">Brand: {necklace.brand}</p>
                  )}
                  <p className="text-sm font-semibold text-gray-900">{necklace.price}</p>
                </div>
              </Link>
              <button 
                onClick={async (e) => {
                  e.stopPropagation();
                  if (isInWishlist(necklace.id)) {
                    await removeFromWishlist(necklace.id);
                  } else {
                    const result = await addToWishlist({ id: necklace.id, name: necklace.name, price: necklace._rawPrice || parseFloat(necklace.price.replace(/[₹$,]/g, '')), image: necklace.image });
                    if (!result.success && result.error?.includes('login')) alert('Please login to add items to wishlist');
                  }
                }}
                className={`absolute top-3 left-3 border w-8 h-8 rounded-sm text-lg cursor-pointer flex items-center justify-center transition-all ${
                  isInWishlist(necklace.id) ? 'bg-red-50 border-red-300 text-red-600 hover:bg-red-100' : 'bg-white border-gray-300 hover:bg-gray-100'
                }`}
              >
                {isInWishlist(necklace.id) ? '♥' : '♡'}
              </button>
              {isInCart(necklace.id) ? (
                <div className="w-full flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white py-2.5 rounded transition-all">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      const item = cartItems.find(i => i.id === necklace.id || i.product_id === necklace.id);
                      if (item && item.quantity > 1) {
                        updateQuantity(item.cartId, item.quantity - 1);
                      } else if (item) {
                        removeFromCart(item.cartId);
                      }
                    }}
                    className="text-xl font-bold hover:scale-110 transition-transform px-2"
                  >
                    −
                  </button>
                  <span className="text-xs font-semibold min-w-[20px] text-center uppercase tracking-wider">
                    {getItemQuantity(necklace.id)}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      const item = cartItems.find(i => i.id === necklace.id || i.product_id === necklace.id);
                      if (item) {
                        updateQuantity(item.cartId, item.quantity + 1);
                      }
                    }}
                    className="text-xl font-bold hover:scale-110 transition-transform px-2"
                  >
                    +
                  </button>
                </div>
              ) : (
                <button 
                  onClick={async (e) => {
                    e.stopPropagation();
                    await addToCart({ id: necklace.id, name: necklace.name, price: necklace._rawPrice || parseFloat(necklace.price.replace(/[₹$,]/g, '')), image: necklace.image, quantity: 1 });
                  }}
                  className="w-full bg-[#3E2F2A] hover:bg-[#2d2219] text-white py-2.5 text-xs uppercase tracking-wider font-medium transition-colors"
                >
                  ADD TO CART
                </button>
              )}
            </div>
          ))
          )}
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Necklaces;
