import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import vendorService from '../../services/vendorService';

const VendorProfile = () => {
  const { user, logout } = useAuth();
  const [vendorProfile, setVendorProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('business'); // business, storefront, documents
  
  const [formData, setFormData] = useState({
    business_name: '',
    business_type: '',
    business_description: '',
    contact_email: '',
    contact_phone: '',
    website_url: '',
    business_address: {
      street: '',
      city: '',
      state: '',
      postal_code: '',
      country: ''
    },
    tax_id: '',
    bank_details: {
      account_holder_name: '',
      account_number: '',
      bank_name: '',
      ifsc_code: ''
    }
  });

  const [storefrontData, setStorefrontData] = useState({
    store_name: '',
    store_description: '',
    banner_image: '',
    logo_image: '',
    social_links: {
      facebook: '',
      instagram: '',
      twitter: '',
      pinterest: ''
    }
  });

  useEffect(() => {
    fetchVendorProfile();
  }, []);

  const fetchVendorProfile = async () => {
    try {
      const vendor = await vendorService.getMyProfile();
      setVendorProfile(vendor);
      
      // Populate form data
      setFormData({
        business_name: vendor.business_name || '',
        business_type: vendor.business_type || '',
        business_description: vendor.business_description || '',
        contact_email: vendor.contact_email || '',
        contact_phone: vendor.contact_phone || '',
        website_url: vendor.website_url || '',
        business_address: vendor.business_address || {
          street: '',
          city: '',
          state: '',
          postal_code: '',
          country: ''
        },
        tax_id: vendor.tax_id || '',
        bank_details: vendor.bank_details || {
          account_holder_name: '',
          account_number: '',
          bank_name: '',
          ifsc_code: ''
        }
      });

      // Fetch storefront data separately
      try {
        const storefront = await vendorService.getMyStorefront();
        setStorefrontData({
          store_name: storefront.store_name || vendor.business_name || '',
          store_description: storefront.store_description || '',
          banner_image: storefront.banner_image || '',
          logo_image: storefront.logo_image || '',
          social_links: storefront.social_links || {
            facebook: '',
            instagram: '',
            twitter: '',
            pinterest: ''
          }
        });
      } catch (storefrontError) {
        console.error('Error fetching storefront:', storefrontError);
        // Use vendor data as fallback
        setStorefrontData({
          store_name: vendor.store_name || vendor.business_name || '',
          store_description: vendor.store_description || '',
          banner_image: vendor.banner_image || '',
          logo_image: vendor.logo_image || '',
          social_links: vendor.social_links || {
            facebook: '',
            instagram: '',
            twitter: '',
            pinterest: ''
          }
        });
      }
    } catch (error) {
      console.error('Error fetching vendor profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    if (name.includes('.')) {
      const [parent, child] = name.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value
        }
      }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleStorefrontChange = (e) => {
    const { name, value } = e.target;
    if (name.includes('.')) {
      const [parent, child] = name.split('.');
      setStorefrontData(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value
        }
      }));
    } else {
      setStorefrontData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      await vendorService.updateMyProfile(formData);
      alert('Profile updated successfully');
      fetchVendorProfile();
    } catch (error) {
      console.error('Error updating profile:', error);
      alert('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateStorefront = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      await vendorService.updateMyStorefront(storefrontData);
      alert('Storefront updated successfully');
      fetchVendorProfile();
    } catch (error) {
      console.error('Error updating storefront:', error);
      alert('Failed to update storefront');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl">Loading profile...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <img src="/Images/1000017875-removebg-preview 9.jpg" alt="Vendor Logo" className="w-12 h-12 object-contain mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Vendor Profile</h1>
                <p className="text-sm text-gray-600">{vendorProfile?.business_name}</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                to="/vendor/dashboard"
                className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300 transition-colors"
              >
                ← Back to Dashboard
              </Link>
              <button
                onClick={logout}
                className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Status Alert */}
        <div className={`mb-6 p-4 rounded-lg ${
          vendorProfile?.status === 'approved'
            ? 'bg-green-50 border border-green-200'
            : vendorProfile?.status === 'pending'
            ? 'bg-yellow-50 border border-yellow-200'
            : 'bg-red-50 border border-red-200'
        }`}>
          <p className={`text-sm font-medium ${
            vendorProfile?.status === 'approved'
              ? 'text-green-800'
              : vendorProfile?.status === 'pending'
              ? 'text-yellow-800'
              : 'text-red-800'
          }`}>
            Status: {vendorProfile?.status?.toUpperCase()}
          </p>
        </div>

        {/* Tabs */}
        <div className="bg-white shadow rounded-lg mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('business')}
                className={`px-6 py-4 text-sm font-medium border-b-2 ${
                  activeTab === 'business'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Business Information
              </button>
              <button
                onClick={() => setActiveTab('storefront')}
                className={`px-6 py-4 text-sm font-medium border-b-2 ${
                  activeTab === 'storefront'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Storefront
              </button>
              <button
                onClick={() => setActiveTab('documents')}
                className={`px-6 py-4 text-sm font-medium border-b-2 ${
                  activeTab === 'documents'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Documents
              </button>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'business' && (
          <div className="bg-white shadow rounded-lg p-6">
            <form onSubmit={handleUpdateProfile} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Business Name *
                  </label>
                  <input
                    type="text"
                    name="business_name"
                    value={formData.business_name}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Business Type
                  </label>
                  <select
                    name="business_type"
                    value={formData.business_type}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select Type</option>
                    <option value="manufacturer">Manufacturer</option>
                    <option value="wholesaler">Wholesaler</option>
                    <option value="retailer">Retailer</option>
                    <option value="artisan">Artisan</option>
                  </select>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Business Description
                  </label>
                  <textarea
                    name="business_description"
                    value={formData.business_description}
                    onChange={handleInputChange}
                    rows="4"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  ></textarea>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Contact Email *
                  </label>
                  <input
                    type="email"
                    name="contact_email"
                    value={formData.contact_email}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Contact Phone *
                  </label>
                  <input
                    type="tel"
                    name="contact_phone"
                    value={formData.contact_phone}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Website URL
                  </label>
                  <input
                    type="url"
                    name="website_url"
                    value={formData.website_url}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="border-t pt-6">
                <h3 className="text-lg font-semibold mb-4">Business Address</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Street Address
                    </label>
                    <input
                      type="text"
                      name="business_address.street"
                      value={formData.business_address.street}
                      onChange={handleInputChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      City
                    </label>
                    <input
                      type="text"
                      name="business_address.city"
                      value={formData.business_address.city}
                      onChange={handleInputChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      State
                    </label>
                    <input
                      type="text"
                      name="business_address.state"
                      value={formData.business_address.state}
                      onChange={handleInputChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Postal Code
                    </label>
                    <input
                      type="text"
                      name="business_address.postal_code"
                      value={formData.business_address.postal_code}
                      onChange={handleInputChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Country
                    </label>
                    <input
                      type="text"
                      name="business_address.country"
                      value={formData.business_address.country}
                      onChange={handleInputChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-4 pt-6 border-t">
                <button
                  type="button"
                  onClick={fetchVendorProfile}
                  className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        )}

        {activeTab === 'storefront' && (
          <div className="bg-white shadow rounded-lg p-6">
            <form onSubmit={handleUpdateStorefront} className="space-y-6">
              <div className="grid grid-cols-1 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Store Name
                  </label>
                  <input
                    type="text"
                    name="store_name"
                    value={storefrontData.store_name}
                    onChange={handleStorefrontChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Store Description
                  </label>
                  <textarea
                    name="store_description"
                    value={storefrontData.store_description}
                    onChange={handleStorefrontChange}
                    rows="4"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  ></textarea>
                </div>

                <div className="border-t pt-6">
                  <h3 className="text-lg font-semibold mb-4">Social Media Links</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Facebook
                      </label>
                      <input
                        type="url"
                        name="social_links.facebook"
                        value={storefrontData.social_links.facebook}
                        onChange={handleStorefrontChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Instagram
                      </label>
                      <input
                        type="url"
                        name="social_links.instagram"
                        value={storefrontData.social_links.instagram}
                        onChange={handleStorefrontChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Twitter
                      </label>
                      <input
                        type="url"
                        name="social_links.twitter"
                        value={storefrontData.social_links.twitter}
                        onChange={handleStorefrontChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Pinterest
                      </label>
                      <input
                        type="url"
                        name="social_links.pinterest"
                        value={storefrontData.social_links.pinterest}
                        onChange={handleStorefrontChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-4 pt-6 border-t">
                <button
                  type="button"
                  onClick={fetchVendorProfile}
                  className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {saving ? 'Saving...' : 'Save Storefront'}
                </button>
              </div>
            </form>
          </div>
        )}

        {activeTab === 'documents' && (
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Business Documents</h3>
            <p className="text-gray-600 mb-6">
              Upload required business documents for verification. All documents should be in PDF, JPG, or PNG format.
            </p>
            
            <div className="space-y-4">
              <div className="border rounded-lg p-4">
                <h4 className="font-medium mb-2">Business License</h4>
                <p className="text-sm text-gray-600 mb-3">Upload your business registration or license</p>
                <input type="file" accept=".pdf,.jpg,.jpeg,.png" className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
              </div>

              <div className="border rounded-lg p-4">
                <h4 className="font-medium mb-2">Tax Certificate</h4>
                <p className="text-sm text-gray-600 mb-3">Upload your GST or tax registration certificate</p>
                <input type="file" accept=".pdf,.jpg,.jpeg,.png" className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
              </div>

              <div className="border rounded-lg p-4">
                <h4 className="font-medium mb-2">Identity Proof</h4>
                <p className="text-sm text-gray-600 mb-3">Upload government-issued ID (Aadhar, PAN, Passport)</p>
                <input type="file" accept=".pdf,.jpg,.jpeg,.png" className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
              </div>

              <div className="border rounded-lg p-4">
                <h4 className="font-medium mb-2">Address Proof</h4>
                <p className="text-sm text-gray-600 mb-3">Upload utility bill or rental agreement</p>
                <input type="file" accept=".pdf,.jpg,.jpeg,.png" className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VendorProfile;
