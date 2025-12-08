import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import ChatList from './chat/ChatList';
import VendorDeliveryChat from './chat/VendorDeliveryChat';

const ChatHub = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('customer-delivery');

  // Determine which chat types are available based on user role
  const availableTabs = [];

  // Customer can chat with delivery boys
  if (user?.role === 'customer') {
    availableTabs.push({
      id: 'customer-delivery',
      name: 'Delivery Chat',
      icon: '🚚',
      description: 'Chat with delivery partners'
    });
  }

  // Delivery boy can chat with both customers and vendors
  if (user?.role === 'delivery_boy') {
    availableTabs.push({
      id: 'customer-delivery',
      name: 'Customer Chat',
      icon: '👥',
      description: 'Chat with customers'
    });
    availableTabs.push({
      id: 'vendor-delivery',
      name: 'Pickup Chat',
      icon: '🏭',
      description: 'Chat with vendors for pickup'
    });
  }

  // Vendor can chat with delivery boys
  if (user?.role === 'vendor') {
    availableTabs.push({
      id: 'vendor-delivery',
      name: 'Pickup Chat',
      icon: '🚚',
      description: 'Chat with delivery partners for pickup'
    });
  }

  // If no tabs available, show access denied
  if (availableTabs.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <div className="text-6xl mb-4">🚫</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Chat Access Denied</h2>
            <p className="text-gray-600">
              Chat functionality is available for customers, vendors, and delivery partners only.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const renderChatComponent = () => {
    switch (activeTab) {
      case 'customer-delivery':
        return <ChatList />;
      case 'vendor-delivery':
        return <VendorDeliveryChat />;
      default:
        return <ChatList />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                  <span className="mr-3">💬</span>
                  Chat Hub
                </h1>
                <p className="mt-2 text-gray-600">
                  Communicate with your partners and coordinate orders
                </p>
              </div>
              
              {/* User role indicator */}
              <div className="bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium">
                {user?.role === 'delivery_boy' ? 'Delivery Partner' : 
                 user?.role === 'vendor' ? 'Vendor' : 
                 user?.role === 'customer' ? 'Customer' : user?.role}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        {availableTabs.length > 1 && (
          <div className="mb-8">
            <nav className="flex space-x-8" aria-label="Chat Types">
              {availableTabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center px-6 py-3 rounded-lg font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'bg-blue-100 text-blue-700 border-2 border-blue-300'
                      : 'bg-white text-gray-600 border-2 border-gray-200 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <span className="mr-2 text-lg">{tab.icon}</span>
                  <div className="text-left">
                    <div className="font-semibold">{tab.name}</div>
                    <div className="text-xs opacity-75">{tab.description}</div>
                  </div>
                </button>
              ))}
            </nav>
          </div>
        )}

        {/* Chat Component */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="border-b border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                <span className="mr-2">
                  {availableTabs.find(tab => tab.id === activeTab)?.icon}
                </span>
                {availableTabs.find(tab => tab.id === activeTab)?.name}
              </h2>
              <div className="text-sm text-gray-500">
                {availableTabs.find(tab => tab.id === activeTab)?.description}
              </div>
            </div>
          </div>
          
          <div className="p-6">
            {renderChatComponent()}
          </div>
        </div>

       
      </div>
    </div>
  );
};

export default ChatHub;