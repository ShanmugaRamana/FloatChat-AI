// controllers/authController.js
const bcrypt = require('bcrypt');
const crypto = require('crypto');
const User = require('../models/User'); // Note the ../ to go up one directory
const sendEmail = require('../utils/sendEmail');

// --- Page Rendering Functions ---
exports.showLandingPage = (req, res) => res.render('landing', { title: 'floatChat' });
exports.showLoginPage = (req, res) => res.render('login', { title: 'Login' });
exports.showSignupPage = (req, res) => res.render('signup', { title: 'Sign Up' });
exports.showVerifyNoticePage = (req, res) => res.render('verify-notice');
exports.showHomePage = async (req, res) => {
    try {
        const user = await User.findById(req.session.userId);
        if (!user || !user.isVerified) return res.redirect('/login');
        res.render('home', { title: 'Home', user: user });
    } catch (error) {
        res.redirect('/login');
    }
};

// --- User Action Functions ---
exports.signupUser = async (req, res) => {
    const { username, email, password } = req.body;
    try {
        const verificationToken = crypto.randomBytes(32).toString('hex');
        const user = new User({ username, email, password, verificationToken });
        await user.save();

        const verificationURL = `http://localhost:3000/verify-email?token=${verificationToken}`;
        const message = `<p>Please verify your email by clicking this link: <a href="${verificationURL}">Verify Account</a></p>`;

        await sendEmail({
            email: user.email,
            subject: 'floatChat Email Verification',
            html: message,
        });

        res.redirect('/verify-notice');
    } catch (error) {
        console.error(error);
        res.status(500).send('Server error during signup.');
    }
};

exports.verifyEmail = async (req, res) => {
    try {
        const token = req.query.token;
        const user = await User.findOne({ verificationToken: token });
        if (!user) return res.status(400).send('Invalid verification token.');

        user.isVerified = true;
        user.verificationToken = undefined;
        await user.save();

        res.redirect('/login');
    } catch (error) {
        res.status(500).send('Server error during verification.');
    }
};

exports.resendVerification = async (req, res) => {
    try {
        const { email } = req.body;
        const user = await User.findOne({ email });
        if (!user || user.isVerified) return res.redirect('/verify-notice');

        const verificationToken = crypto.randomBytes(32).toString('hex');
        user.verificationToken = verificationToken;
        await user.save();

        const verificationURL = `http://localhost:3000/verify-email?token=${verificationToken}`;
        const message = `<p>You requested a new verification link. Please click here: <a href="${verificationURL}">Verify Account</a></p>`;

        await sendEmail({
            email: user.email,
            subject: 'floatChat - New Verification Link',
            html: message,
        });

        res.redirect('/verify-notice');
    } catch (error) {
        console.error("Resend verification error:", error);
        res.status(500).send('Server error.');
    }
};

exports.loginUser = async (req, res) => {
    const { email, password } = req.body;
    try {
        const user = await User.findOne({ email });
        if (!user) return res.status(400).send('Invalid credentials.');

        const isMatch = await bcrypt.compare(password, user.password);
        if (!isMatch) return res.status(400).send('Invalid credentials.');

        if (!user.isVerified) {
            return res.status(401).send('Please verify your email before logging in.');
        }

        req.session.userId = user._id;
        res.redirect('/home');
    } catch (error) {
        res.status(500).send('Server error during login.');
    }
};

exports.logoutUser = (req, res) => {
    req.session.destroy(err => {
        if (err) return res.redirect('/home');
        res.clearCookie('connect.sid');
        res.redirect('/');
    });
};