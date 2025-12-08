import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';

const VendorCustomerChatInterface = ({ orderId, recipientId, recipientName, onClose, onUnreadCountChange }) => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [typing, setTyping] = useState(false);
  const [orderDetails, setOrderDetails] = useState(null);
  const [showQuickReplies, setShowQuickReplies] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [lastReadMessageId, setLastReadMessageId] = useState(null);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  // Quick reply templates for Vendors
  const vendorQuickReplies = [
    "📦 Your order is being prepared",
    "✅ Order is ready for pickup",
    "⏰ Your order will be ready in 30 minutes",
    "🚚 Order has been dispatched",
    "📞 Please call me at your convenience",
    "💰 Payment confirmation required",
    "🔄 There's an update on your order"
  ];

  // Quick reply templates for Customers  
  const customerQuickReplies = [
    "⏰ When will my order be ready?", 
    "📍 Can you confirm the delivery address?",
    "💰 What are the payment options?",
    "🔄 Can I make changes to my order?",
    "📞 Please call me when ready",
    "❓ I have a question about my order",
    "🙏 Thank you for the update"
  ];

  const getQuickReplies = () => {
    return user?.role === 'vendor' ? vendorQuickReplies : customerQuickReplies;
  };

  useEffect(() => {
    fetchOrderDetails();
    fetchMessages();
    // Set up real-time messaging (polling every 3 seconds)
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
      const response = await api.get(`/api/chat/vendor-customer/messages/${orderId}`);
      const fetchedMessages = response.data.messages || [];
      setMessages(fetchedMessages);
      
      // Calculate unread messages (messages not sent by current user and not read)
      const unreadMessages = fetchedMessages.filter(msg => {
        const isNotSentByCurrentUser = msg.sender_id !== currentUserId;
        const isUnread = msg.status !== 'read';
        const isCorrectRecipient = (
          (user.role === 'vendor' && msg.sender_type === 'customer') ||
          (user.role === 'customer' && msg.sender_type === 'vendor')
        );
        
        return isNotSentByCurrentUser && isUnread && isCorrectRecipient;
      });
      setUnreadCount(unreadMessages.length);
      
      // Mark messages as read for incoming messages
      if (fetchedMessages.length > 0) {
        markMessagesAsRead(fetchedMessages);
      }
    } catch (error) {
      console.error('Error fetching vendor-customer messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const markMessagesAsRead = async (messages) => {
    try {
      const userId = user.user_id || user.sub;
      const userRole = user.role;
      
      // Only mark messages as read that were sent TO the current user
      // Vendor can mark customer messages as read
      // Customer can mark vendor messages as read
      const unreadMessages = messages.filter(msg => {
        const isNotSentByCurrentUser = msg.sender_id !== userId;
        const isUnread = msg.status !== 'read';
        const isCorrectRecipient = (
          (userRole === 'vendor' && msg.sender_type === 'customer') ||
          (userRole === 'customer' && msg.sender_type === 'vendor')
        );
        
        return isNotSentByCurrentUser && isUnread && isCorrectRecipient;
      });
      
      for (const message of unreadMessages) {
        if (message.id || message._id) {
          try {
            await api.patch(`/api/chat/vendor-customer/messages/${message.id || message._id}/status`, {
              status: 'read'
            });
            
            // Update local state to show message as read
            setMessages(prev => prev.map(msg => 
              (msg.id === message.id || msg._id === message._id) 
                ? { ...msg, status: 'read' } 
                : msg
            ));
          } catch (error) {
            console.error(`Error marking message ${message.id || message._id} as read:`, error);
          }
        }
      }
      
      // Reset unread count after marking messages as read
      if (unreadMessages.length > 0) {
        setUnreadCount(0);
      }
    } catch (error) {
      console.error('Error in markMessagesAsRead:', error);
    }
  };

  const sendMessage = async (messageText = null) => {
    const textToSend = messageText || newMessage.trim();
    if (!textToSend) return;

    // Get user ID with multiple fallbacks
    const currentUserId = user.user_id || user.sub || user.id || user._id;
    console.log('SendMessage debug:', {
      user: user,
      currentUserId: currentUserId,
      user_id: user.user_id,
      sub: user.sub,
      id: user.id,
      _id: user._id
    });

    const tempMessage = {
      id: Date.now().toString(),
      order_id: orderId,
      sender_id: currentUserId,
      sender_type: user.role,
      recipient_id: recipientId,
      recipient_type: user.role === 'vendor' ? 'customer' : 'vendor',
      message: textToSend,
      timestamp: new Date().toISOString(),
      status: 'sending'
    };

    setMessages(prev => [...prev, tempMessage]);
    setNewMessage('');

    try {
      const response = await api.post('/api/chat/vendor-customer/send-message', {
        order_id: orderId,
        message: textToSend,
        recipient_id: recipientId
      });
      
      // Update the message with server response
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
      console.error('Error sending vendor-customer message:', error);
      // Mark message as failed but keep it visible
      setMessages(prev => prev.map(msg => 
        msg.id === tempMessage.id ? { ...msg, status: 'failed' } : msg
      ));
    }
  };

  const handleQuickReply = (reply) => {
    sendMessage(reply);
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading chat...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg border border-gray-200">
      {/* Chat Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 rounded-t-lg">
        <div className="flex justify-between items-center">
          <div className="flex-1">
            <h3 className="font-semibold text-lg text-white flex items-center">
              <span className="mr-2">💬</span>
              Order #{orderDetails?.order_number || orderId.substring(0, 8)}
            </h3>
            <div className="text-sm text-blue-100 flex items-center">
              {user?.role === 'vendor' ? (
                <span className="flex items-center">
                  <span className="mr-1">👤</span>
                  Chat with {recipientName || 'Customer'}
                </span>
              ) : (
                <span className="flex items-center">
                  <span className="mr-1">🏪</span>
                  Chat with {recipientName || 'Vendor'}
                </span>
              )}
            </div>
          </div>
        </div>
        
        {/* Order status indicator */}
        <div className="mt-2 flex items-center text-sm">
          <span className="bg-white/20 px-2 py-1 rounded-full text-xs">
            {orderDetails?.status?.replace('_', ' ').toUpperCase() || 'ORDER CHAT'}
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
        <div className="flex flex-wrap gap-2">
          {(showQuickReplies ? getQuickReplies() : getQuickReplies().slice(0, 3)).map((reply, index) => (
            <button
              key={index}
              onClick={() => handleQuickReply(reply)}
              className={`px-3 py-1 rounded-full text-xs hover:shadow-sm transition-all ${
                user?.role === 'vendor' 
                  ? 'bg-blue-100 text-blue-700 hover:bg-blue-200' 
                  : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
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
              <span>{user?.role === 'vendor' ? '👤' : '🏪'}</span>
            </div>
            <p className="text-gray-600 mb-6">Start a conversation with {recipientName}</p>
            <div className="max-w-md mx-auto">
              {/* Quick start buttons for empty state */}
              <div className="flex flex-wrap gap-2 justify-center">
                <button
                  onClick={() => handleQuickReply(user?.role === 'vendor' ? '📦 Your order is being prepared' : '⏰ When will my order be ready?')}
                  className={`px-3 py-2 rounded-lg text-sm hover:shadow-sm transition-all ${
                    user?.role === 'vendor' 
                      ? 'bg-blue-100 text-blue-700 hover:bg-blue-200' 
                      : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                  }`}
                >
                  {user?.role === 'vendor' ? '📦 Order Update' : '⏰ Ask about timing'}
                </button>
                <button
                  onClick={() => handleQuickReply(user?.role === 'vendor' ? '📞 Please call me at your convenience' : '📞 Please call me when ready')}
                  className={`px-3 py-2 rounded-lg text-sm hover:shadow-sm transition-all ${
                    user?.role === 'vendor' 
                      ? 'bg-blue-100 text-blue-700 hover:bg-blue-200' 
                      : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                  }`}
                >
                  📞 Request Call
                </button>
              </div>
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
              else if (message.sender_type === user.role) {
                isCurrentUserSender = true;
              }
              // Method 4: Force based on timestamp (recent messages are likely from current user)
              else if (message.timestamp && new Date(message.timestamp).getTime() > Date.now() - 30000) {
                // If message is less than 30 seconds old and no clear sender info, assume it's from current user
                isCurrentUserSender = true;
              }
              
              // Debug: Uncomment the line below if you need to troubleshoot message alignment
              // console.log('Message:', message.message.substring(0, 30), '| Your message:', isCurrentUserSender);
              
              return (
                <div key={message.id || message._id} className={`flex ${isCurrentUserSender ? 'justify-end' : 'justify-start'} mb-3`}>
                  <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg shadow-sm ${
                    isCurrentUserSender 
                      ? 'bg-blue-600 text-white rounded-br-none ml-auto' 
                      : 'bg-gray-100 text-gray-800 border border-gray-200 rounded-bl-none mr-auto'
                  }`} style={{
                    alignSelf: isCurrentUserSender ? 'flex-end' : 'flex-start'
                  }}>
                    <p className="text-sm break-words">{message.message}</p>
                    <div className="flex items-center justify-between mt-2 gap-2">
                      <p className={`text-xs ${isCurrentUserSender ? 'text-blue-100' : 'text-gray-500'}`}>
                        {formatTime(message.timestamp)}
                        {!isCurrentUserSender && (
                          <span className="ml-1 opacity-70">
                            ({message.sender_type === 'vendor' ? 'Vendor' : 'Customer'})
                          </span>
                        )}
                      </p>
                      {isCurrentUserSender && (
                        <div className={`text-xs ${isCurrentUserSender ? 'text-blue-100' : 'text-gray-500'} flex-shrink-0`}>
                          {message.status === 'sending' && '⏳'}
                          {message.status === 'sent' && '✓'}
                          {message.status === 'delivered' && '✓✓'}
                          {message.status === 'read' && <span className="text-blue-200">✓✓</span>}
                          {message.status === 'failed' && <span className="text-red-300">❌</span>}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
            
            {typing && (
              <div className="flex justify-start mb-3">
                <div className="bg-gray-100 border border-gray-200 rounded-lg rounded-bl-none px-4 py-2 max-w-xs shadow-sm">
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
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type your message..."
            className="flex-1 px-4 py-3 bg-gray-50 text-gray-800 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder-gray-500"
          />
          <button
            onClick={() => sendMessage()}
            disabled={!newMessage.trim()}
            className="p-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-full hover:from-blue-600 hover:to-purple-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all"
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

export default VendorCustomerChatInterface;