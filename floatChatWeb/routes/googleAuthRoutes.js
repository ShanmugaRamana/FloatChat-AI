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
            res.redirect('/home');
        }
    }
);

// Route to display the password creation page
router.post('/google/complete', async (req, res) => {
    if (!req.session.googleProfile) {
        return res.redirect('/signup');
    }

    const { password, 'confirm-password': confirmPassword } = req.body;
    const { username, email, isVerified } = req.session.googleProfile;

    // 1. Add password confirmation check
    if (password !== confirmPassword) {
        return res.render('complete-google-signup', {
            username, email,
            error: 'Passwords do not match. Please try again.' // Pass error message
        });
    }

    try {
        const newUser = new User({ username, email, password, isVerified });
        await newUser.save();

        req.session.googleProfile = null;

        req.login(newUser, (err) => {
            if (err) throw err;
            res.redirect('/home');
        });
    } catch (error) {
        // 2. Add specific check for duplicate user error
        if (error.code === 11000) {
            // MongoDB duplicate key error
            return res.render('complete-google-signup', {
                username, email,
                error: 'A user with that email or username already exists.'
            });
        }
        // For any other errors
        console.error("Error completing Google signup:", error);
        res.redirect('/signup');
    }
});

module.exports = router;