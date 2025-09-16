// server.js
const express = require('express');
const path = require('path');
const session = require('express-session');
const MongoStore = require('connect-mongo');
const passport = require('passport'); // <-- Import Passport
require('dotenv').config();

// Import configurations and routes
const connectDB = require('./config/db');
require('./config/passport-setup'); // <-- IMPORTANT: Run the passport config
const authRoutes = require('./routes/authRoutes');
const googleAuthRoutes = require('./routes/googleAuthRoutes'); // <-- Import Google routes

connectDB();

const app = express();
const PORT = 3000;

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// --- Global Middleware ---
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.set('trust proxy', 1);

app.use(session({
    secret: process.env.SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
    store: MongoStore.create({ mongoUrl: process.env.MONGO_URI }),
    cookie: {
        secure: process.env.NODE_ENV === 'production', // Use secure cookies in production
        httpOnly: true, // Prevent client-side access
        sameSite: 'lax', // CSRF protection
        maxAge: 24 * 60 * 60 * 1000 // 24 hours
    }
}));

// --- Passport Middleware ---
app.use(passport.initialize());
app.use(passport.session()); // Allows persistent login sessions

// --- Mount Routers ---
app.use('/', authRoutes);
app.use('/auth', googleAuthRoutes); // <-- Mount Google auth routes

app.listen(PORT, () => console.log(`Server running at http://localhost:${PORT}`));