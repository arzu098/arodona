# Adorona - Jewelry E-Commerce Platform

A comprehensive full-stack jewelry e-commerce platform built with FastAPI (Python) and React (JavaScript).

## 🚀 Features

### Customer Features
- Browse jewelry collections (Necklaces, Rings, Earrings, Bracelets, Pendants)
- Advanced product search and filtering
- Shopping cart and wishlist management
- Secure checkout and order tracking
- Customer reviews and ratings
- User profile and order history

### Vendor Features
- Vendor dashboard for business management
- Product listing and inventory management
- Order fulfillment and tracking
- Analytics and sales reporting
- Customer communication tools

### Admin Features
- Comprehensive admin panel
- User and vendor management
- Order oversight and analytics
- System configuration and settings
- Super admin controls

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: MongoDB
- **Authentication**: JWT tokens
- **File Storage**: Local file system with image processing
- **API Documentation**: Swagger/OpenAPI

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: React Context
- **HTTP Client**: Axios
- **Routing**: React Router

## 📁 Project Structure

```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── databases/       # Database models and repositories
│   │   ├── routes/          # API route handlers
│   │   ├── utils/           # Utility functions
│   │   ├── middleware/      # Custom middleware
│   │   └── migrations/      # Database migrations
│   ├── uploads/             # File storage directory
│   └── requirements.txt     # Python dependencies
│
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API service functions
│   │   ├── context/         # React context providers
│   │   ├── utils/           # Utility functions
│   │   └── data/            # Static data
│   ├── public/              # Static assets
│   └── package.json         # Node.js dependencies
│
└── README.md               # Project documentation
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- MongoDB 4.4+

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the backend directory:
   ```env
   MONGODB_URL=mongodb://localhost:27017
   DATABASE_NAME=adorona
   JWT_SECRET_KEY=your-secret-key-here
   JWT_ALGORITHM=HS256
   ```

5. **Start the backend server**
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 5858
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:3003` or `http://localhost:3004`

## 🔧 API Documentation

Once the backend is running, visit `http://localhost:5858/docs` for interactive API documentation.

## 🐛 Recent Bug Fixes

### Image Loading Issues ✅
- Fixed image loading errors in VendorProducts.jsx
- Added graceful fallback for missing product images
- Improved error handling with placeholder displays

### Product Creation Errors ✅
- Enhanced error debugging in VendorAddProduct.jsx
- Added detailed form validation feedback
- Improved API error logging and reporting

### Error Handling Improvements ✅
- Better API response interceptors with detailed logging
- Enhanced user feedback for validation errors
- Network error handling and retry mechanisms

## 🌟 Key Components

### Backend Highlights
- **Product Management**: Comprehensive product CRUD with image handling
- **User Authentication**: JWT-based auth with role-based permissions
- **File Handling**: Image upload, processing, and storage
- **Database Integration**: MongoDB with robust data modeling

### Frontend Highlights
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Component Architecture**: Reusable, modular React components
- **State Management**: Efficient context-based state handling
- **Error Boundaries**: Graceful error handling throughout the app

## 🔒 Security Features

- JWT token authentication
- Role-based access control
- Input validation and sanitization
- File upload security measures
- CORS protection

## 📱 Responsive Design

The application is fully responsive and works seamlessly across:
- Desktop computers
- Tablets
- Mobile phones

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent Python web framework
- React team for the robust frontend library
- Tailwind CSS for the utility-first styling
- MongoDB for the flexible database solution

---

**Adorona** - Crafting beautiful jewelry shopping experiences ✨