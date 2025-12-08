import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useWishlist } from '../context/WishlistContext';
import { useAuth } from '../context/AuthContext';
import Search from './Search';
import Footer from './Footer';
const Login = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { cartItems, getCartCount } = useCart();
  const { wishlistItems } = useWishlist();
  const { login, deliveryBoyLogin } = useAuth();
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState('');
  const [sessionExpired, setSessionExpired] = useState(false);

  // Check if redirected due to session expiration
  useEffect(() => {
    if (searchParams.get('expired') === 'true') {
      setSessionExpired(true);
      // Clear the expired param from URL
      const newSearchParams = new URLSearchParams(searchParams);
      newSearchParams.delete('expired');
      navigate({ search: newSearchParams.toString() }, { replace: true });
    }
  }, [searchParams, navigate]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setApiError('');

    try {
      // Try regular login first
      let result = await login(formData.email, formData.password);

      // If regular login fails with 401 (invalid credentials), try delivery boy login
      if (!result.success && result.error && (
        result.error.includes('Invalid email or password') || 
        result.error.includes('invalid credentials') ||
        result.error.includes('401')
      )) {
        console.log('Regular login failed with invalid credentials, trying delivery boy login...');
        console.log('Attempting delivery boy login for:', formData.email);
        
        try {
          result = await deliveryBoyLogin(formData.email, formData.password);
          
          if (result.success) {
            console.log('✅ Delivery boy login successful!', result.user);
          } else {
            console.log('❌ Delivery boy login also failed:', result.error);
          }
        } catch (deliveryError) {
          console.log('❌ Delivery boy login error:', deliveryError);
        }
      }

      if (result.success) {
        // Check if 2FA is required
        if (result.require_2fa) {
          alert('2FA is enabled. Please verify with your authenticator app.');
          // You can navigate to a 2FA verification page
          // navigate('/verify-2fa', { state: { temp_token: result.temp_token } });
          return;
        }

        // Login successful
        console.log('Login successful:', result.user);
        
        // Store additional user info for compatibility
        localStorage.setItem('userEmail', result.user.email);
        localStorage.setItem('userRole', result.user.role || 'customer');
        
        // Show success message
        const userName = result.user.first_name || result.user.name || 'User';
        alert(`Welcome back, ${userName}!`);
        
        // Navigate based on user role
        const userRole = result.user.role || 'customer';
        let redirectPath = '/';
        
        switch (userRole) {
          case 'super_admin':
            redirectPath = '/super-admin/dashboard';
            break;
          case 'admin':
            redirectPath = '/admin/dashboard';
            break;
          case 'vendor':
            redirectPath = '/vendor/dashboard';
            break;
          case 'delivery_boy':
            redirectPath = '/delivery/dashboard';
            break;
          case 'customer':
          default:
            redirectPath = '/customer/dashboard';
            break;
        }
        
        navigate(redirectPath);
      } else {
        // Login failed
        setApiError(result.error || 'Invalid email or password');
        setErrors({ 
          email: 'Invalid credentials', 
          password: 'Invalid credentials' 
        });
      }
    } catch (error) {
      console.error('Login error:', error);
      setApiError(error.message || 'An error occurred during login. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4E7D0]">
      {/* Header */}
      <header className="bg-[#3E2F2A] text-white px-4 sm:px-6 lg:px-[5%] py-4 sm:py-5">
        <div className="max-w-[1400px] mx-auto flex justify-between items-center">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 sm:gap-3 cursor-pointer">
            <img src="/Images/1000017875-removebg-preview 9.jpg" alt="Soara Logo" className="w-12 h-12 sm:w-16 sm:h-16 lg:w-20 lg:h-20 object-contain" />
          </Link>

          {/* Navigation - Hidden on mobile */}
          <nav className="hidden md:flex gap-6 lg:gap-11 uppercase text-[11px] sm:text-[12px] lg:text-[13px] tracking-wider font-light">
            <Link to="/rings" className="hover:text-yellow-500 transition-colors">RINGS</Link>
            <Link to="/earrings" className="hover:text-yellow-500 transition-colors">EARRINGS</Link>
            <Link to="/bracelets" className="hover:text-yellow-500 transition-colors">BRACELETS</Link>
            <Link to="/pendents" className="hover:text-yellow-500 transition-colors">PENDENTS</Link>
            <Link to="/necklaces" className="hover:text-yellow-500 transition-colors">NECKLACES</Link>
          </nav>

          {/* Icons */}
          <div className="flex gap-3 sm:gap-4 lg:gap-5 items-center relative">
            <button 
              onClick={() => setIsSearchOpen(!isSearchOpen)}
              className="hover:text-yellow-500 transition-colors"
            >
              <svg width="16" height="16" className="sm:w-[18px] sm:h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
              </svg>
            </button>
            <Search isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
            <Link to="/wishlist" className="hover:text-yellow-500 transition-colors relative">
              <svg width="18" height="18" className="sm:w-[20px] sm:h-[20px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
              </svg>
              {wishlistItems.length > 0 && (
                <span className="absolute -top-2 -right-2 bg-yellow-500 text-[#3E2F2A] text-[10px] sm:text-xs font-bold rounded-full w-4 h-4 sm:w-5 sm:h-5 flex items-center justify-center">
                  {wishlistItems.length}
                </span>
              )}
            </Link>
            <Link to="/login" className="hover:text-yellow-500 transition-colors">
              <svg width="16" height="16" className="sm:w-[18px] sm:h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
            </Link>
            <Link to="/cart" className="hover:text-yellow-500 transition-colors relative">
              <svg width="16" height="16" className="sm:w-[18px] sm:h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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
          </div>
        </div>
      </header>

      {/* Login Form Section */}
      <section className="px-4 sm:px-6 lg:px-[5%] py-8 sm:py-12 lg:py-16 bg-[#F4E7D0]">
        <div className="max-w-[480px] mx-auto">
          {/* Title */}
          <div className="text-center mb-6 sm:mb-8 lg:mb-10">
            <h1 className="text-3xl sm:text-4xl font-serif font-normal text-gray-900 mb-2 sm:mb-3">Welcome Back</h1>
            <p className="text-sm text-gray-800">Sign in to access your account</p>
          </div>

          {/* Login Form */}
          <div className="bg-white rounded-lg shadow-lg p-6 sm:p-8">
            {/* Session Expired Message */}
            {sessionExpired && (
              <div className="mb-4 p-3 bg-yellow-100 border border-yellow-400 text-yellow-800 rounded">
                <p className="text-sm font-medium">Your session has expired. Please log in again.</p>
              </div>
            )}
            
            {/* API Error Message */}
            {apiError && (
              <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                <p className="text-sm">{apiError}</p>
              </div>
            )}
            
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Email Field */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-800 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 border ${
                    errors.email ? 'border-red-500' : 'border-gray-300'
                  } bg-white text-sm text-gray-900 focus:outline-none focus:border-[#3E2F2A] transition-colors`}
                  placeholder="Enter your email"
                />
                {errors.email && (
                  <p className="mt-1 text-xs text-red-600">{errors.email}</p>
                )}
              </div>

              {/* Password Field */}
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-800 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 border ${
                    errors.password ? 'border-red-500' : 'border-gray-300'
                  } bg-white text-sm text-gray-900 focus:outline-none focus:border-[#3E2F2A] transition-colors`}
                  placeholder="Enter your password"
                />
                {errors.password && (
                  <p className="mt-1 text-xs text-red-600">{errors.password}</p>
                )}
              </div>

              {/* Remember Me & Forgot Password */}
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="rememberMe"
                    name="rememberMe"
                    checked={formData.rememberMe}
                    onChange={handleChange}
                    className="w-4 h-4 text-[#3E2F2A] border-gray-300 rounded focus:ring-[#3E2F2A]"
                  />
                  <label htmlFor="rememberMe" className="ml-2 text-sm text-gray-700">
                    Remember me
                  </label>
                </div>
                
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-[#3E2F2A] text-white py-3 text-sm uppercase tracking-wider font-medium hover:bg-[#2d2219] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Signing In...' : 'Sign In'}
              </button>
            </form>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-white text-gray-600">Or continue with</span>
              </div>
            </div>
           

            {/* Sign Up Link */}
            <div className="mt-6 text-center">
              <p className="text-sm text-gray-700">
                Don't have an account?{' '}
                <Link to="/signup" className="text-[#3E2F2A] font-medium hover:text-[#2d2219] transition-colors">
                  Sign Up
                </Link>
              </p>
            </div>


           
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Login;