import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

function Checkout() {
  const navigate = useNavigate();
  const { cartItems, getCartTotal } = useCart();
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(1); // 1: Address, 2: Payment, 3: Review
  const [addresses, setAddresses] = useState([]);
  const [selectedAddressId, setSelectedAddressId] = useState(null);
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState(null);
  const [showAddAddressModal, setShowAddAddressModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Card payment details
  const [cardDetails, setCardDetails] = useState({
    cardNumber: '',
    cardName: '',
    expiryDate: '',
    cvv: ''
  });

  // New address form state
  const [newAddress, setNewAddress] = useState({
    name: '',
    phone: '',
    address: '',
    city: '',
    country: 'United State',
    address_type: 'HOME'
  });

  // Calculate totals
  const subtotal = cartItems.reduce((total, item) => {
    const price = typeof item.price === 'string' 
      ? parseFloat(item.price.replace(/[₹$,\s]/g, ''))
      : item.price;
    return total + (price * item.quantity);
  }, 0);
  const taxes = subtotal * 0.07;
  const deliveryFee = subtotal > 0 ? (subtotal > 5000 ? 0 : 50) : 0;
  const grandTotal = subtotal + taxes + deliveryFee;

  useEffect(() => {
    if (cartItems.length === 0) {
      navigate('/cart');
      return;
    }
    fetchAddresses();
  }, [cartItems, navigate]);

  const fetchAddresses = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/addresses');
      setAddresses(response.data);
      
      // Auto-select default address or first address
      const defaultAddr = response.data.find(addr => addr.is_default);
      if (defaultAddr) {
        setSelectedAddressId(defaultAddr.id);
      } else if (response.data.length > 0) {
        setSelectedAddressId(response.data[0].id);
      }
      
      setLoading(false);
    } catch (err) {
      console.error('Error fetching addresses:', err);
      setError('Failed to load addresses');
      setLoading(false);
    }
  };

  const handleAddAddress = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post('/api/addresses', newAddress);
      setAddresses([...addresses, response.data]);
      setSelectedAddressId(response.data.id);
      setShowAddAddressModal(false);
      setNewAddress({
        name: '',
        phone: '',
        address: '',
        city: '',
        country: 'United State',
        address_type: 'HOME'
      });
    } catch (err) {
      console.error('Error adding address:', err);
      alert('Failed to add address. Please try again.');
    }
  };

  const handleDeleteAddress = async (addressId) => {
    if (!window.confirm('Are you sure you want to delete this address?')) {
      return;
    }
    
    try {
      await api.delete(`/api/addresses/${addressId}`);
      setAddresses(addresses.filter(addr => addr.id !== addressId));
      if (selectedAddressId === addressId) {
        setSelectedAddressId(addresses.length > 1 ? addresses[0].id : null);
      }
    } catch (err) {
      console.error('Error deleting address:', err);
      alert('Failed to delete address.');
    }
  };

  const handleContinue = async () => {
    if (currentStep === 1 && !selectedAddressId) {
      alert('Please select a delivery address');
      return;
    }
    
    if (currentStep === 2 && !selectedPaymentMethod) {
      alert('Please select a payment method');
      return;
    }
    
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
      console.log('Moving to step:', currentStep + 1);
      // Scroll to top when changing steps
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      // Place order
      await placeOrder();
    }
  };

  const placeOrder = async () => {
    try {
      setLoading(true);
      
      // Get selected address details
      const selectedAddress = addresses.find(addr => addr.id === selectedAddressId);
      
      if (!selectedAddress) {
        alert('Please select a delivery address');
        setLoading(false);
        return;
      }

      // Split name into first and last name
      const nameParts = selectedAddress.name.split(' ');
      const firstName = nameParts[0] || '';
      const lastName = nameParts.slice(1).join(' ') || '';
      
      // Prepare order data according to OrderCreateRequest schema
      const orderData = {
        billing_address: {
          type: "billing",
          first_name: firstName || "Customer",
          last_name: lastName || "User",
          address_line1: selectedAddress.address || "Address not provided",
          city: selectedAddress.city || "City not provided",
          state_province: selectedAddress.city || "State not provided", // Using city as state for now
          postal_code: "00000", // Default postal code
          country_code: selectedAddress.country === 'United State' ? 'US' : 'US'
          // Remove empty email and phone to avoid validation issues
        },
        shipping_address: {
          type: "shipping", 
          first_name: firstName || "Customer",
          last_name: lastName || "User",
          address_line1: selectedAddress.address || "Address not provided",
          city: selectedAddress.city || "City not provided",
          state_province: selectedAddress.city || "State not provided",
          postal_code: "00000",
          country_code: selectedAddress.country === 'United State' ? 'US' : 'US'
          // Remove empty email and phone to avoid validation issues
        },
        shipping_method: "standard",
        payment_method: selectedPaymentMethod || "cash_on_delivery",
        notes: "Order placed via checkout",
        marketing_consent: false
      };
      
      // Add phone and email only if they exist and are not empty
      if (selectedAddress.phone && selectedAddress.phone.trim()) {
        orderData.billing_address.phone = selectedAddress.phone.trim();
        orderData.shipping_address.phone = selectedAddress.phone.trim();
      }
      
      // Get user email from auth context or localStorage
      const userEmail = user?.email || localStorage.getItem('userEmail');
      if (userEmail && userEmail.trim()) {
        orderData.billing_address.email = userEmail.trim();
        orderData.shipping_address.email = userEmail.trim();
      }

      console.log('Placing order with data:', orderData);
      
      const response = await api.post('/api/orders/', orderData);
      
      if (response.data && (response.data.success !== false)) {
        const orderId = response.data.order_id || response.data.id || 'Unknown';
        alert('🎉 Order placed successfully! Order ID: ' + orderId);
        
        // Navigate to order confirmation or success page
        navigate('/order-success');
      } else {
        throw new Error(response.data.message || 'Order creation failed');
      }
      
    } catch (error) {
      console.error('Error placing order:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      
      let errorMessage = 'Failed to place order. Please try again.';
      
      if (error.response?.data) {
        if (error.response.data.message) {
          errorMessage = error.response.data.message;
        } else if (error.response.data.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response.data.errors) {
          errorMessage = `Validation errors: ${JSON.stringify(error.response.data.errors)}`;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      alert('❌ ' + errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F4E7D0] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#3E2F2A] mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F4E7D0]">
      {/* Header */}
      <header className="bg-[#3E2F2A] text-white py-4 px-6 lg:px-[5%]">
        <div className="max-w-[1400px] mx-auto">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center">
              <img 
                src="/Images/1000017875-removebg-preview 9.jpg" 
                alt="Soara" 
                className="w-16 h-16 md:w-20 md:h-20 object-contain" 
              />
            </Link>
            <nav className="hidden md:flex items-center gap-8">
              <Link to="/rings" className="hover:text-yellow-400 transition-colors text-sm font-medium">RINGS</Link>
              <Link to="/earrings" className="hover:text-yellow-400 transition-colors text-sm font-medium">EARRINGS</Link>
              <Link to="/bracelets" className="hover:text-yellow-400 transition-colors text-sm font-medium">BRACELETS</Link>
              <Link to="/pendents" className="hover:text-yellow-400 transition-colors text-sm font-medium">PENDENTS</Link>
              <Link to="/necklaces" className="hover:text-yellow-400 transition-colors text-sm font-medium">NECKLACES</Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="px-6 lg:px-[5%] py-12">
        <div className="max-w-[1400px] mx-auto">
          <h1 className="text-3xl md:text-4xl font-serif text-gray-900 mb-8">Checkout</h1>
          
          {/* Debug: Show current step */}
          <div className="mb-4 text-sm text-gray-600">Current Step: {currentStep}</div>

          {/* Progress Steps */}
          <div className="flex items-center justify-center mb-12">
            <div className="flex items-center gap-4">
              {/* Address Step */}
              <div className="flex flex-col items-center">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  currentStep >= 1 ? 'bg-[#3E2F2A] text-white' : 'bg-gray-300 text-gray-600'
                }`}>
                  1
                </div>
                <span className="text-sm mt-2 font-medium">Address</span>
              </div>

              <div className={`w-16 h-0.5 ${currentStep >= 2 ? 'bg-[#3E2F2A]' : 'bg-gray-300'}`}></div>

              {/* Payment Step */}
              <div className="flex flex-col items-center">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  currentStep >= 2 ? 'bg-[#3E2F2A] text-white' : 'bg-gray-300 text-gray-600'
                }`}>
                  2
                </div>
                <span className="text-sm mt-2 font-medium">Payment</span>
              </div>

              <div className={`w-16 h-0.5 ${currentStep >= 3 ? 'bg-[#3E2F2A]' : 'bg-gray-300'}`}></div>

              {/* Review Step */}
              <div className="flex flex-col items-center">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  currentStep >= 3 ? 'bg-[#3E2F2A] text-white' : 'bg-gray-300 text-gray-600'
                }`}>
                  3
                </div>
                <span className="text-sm mt-2 font-medium">Review</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left - Content based on current step */}
            <div className="lg:col-span-2">
              {currentStep === 1 && (
                <div className="bg-white rounded-lg p-6">
                  <h2 className="text-lg font-semibold mb-4">Select Address</h2>
                  
                  {addresses.length > 0 ? (
                    <div className="space-y-4">
                      {addresses.map(address => (
                        <div 
                          key={address.id}
                          className={`p-4 border rounded-lg cursor-pointer ${
                            selectedAddressId === address.id ? 'border-[#3E2F2A] bg-blue-50' : 'border-gray-200'
                          }`}
                          onClick={() => setSelectedAddressId(address.id)}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex items-start gap-3">
                              <input 
                                type="radio" 
                                checked={selectedAddressId === address.id}
                                onChange={() => setSelectedAddressId(address.id)}
                                className="mt-1"
                              />
                              <div>
                                <div className="font-medium">{address.name}</div>
                                <div className="text-gray-600">{address.address}</div>
                                <div className="text-gray-600">{address.city}, {address.country}</div>
                                <div className="text-gray-600">{address.phone}</div>
                              </div>
                            </div>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteAddress(address.id);
                              }}
                              className="text-red-600 hover:text-red-800"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-600">No addresses found. Please add a new address.</p>
                  )}

                  <button
                    onClick={() => setShowAddAddressModal(true)}
                    className="mt-4 w-full border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-[#3E2F2A] transition-colors"
                  >
                    + Add New Address
                  </button>
                </div>
              )}

              {currentStep === 2 && (
                <div className="space-y-4">
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">Select Payment Method</h2>
                  
                  {/* Credit/Debit Card */}
                  <div 
                    className={`bg-white rounded-lg p-6 shadow-sm border-2 transition-all ${
                      selectedPaymentMethod === 'card' ? 'border-[#3E2F2A]' : 'border-gray-200'
                    }`}
                  >
                    <div 
                      className="flex items-center gap-4 cursor-pointer"
                      onClick={() => setSelectedPaymentMethod('card')}
                    >
                      <input 
                        type="radio" 
                        checked={selectedPaymentMethod === 'card'}
                        onChange={() => setSelectedPaymentMethod('card')}
                        className="w-5 h-5"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <svg className="w-6 h-6 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                          </svg>
                          <span className="font-semibold text-gray-900">Credit / Debit Card</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-10 h-6 bg-blue-600 rounded flex items-center justify-center text-white text-xs font-bold">VISA</div>
                          <div className="w-10 h-6 bg-red-600 rounded flex items-center justify-center text-white text-xs font-bold">MC</div>
                          <div className="w-10 h-6 bg-blue-400 rounded flex items-center justify-center text-white text-xs font-bold">AE</div>
                        </div>
                      </div>
                    </div>
                    
                    {selectedPaymentMethod === 'card' && (
                      <div className="mt-6 pt-6 border-t space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Card Number</label>
                          <input
                            type="text"
                            placeholder="1234 5678 9012 3456"
                            value={cardDetails.cardNumber}
                            onChange={(e) => setCardDetails({...cardDetails, cardNumber: e.target.value})}
                            className="w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#3E2F2A]"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Cardholder Name</label>
                          <input
                            type="text"
                            placeholder="JOHN DOE"
                            value={cardDetails.cardName}
                            onChange={(e) => setCardDetails({...cardDetails, cardName: e.target.value})}
                            className="w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#3E2F2A]"
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Expiry Date</label>
                            <input
                              type="text"
                              placeholder="MM/YY"
                              value={cardDetails.expiryDate}
                              onChange={(e) => setCardDetails({...cardDetails, expiryDate: e.target.value})}
                              className="w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#3E2F2A]"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">CVV</label>
                            <input
                              type="password"
                              placeholder="123"
                              value={cardDetails.cvv}
                              onChange={(e) => setCardDetails({...cardDetails, cvv: e.target.value})}
                              className="w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#3E2F2A]"
                            />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* PayPal */}
                  <div 
                    className={`bg-white rounded-lg p-6 shadow-sm border-2 transition-all cursor-pointer ${
                      selectedPaymentMethod === 'paypal' ? 'border-[#3E2F2A]' : 'border-gray-200'
                    }`}
                    onClick={() => setSelectedPaymentMethod('paypal')}
                  >
                    <div className="flex items-center gap-4">
                      <input 
                        type="radio" 
                        checked={selectedPaymentMethod === 'paypal'}
                        onChange={() => setSelectedPaymentMethod('paypal')}
                        className="w-5 h-5"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center text-white font-bold">P</div>
                          <span className="font-semibold text-gray-900">PayPal</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Klarna */}
                  <div 
                    className={`bg-white rounded-lg p-6 shadow-sm border-2 transition-all cursor-pointer ${
                      selectedPaymentMethod === 'klarna' ? 'border-[#3E2F2A]' : 'border-gray-200'
                    }`}
                    onClick={() => setSelectedPaymentMethod('klarna')}
                  >
                    <div className="flex items-center gap-4">
                      <input 
                        type="radio" 
                        checked={selectedPaymentMethod === 'klarna'}
                        onChange={() => setSelectedPaymentMethod('klarna')}
                        className="w-5 h-5"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-pink-600 rounded flex items-center justify-center text-white font-bold text-sm">K</div>
                          <div>
                            <span className="font-semibold text-gray-900 block">Klarna</span>
                            <span className="text-sm text-gray-600">Pay in 4 interest-free installments</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Apple Pay */}
                  <div 
                    className={`bg-white rounded-lg p-6 shadow-sm border-2 transition-all cursor-pointer ${
                      selectedPaymentMethod === 'apple_pay' ? 'border-[#3E2F2A]' : 'border-gray-200'
                    }`}
                    onClick={() => setSelectedPaymentMethod('apple_pay')}
                  >
                    <div className="flex items-center gap-4">
                      <input 
                        type="radio" 
                        checked={selectedPaymentMethod === 'apple_pay'}
                        onChange={() => setSelectedPaymentMethod('apple_pay')}
                        className="w-5 h-5"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-black rounded flex items-center justify-center">
                            <span className="text-white text-xl">🍎</span>
                          </div>
                          <span className="font-semibold text-gray-900">Apple Pay</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Google Pay */}
                  <div 
                    className={`bg-white rounded-lg p-6 shadow-sm border-2 transition-all cursor-pointer ${
                      selectedPaymentMethod === 'google_pay' ? 'border-[#3E2F2A]' : 'border-gray-200'
                    }`}
                    onClick={() => setSelectedPaymentMethod('google_pay')}
                  >
                    <div className="flex items-center gap-4">
                      <input 
                        type="radio" 
                        checked={selectedPaymentMethod === 'google_pay'}
                        onChange={() => setSelectedPaymentMethod('google_pay')}
                        className="w-5 h-5"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-white border border-gray-300 rounded flex items-center justify-center">
                            <span className="text-lg font-bold text-blue-600">G</span>
                          </div>
                          <span className="font-semibold text-gray-900">Google Pay</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Cash on Delivery */}
                  <div 
                    className={`bg-white rounded-lg p-6 shadow-sm border-2 transition-all cursor-pointer ${
                      selectedPaymentMethod === 'cod' ? 'border-[#3E2F2A]' : 'border-gray-200'
                    }`}
                    onClick={() => setSelectedPaymentMethod('cod')}
                  >
                    <div className="flex items-center gap-4">
                      <input 
                        type="radio" 
                        checked={selectedPaymentMethod === 'cod'}
                        onChange={() => setSelectedPaymentMethod('cod')}
                        className="w-5 h-5"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                          </svg>
                          <div>
                            <span className="font-semibold text-gray-900 block">Cash on Delivery</span>
                            <span className="text-sm text-gray-600">Pay when you receive</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Bank Transfer */}
                  <div 
                    className={`bg-white rounded-lg p-6 shadow-sm border-2 transition-all cursor-pointer ${
                      selectedPaymentMethod === 'bank_transfer' ? 'border-[#3E2F2A]' : 'border-gray-200'
                    }`}
                    onClick={() => setSelectedPaymentMethod('bank_transfer')}
                  >
                    <div className="flex items-center gap-4">
                      <input 
                        type="radio" 
                        checked={selectedPaymentMethod === 'bank_transfer'}
                        onChange={() => setSelectedPaymentMethod('bank_transfer')}
                        className="w-5 h-5"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <svg className="w-6 h-6 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
                          </svg>
                          <div>
                            <span className="font-semibold text-gray-900 block">Bank Transfer</span>
                            <span className="text-sm text-gray-600">Direct bank transfer</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {currentStep === 3 && (
                <div className="bg-white rounded-lg p-6">
                  <h2 className="text-lg font-semibold mb-6">Review Order</h2>
                  
                  {/* Selected Address */}
                  <div className="mb-6">
                    <h3 className="text-md font-medium mb-3">Delivery Address</h3>
                    {selectedAddressId && addresses.find(addr => addr.id === selectedAddressId) && (
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <div className="font-medium">{addresses.find(addr => addr.id === selectedAddressId).name}</div>
                        <div className="text-gray-600">{addresses.find(addr => addr.id === selectedAddressId).address}</div>
                        <div className="text-gray-600">{addresses.find(addr => addr.id === selectedAddressId).city}, {addresses.find(addr => addr.id === selectedAddressId).country}</div>
                        <div className="text-gray-600">{addresses.find(addr => addr.id === selectedAddressId).phone}</div>
                      </div>
                    )}
                  </div>

                  {/* Selected Payment Method */}
                  <div className="mb-6">
                    <h3 className="text-md font-medium mb-3">Payment Method</h3>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="font-medium">
                        {selectedPaymentMethod === 'card' && 'Credit/Debit Card'}
                        {selectedPaymentMethod === 'cod' && 'Cash on Delivery'}
                        {selectedPaymentMethod === 'bank_transfer' && 'Bank Transfer'}
                        {!selectedPaymentMethod && 'Not selected'}
                      </div>
                    </div>
                  </div>

                  {/* Order Items */}
                  <div className="mb-6">
                    <h3 className="text-md font-medium mb-4">Order Items ({cartItems.length})</h3>
                    <div className="space-y-4">
                      {cartItems.map((item, index) => {
                        const itemPrice = typeof item.price === 'string' 
                          ? parseFloat(item.price.replace(/[₹$,\s]/g, ''))
                          : item.price;
                        
                        return (
                          <div key={index} className="flex items-center gap-4 p-4 border border-gray-200 rounded-lg">
                            {/* Product Image */}
                            <div className="w-20 h-20 flex-shrink-0">
                              <img 
                                src={item.image || '/images/placeholder-product.jpg'} 
                                alt={item.name}
                                className="w-full h-full object-cover rounded-md"
                                onError={(e) => {
                                  e.target.src = '/images/placeholder-product.jpg';
                                }}
                              />
                            </div>
                            
                            {/* Product Details */}
                            <div className="flex-grow">
                              <h4 className="font-medium text-gray-900">{item.name}</h4>
                              <p className="text-sm text-gray-600 mt-1">
                                {item.description || 'Beautiful jewelry piece crafted with care'}
                              </p>
                              <div className="flex items-center gap-4 mt-2">
                                <span className="text-sm text-gray-600">Qty: {item.quantity}</span>
                                <span className="text-sm font-medium text-gray-900">
                                  ${itemPrice.toFixed(2)} each
                                </span>
                              </div>
                            </div>
                            
                            {/* Item Total */}
                            <div className="text-right">
                              <div className="font-semibold text-gray-900">
                                ${(itemPrice * item.quantity).toFixed(2)}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Order Summary in Review */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="text-md font-medium mb-3">Order Summary</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Subtotal</span>
                        <span className="font-medium">${subtotal.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Taxes (7%)</span>
                        <span className="font-medium">${taxes.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Delivery Fee</span>
                        <span className="font-medium text-green-600">
                          {deliveryFee === 0 ? 'FREE' : `$${deliveryFee.toFixed(2)}`}
                        </span>
                      </div>
                      <div className="border-t pt-2 mt-2">
                        <div className="flex justify-between text-lg font-semibold">
                          <span>Total</span>
                          <span>${grandTotal.toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Right - Order Summary */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg p-6 shadow-sm sticky top-4">
                <h3 className="text-lg font-semibold mb-4">Order Summary</h3>
                
                <div className="space-y-3 mb-6">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Subtotal</span>
                    <span className="font-medium">${subtotal.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Taxes</span>
                    <span className="font-medium">${taxes.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Delivery Fee</span>
                    <span className="font-medium text-green-600">
                      {deliveryFee === 0 ? 'FREE' : `$${deliveryFee.toFixed(2)}`}
                    </span>
                  </div>
                  <div className="border-t pt-3">
                    <div className="flex justify-between">
                      <span className="font-semibold text-lg">Grand Total</span>
                      <span className="font-bold text-lg">${grandTotal.toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                <button 
                  onClick={handleContinue}
                  className="w-full bg-[#3E2F2A] text-white py-3 rounded font-medium hover:bg-[#2d2219] transition-colors"
                >
                  CONTINUE
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Add Address Modal */}
      {showAddAddressModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Add New Address</h2>
              <button
                onClick={() => setShowAddAddressModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleAddAddress} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={newAddress.name}
                  onChange={(e) => setNewAddress({...newAddress, name: e.target.value})}
                  className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#3E2F2A]"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
                <input
                  type="tel"
                  value={newAddress.phone}
                  onChange={(e) => setNewAddress({...newAddress, phone: e.target.value})}
                  className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#3E2F2A]"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
                <input
                  type="text"
                  value={newAddress.address}
                  onChange={(e) => setNewAddress({...newAddress, address: e.target.value})}
                  className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#3E2F2A]"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
                <select
                  value={newAddress.city}
                  onChange={(e) => setNewAddress({...newAddress, city: e.target.value})}
                  className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#3E2F2A]"
                  required
                >
                  <option value="">Select City</option>
                  <option value="New Mexico">New Mexico</option>
                  <option value="New York">New York</option>
                  <option value="California">California</option>
                  <option value="Texas">Texas</option>
                  <option value="Florida">Florida</option>
                </select>
              </div>

              <button
                type="submit"
                className="w-full bg-[#3E2F2A] text-white py-3 rounded font-medium hover:bg-[#2d2219] transition-colors"
              >
                ADD ADDRESS
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Checkout;