import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';

const ChatInterface = ({ orderId, recipientId, recipientName, onClose, onUnreadCountChange }) => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [typing, setTyping] = useState(false);
  const [orderDetails, setOrderDetails] = useState(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  // Quick reply templates for delivery boys
  const quickReplies = [
    "I'll be there in 10 minutes",
    "Can you confirm the landmark?",
    "I'm at your gate",
    "Facing traffic, might be slightly delayed",
    "Please keep exact change ready",
    "Order picked up, on my way",
    "Unable to find address, please call"
  ];

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
      const response = await api.get(`/api/chat/messages/${orderId}`);
      const fetchedMessages = response.data.messages || [];
      setMessages(fetchedMessages);
      
      // Calculate unread messages (messages not sent by current user and not read)
      const unreadMessages = fetchedMessages.filter(msg => {
        const isNotSentByCurrentUser = msg.sender_id !== currentUserId;
        const isUnread = msg.status !== 'read';
        const isCorrectRecipient = (
          (user.role === 'customer' && msg.sender_type === 'delivery') ||
          (user.role === 'delivery' && msg.sender_type === 'customer')
        );
        
        return isNotSentByCurrentUser && isUnread && isCorrectRecipient;
      });
      setUnreadCount(unreadMessages.length);
      
      // Mark messages as read for incoming messages
      if (fetchedMessages.length > 0) {
        markMessagesAsRead(fetchedMessages);
      }
    } catch (error) {
      console.error('Error fetching messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const markMessagesAsRead = async (messages) => {
    try {
      const userId = user.user_id || user.sub;
      const userRole = user.role;
      
      // Only mark messages as read that were sent TO the current user
      // Customer can mark delivery boy messages as read
      // Delivery boy can mark customer messages as read
      const unreadMessages = messages.filter(msg => {
        const isNotSentByCurrentUser = msg.sender_id !== userId;
        const isUnread = msg.status !== 'read';
        const isCorrectRecipient = (
          (userRole === 'customer' && msg.sender_type === 'delivery_boy') ||
          (userRole === 'delivery_boy' && msg.sender_type === 'customer')
        );
        
        console.log(`Message ${msg._id}: sender=${msg.sender_id}, sender_type=${msg.sender_type}, current_user=${userId}, role=${userRole}, can_mark_read=${isNotSentByCurrentUser && isUnread && isCorrectRecipient}`);
        
        return isNotSentByCurrentUser && isUnread && isCorrectRecipient;
      });
      
      console.log(`Found ${unreadMessages.length} messages to mark as read`);
      
      // Reset unread count immediately when marking messages as read
      if (unreadMessages.length > 0) {
        setUnreadCount(0);
      }
      
      for (const message of unreadMessages) {
        if (message.id || message._id) {
          try {
            console.log(`Marking message ${message.id || message._id} as read`);
            await api.patch(`/api/chat/messages/${message.id || message._id}/status`, {
              status: 'read'
            });
            
            // Update local state to show double ticks immediately
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
      console.error('Error marking messages as read:', error);
    }
  };

  const sendMessage = async (messageText = newMessage) => {
    if (!messageText.trim()) return;

    const tempMessage = {
      id: Date.now(),
      order_id: orderId,
      sender_id: user.user_id || user.sub,
      sender_type: user.role,
      message: messageText,
      timestamp: new Date().toISOString(),
      status: 'sending'
    };

    setMessages(prev => [...prev, tempMessage]);
    setNewMessage('');

    try {
      const response = await api.post('/api/chat/send-message', {
        order_id: orderId,
        message: messageText
      });

      // Update the message with server response - show single tick
      setMessages(prev => prev.map(msg => 
        msg.id === tempMessage.id ? { ...response.data, status: 'sent' } : msg
      ));
    } catch (error) {
      console.error('Error sending message:', error);
      // Mark message as failed
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

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'text-yellow-600';
      case 'processing': return 'text-blue-600';
      case 'shipped': return 'text-purple-600';
      case 'out_for_delivery': return 'text-orange-600';
      case 'delivered': return 'text-green-600';
      case 'cancelled': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading chat...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[650px] bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden">
      {/* Chat Header */}
      <div className="bg-blue-600 text-white p-4 rounded-t-lg flex justify-between items-center">
        <div>
          <h3 className="font-semibold text-lg text-white">
            Order #{orderDetails?.order_number || orderId.substring(0, 8)}
          </h3>
          <div className="text-sm text-blue-100">
            Chatting with {recipientName}
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-white hover:text-blue-200 text-2xl"
        >
          ✕
        </button>
      </div>

      {/* Messages Container */}
      <div 
        ref={chatContainerRef}
        className="flex-1 p-4 overflow-y-auto bg-gray-50"
        style={{ maxHeight: '400px', minHeight: '300px' }}
      >
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <div className="text-4xl mb-2">💬</div>
            <p>No messages yet. Start the conversation!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => {
              // Determine if current user is customer or delivery boy
              const currentUserId = user.user_id || user.sub;
              const isCurrentUserSender = message.sender_id === currentUserId;
              
              // Sent messages (by current user) go to LEFT (blue)
              // Received messages go to RIGHT (gray)
              const isSentByCurrentUser = isCurrentUserSender;
              
              return (
                <div key={message.id || message._id} className="mb-4">
                  {/* Timestamp centered */}
                  <div className="text-center text-xs text-gray-400 mb-2">
                    {formatTime(message.timestamp)}
                  </div>
                  
                  <div className={`flex ${isSentByCurrentUser ? 'justify-start' : 'justify-end'}`}>
                    <div className={`max-w-xs lg:max-w-md px-4 py-3 ${
                      isSentByCurrentUser
                        ? 'bg-blue-500 text-white rounded-2xl rounded-bl-md'
                        : 'bg-gray-100 text-gray-800 border border-gray-200 shadow-sm rounded-2xl rounded-br-md'
                    }`}>
                      <p className="text-sm">{message.message}</p>
                      <div className={`text-xs mt-1 flex items-center ${
                        isSentByCurrentUser ? 'justify-start text-blue-100' : 'justify-end text-gray-500'
                      }`}>
                        <span>{formatTime(message.timestamp)}</span>
                        {isSentByCurrentUser && (
                          <span className="ml-2 flex items-center">
                            {/* Sending state */}
                            {message.status === 'sending' && (
                              <span className="text-blue-200">⏳</span>
                            )}
                            {/* Single tick for sent/delivered */}
                            {(message.status === 'sent' || message.status === 'delivered' || !message.status) && (
                              <span className="text-blue-300 text-sm">✓</span>
                            )}
                            {/* Double blue tick for read */}
                            {message.status === 'read' && (
                              <span className="text-blue-400 font-bold text-base">✓✓</span>
                            )}
                            {/* Error state */}
                            {message.status === 'failed' && (
                              <span className="text-red-300">❌</span>
                            )}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
            {typing && (
              <div className="flex justify-start">
                <div className="bg-white text-gray-800 border border-gray-200 px-4 py-3 rounded-2xl rounded-bl-md shadow-sm">
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

      {/* Quick Replies (for delivery boys) */}
      {user.role === 'delivery_boy' && (
        <div className="px-4 py-2 border-t border-gray-200 bg-white">
          <div className="flex flex-wrap gap-2">
            {quickReplies.slice(0, 3).map((reply, index) => (
              <button
                key={index}
                onClick={() => handleQuickReply(reply)}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs hover:bg-gray-200 transition-colors"
              >
                {reply}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Message Input - Always at bottom - FIXED AND ALWAYS VISIBLE */}
      <div className="p-4 border-t-2 border-gray-300 bg-white rounded-b-lg sticky bottom-0 z-10">
        <div className="flex space-x-3 items-center">
          <div className="flex-1 relative">
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              placeholder="Type your message..."
              className="w-full px-4 py-3 text-base bg-gray-50 text-gray-900 border-2 border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder-gray-500 shadow-sm"
              style={{ minHeight: '48px', fontSize: '16px' }}
              autoComplete="off"
              spellCheck="true"
            />
          </div>
          <button
            onClick={() => sendMessage()}
            disabled={!newMessage.trim()}
            className="flex-shrink-0 p-3 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all shadow-lg min-w-[48px] min-h-[48px] flex items-center justify-center"
            title="Send message"
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

export default ChatInterface;