import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';

const Search = ({ isOpen, onClose }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const searchRef = useRef(null);

  // All products data
  const categoryProducts = {
    Rings: [
      { id: 1, name: 'Rose Gold Diamond Ring', price: '₹ 22,999', image: '/Images/17.png' },
      { id: 2, name: 'Gold Prestige Interwined Ring', price: '₹ 18,500', image: '/Images/18.png' },
      { id: 3, name: 'Gold Ring With Zircon', price: '₹ 15,299', image: '/Images/20.png' },
      { id: 4, name: 'Gold Pigeon Blood Ring', price: '₹ 25,999', image: '/Images/17.png' },
      { id: 5, name: 'Forever Diamond Ring', price: '₹ 32,999', image: '/Images/18.png' },
      { id: 6, name: 'Classic Band Ring Set', price: '₹ 28,500', image: '/Images/20.png' },
    ],
    Earrings: [
      { id: 1, name: 'Rose Gold Diamond Earrings', price: '₹ 16,000', image: '/Images/10.png' },
      { id: 2, name: 'Gold Prestige Interwined Earrings', price: '₹ 12,000', image: '/Images/11.png' },
      { id: 3, name: 'Gold Earrings With Zircon', price: '₹ 9,250', image: '/Images/12.png' },
      { id: 4, name: 'Pure 14K Gold Yellow Bee Earring', price: '₹ 12,500', image: '/Images/21.png' },
      { id: 5, name: 'Circle Gold Hoop Earrings', price: '₹ 8,999', image: '/Images/22.png' },
    ],
    Necklaces: [
      { id: 1, name: 'Rose Gold Diamond Necklace', price: '₹ 35,000', image: '/Images/15.png' },
      { id: 2, name: 'Gold Prestige Interwined Necklace', price: '₹ 28,000', image: '/Images/12.png' },
      { id: 3, name: 'Gold Necklace With Zircon', price: '₹ 22,250', image: '/Images/13.png' },
      { id: 4, name: 'Gold Plated Hanging Pendant', price: '₹ 4,500', image: '/Images/12.png' },
    ],
    Bracelets: [
      { id: 1, name: 'Rose Gold Diamond Bracelet', price: '₹ 24,000', image: '/Images/19.png' },
      { id: 2, name: 'Gold Prestige Interwined Bracelet', price: '₹ 18,000', image: '/Images/11.png' },
      { id: 3, name: 'Gold Bracelet With Zircon', price: '₹ 14,250', image: '/Images/10.png' },
      { id: 4, name: 'Minimal Gold Bracelet CG', price: '₹ 11,299', image: '/Images/11.png' },
    ],
    Pendents: [
      { id: 1, name: 'Gold Plated Hanging Pendant', price: '₹ 4,500', image: '/Images/15.png' },
      { id: 2, name: 'Diamond Pendant Set', price: '₹ 18,999', image: '/Images/12.png' },
      { id: 3, name: 'Pearl Drop Pendant', price: '₹ 8,500', image: '/Images/13.png' },
    ],
  };

  const allProducts = Object.entries(categoryProducts).flatMap(([category, products]) => 
    products.map(p => ({ ...p, category }))
  );

  // Handle search
  const handleSearch = (query) => {
    setSearchQuery(query);
    if (query.trim() === '') {
      setSearchResults([]);
      return;
    }

    const lowercaseQuery = query.toLowerCase();
    const results = allProducts.filter(product => 
      product.name.toLowerCase().includes(lowercaseQuery) ||
      product.category.toLowerCase().includes(lowercaseQuery)
    );
    setSearchResults(results);
  };

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  // Reset search when closed
  useEffect(() => {
    if (!isOpen) {
      setSearchQuery('');
      setSearchResults([]);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div 
      ref={searchRef}
      className="absolute top-full right-0 mt-4 w-[450px] bg-white rounded-lg shadow-2xl overflow-hidden"
      style={{
        animation: 'slideDown 0.3s ease-out',
        transformOrigin: 'top right'
      }}
    >
      <style>{`
        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-20px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
      `}</style>

      {/* Search Input */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-3 bg-gray-50 rounded-lg px-4 py-3">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-gray-400">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search for products..."
            className="flex-1 bg-transparent outline-none text-gray-800 placeholder-gray-400"
            autoFocus
          />
          {searchQuery && (
            <button 
              onClick={() => handleSearch('')}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Search Results */}
      <div className="max-h-[400px] overflow-y-auto">
        {searchQuery && searchResults.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="mx-auto mb-3 text-gray-300">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.35-4.35"></path>
            </svg>
            <p className="text-sm">No products found for "{searchQuery}"</p>
          </div>
        ) : searchResults.length > 0 ? (
          <div className="p-2">
            <p className="text-xs text-gray-500 px-3 py-2">{searchResults.length} results found</p>
            {searchResults.map((product, index) => (
              <Link
                key={`${product.category}-${product.id}-${index}`}
                to={`/${product.category.toLowerCase()}`}
                onClick={onClose}
                className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg transition-colors"
              >
                <img src={product.image} alt={product.name} className="w-12 h-12 object-cover rounded" />
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-gray-800 text-sm truncate">{product.name}</h4>
                  <p className="text-xs text-gray-500">{product.category}</p>
                </div>
                <p className="font-semibold text-gray-900 text-sm">{product.price}</p>
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-400">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="mx-auto mb-3 text-gray-300">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.35-4.35"></path>
            </svg>
            <p className="text-sm mb-1">Start typing to search</p>
            <p className="text-xs">Try "ring", "earring", "necklace"...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Search;
