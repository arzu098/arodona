import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import api from '../services/api';

function Checkout() {
  const navigate = useNavigate();
  const { cartItems, getCartTotal } = useCart();
  const [currentStep, setCurrentStep] = useState(1); // 1: Address, 2: Payment, 3: Review
  const [addresses, setAddresses] = useState([]);
  const [selectedAddressId, setSelectedAddressId] = useState(null);
  const [showAddAddressModal, setShowAddAddressModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  const handleContinue = () => {
    if (currentStep === 1 && !selectedAddressId) {
      alert('Please select a delivery address');
      return;
    }
    
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    } else {
      // Place order
      alert('Order placement functionality coming soon!');
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
                <div className="bg-white rounded-lg p-6">
                  <h2 className="text-lg font-semibold mb-4">Payment Method</h2>
                  <p className="text-gray-600">Payment methods will be available here.</p>
                </div>
              )}

              {currentStep === 3 && (
                <div className="bg-white rounded-lg p-6">
                  <h2 className="text-lg font-semibold mb-4">Review Order</h2>
                  <p className="text-gray-600">Order review will be available here.</p>
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