import React, { createContext, useState, useContext, useEffect } from 'react';
import { useAuth } from './AuthContext';
import favoritesService from '../services/favoritesService';

const WishlistContext = createContext();

export const useWishlist = () => {
  const context = useContext(WishlistContext);
  if (!context) {
    throw new Error('useWishlist must be used within a WishlistProvider');
  }
  return context;
};

export const WishlistProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [wishlistItems, setWishlistItems] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Load wishlist from localStorage for guest users on mount
  useEffect(() => {
    if (!isAuthenticated) {
      const savedWishlist = localStorage.getItem('guestWishlist');
      if (savedWishlist) {
        try {
          setWishlistItems(JSON.parse(savedWishlist));
        } catch (e) {
          console.error('Error parsing guest wishlist:', e);
          setWishlistItems([]);
        }
      }
    }
  }, []);

  // Fetch wishlist from backend when user changes or on mount
  useEffect(() => {
    if (isAuthenticated) {
      // When user logs in, migrate guest wishlist to backend
      const migrateGuestWishlist = async () => {
        const savedWishlist = localStorage.getItem('guestWishlist');
        if (savedWishlist) {
          try {
            const guestItems = JSON.parse(savedWishlist);
            // Add each guest item to backend wishlist
            for (const item of guestItems) {
              try {
                const productId = item.product_id || item.id || item._id;
                await favoritesService.toggleFavorite(productId);
              } catch (error) {
                console.error('Error migrating wishlist item:', error);
              }
            }
            // Clear guest wishlist after migration
            localStorage.removeItem('guestWishlist');
          } catch (e) {
            console.error('Error migrating guest wishlist:', e);
          }
        }
        // Fetch the updated wishlist from backend
        await fetchWishlist();
      };
      
      migrateGuestWishlist();
    } else {
      // Load from localStorage for guest users
      const savedWishlist = localStorage.getItem('guestWishlist');
      if (savedWishlist) {
        try {
          setWishlistItems(JSON.parse(savedWishlist));
        } catch (e) {
          console.error('Error parsing guest wishlist:', e);
          setWishlistItems([]);
        }
      }
    }
  }, [user, isAuthenticated]);

  const fetchWishlist = async () => {
    if (!isAuthenticated) {
      setWishlistItems([]);
      setIsLoading(false);
      return;
    }
    
    try {
      setIsLoading(true);
      const data = await favoritesService.getFavorites();
      console.log('Wishlist data:', data);
      // Backend returns { count, items } where each item has { favorite_id, created_at, product }
      setWishlistItems(data.items || data.favorites || []);
    } catch (error) {
      console.error('Error fetching wishlist:', error);
      console.error('Error details:', error.response?.data);
      setWishlistItems([]);
    } finally {
      setIsLoading(false);
    }
  };

  const addToWishlist = async (product) => {
    if (!isAuthenticated) {
      // Guest user - store in localStorage
      try {
        setIsLoading(true);
        const productId = product.id || product._id || product.product_id;
        
        setWishlistItems(prev => {
          // Check if already in wishlist
          const exists = prev.find(item => 
            (item.id || item._id || item.product_id) === productId
          );
          
          if (exists) {
            console.log('Product already in wishlist');
            return prev;
          }
          
          const newWishlist = [...prev, {
            id: productId,
            product_id: productId,
            name: product.name,
            price: product.price,
            image: product.image,
            _rawPrice: product._rawPrice,
            added_at: new Date().toISOString()
          }];
          
          // Save to localStorage
          localStorage.setItem('guestWishlist', JSON.stringify(newWishlist));
          return newWishlist;
        });
        
        return { success: true };
      } catch (error) {
        console.error('Error adding to guest wishlist:', error);
        return { success: false, error: error.message };
      } finally {
        setIsLoading(false);
      }
    }
    
    // Authenticated user - use backend
    try {
      setIsLoading(true);
      const productId = product.id || product._id || product.product_id;
      console.log('Adding to wishlist:', productId);
      const result = await favoritesService.toggleFavorite(productId);
      console.log('Wishlist toggle result:', result);
      
      // Refresh the list after any toggle action
      await fetchWishlist();
      
      // Return success regardless of add/remove (toggle always succeeds)
      return { success: true, action: result.action };
    } catch (error) {
      console.error('Error adding to wishlist:', error);
      console.error('Error details:', error.response?.data);
      return { success: false, error: error.response?.data?.detail || error.message };
    } finally {
      setIsLoading(false);
    }
  };

  const removeFromWishlist = async (productId) => {
    if (!isAuthenticated) {
      // Guest user - remove from localStorage
      try {
        setIsLoading(true);
        setWishlistItems(prev => {
          const newWishlist = prev.filter(item => 
            (item.id || item._id || item.product_id) !== productId
          );
          localStorage.setItem('guestWishlist', JSON.stringify(newWishlist));
          return newWishlist;
        });
        return { success: true };
      } catch (error) {
        console.error('Error removing from guest wishlist:', error);
        return { success: false, error: error.message };
      } finally {
        setIsLoading(false);
      }
    }
    
    // Authenticated user - use backend
    try {
      setIsLoading(true);
      // Find the favorite item to get its ID
      const favoriteItem = wishlistItems.find(item => 
        item.product_id === productId || item.id === productId || item._id === productId
      );
      
      console.log('Removing from wishlist:', productId, favoriteItem);
      
      if (favoriteItem && favoriteItem._id) {
        await favoritesService.removeFavorite(favoriteItem._id);
      } else {
        // If we don't have the favorite ID, use toggle
        await favoritesService.toggleFavorite(productId);
      }
      
      await fetchWishlist(); // Refresh the list
      return { success: true };
    } catch (error) {
      console.error('Error removing from wishlist:', error);
      return { success: false, error: error.response?.data?.detail || error.message };
    } finally {
      setIsLoading(false);
    }
  };

  const isInWishlist = (productId) => {
    return wishlistItems.some(item => {
      // Check if item has nested product object (backend format)
      if (item.product && item.product.id) {
        return item.product.id === productId || item.product._id === productId;
      }
      // Check if item is the product itself (guest format)
      return item.product_id === productId || item.id === productId || item._id === productId;
    });
  };

  const clearWishlist = async () => {
    try {
      setIsLoading(true);
      // Remove all favorites one by one
      for (const item of wishlistItems) {
        if (item._id) {
          await favoritesService.removeFavorite(item._id);
        }
      }
      setWishlistItems([]);
      return { success: true };
    } catch (error) {
      console.error('Error clearing wishlist:', error);
      return { success: false, error: error.message };
    } finally {
      setIsLoading(false);
    }
  };

  const value = {
    wishlistItems,
    isLoading,
    addToWishlist,
    removeFromWishlist,
    isInWishlist,
    clearWishlist,
    fetchWishlist
  };

  return (
    <WishlistContext.Provider value={value}>
      {children}
    </WishlistContext.Provider>
  );
};
