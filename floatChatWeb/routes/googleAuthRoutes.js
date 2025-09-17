// routes/googleAuthRoutes.js
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
        // LOGGING: Check the message from Passport
        console.log('▶️ Google callback executed. Auth Info:', req.authInfo);

        if (req.authInfo && req.authInfo.message === 'COMPLETE_SIGNUP') {
            console.log('- - -> Redirecting to /auth/google/complete');
            res.redirect('/auth/google/complete');
        } else {
            console.log('✅ Redirecting to /home');
            // Set session for existing user
            req.session.userId = req.user._id;
            res.redirect('/home');
        }
    }
);

// Route to display the password creation page (GET request)
router.get('/google/complete', (req, res) => {
    if (!req.session.googleProfile) {
        console.log('❌ No Google profile in session, redirecting to signup');
        return res.redirect('/signup');
    }

    const { username, email } = req.session.googleProfile;
    console.log('✅ Rendering complete-google-signup page for:', email);
    
    res.render('complete-google-signup', {
        username, 
        email,
        error: null // No error initially
    });
});

// Route to handle the password creation form submission (POST request)
router.post('/google/complete', async (req, res) => {
    if (!req.session.googleProfile) {
        console.log('❌ No Google profile in session during POST');
        return res.redirect('/signup');
    }

    const { password, 'confirm-password': confirmPassword } = req.body;
    const { username, email, isVerified } = req.session.googleProfile;

    console.log('📝 Processing Google signup completion for:', email);

    // 1. Add password confirmation check
    if (password !== confirmPassword) {
        console.log('❌ Password mismatch');
        return res.render('complete-google-signup', {
            username, email,
            error: 'Passwords do not match. Please try again.'
        });
    }

    // 2. Check if password is provided
    if (!password || password.trim() === '') {
        return res.render('complete-google-signup', {
            username, email,
            error: 'Password is required.'
        });
    }

    try {
        // 3. Check if user already exists (additional safety check)
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

        console.log('✅ Creating new user:', email);
        const newUser = new User({ 
            username, 
            email, 
            password, 
            isVerified // This should be true from Google auth
        });
        
        await newUser.save();
        console.log('✅ User saved successfully:', newUser._id);

        // Clear the Google profile from session
        req.session.googleProfile = null;

        // Set the user session
        req.session.userId = newUser._id;
        
        console.log('✅ Redirecting to home');
        res.redirect('/home');

    } catch (error) {
        console.error("❌ Error completing Google signup:", error);
        
        // Handle specific MongoDB errors
        if (error.code === 11000) {
            return res.render('complete-google-signup', {
                username, email,
                error: 'A user with that email or username already exists.'
            });
        }
        
        // For validation errors
        if (error.name === 'ValidationError') {
            const errorMessage = Object.values(error.errors).map(e => e.message).join(', ');
            return res.render('complete-google-signup', {
                username, email,
                error: `Validation error: ${errorMessage}`
            });
        }
        
        // For any other errors
        res.render('complete-google-signup', {
            username, email,
            error: 'An error occurred while creating your account. Please try again.'
        });
    }
});

module.exports = router;