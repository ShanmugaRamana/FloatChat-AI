const express = require('express');
const router = express.Router();
const passport = require('passport');
const User = require('../models/User');

// Route to start the Google authentication
router.get('/google', passport.authenticate('google', {
    scope: ['profile', 'email']
}));

// The callback route after Google has authenticated the user
router.get('/google/callback',
    passport.authenticate('google', { failureRedirect: '/login' }),
    (req, res) => {
        console.log('▶️ Google callback executed');
        console.log('📊 User object:', JSON.stringify(req.user, null, 2));
        console.log('📊 Session pendingGoogleUser:', req.session.pendingGoogleUser);
        
        // Check if this is a new Google user that needs completion
        if (req.user && (req.user.isNewGoogleUser || req.user.needsCompletion)) {
            console.log('➕ New Google user detected - redirecting to complete signup');
            return res.redirect('/auth/google/complete');
        } 
        
        // Existing user - set session and redirect to home
        if (req.user && req.user._id && req.user._id !== 'new_google_signup') {
            console.log('✅ Existing user - setting session and redirecting to home');
            req.session.userId = req.user._id;
            return res.redirect('/home');
        }

        // Fallback - something went wrong
        console.log('❌ Unexpected state in callback - req.user:', req.user);
        res.redirect('/login');
    }
);

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
    console.log('Password provided:', !!password);
    console.log('Confirm password provided:', !!confirmPassword);

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
        // Double-check if user already exists
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

        console.log('✅ Creating new user with data:', { username, email, isVerified });
        
        const newUser = new User({ 
            username, 
            email, 
            password, 
            isVerified: true // Google users are pre-verified
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
        console.error("Error details:", error.message);
        
        // Handle specific MongoDB errors
        if (error.code === 11000) {
            const field = Object.keys(error.keyPattern)[0];
            return res.render('complete-google-signup', {
                username, email,
                error: `A user with that ${field} already exists.`
            });
        }
        
        // Handle validation errors
        if (error.name === 'ValidationError') {
            const errorMessages = Object.values(error.errors).map(e => e.message);
            return res.render('complete-google-signup', {
                username, email,
                error: `Validation error: ${errorMessages.join(', ')}`
            });
        }
        
        // Generic error
        res.render('complete-google-signup', {
            username, email,
            error: 'An error occurred while creating your account. Please try again.'
        });
    }
});

module.exports = router;