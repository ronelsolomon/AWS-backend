import { CognitoUser, CognitoUserPool, AuthenticationDetails, CognitoUserSession } from 'amazon-cognito-identity-js';

const poolData = {
  UserPoolId: process.env.REACT_APP_USER_POOL_ID || '',
  ClientId: process.env.REACT_APP_CLIENT_ID || ''
};

export const userPool = new CognitoUserPool(poolData);

interface SignUpParams {
  email: string;
  password: string;
  name: string;
}

export const signUp = async ({ email, password, name }: SignUpParams): Promise<CognitoUser> => {
  return new Promise((resolve, reject) => {
    const attributeList = [
      {
        Name: 'email',
        Value: email
      },
      {
        Name: 'name',
        Value: name
      }
    ];

    userPool.signUp(email, password, attributeList, [], (err, result) => {
      if (err) {
        reject(err);
        return;
      }
      if (result) {
        resolve(result.user);
      }
    });
  });
};

export const signIn = (email: string, password: string): Promise<CognitoUserSession> => {
  const authenticationDetails = new AuthenticationDetails({
    Username: email,
    Password: password
  });

  const userData = {
    Username: email,
    Pool: userPool
  };

  const cognitoUser = new CognitoUser(userData);

  return new Promise((resolve, reject) => {
    cognitoUser.authenticateUser(authenticationDetails, {
      onSuccess: (session) => {
        localStorage.setItem('token', session.getIdToken().getJwtToken());
        resolve(session);
      },
      onFailure: (err) => {
        reject(err);
      },
      newPasswordRequired: () => {
        // Handle case where user needs to set a new password
        reject(new Error('New password required'));
      }
    });
  });
};

export const signOut = (): void => {
  const user = userPool.getCurrentUser();
  if (user) {
    user.signOut();
  }
  localStorage.removeItem('token');
};

export const getCurrentUser = (): Promise<CognitoUser | null> => {
  return new Promise((resolve) => {
    const user = userPool.getCurrentUser();
    
    if (!user) {
      resolve(null);
      return;
    }

    user.getSession((err: Error | null) => {
      if (err) {
        resolve(null);
        return;
      }
      resolve(user);
    });
  });
};

export const getToken = (): string | null => {
  return localStorage.getItem('token');
};

export const isAuthenticated = async (): Promise<boolean> => {
  try {
    const user = await getCurrentUser();
    return !!user;
  } catch (error) {
    return false;
  }
};
