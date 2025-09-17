// server.js
const express = require('express');
const path = require('path');
const session = require('express-session');
const MongoStore = require('connect-mongo');
const passport = require('passport');
require('dotenv').config();

// Import configurations and routes
const connectDB = require('./config/db');
require('./config/passport-setup'); // IMPORTANT: Run the passport config
const authRoutes = require('./routes/authRoutes');
const googleAuthRoutes = require('./routes/googleAuthRoutes');

connectDB();

const app = express();
const PORT = process.env.PORT || 3000;

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// --- Global Middleware ---
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.set('trust proxy', 1);

// Session configuration
app.use(session({
    secret: process.env.SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
    store: MongoStore.create({ mongoUrl: process.env.MONGO_URI }),
    cookie: {
        secure: process.env.NODE_ENV === 'production',
        httpOnly: true,
        sameSite: 'lax',
        maxAge: 24 * 60 * 60 * 1000 // 24 hours
    }
}));

// --- Passport Middleware ---
app.use(passport.initialize());
app.use(passport.session());

// --- Debug Middleware for Google Auth ---
const debugMiddleware = (req, res, next) => {
    // Only log for Google auth related routes
    if (req.path.includes('/auth/google') || req.path.includes('/google')) {
        console.log('='.repeat(50));
        console.log('🐛 DEBUG:', new Date().toISOString());
        console.log('📍 Path:', req.path);
        console.log('📍 Method:', req.method);
        console.log('📍 Query:', req.query);
        console.log('📍 Body:', req.body);
        console.log('👤 User:', req.user ? { 
            id: req.user._id, 
            email: req.user.email,
            isNewGoogleUser: req.user.isNewGoogleUser 
        } : 'No user');
        console.log('🔐 Session userId:', req.session.userId);
        console.log('🔐 Session pendingGoogleUser:', req.session.pendingGoogleUser);
        console.log('🔐 Session ID:', req.sessionID);
        console.log('='.repeat(50));
    }
    next();
};

app.use(debugMiddleware);

// --- Mount Routers ---
app.use('/', authRoutes);
app.use('/auth', googleAuthRoutes);

// --- Error Handling Middleware ---
const errorHandler = (err, req, res, next) => {
    console.error('❌ Error Handler triggered:', err.message);
    console.error('❌ Stack:', err.stack);
    console.error('❌ Path:', req.path);
    console.error('❌ Session exists:', !!req.session);
    console.error('❌ User exists:', !!req.user);
    
    if (req.path.includes('/auth/google')) {
        console.log('❌ Google auth error - redirecting to login');
        return res.redirect('/login?error=auth_failed');
    }
    
    res.status(500).send('Something went wrong!');
};

app.use(errorHandler);

// --- 404 Handler ---
app.use((req, res) => {
    console.log('❌ 404 - Path not found:', req.originalUrl);
    res.status(404).send('Page not found');
});

// --- Start Server ---
app.listen(PORT, () => {
    console.log(`🚀 Server running at http://localhost:${PORT}`);
    console.log(`🌍 Environment: ${process.env.NODE_ENV || 'development'}`);
    console.log(`🔗 Google Callback URL: ${process.env.CALLBACK_URL}`);
});