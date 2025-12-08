import React, { useState } from 'react';

const ImageSlider = ({ 
  images, 
  productName, 
  className = "w-full h-48", 
  showThumbnails = true, 
  showDots = true, 
  compact = false 
}) => {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [imageLoadErrors, setImageLoadErrors] = useState(new Set());

  // Helper function to get image URL
  const getImageUrl = (image) => {
    if (!image) return null;
    
    let imageUrl = null;
    
    if (typeof image === 'string') {
      imageUrl = image.trim();
    } else if (typeof image === 'object' && image.url) {
      imageUrl = image.url.trim();
    }
    
    if (!imageUrl) return null;
    
    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5858';
    
    if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
      return imageUrl;
    }
    
    if (imageUrl.startsWith('/uploads')) {
      return `${API_BASE_URL}${imageUrl}`;
    }
    
    if (imageUrl.startsWith('/static')) {
      return `${API_BASE_URL}${imageUrl.replace('/static', '/uploads')}`;
    }
    
    if (imageUrl.startsWith('products/') || imageUrl.startsWith('uploads/')) {
      const cleanUrl = imageUrl.startsWith('uploads/') ? imageUrl.substring(8) : imageUrl;
      return `${API_BASE_URL}/uploads/${cleanUrl}`;
    }
    
    return `${API_BASE_URL}/uploads/${imageUrl}`;
  };

  const handleImageError = (index) => {
    setImageLoadErrors(prev => new Set([...prev, index]));
    console.warn('Image failed to load:', getImageUrl(images[index]));
  };

  const nextImage = () => {
    setCurrentImageIndex((prev) => (prev + 1) % images.length);
  };

  const prevImage = () => {
    setCurrentImageIndex((prev) => (prev - 1 + images.length) % images.length);
  };

  const goToImage = (index) => {
    setCurrentImageIndex(index);
  };

  if (!images || images.length === 0) {
    return (
      <div className={`${className} bg-gray-200 flex items-center justify-center rounded-lg`}>
        <div className="text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p className="mt-2 text-sm text-gray-500">No Image</p>
        </div>
      </div>
    );
  }

  const currentImage = images[currentImageIndex];
  const imageUrl = getImageUrl(currentImage);
  const hasError = imageLoadErrors.has(currentImageIndex);

  return (
    <div className={`${className} relative group rounded-lg overflow-hidden bg-gray-100`}>
      {/* Main Image */}
      {imageUrl && !hasError ? (
        <img
          src={imageUrl}
          alt={currentImage?.alt_text || `${productName} - Image ${currentImageIndex + 1}`}
          className="w-full h-full object-cover"
          onError={() => handleImageError(currentImageIndex)}
        />
      ) : (
        <div className="w-full h-full bg-gray-200 flex items-center justify-center">
          <div className="text-center">
            <svg className="mx-auto h-8 w-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p className="text-xs text-gray-500 mt-1">Error</p>
          </div>
        </div>
      )}

      {/* Navigation Arrows - Only show if more than 1 image */}
      {images.length > 1 && (
        <>
          <button
            onClick={prevImage}
            className="absolute left-2 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 hover:bg-opacity-75 text-white p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <button
            onClick={nextImage}
            className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 hover:bg-opacity-75 text-white p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </>
      )}

      {/* Image Counter */}
      {images.length > 1 && (
        <div className="absolute top-2 right-2 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded">
          {currentImageIndex + 1}/{images.length}
        </div>
      )}

      {/* Dots Indicator - Only show if more than 1 image, less than 6 images, and showDots is true */}
      {images.length > 1 && images.length <= 5 && showDots && (
        <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 flex space-x-1">
          {images.map((_, index) => (
            <button
              key={index}
              onClick={() => goToImage(index)}
              className={`w-2 h-2 rounded-full transition-colors duration-200 ${
                index === currentImageIndex ? 'bg-white' : 'bg-white bg-opacity-50 hover:bg-opacity-75'
              }`}
            />
          ))}
        </div>
      )}

      {/* Image thumbnails - Only show if more than 5 images and showThumbnails is true */}
      {images.length > 5 && showThumbnails && (
        <div className="absolute bottom-2 left-2 right-2 flex space-x-1 overflow-x-auto">
          {images.map((image, index) => {
            const thumbUrl = getImageUrl(image);
            return (
              <button
                key={index}
                onClick={() => goToImage(index)}
                className={`flex-shrink-0 w-8 h-8 rounded border-2 transition-all duration-200 ${
                  index === currentImageIndex ? 'border-white' : 'border-transparent opacity-70 hover:opacity-100'
                }`}
              >
                {thumbUrl && !imageLoadErrors.has(index) ? (
                  <img
                    src={thumbUrl}
                    alt={`Thumb ${index + 1}`}
                    className="w-full h-full object-cover rounded"
                    onError={() => handleImageError(index)}
                  />
                ) : (
                  <div className="w-full h-full bg-gray-300 rounded flex items-center justify-center">
                    <svg className="w-3 h-3 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ImageSlider;