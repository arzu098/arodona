import React from 'react';
import { useNavigate, Link } from 'react-router-dom';

const OrderSuccess = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 text-center">
        <div>
          {/* Success Icon */}
          <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-6">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
            </svg>
          </div>

          {/* Success Message */}
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Order Placed Successfully!
          </h2>
          
          <p className="text-gray-600 mb-8">
            Thank you for your order. We'll send you a confirmation email shortly with your order details and tracking information.
          </p>

          {/* Action Buttons */}
          <div className="space-y-4">
            <Link
              to="/"
              className="w-full inline-flex justify-center items-center px-6 py-3 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150 ease-in-out"
            >
              Continue Shopping
            </Link>
            
            <Link
              to="/orders"
              className="w-full inline-flex justify-center items-center px-6 py-3 border border-gray-300 rounded-md shadow-sm text-base font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150 ease-in-out"
            >
              View My Orders
            </Link>

            <button
              onClick={() => navigate('/')}
              className="w-full inline-flex justify-center items-center px-6 py-3 border border-gray-300 rounded-md shadow-sm text-base font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150 ease-in-out"
            >
              Go to Homepage
            </button>
          </div>

          {/* Additional Info */}
          <div className="mt-8 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>What's next?</strong><br />
              • You'll receive an email confirmation<br />
              • Track your order in "My Orders"<br />
              • Get updates via SMS/Email<br />
              • Contact support if needed
            </p>
          </div>

          {/* Contact Support */}
          <div className="mt-6 text-sm text-gray-500">
            Need help? <Link to="/contact" className="text-blue-600 hover:underline">Contact Support</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderSuccess;