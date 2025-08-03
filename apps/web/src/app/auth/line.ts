// /auth/line.ts

export interface LineUserProfile {
    id: string;
    name: string;
    image?: string;
}

// Define the LineProfile interface based on expected properties
export interface LineProfile {
    userId: string;
    displayName: string;
    pictureUrl?: string;
}

export const LineProvider = {
    id: 'line',
    name: 'LINE',
    type: 'oauth' as const,
    version: '2.0',
    clientId: process.env.LINE_CHANNEL_ID!,
    clientSecret: process.env.LINE_CHANNEL_SECRET!,
    authorization: {
        url: 'https://access.line.me/oauth2/v2.1/authorize',
        params: {
            scope: 'profile openid email',
            response_type: 'code',
        }
    },
    token: 'https://api.line.me/oauth2/v2.1/token',
    userinfo: 'https://api.line.me/v2/profile',
    profile(profile: LineProfile): LineUserProfile {
        return {
            id: profile.userId,
            name: profile.displayName,
            image: profile.pictureUrl,
        }
    },
};