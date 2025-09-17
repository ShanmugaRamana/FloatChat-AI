// config/passport-setup.js
const passport = require('passport');
const GoogleStrategy = require('passport-google-oauth20').Strategy;
const User = require('../models/User');

passport.serializeUser((user, done) => {
    done(null, user.id);
});

passport.deserializeUser(async (id, done) => {
    try {
        const user = await User.findById(id);
        done(null, user);
    } catch (error) {
        done(error, null);
    }
});

passport.use(
    new GoogleStrategy({
        clientID: process.env.GOOGLE_CLIENT_ID,
        clientSecret: process.env.GOOGLE_CLIENT_SECRET,
        callbackURL: process.env.CALLBACK_URL,
        passReqToCallback: true
    },
    async (req, accessToken, refreshToken, profile, done) => {
        try {
            console.log('🔍 Google Strategy: Processing profile:', profile.emails[0].value);
            
            let user = await User.findOne({ email: profile.emails[0].value });

            if (user) {
                console.log('✅ Existing user found in DB:', user.email);
                return done(null, user);
            } else {
                console.log('➕ New user detected. Setting up for signup completion:', profile.emails[0].value);
                
                // Store Google profile data in session for later use
                req.session.googleProfile = {
                    username: profile.displayName,
                    email: profile.emails[0].value,
                    isVerified: true // Google users are pre-verified
                };
                
                // Save the session before proceeding
                req.session.save((err) => {
                    if (err) {
                        console.error('❌ Session save error:', err);
                        return done(err, false);
                    }
                    console.log('✅ Session saved with Google profile');
                    return done(null, false, { message: 'COMPLETE_SIGNUP' });
                });
            }
        } catch (error) {
            console.error('❌ Error in Google Strategy:', error);
            return done(error, false);
        }
    })
);