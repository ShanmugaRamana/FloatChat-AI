const express = require('express');
const router = express.Router();
const passport = require('passport');
const User = require('../models/User');

// Route to start the Google authentication
router.get('/google', passport.authenticate('google', {
    scope: ['profile', 'email']
}));

// Custom callback route that handles both success and "no user" cases
router.get('/google/callback', (req, res, next) => {
    passport.authenticate('google', (err, user, info) => {
        console.log('▶️ Custom Google callback executed');
        console.log('📊 Error:', err);
        console.log('📊 User:', user);
        console.log('📊 Info:', info);
        console.log('📊 Session pendingGoogleUser:', req.session.pendingGoogleUser);
        
        if (err) {
            console.error('❌ Authentication error:', err);
            return res.redirect('/login');
        }
        
        if (user) {
            // Existing user - log them in
            console.log('✅ Existing user found - logging in');
            req.logIn(user, (err) => {
                if (err) {
                    console.error('❌ Login error:', err);
                    return res.redirect('/login');
                }
                req.session.userId = user._id;
                return res.redirect('/home');
            });
        } else if (req.session.pendingGoogleUser) {
            // New user - redirect to complete signup
            console.log('➕ New user with pending data - redirecting to complete');
            return res.redirect('/auth/google/complete');
        } else {
            // Something went wrong
            console.log('❌ No user and no pending data - redirecting to login');
            return res.redirect('/login');
        }
    })(req, res, next);
});

// Route to display the password creation page (GET request)
router.get('/google/complete', (req, res) => {
    console.log('📄 GET /auth/google/complete called');
    console.log('Session pendingGoogleUser:', req.session.pendingGoogleUser);
    
    if (!req.session.pendingGoogleUser) {
        console.log('❌ No pending Google user in session');
        return res.redirect('/signup');
    }

    const { username, email } = req.session.pendingGoogleUser;
    console.log('✅ Rendering complete-google-signup page for:', email);
    
    res.render('complete-google-signup', {
        username, 
        email,
        error: null
    });
});

// Route to handle the password creation form submission (POST request)
router.post('/google/complete', async (req, res) => {
    console.log('📝 POST /auth/google/complete called');
    console.log('Session pendingGoogleUser:', req.session.pendingGoogleUser);
    
    if (!req.session.pendingGoogleUser) {
        console.log('❌ No pending Google user in session during POST');
        return res.redirect('/signup');
    }

    const { password, 'confirm-password': confirmPassword } = req.body;
    const { username, email, isVerified } = req.session.pendingGoogleUser;

    console.log('📝 Processing Google signup completion for:', email);

    // Validation checks
    if (!password || password.trim() === '') {
        return res.render('complete-google-signup', {
            username, email,
            error: 'Password is required.'
        });
    }

    if (password !== confirmPassword) {
        console.log('❌ Password mismatch');
        return res.render('complete-google-signup', {
            username, email,
            error: 'Passwords do not match. Please try again.'
        });
    }

    try {
        // Check if user already exists
        const existingUser = await User.findOne({ 
            $or: [{ email }, { username }] 
        });
        
        if (existingUser) {
            console.log('❌ User already exists:', email);
            return res.render('complete-google-signup', {
                username, email,
                error: 'A user with that email or username already exists.'
            });
        }

        console.log('✅ Creating new user:', { username, email, isVerified });
        
        const newUser = new User({ 
            username, 
            email, 
            password, 
            isVerified: true
        });
        
        const savedUser = await newUser.save();
        console.log('✅ User saved successfully with ID:', savedUser._id);

        // Clear the pending Google user from session
        delete req.session.pendingGoogleUser;
        
        // Set the regular user session
        req.session.userId = savedUser._id;
        
        console.log('✅ Session userId set to:', req.session.userId);
        console.log('✅ Redirecting to home');
        
        res.redirect('/home');

    } catch (error) {
        console.error("❌ Error completing Google signup:", error);
        
        if (error.code === 11000) {
            const field = Object.keys(error.keyPattern || {})[0] || 'field';
            return res.render('complete-google-signup', {
                username, email,
                error: `A user with that ${field} already exists.`
            });
        }
        
        if (error.name === 'ValidationError') {
            const errorMessages = Object.values(error.errors).map(e => e.message);
            return res.render('complete-google-signup', {
                username, email,
                error: `Validation error: ${errorMessages.join(', ')}`
            });
        }
        
        res.render('complete-google-signup', {
            username, email,
            error: 'An error occurred while creating your account. Please try again.'
        });
    }
});

module.exports = router;