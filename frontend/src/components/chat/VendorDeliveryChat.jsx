import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import VendorDeliveryChatInterface from './VendorDeliveryChatInterface';

const VendorDeliveryChat = () => {
  const { user } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedChat, setSelectedChat] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchConversations();
    // Auto-refresh conversations every 10 seconds
    const interval = setInterval(fetchConversations, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchConversations = async () => {
    try {
      setRefreshing(true);
      const response = await api.get('/api/chat/vendor-delivery/conversations');
      setConversations(response.data.conversations || []);
    } catch (error) {
      console.error('Error fetching vendor-delivery conversations:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleChatSelect = (conversation) => {
    setSelectedChat(conversation);
    // Mark messages as read when opening chat
    markAsRead(conversation.order_id);
  };

  const markAsRead = async (orderId) => {
    try {
      // This would typically be handled when viewing messages
      await fetchConversations(); // Refresh to update unread counts
    } catch (error) {
      console.error('Error marking as read:', error);
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = diffMs / (1000 * 60 * 60);
    const diffDays = diffMs / (1000 * 60 * 60 * 24);

    if (diffHours < 1) {
      return Math.floor(diffMs / (1000 * 60)) + 'm ago';
    } else if (diffHours < 24) {
      return Math.floor(diffHours) + 'h ago';
    } else if (diffDays < 7) {
      return Math.floor(diffDays) + 'd ago';
    } else {
      return date.toLocaleDateString();
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'shipped': return 'bg-purple-100 text-purple-800';
      case 'out_for_delivery': return 'bg-orange-100 text-orange-800';
      case 'delivered': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (selectedChat) {
    return (
      <VendorDeliveryChatInterface
        orderId={selectedChat.order_id}
        recipientId={selectedChat.recipient_id}
        recipientName={selectedChat.recipient_name}
        onClose={() => setSelectedChat(null)}
      />
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading vendor-delivery conversations...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg h-[600px] flex flex-col">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-blue-600 text-white p-4 rounded-t-lg flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold flex items-center">
            <span className="mr-2">🏭</span>
            <span className="mr-2">↔️</span>
          </h2>
          <p className="text-sm opacity-90">
            {user?.role === 'vendor' ? 'Chat with delivery partners' : 'Chat with vendors for pickup'}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={fetchConversations}
            disabled={refreshing}
            className="text-white hover:text-gray-200 disabled:opacity-50"
          >
            <svg 
              className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <div className="text-6xl mb-4 flex items-center">
              <span>🏭</span>
              <span className="mx-2">💬</span>
            </div>
            <h3 className="text-lg font-medium mb-2">No pickup conversations available</h3>
            <p className="text-sm text-center px-4">
              {user?.role === 'vendor' 
                ? 'Assign delivery boys to orders to start pickup coordination' 
                : 'Wait for orders to be assigned to you for pickup coordination'
              }
            </p>
            <div className="mt-4 text-xs text-gray-400">
              {user?.role === 'vendor' 
                ? 'Go to Orders → Assign Delivery Boy to create conversations' 
                : 'Conversations will appear when vendors assign orders to you'
              }
            </div>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {conversations.map((conversation) => (
              <div
                key={conversation.order_id}
                onClick={() => handleChatSelect(conversation)}
                className="p-4 hover:bg-gray-50 cursor-pointer transition-colors border-l-4 border-l-blue-500"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="text-sm font-medium text-gray-900 truncate flex items-center">
                        {user?.role === 'vendor' ? (
                          <span className="mr-2">🚚</span>
                        ) : (
                          <span className="mr-2">🏭</span>
                        )}
                        {conversation.recipient_name}
                      </h3>
                      <div className="flex items-center space-x-2">
                        {conversation.unread_count > 0 && (
                          <span className="bg-red-500 text-white text-xs rounded-full px-2 py-1 min-w-[20px] text-center">
                            {conversation.unread_count}
                          </span>
                        )}
                        <span className="text-xs text-gray-500">
                          {formatTimestamp(conversation.last_timestamp)}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <p className="text-sm text-gray-600 truncate max-w-[200px]">
                        {conversation.last_message}
                      </p>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(conversation.order_status)}`}>
                          {conversation.order_status?.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-xs text-gray-500">
                        Order: {conversation.order_number}
                      </span>
                      <span className="text-xs text-green-600 font-medium">
                        📦 Pickup Chat
                      </span>
                    </div>
                  </div>
                  
                  <div className="ml-4">
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-gray-200 p-3 bg-gray-50 rounded-b-lg">
        <div className="text-xs text-center text-gray-500 flex items-center justify-center">
          <span className="mr-2">📞</span>
          Pickup coordination messages - Auto-refresh every 10 seconds
        </div>
      </div>
    </div>
  );
};

export default VendorDeliveryChat;