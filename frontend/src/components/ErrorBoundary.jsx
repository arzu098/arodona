import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // You can log error info here if needed
    // console.error('ErrorBoundary caught an error', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#F4E7D0] flex items-center justify-center">
          <div className="text-center">
            <div className="text-xl text-red-600 mb-4">Something went wrong in this section.</div>
            <div className="text-gray-700 mb-4">{this.state.error?.message || 'Unknown error.'}</div>
            <button
              onClick={() => window.location.reload()}
              className="bg-[#3E2F2A] text-white px-4 py-2 rounded hover:bg-opacity-80"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
