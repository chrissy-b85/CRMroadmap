import { initAuth0 } from "@auth0/nextjs-auth0";

const auth0 = initAuth0({
  secret: process.env.AUTH0_SECRET!,
  baseURL: process.env.AUTH0_BASE_URL!,
  issuerBaseURL: process.env.AUTH0_ISSUER_BASE_URL!,
  clientID: process.env.AUTH0_CLIENT_ID!,
  clientSecret: process.env.AUTH0_CLIENT_SECRET!,
  authorizationParams: {
    audience: process.env.NEXT_PUBLIC_AUTH0_AUDIENCE,
    scope: "openid profile email",
  },
});

export default auth0;
