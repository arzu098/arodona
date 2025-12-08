import React, { createContext, useState, useContext, useEffect } from 'react';
import { useAuth } from './AuthContext';
import cartService from '../services/cartService';

const CartContext = createContext();

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};

export const CartProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [cartItems, setCartItems] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [cartData, setCartData] = useState(null);

  // Define fetchCart function first
  const fetchCart = async () => {
    if (!isAuthenticated) {
      // For guest users, just use localStorage
      const savedCart = localStorage.getItem('guestCart');
      if (savedCart) {
        try {
          setCartItems(JSON.parse(savedCart));
        } catch (e) {
          console.error('Error parsing guest cart:', e);
          setCartItems([]);
        }
      }
      return;
    }

    // For authenticated users, fetch from backend
    try {
      setIsLoading(true);
      const data = await cartService.getCart();
      console.log('Cart fetched from backend:', data);
      setCartData(data);
      
      // Map backend cart items to frontend format
      const mappedItems = (data.items || []).map(item => ({
        cartId: item.id,
        id: item.product_id,
        name: item.product_name,
        price: item.unit_price || item.price || 0,
        originalPrice: item.compare_at_price,
        image: item.image_url,
        quantity: item.quantity,
        size: item.size,
        vendorId: item.vendor_id,
        vendorName: item.vendor_name,
        sku: item.sku,
        inStock: item.in_stock,
        availableQuantity: item.available_quantity
      }));
      
      setCartItems(mappedItems);
    } catch (error) {
      console.error('Error fetching cart:', error);
      // Fallback to empty cart on error
      setCartItems([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Load cart when authentication status changes
  useEffect(() => {
    const initializeCart = async () => {
      if (!isAuthenticated) {
        // Guest user - load from localStorage
        const savedCart = localStorage.getItem('guestCart');
        if (savedCart) {
          try {
            const parsed = JSON.parse(savedCart);
            setCartItems(parsed);
          } catch (e) {
            console.error('Error parsing guest cart:', e);
            setCartItems([]);
          }
        }
      } else {
        // Authenticated user - migrate guest cart if exists, then fetch backend cart
        const savedCart = localStorage.getItem('guestCart');
        if (savedCart) {
          try {
            const guestItems = JSON.parse(savedCart);
            console.log('Migrating guest cart items:', guestItems.length);
            // Add each guest item to backend cart
            for (const item of guestItems) {
              try {
                const itemData = {
                  product_id: String(item.product_id || item.id),
                  quantity: item.quantity || 1
                };
                if (item.selectedSize || item.size) {
                  itemData.size = item.selectedSize || item.size;
                }
                if (item.selectedColor || item.color) {
                  itemData.variant_id = item.selectedColor || item.color;
                }
                await cartService.addToCart(itemData);
              } catch (error) {
                console.error('Error migrating cart item:', error);
              }
            }
            // Clear guest cart after migration
            localStorage.removeItem('guestCart');
            console.log('Guest cart migrated and cleared');
          } catch (e) {
            console.error('Error migrating guest cart:', e);
          }
        }
        
        // Always fetch cart from backend for authenticated users
        await fetchCart();
      }
    };
    
    initializeCart();
  }, [isAuthenticated]); // Only depend on isAuthenticated to avoid infinite loops

  const addToCart = async (product) => {
    if (!isAuthenticated) {
      // Guest user - use localStorage
      try {
        const localItem = {
          ...product,
          cartId: product.cartId || `guest-${Date.now()}-${Math.random()}`,
          product_id: product.id || product._id || product.product_id,
          id: product.id || product._id || product.product_id,
          quantity: product.quantity || 1,
          name: product.name,
          price: product.price,
          image: product.image,
          selectedColor: product.selectedColor || product.color,
          selectedSize: product.selectedSize || product.size
        };

        setCartItems(prev => {
          const existing = prev.find(item => 
            (item.product_id === localItem.product_id || item.id === localItem.id) &&
            item.selectedSize === localItem.selectedSize &&
            item.selectedColor === localItem.selectedColor
          );
          
          let newCart;
          if (existing) {
            newCart = prev.map(item =>
              item.cartId === existing.cartId
                ? { ...item, quantity: item.quantity + localItem.quantity }
                : item
            );
          } else {
            newCart = [...prev, localItem];
          }
          
          // Save to localStorage
          localStorage.setItem('guestCart', JSON.stringify(newCart));
          return newCart;
        });
        
        return { success: true };
      } catch (error) {
        console.error('Error adding to guest cart:', error);
        return { success: false, error: error.message };
      }
    }

    // Authenticated user - use backend
    try {
      setIsLoading(true);
      
      // Prepare item data for backend - remove null fields
      const itemData = {
        product_id: String(product.id || product._id || product.product_id),
        quantity: product.quantity || 1
      };
      
      // Only add optional fields if they exist
      if (product.selectedSize || product.size) {
        itemData.size = product.selectedSize || product.size;
      }
      if (product.selectedColor || product.color || product.variant_id) {
        itemData.variant_id = product.selectedColor || product.color || product.variant_id;
      }
      if (product.personalization) {
        itemData.personalization = product.personalization;
      }
      if (product.gift_message) {
        itemData.gift_message = product.gift_message;
      }
      
      console.log('Adding to cart with data:', itemData);
      
      const data = await cartService.addToCart(itemData);
      console.log('Cart updated:', data);
      setCartData(data);
      
      // Map backend cart items to frontend format (same as fetchCart)
      const mappedItems = (data.items || []).map(item => {
        const mappedItem = {
          cartId: item.id,
          id: item.product_id,
          name: item.product_name,
          price: item.unit_price || item.price || 0,
          originalPrice: item.compare_at_price,
          image: item.image_url,
          quantity: item.quantity,
          size: item.size,
          vendorId: item.vendor_id,
          vendorName: item.vendor_name,
          sku: item.sku,
          inStock: item.in_stock,
          availableQuantity: item.available_quantity
        };
        return mappedItem;
      });
      
      setCartItems(mappedItems);
      return { success: true };
    } catch (error) {
      console.error('Error adding to cart:', error);
      console.error('Error details:', error.response?.data || error.message);
      
      // Fallback: Add to local state if backend fails
      const localItem = {
        ...product,
        cartId: Date.now(),
        product_id: product.id || product._id,
        quantity: product.quantity || 1
      };
      
      setCartItems(prev => {
        const existing = prev.find(item => 
          (item.product_id === localItem.product_id || item.id === localItem.id) &&
          item.selectedSize === localItem.selectedSize
        );
        if (existing) {
          return prev.map(item =>
            (item.product_id === localItem.product_id || item.id === localItem.id) &&
            item.selectedSize === localItem.selectedSize
              ? { ...item, quantity: item.quantity + localItem.quantity }
              : item
          );
        }
        return [...prev, localItem];
      });
      
      return { 
        success: false, 
        error: error.response?.data?.detail || error.message || 'Failed to add to cart',
        fallback: true 
      };
    } finally {
      setIsLoading(false);
    }
  };

  const removeFromCart = async (itemId) => {
    if (!isAuthenticated) {
      // Guest user - remove from localStorage
      try {
        setCartItems(prev => {
          const newCart = prev.filter(item => item.cartId !== itemId);
          localStorage.setItem('guestCart', JSON.stringify(newCart));
          return newCart;
        });
        return { success: true };
      } catch (error) {
        console.error('Error removing from guest cart:', error);
        return { success: false, error: error.message };
      }
    }

    // Authenticated user - use backend
    try {
      setIsLoading(true);
      const data = await cartService.removeFromCart(itemId);
      setCartData(data);
      
      // Map backend cart items to frontend format
      const mappedItems = (data.items || []).map(item => ({
        cartId: item.id,
        id: item.product_id,
        name: item.product_name,
        price: item.unit_price || item.price || 0,
        originalPrice: item.compare_at_price,
        image: item.image_url,
        quantity: item.quantity,
        size: item.size,
        vendorId: item.vendor_id,
        vendorName: item.vendor_name,
        sku: item.sku,
        inStock: item.in_stock,
        availableQuantity: item.available_quantity
      }));
      
      setCartItems(mappedItems);
      return { success: true };
    } catch (error) {
      console.error('Error removing from cart:', error);
      return { success: false, error: error.message };
    } finally {
      setIsLoading(false);
    }
  };

  const updateQuantity = async (itemId, quantity) => {
    if (quantity <= 0) {
      return removeFromCart(itemId);
    }
    
    if (!isAuthenticated) {
      // Guest user - update in localStorage
      try {
        setCartItems(prev => {
          const newCart = prev.map(item =>
            item.cartId === itemId
              ? { ...item, quantity: quantity }
              : item
          );
          localStorage.setItem('guestCart', JSON.stringify(newCart));
          return newCart;
        });
        return { success: true };
      } catch (error) {
        console.error('Error updating guest cart quantity:', error);
        return { success: false, error: error.message };
      }
    }

    // Authenticated user - use backend
    try {
      setIsLoading(true);
      const data = await cartService.updateQuantity(itemId, quantity);
      setCartData(data);
      
      // Map backend cart items to frontend format
      const mappedItems = (data.items || []).map(item => ({
        cartId: item.id,
        id: item.product_id,
        name: item.product_name,
        price: item.unit_price || item.price || 0,
        originalPrice: item.compare_at_price,
        image: item.image_url,
        quantity: item.quantity,
        size: item.size,
        vendorId: item.vendor_id,
        vendorName: item.vendor_name,
        sku: item.sku,
        inStock: item.in_stock,
        availableQuantity: item.available_quantity
      }));
      
      setCartItems(mappedItems);
      return { success: true };
    } catch (error) {
      console.error('Error updating quantity:', error);
      return { success: false, error: error.message };
    } finally {
      setIsLoading(false);
    }
  };

  const clearCart = async () => {
    if (!isAuthenticated) {
      // Guest user - clear localStorage
      try {
        setCartItems([]);
        localStorage.removeItem('guestCart');
        return { success: true };
      } catch (error) {
        console.error('Error clearing guest cart:', error);
        return { success: false, error: error.message };
      }
    }

    // Authenticated user - use backend
    try {
      setIsLoading(true);
      const data = await cartService.clearCart();
      setCartData(data);
      setCartItems([]);
      return { success: true };
    } catch (error) {
      console.error('Error clearing cart:', error);
      return { success: false, error: error.message };
    } finally {
      setIsLoading(false);
    }
  };

  const getCartTotal = () => {
    if (cartData && cartData.total_price !== undefined) {
      return cartData.total_price;
    }
    return cartItems.reduce((total, item) => {
      const price = typeof item.price === 'string' 
        ? parseFloat(item.price.replace(/[₹$,\s]/g, ''))
        : item.price || 0;
      return total + (price * (item.quantity || 1));
    }, 0);
  };

  const getCartCount = () => {
    return cartItems.reduce((count, item) => count + (item.quantity || 1), 0);
  };

  const isInCart = (productId) => {
    return cartItems.some(item => item.product_id === productId || item.id === productId);
  };

  const getItemQuantity = (productId) => {
    const item = cartItems.find(item => item.product_id === productId || item.id === productId);
    return item ? item.quantity : 0;
  };

  return (
    <CartContext.Provider value={{
      cartItems,
      cartData,
      isLoading,
      addToCart,
      removeFromCart,
      updateQuantity,
      clearCart,
      getCartTotal,
      getCartCount,
      isInCart,
      getItemQuantity,
      fetchCart
    }}>
      {children}
    </CartContext.Provider>
  );
};
