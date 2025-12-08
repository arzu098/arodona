import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { CartProvider } from './context/CartContext'
import { WishlistProvider } from './context/WishlistContext'
import { AuthProvider } from './context/AuthContext'
import Home from './components/Home'
import Rings from './components/Rings'
import Bracelets from './components/Bracelets'
import Earrings from './components/Earrings'
import Necklaces from './components/Necklaces'
import Pendents from './components/Pendents'
import Shop from './components/Shop'
import ProductDetail from './components/ProductDetail'
import Cart from './components/Cart'
import Checkout from './components/Checkout'
import Wishlist from './components/Wishlist'
import Login from './components/Login'
import ScrollToTop from './components/ScrollToTop'
import ProtectedRoute from './components/ProtectedRoute'
import AdminDashboard from './components/AdminDashboard'
import VendorDashboard from './components/VendorDashboard'
import CustomerDashboard from './components/CustomerDashboard'
import SuperAdminDashboard from './components/dashboards/SuperAdminDashboard'
import DashboardRedirect from './components/DashboardRedirect'
import Signup from './components/Signup'
import AdminUsers from './components/admin/AdminUsers'
import AdminVendors from './components/admin/AdminVendors'
import AdminOrders from './components/admin/AdminOrders'
import AdminSettings from './components/admin/AdminSettings'
import VendorProducts from './components/vendor/VendorProducts'
import VendorAddProduct from './components/vendor/VendorAddProduct'
import VendorOrders from './components/vendor/VendorOrders'
import VendorProfile from './components/vendor/VendorProfile'
import VendorAnalytics from './components/vendor/VendorAnalytics'
import DeliveryBoyDashboard from './components/delivery/DeliveryBoyDashboard'
import DeliveryOrders from './components/delivery/DeliveryOrders'
import DeliveryProfile from './components/delivery/DeliveryProfile'
import OrderSuccess from './components/OrderSuccess'
import ErrorBoundary from './components/ErrorBoundary'
import ChatHub from './components/ChatHub'

function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <WishlistProvider>
          <Router>
            <ScrollToTop />
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/rings" element={<Rings />} />
              <Route path="/earrings" element={<Earrings />} />
              <Route path="/bracelets" element={<Bracelets />} />
              <Route path="/necklaces" element={<Necklaces />} />
              <Route path="/pendents" element={<Pendents />} />
              <Route path="/shop" element={<Shop />} />
              <Route path="/product/:id" element={<ProductDetail />} />
              <Route path="/cart" element={<Cart />} />
              <Route 
                path="/checkout" 
                element={
                  <ProtectedRoute requireAuth={true}>
                    <Checkout />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/order-success" 
                element={
                  <ProtectedRoute requireAuth={true}>
                    <OrderSuccess />
                  </ProtectedRoute>
                } 
              />
              <Route path="/wishlist" element={<Wishlist />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              
              {/* Protected Dashboard Routes */}
              <Route 
                path="/super-admin" 
                element={<Navigate to="/super-admin/dashboard" replace />} 
              />
              <Route 
                path="/super-admin/dashboard" 
                element={
                  <ProtectedRoute roles={['super_admin']}>
                    <SuperAdminDashboard />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/admin" 
                element={<Navigate to="/admin/dashboard" replace />} 
              />
              <Route 
                path="/admin/dashboard" 
                element={
                  <ProtectedRoute roles={['admin']}>
                    <AdminDashboard />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/vendor" 
                element={<Navigate to="/vendor/dashboard" replace />} 
              />
              <Route 
                path="/vendor/dashboard" 
                element={
                  <ProtectedRoute roles={['vendor']}>
                    <VendorDashboard />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/customer" 
                element={<Navigate to="/customer/dashboard" replace />} 
              />
              <Route 
                path="/customer/dashboard" 
                element={
                  <ProtectedRoute roles={['customer']}>
                    <CustomerDashboard />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/delivery" 
                element={<Navigate to="/delivery/dashboard" replace />} 
              />
              <Route 
                path="/delivery/dashboard" 
                element={
                  <ProtectedRoute roles={['delivery_boy']}>
                    <DeliveryBoyDashboard />
                  </ProtectedRoute>
                } 
              />
              
              {/* Admin Sub-Routes */}
              <Route 
                path="/admin/users" 
                element={
                  <ProtectedRoute roles={['admin']}>
                    <AdminUsers />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/admin/vendors" 
                element={
                  <ProtectedRoute roles={['admin']}>
                    <AdminVendors />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/admin/orders" 
                element={
                  <ProtectedRoute roles={['admin']}>
                    <AdminOrders />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/admin/settings" 
                element={
                  <ProtectedRoute roles={['admin']}>
                    <AdminSettings />
                  </ProtectedRoute>
                } 
              />
              
              {/* Vendor Sub-Routes */}
              <Route 
                path="/vendor/products" 
                element={
                  <ProtectedRoute roles={['vendor']}>
                    <VendorProducts />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/vendor/products/add" 
                element={
                  <ProtectedRoute roles={['vendor']}>
                    <VendorAddProduct />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/vendor/products/edit/:id" 
                element={
                  <ProtectedRoute roles={['vendor']}>
                    <VendorAddProduct />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/vendor/orders" 
                element={
                  <ProtectedRoute roles={['vendor']}>
                    <VendorOrders />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/vendor/profile" 
                element={
                  <ProtectedRoute roles={['vendor']}>
                    <VendorProfile />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/vendor/analytics" 
                element={
                  <ProtectedRoute roles={['vendor']}>
                    <VendorAnalytics />
                  </ProtectedRoute>
                } 
              />
              
              
              <Route 
                path="/delivery/orders" 
                element={
                  <ProtectedRoute roles={['delivery_boy']}>
                    <DeliveryOrders />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/delivery/profile" 
                element={
                  <ProtectedRoute roles={['delivery_boy']}>
                    <ErrorBoundary>
                      <DeliveryProfile />
                    </ErrorBoundary>
                  </ProtectedRoute>
                } 
              />
              
              {/* Chat Hub Route - accessible to customers, vendors, and delivery boys */}
              <Route 
                path="/chat" 
                element={
                  <ProtectedRoute roles={['customer', 'vendor', 'delivery_boy']}>
                    <ChatHub />
                  </ProtectedRoute>
                } 
              />
              
              {/* Default dashboard route - redirects based on role */}
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <DashboardRedirect />
                  </ProtectedRoute>
                } 
              />
            </Routes>
          </Router>
        </WishlistProvider>
      </CartProvider>
    </AuthProvider>
  )
}

export default App
