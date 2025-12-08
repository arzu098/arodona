import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useWishlist } from '../context/WishlistContext';
import { useAuth } from '../context/AuthContext';
import productService from '../services/productService';
import { formatProduct } from '../utils/imageUtils';
import Search from './Search';
import Footer from './Footer';

const Home = () => {
  const { addToCart, cartItems, isInCart, getCartCount, getItemQuantity, updateQuantity, removeFromCart } = useCart();
  const { addToWishlist, removeFromWishlist, isInWishlist, wishlistItems } = useWishlist();
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState('Earrings');
  const [currentPage, setCurrentPage] = useState(0);
  const [slideDirection, setSlideDirection] = useState('');
  const [isAnimating, setIsAnimating] = useState(false);
  const [testimonialPage, setTestimonialPage] = useState(0);
  const [testimonialSlideDirection, setTestimonialSlideDirection] = useState('');
  const [isTestimonialAnimating, setIsTestimonialAnimating] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  // State for products from backend
  const [categoryProducts, setCategoryProducts] = useState({
    Rings: [],
    Earrings: [],
    Necklaces: [],
    Bracelets: [],
  });
  const [bestsellerProducts, setBestsellerProducts] = useState([]);
  const [popularProducts, setPopularProducts] = useState([]);
  const [isLoadingProducts, setIsLoadingProducts] = useState(true);
  
  // Fetch products from backend
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setIsLoadingProducts(true);
        
        // Fetch products for each category with increased limit
        const categories = ['rings', 'earrings', 'necklaces', 'bracelets'];
        const categoryData = {};
        
        for (const category of categories) {
          const response = await productService.getProductsByCategory(category, { limit: 12 });
          const products = response.products || response.items || [];
          
          // Debug: Log first product to see available fields
          if (products.length > 0) {
            console.log(`Sample ${category} product:`, products[0]);
            console.log(`Brand field:`, products[0].brand);
            console.log(`Vendor ID:`, products[0].vendor_id);
          }
          
          // Transform backend products to frontend format
          categoryData[category.charAt(0).toUpperCase() + category.slice(1)] = products.map(formatProduct);
        }
        
        setCategoryProducts(categoryData);
        
        // Fetch featured/bestseller products
        const featuredResponse = await productService.getFeaturedProducts();
        const featured = featuredResponse.products || featuredResponse.items || [];
        setBestsellerProducts(featured.slice(0, 8).map(formatProduct));
        
        // Use same featured products for popular (or fetch differently if needed)
        setPopularProducts(featured.slice(0, 8).map(formatProduct));
        
      } catch (error) {
        console.error('Error fetching products:', error);
        // Fallback to empty arrays on error
        setCategoryProducts({
          Rings: [],
          Earrings: [],
          Necklaces: [],
          Bracelets: [],
        });
        setBestsellerProducts([]);
        setPopularProducts([]);
      } finally {
        setIsLoadingProducts(false);
      }
    };
    
    fetchProducts();
  }, []);
  
  // Handle user icon click - redirect to dashboard if logged in
  const handleUserIconClick = () => {
    if (isAuthenticated && user) {
      // Redirect based on user role
      switch (user.role) {
        case 'super_admin':
          navigate('/super-admin/dashboard');
          break;
        case 'admin':
          navigate('/admin/dashboard');
          break;
        case 'vendor':
          navigate('/vendor/dashboard');
          break;
        case 'customer':
          navigate('/customer/dashboard');
          break;
        default:
          navigate('/login');
      }
    } else {
      navigate('/login');
    }
  };
  
  const categories = [
    { name: 'Rings', image: '/Images/1.png' },
    { name: 'Earrings', image: '/Images/2.png' },
    { name: 'Bracelets', image: '/Images/3.png' },
    { name: 'Pendents', image: '/Images/15.png' },
    { name: 'Necklaces', image: '/Images/4.png' },
  ];

  const allTestimonials = [
    {
      id: 1,
      name: 'Ralph Edwards',
      title: '"Luxury and elegance in every piece!"',
      text: 'The attention to detail in every piece is breathtaking. Truly a work of art.',
      rating: 5,
      image: '👤'
    },
    {
      id: 2,
      name: 'Eleanor Pena',
      title: '"Perfect gift for my loved ones!"',
      text: 'The intricate details and premium finish make every piece a memorable keepsake.',
      rating: 5,
      image: '👤'
    },
    {
      id: 3,
      name: 'Sara Taylor',
      title: '"Outstanding craftsmanship!"',
      text: 'I love your system, totally blown away by the service and attention to detail. Thanks!',
      rating: 5,
      image: '👤'
    },
    {
      id: 4,
      name: 'Jennifer Lewis',
      title: '"Exceptional quality and design!"',
      text: 'Thank you for my loved ones! Great quality products and excellent customer service.',
      rating: 5,
      image: '👤'
    },
    {
      id: 5,
      name: 'Michael Chen',
      title: '"Best jewelry shopping experience!"',
      text: 'From browsing to purchase, everything was seamless. The quality exceeded my expectations.',
      rating: 5,
      image: '👤'
    },
    {
      id: 6,
      name: 'Emily Watson',
      title: '"Timeless pieces worth every penny!"',
      text: 'Each piece tells a story. The craftsmanship and attention to detail are unmatched.',
      rating: 5,
      image: '👤'
    },
    {
      id: 7,
      name: 'David Martinez',
      title: '"Stunning collection and service!"',
      text: 'Beautiful designs that catch everyone\'s eye. The customer service made my experience even better.',
      rating: 5,
      image: '👤'
    },
    {
      id: 8,
      name: 'Sophia Anderson',
      title: '"Absolutely love my new bracelet!"',
      text: 'The quality is fantastic and it arrived beautifully packaged. Will definitely shop here again!',
      rating: 5,
      image: '👤'
    },
    {
      id: 9,
      name: 'James Wilson',
      title: '"Premium jewelry at its finest!"',
      text: 'Purchased an engagement ring and couldn\'t be happier. The sparkle is incredible and my fiancée loves it!',
      rating: 5,
      image: '👤'
    },
    {
      id: 10,
      name: 'Olivia Brown',
      title: '"Elegant and sophisticated designs!"',
      text: 'Every piece I\'ve purchased has been stunning. The quality speaks for itself - highly recommend!',
      rating: 5,
      image: '👤'
    },
    {
      id: 11,
      name: 'Daniel Garcia',
      title: '"Worth every rupee spent!"',
      text: 'Investment in quality jewelry. The pieces are timeless and the craftsmanship is extraordinary.',
      rating: 5,
      image: '👤'
    },
    {
      id: 12,
      name: 'Isabella Rodriguez',
      title: '"My go-to jewelry store!"',
      text: 'From casual pieces to special occasions, they have it all. Always impressed with the selection and quality.',
      rating: 5,
      image: '👤'
    },
  ];

  const getSupport = [
    {
      title: 'Free Shipping',
      description: 'Tell about your service',
      image: '/Images/70.png',
    },
    {
      title: '14 Days Return',
      description: 'within 14 days for an exchange',
      image: '/Images/71.png',
    },
    {
      title: 'Support 24/7',
      description: 'Contact us 24 hours a day',
      image: '/Images/72.png',
    },
    {
      title: 'Flexible Payment',
      description: 'Pay with multiple credit cards',
      image: '/Images/73.png',
    },
  ];

  return (
    <div className="w-full overflow-x-hidden">
      {/* Header */}
      <header className="absolute top-0 left-0 right-0 z-50 bg-transparent">
        <div className="flex justify-between items-center px-4 sm:px-6 lg:px-[5%] py-4 sm:py-6 text-white">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 sm:gap-3 z-50">
            <img src="/Images/1000017875-removebg-preview 9.jpg" alt="Soara Logo" className="w-12 h-12 sm:w-16 sm:h-16 lg:w-20 lg:h-20 object-contain" />
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex gap-6 xl:gap-11 uppercase text-[11px] xl:text-[13px] tracking-wider font-light">
            <Link to="/rings" className="hover:text-yellow-500 transition-colors">RINGS</Link>
            <Link to="/earrings" className="hover:text-yellow-500 transition-colors">EARRINGS</Link>
            <Link to="/bracelets" className="hover:text-yellow-500 transition-colors">BRACELETS</Link>
            <Link to="/pendents" className="hover:text-yellow-500 transition-colors">PENDENTS</Link>
            <Link to="/necklaces" className="hover:text-yellow-500 transition-colors">NECKLACES</Link>
          </nav>

          {/* Tablet Navigation - Shows between md and lg */}
          <nav className="hidden md:flex lg:hidden gap-4 uppercase text-[10px] tracking-wider font-light">
            <Link to="/rings" className="hover:text-yellow-500 transition-colors">RINGS</Link>
            <Link to="/earrings" className="hover:text-yellow-500 transition-colors">EARRINGS</Link>
            <Link to="/bracelets" className="hover:text-yellow-500 transition-colors">BRACELETS</Link>
            <Link to="/pendents" className="hover:text-yellow-500 transition-colors">PENDENTS</Link>
            <Link to="/necklaces" className="hover:text-yellow-500 transition-colors">NECKLACES</Link>
          </nav>

          {/* Desktop & Tablet Icons */}
          <div className="hidden md:flex gap-3 lg:gap-4 xl:gap-6 items-center relative">
            <button 
              onClick={() => setIsSearchOpen(!isSearchOpen)}
              className="bg-transparent border-none text-white/90 cursor-pointer hover:text-yellow-500 transition-colors"
              aria-label="Search"
            >
              <svg width="18" height="18" className="lg:w-5 lg:h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
              </svg>
            </button>
            <Search isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
            <Link to="/wishlist" className="bg-transparent border-none text-white/90 cursor-pointer hover:text-yellow-500 transition-colors relative">
              <svg width="18" height="18" className="lg:w-5 lg:h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
              </svg>
              {wishlistItems.length > 0 && (
                <span className="absolute -top-2 -right-2 bg-yellow-500 text-[#3E2F2A] text-[10px] lg:text-xs font-bold rounded-full w-4 h-4 lg:w-5 lg:h-5 flex items-center justify-center">
                  {wishlistItems.length}
                </span>
              )}
            </Link>
            <button 
              onClick={handleUserIconClick}
              className="bg-transparent border-none text-white/90 cursor-pointer hover:text-yellow-500 transition-colors"
              aria-label={isAuthenticated ? "Go to Dashboard" : "Login"}
            >
              <svg width="18" height="18" className="lg:w-5 lg:h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
            </button>
            <Link to="/cart" className="bg-transparent border-none text-white/90 cursor-pointer hover:text-yellow-500 transition-colors relative">
              <svg width="18" height="18" className="lg:w-5 lg:h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <path d="M16 10a4 4 0 0 1-8 0"></path>
              </svg>
              {getCartCount() > 0 && (
                <span className="absolute -top-2 -right-2 bg-yellow-500 text-[#3E2F2A] text-[10px] lg:text-xs font-bold rounded-full w-4 h-4 lg:w-5 lg:h-5 flex items-center justify-center">
                  {getCartCount()}
                </span>
              )}
            </Link>
          </div>

          {/* Mobile Icons & Hamburger - Only on small screens */}
          <div className="flex md:hidden gap-3 items-center z-50">
            <Link to="/wishlist" className="text-white/90 hover:text-yellow-500 transition-colors relative">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
              </svg>
              {wishlistItems.length > 0 && (
                <span className="absolute -top-1 -right-1 bg-yellow-500 text-[#3E2F2A] text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
                  {wishlistItems.length}
                </span>
              )}
            </Link>
            <Link to="/cart" className="text-white/90 hover:text-yellow-500 transition-colors relative">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <path d="M16 10a4 4 0 0 1-8 0"></path>
              </svg>
              {getCartCount() > 0 && (
                <span className="absolute -top-1 -right-1 bg-yellow-500 text-[#3E2F2A] text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
                  {getCartCount()}
                </span>
              )}
            </Link>
            {/* Hamburger Menu Button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="text-white/90 hover:text-yellow-500 transition-colors p-1"
              aria-label="Toggle menu"
            >
              {isMobileMenuOpen ? (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              ) : (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="3" y1="12" x2="21" y2="12"></line>
                  <line x1="3" y1="6" x2="21" y2="6"></line>
                  <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Mobile Slide-in Menu - Only for small screens */}
        <div 
          className={`fixed top-0 right-0 h-auto max-h-screen w-[280px] bg-[#2A1F1A] shadow-2xl transform transition-transform duration-300 ease-in-out md:hidden overflow-y-auto ${
            isMobileMenuOpen ? 'translate-x-0' : 'translate-x-full'
          }`}
          style={{ zIndex: 100000 }}
        >
          <div className="flex flex-col h-full">
            {/* Close Button */}
            <div className="flex justify-end p-6">
              <button
                onClick={() => setIsMobileMenuOpen(false)}
                className="text-white/90 hover:text-yellow-500 transition-colors"
                aria-label="Close menu"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            {/* Mobile Navigation Links */}
            <nav className="flex flex-col px-6 space-y-6">
              <Link 
                to="/rings" 
                className="text-white uppercase text-sm tracking-wider font-light hover:text-yellow-500 transition-colors py-2 border-b border-white/10"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                RINGS
              </Link>
              <Link 
                to="/earrings" 
                className="text-white uppercase text-sm tracking-wider font-light hover:text-yellow-500 transition-colors py-2 border-b border-white/10"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                EARRINGS
              </Link>
              <Link 
                to="/bracelets" 
                className="text-white uppercase text-sm tracking-wider font-light hover:text-yellow-500 transition-colors py-2 border-b border-white/10"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                BRACELETS
              </Link>
              <Link 
                to="/pendents" 
                className="text-white uppercase text-sm tracking-wider font-light hover:text-yellow-500 transition-colors py-2 border-b border-white/10"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                PENDENTS
              </Link>
              <Link 
                to="/necklaces" 
                className="text-white uppercase text-sm tracking-wider font-light hover:text-yellow-500 transition-colors py-2 border-b border-white/10"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                NECKLACES
              </Link>
            </nav>

            {/* Mobile Actions */}
            <div className="mt-8 px-6 space-y-4">
              <button 
                onClick={() => {
                  setIsSearchOpen(true);
                  setIsMobileMenuOpen(false);
                }}
                className="w-full flex items-center gap-3 text-white hover:text-yellow-500 transition-colors py-3"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8"></circle>
                  <path d="m21 21-4.35-4.35"></path>
                </svg>
                <span className="text-sm uppercase tracking-wider">Search</span>
              </button>
              <button 
                onClick={() => {
                  handleUserIconClick();
                  setIsMobileMenuOpen(false);
                }}
                className="w-full flex items-center gap-3 text-white hover:text-yellow-500 transition-colors py-3"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
                <span className="text-sm uppercase tracking-wider">
                  {isAuthenticated ? 'Dashboard' : 'Login / Sign Up'}
                </span>
              </button>
            </div>
          </div>
        </div>
      </header>
      {/* Hero Section */}
      <section className="relative w-full min-h-screen overflow-hidden" style={{ zIndex: 1 }}>
        {/* Single background image 101.png */}
        <div className="absolute inset-0 w-full h-full">
          <img src="/Images/101.png" alt="Hero Background" className="w-full h-full object-cover object-center" />
        </div>
        <div className="relative max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-[5%] pt-24 sm:pt-28 lg:pt-32 pb-12 sm:pb-16 lg:pb-20 min-h-screen flex flex-col lg:flex-row items-center justify-center gap-8 lg:gap-0">
          {/* LEFT SIDE - Text Content */}
          <div className="flex-1 relative w-full lg:h-[600px] flex items-center justify-center lg:justify-start mb-8 lg:mb-0">
            {/* MAIN TITLE - On LEFT side */}
            <div className="text-white max-w-[700px] text-center lg:text-left px-4 sm:px-0">
              <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-[59px] font-serif font-normal leading-tight sm:leading-snug lg:leading-[1.3] mb-3 sm:mb-4">
                Unveiling the Beauty
                <br />
                of Fine Jewellery
              </h1>
              <p className="text-sm sm:text-base lg:text-xl text-white/95 mb-6 sm:mb-8 leading-relaxed">
                Handpicked gemstones and intricate designs for a lifetime of luxury.
              </p>
              <Link to="/shop" className="bg-transparent border border-white text-white px-6 sm:px-8 py-2.5 sm:py-3 text-sm sm:text-base font-normal cursor-pointer hover:bg-white hover:text-[#8b7562] transition-all inline-flex items-center gap-2 sm:gap-3 tracking-[0.15em] uppercase shadow-lg">
                SHOP NOW
                <span className="text-sm sm:text-base">→</span>
              </Link>
            </div>
          </div>

          {/* New Bracelets Card - Mobile: below text, Desktop: absolute right side */}
          <div className="w-full max-w-[600px] lg:w-[500px] lg:absolute lg:right-[5%] lg:top-1/2 lg:-translate-y-1/2 flex flex-col items-center lg:items-start gap-6">
            <div className="flex flex-col sm:flex-row lg:flex-row items-center gap-6 sm:gap-8 lg:gap-10 relative">
              {/* Circular product card */}
              <div className="relative w-[180px] sm:w-[200px] lg:w-[150px] xl:w-[200px] h-[180px] sm:h-[200px] lg:h-[150px] xl:h-[200px] flex-shrink-0">
                {/* Outer circle with subtle gradient */}
                <div className="w-full h-full rounded-full bg-gradient-to-br from-[#a89584]/15 to-[#c9b8a3]/25 backdrop-blur-sm flex items-center justify-center relative">
                  {/* Small dot indicator at top center */}
                  <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-2 xl:w-2.5 h-2 xl:h-2.5 bg-gray-800 rounded-full"></div>
                  
                  {/* Inner circle - tan/beige color with bracelet */}
                  <div className="w-[160px] sm:w-[180px] lg:w-[135px] xl:w-[180px] h-[160px] sm:h-[180px] lg:h-[135px] xl:h-[180px] rounded-full bg-[#d4c4b0] flex items-center justify-center overflow-hidden shadow-2xl">
                    <img 
                      src="/Images/young-woman-wearing-elegant-pearl-jewelry-grey-background-closeup 2.jpg" 
                      alt="Pearl and Gold Bracelet" 
                      className="w-full h-full object-cover scale-110"
                    />
                  </div>

                  {/* Connecting line - Only visible on large screens */}
                  <div className="hidden lg:block absolute top-1/2 right-0 w-[100px] xl:w-[120px] h-[2px] bg-[#8b7562] transform translate-x-full -translate-y-1/2"></div>
                </div>
              </div>

              {/* Text content */}
              <div className="text-white text-center sm:text-left lg:text-left">
                {/* Title */}
                <div className="mb-4">
                  <h3 className="text-xl sm:text-2xl lg:text-xl xl:text-2xl font-serif font-normal leading-tight mb-2 lg:mb-1">New Bracelets</h3>
                  <div className="w-full max-w-[200px] h-[2px] bg-white mx-auto sm:mx-0"></div>
                </div>

                {/* Description text */}
                <div className="text-white/90 text-sm sm:text-base leading-relaxed max-w-[300px] mx-auto sm:mx-0 lg:text-left lg:max-w-[250px]">
                  <p>
                    Discover handcrafted bracelets that complement your unique charm.
                  </p>
                </div>
              </div>
            </div>

            {/* Navigation arrows */}
            <div className="flex gap-4 sm:gap-6 lg:gap-6 xl:gap-10 items-center justify-center sm:justify-start lg:absolute lg:ml-[550px] xl:lg:ml-[650px] lg:mt-[220px] xl:lg:mt-[260px]">
              <button className="w-10 sm:w-12 h-10 sm:h-12 rounded-full border border-white/25 bg-[#8b7562]/60 backdrop-blur-sm text-white text-base sm:text-lg flex items-center justify-center hover:bg-white/15 hover:border-white/40 transition-all">
                ←
              </button>
              <button className="w-10 sm:w-12 h-10 sm:h-12 rounded-full border border-white/25 bg-white/10 backdrop-blur-sm text-white text-base sm:text-lg flex items-center justify-center hover:bg-white/20 hover:border-white/40 transition-all">
                →
              </button>
            </div>
          </div>
        </div>
      </section>
      {/* Shop by Category */}
      <section className="px-4 sm:px-6 lg:px-[5%] py-12 sm:py-16 lg:py-20 bg-[#fceec6]">
        <div className="max-w-[1400px] mx-auto flex flex-col lg:flex-row gap-8 sm:gap-10 lg:gap-12 items-start">
          {/* Left Side - Category List */}
          <div className="w-full lg:w-[65%] flex flex-col">
            <h2 className="text-2xl sm:text-3xl font-serif font-normal text-gray-900 mb-6 sm:mb-8 pb-3 sm:pb-4 border-b border-gray-900">Shop By Category</h2>
            <div className="flex flex-col justify-between flex-1">
              {categories.map((category, index) => (
                <Link 
                  key={index} 
                  to={`/${category.name.toLowerCase()}`}
                  className="flex items-center justify-between py-4 sm:py-5 lg:py-6 group cursor-pointer transition-all"
                >
                  <span className="text-base sm:text-lg lg:text-xl font-light text-gray-900 group-hover:text-gray-700 transition-colors">{category.name}</span>
                  {index === 0 ? (
                    <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-gray-900 flex items-center justify-center group-hover:bg-gray-700 transition-colors">
                      <svg width="14" height="14" className="sm:w-4 sm:h-4" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                        <polyline points="9 18 15 12 9 6"></polyline>
                      </svg>
                    </div>
                  ) : (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="sm:w-4 sm:h-4 text-gray-900 group-hover:text-gray-700 transition-colors">
                      <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                  )}
                </Link>
              ))}
            </div>
          </div>
          {/* Right Side - Image */}
          <div className="w-full lg:w-[30%] rounded-xs overflow-hidden h-[300px] sm:h-[350px] lg:h-[400px] lg:mt-16">
            <img 
              src="/Images/1.png" 
              alt="Jewelry Collection" 
              className="w-full h-full object-cover"
            />
          </div>
        </div>
      </section>
      {/* Featured Banner
      <section className="px-[5%] py-12 bg-cream">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-[1400px] mx-auto">
          <div className="lg:col-span-2 rounded-2xl overflow-hidden relative">
            <img src="/Images/40.png" alt="Gold Jewelry" className="w-full h-full object-cover hover:scale-105 transition-transform duration-500" />
          </div>
          <div className="rounded-2xl overflow-hidden relative">
            <img src="/Images/41.png" alt="Ring Collection" className="w-full h-full object-cover hover:scale-105 transition-transform duration-500" />
          </div>
        </div>
      </section> */}
      {/* Bestseller Products */}
      <section className="px-4 sm:px-6 lg:px-[5%] py-12 sm:py-16 lg:py-20 bg-[#fceec6]">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 sm:mb-12 max-w-[1400px] mx-auto gap-4">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-normal text-gray-600 tracking-wide">Bestseller Products</h2>
          <Link to="/shop" className="text-sm sm:text-base text-primary hover:text-primary-dark transition-colors">
            View All →
          </Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6 lg:gap-8 max-w-[1400px] mx-auto">
          {bestsellerProducts.map((product) => (
            <div key={product.id} className="bg-white rounded-lg overflow-hidden hover:-translate-y-1 hover:shadow-xl transition-all relative group">
              <Link to={`/product/${product.id}`} className="block cursor-pointer">
                <div className="w-full h-[200px] sm:h-[220px] lg:h-[250px] flex items-center justify-center bg-white relative">
                  <img src={product.image} alt={product.name} className="max-w-[90%] max-h-[90%] object-contain" />
                </div>
                <div className="p-3 sm:p-4">
                  <h3 className="text-xs sm:text-sm font-normal text-gray-800 mb-2 min-h-[2.5rem]">{product.name}</h3>
                  {(product.brand || product.vendor_id) && (
                    <p className="text-xs text-gray-500 mb-2">
                      {product.brand ? `Brand: ${product.brand}` : 'Vendor Product'}
                    </p>
                  )}
                </div>
              </Link>
              <button 
                onClick={async (e) => {
                  e.stopPropagation();
                  const wishlistProduct = {
                    id: product.id,
                    name: product.name,
                    price: product.price,
                    image: product.image
                  };
                  if (isInWishlist(product.id)) {
                    const result = await removeFromWishlist(product.id);
                    if (!result.success) {
                      console.error('Failed to remove from wishlist:', result.error);
                    }
                  } else {
                    const result = await addToWishlist(wishlistProduct);
                    if (!result.success) {
                      console.error('Failed to add to wishlist:', result.error);
                      if (result.error && result.error.includes('login')) {
                        alert('Please login to add items to wishlist');
                      } else if (result.error && result.error.includes('not found')) {
                        console.warn('Product not found in database - using demo products');
                      } else {
                        console.error('Wishlist error:', result.error);
                      }
                    }
                  }
                }}
                className={`absolute top-2 sm:top-2.5 left-2 sm:left-2.5 border w-8 h-8 sm:w-9 sm:h-9 rounded-sm text-lg sm:text-xl cursor-pointer flex items-center justify-center transition-all ${
                  isInWishlist(product.id)
                    ? 'bg-red-50 border-red-300 text-red-600 hover:bg-red-100'
                    : 'bg-white border-gray-300 hover:bg-gray-100'
                }`}
              >
                {isInWishlist(product.id) ? '♥' : '♡'}
              </button>
              <div className="px-3 sm:px-4 pb-3 sm:pb-4">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                  <p className="text-base sm:text-lg font-semibold text-gray-900">{product.price}</p>
                  {isInCart(product.id) ? (
                    <div className="flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white px-3 sm:px-4 py-1.5 sm:py-2 rounded transition-all w-full sm:w-auto">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          const item = cartItems.find(i => i.id === product.id || i.product_id === product.id);
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
                      <span className="text-[10px] sm:text-xs font-semibold min-w-[20px] text-center uppercase tracking-wider">
                        {getItemQuantity(product.id)}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          const item = cartItems.find(i => i.id === product.id || i.product_id === product.id);
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
                        const result = await addToCart({
                          id: product.id,
                          name: product.name,
                          price: product._rawPrice || parseFloat(product.price.replace(/[₹$,]/g, '')),
                          image: product.image,
                          quantity: 1
                        });
                        if (!result.success && !result.fallback) {
                          console.error('Failed to add to cart:', result.error);
                          alert('Failed to add to cart. Please try again.');
                        } else if (result.fallback) {
                          console.warn('Added to cart locally (backend unavailable)');
                        }
                      }}
                      className="bg-[#3E2F2A] hover:bg-[#2d2219] text-white px-3 sm:px-4 py-1.5 sm:py-2 text-[10px] sm:text-xs uppercase tracking-wider font-medium transition-all w-full sm:w-auto"
                    >
                      ADD TO CART
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Ring Stacks Section */}
      <section className="px-4 sm:px-6 lg:px-[5%] py-12 sm:py-16 lg:py-20 bg-[#F4E7D0]">
        <div className="flex flex-col md:flex-row items-center gap-10 sm:gap-12 lg:gap-20 max-w-[1400px] mx-auto">
          <div className="flex-1 w-full">
            <img src="/Images/12.png" alt="Ring Stack" className="w-full h-auto rounded-xs shadow-2xl" />
          </div>
          <div className="flex-1 w-full">
            <h2 className="text-2xl sm:text-3xl font-normal text-gray-800 leading-relaxed mb-4 sm:mb-6">
              More than Jewellery — it's your story in light.
            </h2>
            <p className="text-sm sm:text-base text-gray-700 mb-6 sm:mb-8 leading-relaxed">
              For every heartbeat and memory, discover jewelry that embodies love, beauty, and timeless elegance.
            </p>
            <Link to="/shop" className="bg-transparent text-gray-800 border-b border-gray-800 px-0 py-1 text-xs sm:text-sm cursor-pointer hover:text-gray-600 transition-all uppercase tracking-wider flex items-center gap-2">
              SHOP NOW 
              <span>→</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Adorn Your Soul Section */}
      <section className="px-4 sm:px-6 lg:px-[5%] -mt-[20px] sm:-mt-[30px] lg:-mt-[40px] bg-[#F4E7D0]">
        <div className="flex flex-col md:flex-row items-center gap-10 sm:gap-12 lg:gap-20 max-w-[1400px] mx-auto">
       
          <div className="flex-1 w-full order-1 md:order-2">
            <img src="/Images/13.png" alt="Necklace and Bracelet" className="w-full h-auto rounded-xs shadow-xs" />
          </div>
             <div className="flex-1 w-full order-2 md:order-1">
            <h2 className="text-2xl sm:text-3xl font-normal text-gray-800 leading-snug mb-6 sm:mb-8">
              Adorn your soul with brilliance that
              <br className="hidden sm:block" />
              captures your essence.
            </h2>
            <p className="text-sm sm:text-base text-gray-700 mb-6 sm:mb-8 leading-relaxed">
              Each masterpiece is an expression of individuality — where every curve, sparkle,
              <br className="hidden sm:block" />
              and detail mirrors your soul.
            </p>
            <Link to="/shop" className="bg-transparent text-gray-800 border-b border-gray-800 px-0 py-1 text-xs sm:text-sm cursor-pointer hover:text-gray-600 transition-all uppercase tracking-wider flex items-center gap-2">
              SHOP NOW 
              <span>→</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Popular Products */}
      <section className="px-4 sm:px-6 lg:px-[5%] py-12 sm:py-16 lg:py-20 bg-[#fceec6]">
        <div className="max-w-[1400px] mx-auto">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 sm:mb-12 gap-4">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-normal text-gray-800 tracking-wide">Popular Products</h2>
            <div className="flex gap-2 sm:gap-3">
              <button 
                onClick={() => {
                  if (isAnimating) return;
                  setIsAnimating(true);
                  setSlideDirection('left');
                  setTimeout(() => {
                    const totalProducts = categoryProducts[selectedCategory]?.length || 0;
                    const maxPage = Math.ceil(totalProducts / 4) - 1;
                    setCurrentPage(prev => prev > 0 ? prev - 1 : maxPage);
                    setSlideDirection('');
                    setTimeout(() => {
                      setIsAnimating(false);
                    }, 100);
                  }, 500);
                }}
                className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-gray-800 text-white flex items-center justify-center hover:bg-gray-600 transition-colors disabled:opacity-50 text-sm sm:text-base"
                disabled={isAnimating}
              >
                ←
              </button>
              <button 
                onClick={() => {
                  if (isAnimating) return;
                  setIsAnimating(true);
                  setSlideDirection('right');
                  setTimeout(() => {
                    const totalProducts = categoryProducts[selectedCategory]?.length || 0;
                    const maxPage = Math.ceil(totalProducts / 4) - 1;
                    setCurrentPage(prev => prev < maxPage ? prev + 1 : 0);
                    setSlideDirection('');
                    setTimeout(() => {
                      setIsAnimating(false);
                    }, 100);
                  }, 500);
                }}
                className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-gray-800 text-white flex items-center justify-center hover:bg-gray-600 transition-colors disabled:opacity-50 text-sm sm:text-base"
                disabled={isAnimating}
              >
                →
              </button>
            </div>
          </div>

          <div className="flex flex-col lg:flex-row gap-6 sm:gap-8">
            {/* Left side - Category cards */}
            <div className="w-full lg:w-[560px] grid grid-cols-2 gap-3 sm:gap-4 h-auto lg:h-[816px]">
              {/* RINGS Card */}
              <div 
                onClick={() => {
                  setSelectedCategory('Rings');
                  setCurrentPage(0);
                }}
                className={`${selectedCategory === 'Rings' ? 'bg-[#4A3728]' : 'bg-white'} rounded-lg p-10 sm:p-12 lg:p-20 flex flex-col items-center justify-center cursor-pointer hover:shadow-lg transition-all group`}
              >
                <div className="w-12 h-12 sm:w-14 sm:h-14 lg:w-16 lg:h-16 mb-3 sm:mb-4 flex items-center justify-center">
                  <svg width="40" height="40" viewBox="0 0 100 100" className={`sm:w-12 sm:h-12 lg:w-[50px] lg:h-[50px] ${selectedCategory === 'Rings' ? 'text-white' : 'text-gray-800'} group-hover:text-gray-600`}>
                    <circle cx="50" cy="50" r="25" fill="none" stroke="currentColor" strokeWidth="3"/>
                    <circle cx="50" cy="35" r="8" fill="currentColor"/>
                  </svg>
                </div>
                <h3 className={`text-xs sm:text-sm uppercase tracking-wider ${selectedCategory === 'Rings' ? 'text-white' : 'text-gray-800'}`}>RINGS</h3>
              </div>

              {/* EARRINGS Card */}
              <div 
                onClick={() => {
                  setSelectedCategory('Earrings');
                  setCurrentPage(0);
                }}
                className={`${selectedCategory === 'Earrings' ? 'bg-[#4A3728]' : 'bg-white'} rounded-lg p-10 sm:p-12 lg:p-20 flex flex-col items-center justify-center cursor-pointer hover:shadow-lg transition-all group`}
              >
                <div className="w-12 h-12 sm:w-14 sm:h-14 lg:w-16 lg:h-16 mb-3 sm:mb-4 flex items-center justify-center">
                  <svg width="40" height="40" viewBox="0 0 100 100" className={`sm:w-12 sm:h-12 lg:w-[50px] lg:h-[50px] ${selectedCategory === 'Earrings' ? 'text-white' : 'text-gray-800'}`}>
                    <circle cx="40" cy="40" r="6" fill="currentColor"/>
                    <circle cx="60" cy="40" r="6" fill="currentColor"/>
                    <path d="M 40 45 Q 40 65, 35 70" fill="none" stroke="currentColor" strokeWidth="3"/>
                    <path d="M 60 45 Q 60 65, 65 70" fill="none" stroke="currentColor" strokeWidth="3"/>
                  </svg>
                </div>
                <h3 className={`text-xs sm:text-sm uppercase tracking-wider ${selectedCategory === 'Earrings' ? 'text-white' : 'text-gray-800'}`}>EARRINGS</h3>
              </div>

              {/* NECKLACES Card */}
              <div 
                onClick={() => {
                  setSelectedCategory('Necklaces');
                  setCurrentPage(0);
                }}
                className={`${selectedCategory === 'Necklaces' ? 'bg-[#4A3728]' : 'bg-white'} rounded-lg p-10 sm:p-12 lg:p-20 flex flex-col items-center justify-center cursor-pointer hover:shadow-lg transition-all group`}
              >
                <div className="w-12 h-12 sm:w-14 sm:h-14 lg:w-16 lg:h-16 mb-3 sm:mb-4 flex items-center justify-center">
                  <svg width="40" height="40" viewBox="0 0 100 100" className={`sm:w-12 sm:h-12 lg:w-[50px] lg:h-[50px] ${selectedCategory === 'Necklaces' ? 'text-white' : 'text-gray-800'} group-hover:text-gray-600`}>
                    <path d="M 30 30 Q 50 50, 70 30" fill="none" stroke="currentColor" strokeWidth="3"/>
                    <circle cx="50" cy="55" r="8" fill="currentColor"/>
                  </svg>
                </div>
                <h3 className={`text-xs sm:text-sm uppercase tracking-wider ${selectedCategory === 'Necklaces' ? 'text-white' : 'text-gray-800'}`}>NECKLACES</h3>
              </div>

              {/* BRACELETS Card */}
              <div 
                onClick={() => {
                  setSelectedCategory('Bracelets');
                  setCurrentPage(0);
                }}
                className={`${selectedCategory === 'Bracelets' ? 'bg-[#4A3728]' : 'bg-white'} rounded-lg p-10 sm:p-12 lg:p-20 flex flex-col items-center justify-center cursor-pointer hover:shadow-lg transition-all group`}
              >
                <div className="w-12 h-12 sm:w-14 sm:h-14 lg:w-16 lg:h-16 mb-3 sm:mb-4 flex items-center justify-center">
                  <svg width="40" height="40" viewBox="0 0 100 100" className={`sm:w-12 sm:h-12 lg:w-[50px] lg:h-[50px] ${selectedCategory === 'Bracelets' ? 'text-white' : 'text-gray-800'} group-hover:text-gray-600`}>
                    <circle cx="50" cy="50" r="20" fill="none" stroke="currentColor" strokeWidth="3"/>
                    <circle cx="50" cy="35" r="4" fill="currentColor"/>
                    <circle cx="50" cy="65" r="4" fill="currentColor"/>
                    <circle cx="35" cy="50" r="4" fill="currentColor"/>
                    <circle cx="65" cy="50" r="4" fill="currentColor"/>
                  </svg>
                </div>
                <h3 className={`text-xs sm:text-sm uppercase tracking-wider ${selectedCategory === 'Bracelets' ? 'text-white' : 'text-gray-800'}`}>BRACELETS</h3>
              </div>
            </div>

            {/* Right side - Product display */}
            <div className="flex-1 relative min-h-[500px] sm:min-h-[600px] lg:min-h-[816px] overflow-hidden">
              <div 
                key={`${selectedCategory}-${currentPage}`}
                className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6 absolute inset-0 transition-all duration-500 ease-in-out"
                style={{
                  transform: slideDirection === 'left' ? 'translateX(-120%)' : 
                            slideDirection === 'right' ? 'translateX(120%)' : 
                            'translateX(0)',
                  opacity: slideDirection ? 0 : 1,
                }}
              >
                {isLoadingProducts ? (
                  <div className="col-span-2 flex items-center justify-center h-[300px]">
                    <p className="text-gray-500">Loading products...</p>
                  </div>
                ) : categoryProducts[selectedCategory]?.length === 0 ? (
                  <div className="col-span-2 flex items-center justify-center h-[300px]">
                    <p className="text-gray-500">No products available in this category</p>
                  </div>
                ) : (
                  categoryProducts[selectedCategory]?.slice(currentPage * 4, (currentPage * 4) + 4).map((product, index) => (
                  <Link 
                    key={product.id} 
                    to={`/product/${product.id}`}
                    className="bg-[#F5F3F0] rounded-lg p-0 hover:shadow-lg transition-shadow cursor-pointer relative group flex flex-col overflow-hidden h-[300px] sm:h-[350px] lg:h-[380px] block"
                  >
                    {/* Wishlist Heart Button */}
                    <button
                      onClick={async (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        if (isInWishlist(product.id)) {
                          const result = await removeFromWishlist(product.id);
                          if (!result.success) {
                            console.error('Failed to remove from wishlist:', result.error);
                          }
                        } else {
                          const result = await addToWishlist(product);
                          if (!result.success) {
                            console.error('Failed to add to wishlist:', result.error);
                            if (result.error && result.error.includes('login')) {
                              alert('Please login to add items to wishlist');
                            } else if (result.error && result.error.includes('not found')) {
                              console.warn('Product not found in database - using demo products');
                            } else {
                              console.error('Wishlist error:', result.error);
                            }
                          }
                        }
                      }}
                      className={`absolute top-2 sm:top-2.5 left-2 sm:left-2.5 z-10 text-xl sm:text-2xl transition-all duration-300 ${
                        isInWishlist(product.id)
                          ? 'text-red-500 scale-110'
                          : 'text-gray-400 hover:text-red-400'
                      }`}
                      style={{
                        background: 'rgba(255, 255, 255, 0.9)',
                        borderRadius: '50%',
                        width: '32px',
                        height: '32px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        border: '1px solid rgba(0, 0, 0, 0.1)',
                      }}
                    >
                      {isInWishlist(product.id) ? '♥' : '♡'}
                    </button>
                    {/* Product Image */}
                    <div className="w-full h-[200px] sm:h-[240px] lg:h-[280px] flex items-center justify-center bg-[#F5F3F0] relative overflow-hidden">
                      <img src={product.image} alt={product.name} className="w-full h-full object-cover p-3 sm:p-4" />
                    </div>
                    
                    {/* Product Info */}
                    <div className="p-3 sm:p-4 pt-2 flex flex-col bg-white flex-grow">
                      <h3 className="text-xs sm:text-sm font-normal text-gray-800 mb-1 leading-tight">{product.name}</h3>
                      {product.brand && (
                        <p className="text-[10px] sm:text-xs text-gray-500 mb-1">Brand: {product.brand}</p>
                      )}
                      <div className="flex items-center gap-2 mb-2">
                        <p className="text-sm sm:text-base font-semibold text-gray-800">{product.price}</p>
                        <p className="text-xs sm:text-sm text-gray-400 line-through">{product.oldPrice}</p>
                      </div>
                      {/* Color indicator dot */}
                      <div className="flex gap-1.5">
                        <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-[#D4AF37] border border-gray-300"></div>
                      </div>
                    </div>
                  </Link>
                ))
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Elegant Ring Banner */}
      <section className="px-4 sm:px-6 lg:px-[5%] py-8 sm:py-10 lg:py-12 bg-[#fceec6]">
        <img src="/Images/gold-ring-with-diamonds 1.jpg" alt="Elegant Ring" className="w-full h-[300px] sm:h-[400px] lg:h-[500px] object-cover rounded-2xl sm:rounded-3xl shadow-2xl" />
      </section>

      {/* Testimonials */}
      <section className="px-4 sm:px-6 lg:px-[5%] py-12 sm:py-16 lg:py-20 bg-[#fceec6]">
        <div className="max-w-[1400px] mx-auto">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 sm:mb-12 gap-4">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-serif font-normal text-gray-800 tracking-wide">Testimonials</h2>
            <div className="flex gap-2 sm:gap-3">
              <button 
                onClick={() => {
                  if (isTestimonialAnimating) return;
                  setIsTestimonialAnimating(true);
                  setTestimonialSlideDirection('left');
                  setTimeout(() => {
                    const maxPage = Math.ceil(allTestimonials.length / 2) - 1;
                    setTestimonialPage(prev => prev > 0 ? prev - 1 : maxPage);
                    setTestimonialSlideDirection('');
                    setTimeout(() => {
                      setIsTestimonialAnimating(false);
                    }, 100);
                  }, 500);
                }}
                className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-white border border-gray-300 text-gray-600 flex items-center justify-center hover:bg-gray-800 hover:text-white hover:border-gray-800 transition-all text-base sm:text-lg disabled:opacity-50"
                disabled={isTestimonialAnimating}
              >
                ←
              </button>
              <button 
                onClick={() => {
                  if (isTestimonialAnimating) return;
                  setIsTestimonialAnimating(true);
                  setTestimonialSlideDirection('right');
                  setTimeout(() => {
                    const maxPage = Math.ceil(allTestimonials.length / 2) - 1;
                    setTestimonialPage(prev => prev < maxPage ? prev + 1 : 0);
                    setTestimonialSlideDirection('');
                    setTimeout(() => {
                      setIsTestimonialAnimating(false);
                    }, 100);
                  }, 500);
                }}
                className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-gray-800 text-white flex items-center justify-center hover:bg-gray-700 transition-all text-base sm:text-lg disabled:opacity-50"
                disabled={isTestimonialAnimating}
              >
                →
              </button>
            </div>
          </div>
          
          <div className="relative overflow-hidden min-h-[250px] sm:min-h-[280px] lg:min-h-[300px]">
            <div 
              key={testimonialPage}
              className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 max-w-[1200px] transition-all duration-500 ease-in-out"
              style={{
                transform: testimonialSlideDirection === 'left' ? 'translateX(120%)' : 
                          testimonialSlideDirection === 'right' ? 'translateX(-120%)' : 
                          'translateX(0)',
                opacity: testimonialSlideDirection ? 0 : 1,
              }}
            >
              {allTestimonials.slice(testimonialPage * 2, (testimonialPage * 2) + 2).map((testimonial, index) => (
                <div 
                  key={testimonial.id} 
                  className="bg-white rounded-xl sm:rounded-2xl p-5 sm:p-6 lg:p-8 shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
                  style={{
                    transitionDelay: `${index * 100}ms`
                  }}
                >
                <div className="flex items-start gap-3 mb-3 sm:mb-4">
                  <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-gray-200 flex items-center justify-center text-lg sm:text-xl flex-shrink-0">
                    {testimonial.image}
                  </div>
                  <div className="flex-1">
                    <h4 className="text-xs sm:text-sm font-medium text-gray-800 mb-0">{testimonial.name}</h4>
                  </div>
                </div>
                
                <h3 className="text-lg sm:text-xl font-normal text-gray-900 mb-2 sm:mb-3 leading-tight">
                  {testimonial.title}
                </h3>
                
                <p className="text-xs sm:text-sm text-gray-600 leading-relaxed mb-3 sm:mb-4">
                  {testimonial.text}
                </p>
                
                <div className="flex text-gray-800 text-sm sm:text-base">
                  {'★'.repeat(testimonial.rating)}
                </div>
              </div>
            ))}
            </div>
          </div>
        </div>
      </section>

      {/* Get Inspired Section */}
      <section className="px-4 sm:px-6 lg:px-[5%] py-12 sm:py-16 lg:py-20 bg-[#fceec6]">
        <div className="max-w-[1400px] mx-auto">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-serif font-normal text-gray-800 mb-8 sm:mb-10 lg:mb-12">Get Inspired</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <div className="rounded-xs overflow-hidden h-[180px] sm:h-[300px] lg:h-[450px] hover:scale-105 transition-transform duration-300 cursor-pointer">
              <img 
                src="/Images/20.png" 
                alt="Jewelry inspiration 1" 
                className="w-full h-full object-cover"
              />
            </div>
            <div className="rounded-xs overflow-hidden h-[180px] sm:h-[300px] lg:h-[450px] hover:scale-105 transition-transform duration-300 cursor-pointer">
              <img 
                src="/Images/21.png" 
                alt="Jewelry inspiration 2" 
                className="w-full h-full object-cover"
              />
            </div>
            <div className="rounded-xs overflow-hidden h-[180px] sm:h-[300px] lg:h-[450px] hover:scale-105 transition-transform duration-300 cursor-pointer">
              <img 
                src="/Images/22.png" 
                alt="Jewelry inspiration 3" 
                className="w-full h-full object-cover"
              />
            </div>
            <div className="rounded-xs overflow-hidden h-[180px] sm:h-[300px] lg:h-[450px] hover:scale-105 transition-transform duration-300 cursor-pointer">
              <img 
                src="/Images/23.png" 
                alt="Jewelry inspiration 4" 
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Get Support Section */}
      <section className="px-4 sm:px-6 lg:px-[5%] py-8 sm:py-10 lg:py-12 bg-[#3E3833]">
        <div className="max-w-[1400px] mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
            {/* Free Shipping */}
            <div className="flex items-center gap-3 sm:gap-4 text-white">
              <div className="w-10 h-10 sm:w-12 sm:h-12 flex items-center justify-center flex-shrink-0">
                <svg width="32" height="32" className="sm:w-10 sm:h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M13 16V6a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h1m8-1a1 1 0 0 0 1 1h2.5a2.5 2.5 0 1 0 0-5H13V6h6.5L22 12h-2.5M13 16h-2m-5 0H4m4 0a2 2 0 1 0 4 0m-4 0a2 2 0 1 1 4 0"/>
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-sm sm:text-base font-medium mb-0.5 sm:mb-1">Free Shipping</h3>
                <p className="text-xs sm:text-sm text-gray-300">You will love at great low price</p>
              </div>
            </div>

            {/* 15 Days Returns */}
            <div className="flex items-center gap-3 sm:gap-4 text-white">
              <div className="w-10 h-10 sm:w-12 sm:h-12 flex items-center justify-center flex-shrink-0">
                <svg width="32" height="32" className="sm:w-10 sm:h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M9 14l-5-5m0 0l5-5M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5v0a5.5 5.5 0 0 1-5.5 5.5H13"/>
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-sm sm:text-base font-medium mb-0.5 sm:mb-1">15 Days Returns</h3>
                <p className="text-xs sm:text-sm text-gray-300">Within 15 days for an exchange</p>
              </div>
            </div>

            {/* Customer Support */}
            <div className="flex items-center gap-3 sm:gap-4 text-white">
              <div className="w-10 h-10 sm:w-12 sm:h-12 flex items-center justify-center flex-shrink-0">
                <svg width="32" height="32" className="sm:w-10 sm:h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-sm sm:text-base font-medium mb-0.5 sm:mb-1">Customer Support</h3>
                <p className="text-xs sm:text-sm text-gray-300">24 hours a day, 7 days a week</p>
              </div>
            </div>

            {/* Flexible Payment */}
            <div className="flex items-center gap-3 sm:gap-4 text-white">
              <div className="w-10 h-10 sm:w-12 sm:h-12 flex items-center justify-center flex-shrink-0">
                <svg width="32" height="32" className="sm:w-10 sm:h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <rect x="2" y="5" width="20" height="14" rx="2"/>
                  <line x1="2" y1="10" x2="22" y2="10"/>
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-sm sm:text-base font-medium mb-0.5 sm:mb-1">Flexible Payment</h3>
                <p className="text-xs sm:text-sm text-gray-300">Pay with multiple credit cards</p>
              </div>
            </div>
          </div>
        </div>
      </section>
<Footer />
    </div>
  );
};

export default Home;
