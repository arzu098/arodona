import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const Footer = () => {
  const [email, setEmail] = useState('');

  const handleNewsletterSubmit = (e) => {
    e.preventDefault();
    console.log('Newsletter subscription:', email);
    setEmail('');
  };

  return (
    <>
      {/* Newsletter Section */}
      <section className="bg-[#fceec6] px-4 sm:px-6 lg:px-[5%] py-12 sm:py-16 lg:py-20">
        <div className="max-w-[1400px] mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 sm:gap-10 md:gap-12 lg:gap-16 items-start">
            
            {/* Contact Us */}
            <div className="text-center md:text-left">
              <h3 className="text-base sm:text-lg md:text-xl font-bold text-gray-900 mb-3 sm:mb-4 uppercase tracking-wide">
                Contact Us
              </h3>
              <a 
                href="tel:+14055550128" 
                className="text-gray-700 hover:text-gray-900 text-sm sm:text-base md:text-lg font-medium transition-colors block"
              >
                (405) 555-0128
              </a>
            </div>

            {/* Newsletter */}
            <div className="text-center">
              <h2 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-serif text-gray-900 mb-2 sm:mb-3">
                Let's Get In Touch!
              </h2>
              <p className="text-xs sm:text-sm text-gray-700 mb-4 sm:mb-6">
                What's inside? Exclusive sales, new arrivals & more
              </p>
              
              <form onSubmit={handleNewsletterSubmit} className="flex flex-col sm:flex-row gap-2 max-w-md mx-auto">
                <input 
                  type="email" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email Address" 
                  required
                  className="w-full flex-1 px-3 sm:px-4 py-2 sm:py-2.5 border border-gray-400 bg-white text-xs sm:text-sm text-gray-700 focus:outline-none focus:border-gray-600 transition-colors"
                />
                <button 
                  type="submit"
                  className="w-full sm:w-auto bg-black text-white px-5 sm:px-6 py-2 sm:py-2.5 text-xs font-semibold hover:bg-gray-800 transition-colors uppercase tracking-wider"
                >
                  Sign Up
                </button>
              </form>
            </div>

            {/* Social Networks */}
            <div className="text-center md:text-right">
              <h3 className="text-base sm:text-lg md:text-xl font-bold text-gray-900 mb-3 sm:mb-4 uppercase tracking-wide">
                Social Networks
              </h3>
              <div className="flex gap-3 sm:gap-4 justify-center md:justify-end">
                <a 
                  href="https://facebook.com" 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-[#2d3436] hover:bg-gray-900 text-white flex items-center justify-center transition-all"
                  aria-label="Facebook"
                >
                  <svg width="16" height="16" className="sm:w-[18px] sm:h-[18px]" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                  </svg>
                </a>
                <a 
                  href="https://instagram.com" 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-[#2d3436] hover:bg-gray-900 text-white flex items-center justify-center transition-all"
                  aria-label="Instagram"
                >
                  <svg width="16" height="16" className="sm:w-[18px] sm:h-[18px]" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                  </svg>
                </a>
                <a 
                  href="https://twitter.com" 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-[#2d3436] hover:bg-gray-900 text-white flex items-center justify-center transition-all"
                  aria-label="Twitter"
                >
                  <svg width="16" height="16" className="sm:w-[18px] sm:h-[18px]" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
                  </svg>
                </a>
                <a 
                  href="https://youtube.com" 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-[#2d3436] hover:bg-gray-900 text-white flex items-center justify-center transition-all"
                  aria-label="YouTube"
                >
                  <svg width="16" height="16" className="sm:w-[18px] sm:h-[18px]" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                  </svg>
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Footer */}
      <footer className="bg-[#fceec6] border-t border-gray-300">
        <div className="px-4 sm:px-6 lg:px-[5%] py-6 sm:py-8 md:py-10">
          <div className="max-w-[1400px] mx-auto">
            {/* Logo and Navigation Links */}
            <div className="flex flex-col md:flex-row items-center justify-center gap-4 sm:gap-6 md:gap-8 lg:gap-10">
              <img 
                src="/Images/1000017875-removebg-preview 9.jpg" 
                alt="Soara Logo" 
                className="h-12 sm:h-16 md:h-20 object-contain" 
              />
              
              <nav className="flex flex-wrap justify-center gap-3 sm:gap-4 md:gap-6 lg:gap-8 xl:gap-10">
                <Link to="/rings" className="text-gray-800 hover:text-gray-900 text-xs sm:text-sm font-medium uppercase tracking-wide transition-colors">
                  Rings
                </Link>
                <Link to="/bracelets" className="text-gray-800 hover:text-gray-900 text-xs sm:text-sm font-medium uppercase tracking-wide transition-colors">
                  Bracelets
                </Link>
                <Link to="/about" className="text-gray-800 hover:text-gray-900 text-xs sm:text-sm font-medium uppercase tracking-wide transition-colors">
                  About Us
                </Link>
                <Link to="/contact" className="text-gray-800 hover:text-gray-900 text-xs sm:text-sm font-medium uppercase tracking-wide transition-colors">
                  Contact Us
                </Link>
                <Link to="/terms" className="text-gray-800 hover:text-gray-900 text-xs sm:text-sm font-medium uppercase tracking-wide transition-colors">
                  Terms & Conditions
                </Link>
                <Link to="/privacy" className="text-gray-800 hover:text-gray-900 text-xs sm:text-sm font-medium uppercase tracking-wide transition-colors">
                  Privacy Policy
                </Link>
              </nav>
            </div>
          </div>
        </div>
      </footer>

      {/* Bottom Footer - Dark Section */}
      <div className="bg-[#534741] px-4 sm:px-6 lg:px-[5%] py-5 sm:py-6">
        <div className="max-w-[1400px] mx-auto">
          <div className="flex flex-col lg:flex-row justify-between items-center gap-5 sm:gap-6">
            
            {/* Copyright */}
            <div className="text-center lg:text-left order-2 lg:order-1">
              <p className="text-xs sm:text-sm text-gray-300">
                © 2025 Soara Jewelry. All Rights Reserved.
              </p>
              <p className="text-[10px] sm:text-xs text-gray-400 mt-1">
                Crafted with <span className="text-red-400">❤</span> for jewelry lovers worldwide
              </p>
            </div>

            {/* Payment Methods */}
            <div className="text-center order-1 lg:order-2">
              <p className="text-[10px] sm:text-xs text-gray-400 mb-2 sm:mb-3 uppercase tracking-wider">
                Secure Payment Options
              </p>
              <div className="flex gap-1.5 sm:gap-2 items-center justify-center flex-wrap">
                <div className="w-10 h-7 sm:w-12 sm:h-8 bg-white rounded flex items-center justify-center" title="Mastercard">
                  <svg className="w-6 h-6 sm:w-7 sm:h-7" viewBox="0 0 24 24">
                    <circle cx="9" cy="12" r="7" fill="#EB001B"/>
                    <circle cx="15" cy="12" r="7" fill="#F79E1B"/>
                    <path d="M12 5.5c1.5 1.2 2.5 3 2.5 5s-1 3.8-2.5 5c-1.5-1.2-2.5-3-2.5-5s1-3.8 2.5-5z" fill="#FF5F00"/>
                  </svg>
                </div>
                <div className="w-10 h-7 sm:w-12 sm:h-8 bg-white rounded flex items-center justify-center" title="Visa">
                  <span className="text-[#1434CB] text-sm sm:text-base font-bold">VISA</span>
                </div>
                <div className="w-10 h-7 sm:w-12 sm:h-8 bg-white rounded flex items-center justify-center" title="American Express">
                  <span className="text-[#00579F] text-xs sm:text-sm font-bold">AMEX</span>
                </div>
                <div className="w-10 h-7 sm:w-12 sm:h-8 bg-white rounded flex items-center justify-center" title="Discover">
                  <span className="text-[#FF5F00] text-xs sm:text-sm font-bold">DISC</span>
                </div>
                <div className="w-10 h-7 sm:w-12 sm:h-8 bg-white rounded flex items-center justify-center" title="PayPal">
                  <span className="text-[#003087] text-xs sm:text-sm font-bold">PayPal</span>
                </div>
                <div className="w-10 h-7 sm:w-12 sm:h-8 bg-white rounded flex items-center justify-center" title="Google Pay">
                  <span className="text-gray-700 text-[10px] sm:text-xs font-bold">GPay</span>
                </div>
              </div>
            </div>

            {/* Trust Badges */}
            <div className="flex gap-3 sm:gap-4 items-center order-3">
              <div className="text-center">
                <div className="w-10 h-10 sm:w-12 sm:h-12 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-1">
                  <svg className="w-5 h-5 sm:w-6 sm:h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <p className="text-[9px] sm:text-[10px] text-gray-300 uppercase font-medium">Secure</p>
              </div>
              <div className="text-center">
                <div className="w-10 h-10 sm:w-12 sm:h-12 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-1">
                  <svg className="w-5 h-5 sm:w-6 sm:h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-[9px] sm:text-[10px] text-gray-300 uppercase font-medium">Fast Ship</p>
              </div>
              <div className="text-center">
                <div className="w-10 h-10 sm:w-12 sm:h-12 bg-yellow-500 rounded-full flex items-center justify-center mx-auto mb-1">
                  <svg className="w-5 h-5 sm:w-6 sm:h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                  </svg>
                </div>
                <p className="text-[9px] sm:text-[10px] text-gray-300 uppercase font-medium">Certified</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Footer;
