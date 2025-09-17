// routes/authRoutes.js
const express = require('express');
const router = express.Router();
const authController = require('../controllers/authController');

// --- Middleware (moved here for route-specific use) ---
const requireLogin = (req, res, next) => {
    if (!req.session.userId) return res.redirect('/login');
    next();
};

const setNoCache = (req, res, next) => {
    res.setHeader('Cache-Control', 'no-store');
    next();
};

// --- GET Routes (Page Rendering) ---
router.get('/', authController.showLandingPage);
router.get('/login', authController.showLoginPage);
router.get('/signup', authController.showSignupPage);
router.get('/verify-notice', authController.showVerifyNoticePage);
router.get('/home', requireLogin, setNoCache, authController.showHomePage);
router.get('/verify-email', authController.verifyEmail);

// --- POST Routes (Form Submissions) ---
router.post('/signup', authController.signupUser);
router.post('/login', authController.loginUser);
router.post('/logout', authController.logoutUser);
router.post('/resend-verification', authController.resendVerification);

router.get('/dashboard', requireLogin, setNoCache, authController.showDashboardPage);
router.get('/samudura', requireLogin, setNoCache, authController.showSamuduraPage);

module.exports = router;