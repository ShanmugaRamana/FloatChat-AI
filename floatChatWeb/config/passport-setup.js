const passport = require('passport');
const GoogleStrategy = require('passport-google-oauth20').Strategy;
const User = require('../models/User');

// Simple serialization - only for real users
passport.serializeUser((user, done) => {
    console.log('🔄 Serializing user:', user._id);
    done(null, user._id);
});

passport.deserializeUser(async (id, done) => {
    try {
        console.log('🔄 Deserializing user ID:', id);
        const user = await User.findById(id);
        console.log('🔄 Found user:', user ? user.email : 'No user');
        done(null, user);
    } catch (error) {
        console.error('❌ Deserialize error:', error);
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
                return done(null, user); // This will work fine with serialization
            } else {
                console.log('➕ New user detected:', profile.emails[0].value);
                
                // Store the Google profile in session
                req.session.pendingGoogleUser = {
                    username: profile.displayName,
                    email: profile.emails[0].value,
                    isVerified: true
                };
                
                // Save session explicitly
                req.session.save((err) => {
                    if (err) {
                        console.error('❌ Session save error:', err);
                        return done(err, false);
                    }
                    console.log('✅ Session saved successfully');
                    
                    // Don't return a user object - this will cause passport to not serialize anything
                    // Instead, we'll handle this in the callback route
                    return done(null, false); // No error, but no user either
                });
            }
        } catch (error) {
            console.error('❌ Error in Google Strategy:', error);
            return done(error, false);
        }
    })
);