import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';

const VendorDeliveryChatInterface = ({ orderId, recipientId, recipientName, onClose, onUnreadCountChange }) => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [typing, setTyping] = useState(false);
  const [orderDetails, setOrderDetails] = useState(null);
  const [showLocationShare, setShowLocationShare] = useState(false); // Not fully implemented in UI but kept for future
  const [showQuickReplies, setShowQuickReplies] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  // Quick reply templates for Vendors
  const vendorQuickReplies = [
    "📦 Package is ready for pickup",
    "🚪 Please come to Gate 3",
    "⏱️ Packaging will be complete in 10 minutes",
    "📋 Waiting for the final label",
    "📍 I'm at the loading dock",
    "✅ Order is packed and ready",
    "🔄 Please wait, preparing your order"
  ];

  // Quick reply templates for Delivery Boys
  const deliveryBoyQuickReplies = [
    "🚗 I am arriving in 5 minutes for pickup",
    "📦 Is the package ready for Order?",
    "🚪 Please confirm the exact pickup gate/dock",
    "🚦 Facing traffic, will be slightly delayed",
    "📍 I'm at your location, where should I come?",
    "✅ Package picked up successfully",
    "❓ Having trouble locating the pickup point"
  ];

  const getQuickReplies = () => {
    return user?.role === 'vendor' ? vendorQuickReplies : deliveryBoyQuickReplies;
  };

  useEffect(() => {
    fetchOrderDetails();
    fetchMessages();
    // Set up real-time messaging (polling every 3 seconds for pickup coordination)
    const interval = setInterval(fetchMessages, 3000);
    return () => clearInterval(interval);
  }, [orderId]);

  // Notify parent component of unread count changes
  useEffect(() => {
    if (onUnreadCountChange) {
      onUnreadCountChange(unreadCount);
    }
  }, [unreadCount, onUnreadCountChange]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchOrderDetails = async () => {
    try {
      const response = await api.get(`/api/orders/${orderId}`);
      setOrderDetails(response.data);
    } catch (error) {
      console.error('Error fetching order details:', error);
    }
  };

  const fetchMessages = async () => {
    try {
      const currentUserId = user.user_id || user.sub || user.id || user._id;
      const response = await api.get(`/api/chat/vendor-delivery/messages/${orderId}`);
      const fetchedMessages = response.data.messages || [];
      setMessages(fetchedMessages);

      // Calculate unread messages (messages not sent by current user and not read)
      const unreadMessages = fetchedMessages.filter(msg => {
        const isNotSentByCurrentUser = msg.sender_id !== currentUserId;
        const isUnread = msg.status !== 'read';
        const isCorrectRecipient = (
          (user.role === 'vendor' && msg.sender_type === 'delivery') ||
          (user.role === 'delivery' && msg.sender_type === 'vendor')
        );
        
        return isNotSentByCurrentUser && isUnread && isCorrectRecipient;
      });
      setUnreadCount(unreadMessages.length);

      // Mark messages as read for incoming messages
      if (fetchedMessages.length > 0) {
        markMessagesAsRead(fetchedMessages);
      }
    } catch (error) {
      console.error('Error fetching vendor-delivery messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const markMessagesAsRead = async (messages) => {
    try {
      const userId = user?.user_id || user?.sub;
      const userRole = user?.role;

      if (!userId || !userRole) return;

      // Only mark messages as read that were sent TO the current user
      const unreadMessages = messages.filter(msg => {
        const isNotSentByCurrentUser = msg.sender_id !== userId;
        const isUnread = msg.status !== 'read';
        const isCorrectRecipient = (
          (userRole === 'vendor' && msg.sender_type === 'delivery_boy') ||
          (userRole === 'delivery_boy' && msg.sender_type === 'vendor')
        );

        return isNotSentByCurrentUser && isUnread && isCorrectRecipient;
      });

      // Simple implementation: Iterate and send patch request for each unread message
      for (const message of unreadMessages) {
        const msgId = message.id || message._id;
        if (msgId) {
          try {
            await api.patch(`/api/chat/vendor-delivery/messages/${msgId}/status`, {
              status: 'read'
            });

            // Update local state to show double ticks immediately
            setMessages(prev => prev.map(msg =>
              (msg.id === msgId || msg._id === msgId)
                ? { ...msg, status: 'read' }
                : msg
            ));
          } catch (error) {
            console.error(`Error marking message ${msgId} as read:`, error);
          }
        }
      }
      
      // Reset unread count after marking messages as read
      if (unreadMessages.length > 0) {
        setUnreadCount(0);
      }
    } catch (error) {
      console.error('Error marking messages as read:', error);
    }
  };

  const sendMessage = async (messageText = newMessage) => {
    if (!messageText.trim() || !user) return;

    // Get user ID with multiple fallbacks
    const currentUserId = user.user_id || user.sub || user.id || user._id;
    console.log('Delivery Chat SendMessage debug:', {
      user: user,
      currentUserId: currentUserId,
      user_id: user.user_id,
      sub: user.sub,
      id: user.id,
      _id: user._id
    });

    const tempMessage = {
      id: `temp-${Date.now()}`,
      order_id: orderId,
      sender_id: currentUserId,
      sender_type: user.role,
      message: messageText,
      timestamp: new Date().toISOString(),
      status: 'sending'
    };

    // Add message to UI immediately
    setMessages(prev => [...prev, tempMessage]);
    setNewMessage(''); // Clear input field

    // Scroll to bottom to show the new message immediately
    setTimeout(() => {
      scrollToBottom();
    }, 50);

    try {
      const response = await api.post('/api/chat/vendor-delivery/send-message', {
        order_id: orderId,
        message: messageText
      });

      // Update the message with server response - show single tick (sent/delivered)
      setMessages(prev => prev.map(msg =>
        msg.id === tempMessage.id
          ? { ...response.data, status: 'sent', id: response.data.id || response.data._id }
          : msg
      ));

      // Scroll to bottom to show the new message
      setTimeout(() => {
        scrollToBottom();
      }, 100);
    } catch (error) {
      console.error('Error sending vendor-delivery message:', error);
      // Mark message as failed but keep it visible
      setMessages(prev => prev.map(msg =>
        msg.id === tempMessage.id ? { ...msg, status: 'failed' } : msg
      ));
    }
  };

  const handleQuickReply = (reply) => {
    sendMessage(reply);
    setShowQuickReplies(false); // Hide quick replies after selection
  };

  const shareLocation = async () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          const locationMessage = `📍 My location: https://maps.google.com/?q=${latitude},${longitude}`;
          sendMessage(locationMessage);
        },
        (error) => {
          console.error('Error getting location:', error);
          alert('Unable to get location. Please ensure location permissions are enabled.');
        }
      );
    } else {
      alert('Geolocation is not supported by this browser.');
    }
  };

  const initiateCall = () => {
    // This would integrate with your existing call functionality
    // You would typically fetch the recipient's phone number here
    if (recipientName) {
      // Placeholder for call functionality
      alert(`Initiating call to ${recipientName}...`);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const renderReadReceipt = (status) => {
    switch (status) {
      case 'sending':
        return <span className="text-white/70">⏳</span>; // Sending
      case 'sent':
      case 'delivered':
        return <span className="text-white/80 text-sm">✓</span>; // Delivered (Single Tick)
      case 'read':
        return <span className="text-white font-bold text-base">✓✓</span>; // Read (Double Tick)
      case 'failed':
        return <span className="text-red-300">❌</span>; // Failed
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading pickup chat...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg border border-gray-200">
      {/* Chat Header */}
      <div className="bg-gradient-to-r from-green-600 to-blue-600 text-white p-4 rounded-t-lg">
        <div className="flex justify-between items-center">
          <div className="flex-1">
            <h3 className="font-semibold text-lg text-white flex items-center">
              <span className="mr-2">📦</span>
              Order #{orderDetails?.order_number || orderId.substring(0, 8)}
            </h3>
          </div>

          {/* Action buttons (Call and Close) */}
          <div className="flex items-center space-x-2">
            <button
              onClick={initiateCall}
              className="p-2 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
              title={`Call ${recipientName}`}
            >
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.408 5.408l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
              title="Close Chat"
            >
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Order status indicator */}
        <div className="mt-2 flex items-center text-sm">
          <span className="bg-white/20 px-2 py-1 rounded-full text-xs">
            {orderDetails?.status?.replace('_', ' ').toUpperCase() || 'PICKUP PENDING'}
          </span>
        </div>
      </div>

      {/* Quick Replies Section */}
      <div className="px-4 py-2 border-t border-gray-200 bg-white">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-600">Quick Replies:</span>
          <button
            onClick={() => setShowQuickReplies(!showQuickReplies)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            {showQuickReplies ? 'Hide' : 'Show All'}
          </button>
        </div>
        <div className="flex flex-wrap gap-2 max-h-24 overflow-y-auto">
          {(showQuickReplies ? getQuickReplies() : getQuickReplies().slice(0, 3)).map((reply, index) => (
            <button
              key={index}
              onClick={() => handleQuickReply(reply)}
              className={`px-3 py-1 rounded-full text-xs hover:shadow-sm transition-all whitespace-nowrap ${
                user?.role === 'vendor'
                  ? 'bg-green-100 text-green-700 hover:bg-green-200'
                  : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
              }`}
            >
              {reply}
            </button>
          ))}
        </div>
      </div>

      {/* Messages Container */}
      <div
        ref={chatContainerRef}
        className="flex-1 p-4 overflow-y-auto bg-gray-50"
      >
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <div className="text-4xl mb-4 flex justify-center items-center">
              <span className="mx-2">💬</span>
              <span>🚚</span>
            </div>
            <p className="text-gray-600 mb-4">Start pickup coordination with {recipientName}</p>
            <div className="text-sm text-gray-500 mb-6">
              Order: {orderDetails?.order_number || orderId?.substring(0, 8)}
            </div>
            <div className="max-w-md mx-auto">
              {/* Quick start buttons for empty state */}
              <div className="flex flex-wrap gap-2 justify-center mb-4">
                <button
                  onClick={() => handleQuickReply(user?.role === 'vendor' ? '📦 Package is ready for pickup' : '🚗 I am arriving in 5 minutes for pickup')}
                  className={`px-3 py-2 rounded-lg text-sm hover:shadow-sm transition-all ${
                    user?.role === 'vendor'
                      ? 'bg-green-100 text-green-700 hover:bg-green-200'
                      : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                  }`}
                >
                  {user?.role === 'vendor' ? '📦 Package Ready' : '🚗 Arriving Soon'}
                </button>
                <button
                  onClick={shareLocation} // Use shareLocation function
                  className={`px-3 py-2 rounded-lg text-sm hover:shadow-sm transition-all ${
                    user?.role === 'vendor'
                      ? 'bg-green-100 text-green-700 hover:bg-green-200'
                      : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                  }`}
                >
                  📍 Share Location
                </button>
              </div>
              <p className="text-xs text-gray-400">Click a quick reply or type your own message below</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => {
              // Force correct alignment based on message characteristics
              let isCurrentUserSender = false;
              
              // Method 1: Check if message status is 'sending' (definitely user's message)
              if (message.status === 'sending') {
                isCurrentUserSender = true;
              }
              // Method 2: Check if it's a temp message
              else if (message.id?.toString().includes('temp-')) {
                isCurrentUserSender = true;
              }
              // Method 3: Check if sender_type matches current user role
              else if (message.sender_type === user?.role) {
                isCurrentUserSender = true;
              }
              // Method 4: Force based on timestamp (recent messages are likely from current user)
              else if (message.timestamp && new Date(message.timestamp).getTime() > Date.now() - 30000) {
                isCurrentUserSender = true;
              }
              
              // Debug: Uncomment the line below if you need to troubleshoot message alignment
              // console.log('Message:', message.message.substring(0, 30), '| Your message:', isCurrentUserSender);

              return (
                <div key={message.id || message._id} className="mb-3">
                  {/* Message Bubble */}
                  <div className={`flex ${isCurrentUserSender ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg shadow-sm ${
                      isCurrentUserSender
                        ? 'bg-blue-600 text-white rounded-br-none ml-auto' // Your message (Right)
                        : 'bg-gray-100 text-gray-800 border border-gray-200 rounded-bl-none mr-auto' // Recipient's message (Left)
                    }`} style={{
                      alignSelf: isCurrentUserSender ? 'flex-end' : 'flex-start'
                    }}>
                      <p className="text-sm break-words">{message.message}</p>
                      <div className={`text-xs mt-2 flex items-center gap-2 ${
                        isCurrentUserSender ? 'justify-end text-blue-100' : 'justify-start text-gray-500'
                      }`}>
                        <span>{formatTime(message.timestamp)}</span>
                        {!isCurrentUserSender && (
                          <span className="opacity-70">
                            ({message.sender_type === 'vendor' ? 'Vendor' : 'Delivery Boy'})
                          </span>
                        )}
                        {/* Read Receipt / Status */}
                        {isCurrentUserSender && (
                          <span className="flex items-center flex-shrink-0">
                            {renderReadReceipt(message.status)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
            {typing && (
              <div className="flex justify-start mb-3">
                <div className="bg-gray-100 text-gray-800 border border-gray-200 px-4 py-3 rounded-lg rounded-bl-none shadow-sm">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {recipientName} is typing...
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Message Input - Always at bottom */}
      <div className="p-4 border-t border-gray-200 bg-white rounded-b-lg">
        <div className="flex space-x-2 items-center">
          <button
            onClick={shareLocation}
            className="p-3 bg-gray-200 text-gray-600 rounded-full hover:bg-gray-300 transition-colors"
            title="Share Location"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.828 0l-4.243-4.243m11.314-11.314L12 3m4.95 0l-1.414 1.414M16 11H8m-2 4h12a2 2 0 002-2V7a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" />
            </svg>
          </button>
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type pickup coordination message..."
            className="flex-1 px-4 py-3 bg-gray-50 text-gray-800 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder-gray-500"
          />
          <button
            onClick={() => sendMessage()}
            disabled={!newMessage.trim()}
            className="p-3 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-full hover:from-green-600 hover:to-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default VendorDeliveryChatInterface;