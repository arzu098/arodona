import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Signup = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    phone: '',
    role: 'customer' // Only customer registration allowed
  });

  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.first_name.trim()) {
      newErrors.first_name = 'First name is required';
    }
    
    if (!formData.last_name.trim()) {
      newErrors.last_name = 'Last name is required';
    }
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    } else if (formData.password.length > 128) {
      newErrors.password = 'Password must be less than 128 characters';
    }
    
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
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
      // Call the register function from AuthContext
      const result = await register({
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name,
        last_name: formData.last_name,
        phone: formData.phone || null,
        role: formData.role
      });

      if (result.success) {
        // Registration successful
        alert(`Registration successful! Welcome ${formData.first_name}!`);
        
        // Navigate to login page
        navigate('/login');
      } else {
        // Registration failed
        setApiError(result.error || 'Registration failed. Please try again.');
      }
    } catch (error) {
      console.error('Registration error:', error);
      setApiError(error.message || 'An error occurred during registration. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4E7D0] py-8 sm:py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto">
        {/* Header */}
        <div className="text-center mb-6 sm:mb-8">
          <Link to="/" className="inline-block mb-4">
            <img src="/Images/1000017875-removebg-preview 9.jpg" alt="Soara Logo" className="w-16 h-16 sm:w-20 sm:h-20 object-contain mx-auto" />
          </Link>
          <h2 className="text-2xl sm:text-3xl font-serif font-normal text-gray-900 mb-2">Create Account</h2>
          <p className="text-sm text-gray-600">Join our jewelry community</p>
        </div>

        {/* Registration Form */}
        <div className="bg-white rounded-lg shadow-lg p-6 sm:p-8">
          {/* API Error Message */}
          {apiError && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              <p className="text-sm">{apiError}</p>
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Account Type Info - Read Only */}
            <div>
              <label htmlFor="role" className="block text-sm font-medium text-gray-800 mb-2">
                Account Type
              </label>
              <div className="w-full px-4 py-3 border border-gray-200 bg-gray-50 text-sm text-gray-700 rounded">
                Customer Account
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Public registration is available for customers only. Vendor and admin accounts must be created by authorized personnel.
              </p>
            </div>

            {/* Name Fields */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              <div>
                <label htmlFor="first_name" className="block text-xs sm:text-sm font-medium text-gray-800 mb-2">
                  First Name
                </label>
                <input
                  type="text"
                  id="first_name"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border ${
                    errors.first_name ? 'border-red-500' : 'border-gray-300'
                  } bg-white text-sm text-gray-900 focus:outline-none focus:border-[#3E2F2A] transition-colors`}
                  placeholder="First name"
                />
                {errors.first_name && (
                  <p className="mt-1 text-xs text-red-600">{errors.first_name}</p>
                )}
              </div>
              <div>
                <label htmlFor="last_name" className="block text-xs sm:text-sm font-medium text-gray-800 mb-2">
                  Last Name
                </label>
                <input
                  type="text"
                  id="last_name"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border ${
                    errors.last_name ? 'border-red-500' : 'border-gray-300'
                  } bg-white text-sm text-gray-900 focus:outline-none focus:border-[#3E2F2A] transition-colors`}
                  placeholder="Last name"
                />
                {errors.last_name && (
                  <p className="mt-1 text-xs text-red-600">{errors.last_name}</p>
                )}
              </div>
            </div>

            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-xs sm:text-sm font-medium text-gray-800 mb-2">
                Email Address
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border ${
                  errors.email ? 'border-red-500' : 'border-gray-300'
                } bg-white text-sm text-gray-900 focus:outline-none focus:border-[#3E2F2A] transition-colors`}
                placeholder="Enter your email"
              />
              {errors.email && (
                <p className="mt-1 text-xs text-red-600">{errors.email}</p>
              )}
            </div>

            {/* Phone Field */}
            <div>
              <label htmlFor="phone" className="block text-xs sm:text-sm font-medium text-gray-800 mb-2">
                Phone Number (Optional)
              </label>
              <input
                type="tel"
                id="phone"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                className="w-full px-3 sm:px-4 py-2.5 sm:py-3 border border-gray-300 bg-white text-sm text-gray-900 focus:outline-none focus:border-[#3E2F2A] transition-colors"
                placeholder="Enter your phone number"
              />
            </div>

            {/* Password Fields */}
            <div>
              <label htmlFor="password" className="block text-xs sm:text-sm font-medium text-gray-800 mb-2">
                Password
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border ${
                  errors.password ? 'border-red-500' : 'border-gray-300'
                } bg-white text-sm text-gray-900 focus:outline-none focus:border-[#3E2F2A] transition-colors`}
                placeholder="Enter your password"
              />
              {errors.password && (
                <p className="mt-1 text-xs text-red-600">{errors.password}</p>
              )}
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-xs sm:text-sm font-medium text-gray-800 mb-2">
                Confirm Password
              </label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border ${
                  errors.confirmPassword ? 'border-red-500' : 'border-gray-300'
                } bg-white text-sm text-gray-900 focus:outline-none focus:border-[#3E2F2A] transition-colors`}
                placeholder="Confirm your password"
              />
              {errors.confirmPassword && (
                <p className="mt-1 text-xs text-red-600">{errors.confirmPassword}</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-[#3E2F2A] text-white py-3 text-sm uppercase tracking-wider font-medium hover:bg-[#2d2219] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          {/* Login Link */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-700">
              Already have an account?{' '}
              <Link to="/login" className="text-[#3E2F2A] font-medium hover:text-[#2d2219] transition-colors">
                Sign In
              </Link>
            </p>
          </div>

            {/* Registration Info */}
            <div className="mt-4 sm:mt-6 p-3 sm:p-4 bg-blue-50 border border-blue-200 rounded">
              <p className="text-xs font-semibold text-gray-800 mb-2">Customer Registration</p>
              <div className="text-xs text-gray-700 space-y-1">
                <p>• Browse our exclusive jewelry collection</p>
                <p>• Add items to favorites and cart</p>
                <p>• Place and track orders</p>
                <p>• Manage your profile and preferences</p>
              </div>
              <p className="text-xs text-gray-600 mt-2 font-medium">
                Need a vendor or admin account? Contact our support team for assistance.
              </p>
            </div>
        </div>
      </div>
    </div>
  );
};

export default Signup;