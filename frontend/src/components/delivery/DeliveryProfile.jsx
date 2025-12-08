import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import ErrorBoundary from '../ErrorBoundary';

const DeliveryProfile = () => {
  const { user, logout } = useAuth();
  const [profile, setProfile] = useState({
    name: '',
    phone: '',
    email: '',
    address: '',
    aadhar_number: '',
    driving_license: '',
    vehicle_number: '',
    vehicle_type: '',
    bank_account: '',
    ifsc_code: '',
    emergency_contact: '',
    emergency_phone: '',
    profile_image: '',
    documents: []
  });
  const [stats, setStats] = useState({
    total_deliveries: 0,
    successful_deliveries: 0,
    rating: 0,
    earnings_this_month: 0,
    earnings_total: 0,
    efficiency_score: 0
  });
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [showDocuments, setShowDocuments] = useState(false);

  useEffect(() => {
    // Check if user is authenticated and has delivery_boy role
    if (!user) {
      setLoading(false);
      return;
    }

    if (user.role !== 'delivery_boy') {
      console.error('Access denied: User is not a delivery boy', { userRole: user.role });
      setLoading(false);
      return;
    }

    fetchProfile();
  }, [user]);

  const fetchProfile = async () => {
    try {
      const [profileResponse, statsResponse] = await Promise.all([
        api.get('/api/delivery/profile'),
        api.get('/api/delivery/dashboard-stats')
      ]);
      setProfile(profileResponse.data.data || profileResponse.data);
      setStats(statsResponse.data);
    } catch (error) {
      console.error('Error fetching profile:', error);
      // Handle authentication errors
      if (error.status === 401 || error.status === 404) {
        setProfile(null);
        setStats(null);
        return;
      }
      setProfile(null);
      setStats(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    try {
      console.log('Sending profile data:', profile);
      
      // Clean the profile data - remove empty strings and unnecessary fields
      const cleanProfile = {};
      Object.keys(profile).forEach(key => {
        if (profile[key] !== '' && profile[key] !== null && profile[key] !== undefined) {
          // Skip fields that shouldn't be updated
          if (!['_id', 'id', 'role', 'hashed_password', 'created_at', 'updated_at'].includes(key)) {
            cleanProfile[key] = profile[key];
          }
        }
      });
      
      console.log('Clean profile data:', cleanProfile);
      
      const response = await api.put('/api/delivery/profile', cleanProfile);
      console.log('Profile update response:', response.data);
      
      setEditing(false);
      alert('Profile updated successfully!');
    } catch (error) {
      console.error('Error updating profile:', error);
      
      // More detailed error message
      if (error.response) {
        console.error('Error response:', error.response.data);
        alert(`Error updating profile: ${error.response.data.detail || 'Unknown error'}`);
      } else {
        alert('Error updating profile: Network error or server unavailable');
      }
    }
  };

  const handleInputChange = (field, value) => {
    setProfile(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const getDocumentStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'verified': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getDocumentStatusText = (status) => {
    switch (status?.toLowerCase()) {
      case 'verified': return 'Verified';
      case 'pending': return 'Under Review';
      case 'rejected': return 'Rejected';
      default: return 'Unknown';
    }
  };

  // Check if user is not authenticated
  if (!user) {
    return (
      <div className="min-h-screen bg-[#F4E7D0] flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-red-600 mb-4">Please log in to access the delivery profile</div>
          <button 
            onClick={() => window.location.href = '/login'}
            className="bg-[#3E2F2A] text-white px-4 py-2 rounded hover:bg-opacity-80"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  // Check if user has the correct role
  if (user.role !== 'delivery_boy') {
    return (
      <div className="min-h-screen bg-[#F4E7D0] flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-red-600 mb-4">
            Access Denied: This page is only for delivery boys
          </div>
          <div className="text-gray-600 mb-4">
            Current role: {user.role || 'Unknown'}
          </div>
          <button 
            onClick={() => window.history.back()}
            className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F4E7D0] flex items-center justify-center">
        <div className="text-xl text-[#3E2F2A]">Loading profile...</div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="min-h-screen bg-[#F4E7D0] flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-red-600 mb-4">Could not load delivery profile. Please try again or contact support.</div>
          <button 
            onClick={() => window.location.reload()}
            className="bg-[#3E2F2A] text-white px-4 py-2 rounded hover:bg-opacity-80"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
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
                <h1 className="text-xl font-bold">My Profile</h1>
                <p className="text-yellow-400 text-sm">Personal Information & Settings</p>
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
              <Link to="/delivery/orders" className="hover:text-yellow-400 transition-colors">
                Order List
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
             
              <Link to="/delivery/orders" className="block py-2 hover:text-yellow-400 transition-colors">
                Order List
              </Link>
              <button onClick={logout} className="block py-2 hover:text-yellow-400 transition-colors w-full text-left">
                Logout
              </button>
            </nav>
          )}
        </header>

        <div className="p-6">
         

          {/* Profile Information */}
          <div className="bg-white rounded-lg shadow-md">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold text-[#3E2F2A]">Personal Information</h2>
                <button
                  onClick={() => editing ? handleSaveProfile() : setEditing(true)}
                  className={`px-6 py-2 rounded-lg transition-colors ${
                    editing 
                      ? 'bg-green-600 hover:bg-green-700 text-white' 
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  }`}
                >
                  {editing ? '💾 Save' : '✏️ Edit'}
                </button>
              </div>
            </div>

            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Personal Details */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-[#3E2F2A] mb-4">Personal Details</h3>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                    {editing ? (
                      <input
                        type="text"
                        value={profile.name}
                        onChange={(e) => handleInputChange('name', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    ) : (
                      <p className="text-gray-900">{profile.name}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
                    {editing ? (
                      <input
                        type="tel"
                        value={profile.phone}
                        onChange={(e) => handleInputChange('phone', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    ) : (
                      <p className="text-gray-900">{profile.phone}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    {editing ? (
                      <input
                        type="email"
                        value={profile.email}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    ) : (
                      <p className="text-gray-900">{profile.email}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
                    {editing ? (
                      <textarea
                        value={profile.address}
                        onChange={(e) => handleInputChange('address', e.target.value)}
                        rows="3"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    ) : (
                      <p className="text-gray-900">{profile.address}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Aadhar Number</label>
                    {editing ? (
                      <input
                        type="text"
                        value={profile.aadhar_number}
                        onChange={(e) => handleInputChange('aadhar_number', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    ) : (
                      <p className="text-gray-900">{profile.aadhar_number}</p>
                    )}
                  </div>
                </div>

                {/* Emergency Contact */}
                <div className="md:col-span-2 space-y-4">
                  <h3 className="text-lg font-semibold text-[#3E2F2A] mb-4">Emergency Contact</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Emergency Contact Person</label>
                      {editing ? (
                        <input
                          type="text"
                          value={profile.emergency_contact}
                          onChange={(e) => handleInputChange('emergency_contact', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      ) : (
                        <p className="text-gray-900">{profile.emergency_contact}</p>
                      )}
                    </div>

                    <div>
          
                      {editing ? (
                        <input
                          type="tel"
                          value={profile.emergency_phone}
                          onChange={(e) => handleInputChange('emergency_phone', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      ) : (
                        <p className="text-gray-900">{profile.emergency_phone}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {editing && (
                <div className="mt-6 pt-4 border-t flex space-x-4">
                  <button
                    onClick={handleSaveProfile}
                    className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors"
                  >
                    💾 Save
                  </button>
                  <button
                    onClick={() => setEditing(false)}
                    className="bg-gray-300 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-400 transition-colors"
                  >
                    ❌ Cancel
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default DeliveryProfile;