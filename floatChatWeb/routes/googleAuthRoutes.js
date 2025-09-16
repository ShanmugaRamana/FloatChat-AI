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
router.get('/google/complete', (req, res) => {
    if (!req.session.googleProfile) {
        return res.redirect('/signup');
    }
    res.render('complete-google-signup', {
        username: req.session.googleProfile.username,
        email: req.session.googleProfile.email
    });
});

// Route to handle the password form submission
router.post('/google/complete', async (req, res) => {
    if (!req.session.googleProfile) {
        return res.redirect('/signup');
    }

    const { password } = req.body;
    const { username, email, isVerified } = req.session.googleProfile;

    try {
        const newUser = new User({ username, email, password, isVerified });
        await newUser.save();

        // Clear the temporary session data
        req.session.googleProfile = null;

        // Log the new user in
        req.login(newUser, (err) => {
            if (err) throw err;
            res.redirect('/home');
        });
    } catch (error) {
        console.error(error);
        res.redirect('/signup');
    }
});

module.exports = router;