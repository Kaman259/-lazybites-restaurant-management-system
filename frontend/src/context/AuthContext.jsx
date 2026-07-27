import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signOut,
  updateProfile,
} from "firebase/auth";

import {
  createApplicationSession,
  getCurrentAccount,
  registerCustomerAccount,
} from "../api/authApi";
import { firebaseAuth } from "../firebase/config";

const AuthContext = createContext(null);

function getDefaultPath(role) {
  if (role === "ADMIN" || role === "STAFF") {
    return "/staff/dashboard";
  }

  if (role === "CUSTOMER") {
    return "/customer";
  }

  return "/login";
}

export function AuthProvider({ children }) {
  const [firebaseUser, setFirebaseUser] = useState(null);
  const [appUser, setAppUser] = useState(null);
  const [customer, setCustomer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sessionError, setSessionError] = useState("");

  const clearLocalSession = useCallback(() => {
    setAppUser(null);
    setCustomer(null);
    setSessionError("");
  }, []);

  const applySession = useCallback((sessionData) => {
    setAppUser(sessionData.user);
    setCustomer(sessionData.customer ?? null);
    setSessionError("");
  }, []);

  const loadCurrentAccount = useCallback(async () => {
    const sessionData = await getCurrentAccount();
    applySession(sessionData);

    return sessionData;
  }, [applySession]);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(
      firebaseAuth,
      async (currentFirebaseUser) => {
        setFirebaseUser(currentFirebaseUser);

        if (!currentFirebaseUser) {
          clearLocalSession();
          setLoading(false);
          return;
        }

        try {
          await currentFirebaseUser.getIdToken(true);
          await loadCurrentAccount();
        } catch (error) {
          clearLocalSession();

          if (error.status !== 404) {
            setSessionError(
              error.message ?? "The account session could not be loaded.",
            );
          }
        } finally {
          setLoading(false);
        }
      },
    );

    return unsubscribe;
  }, [clearLocalSession, loadCurrentAccount]);

  const registerCustomer = useCallback(
    async ({ fullName, email, password, phone, address }) => {
      setSessionError("");

      let createdFirebaseUser = null;

      try {
        const credential = await createUserWithEmailAndPassword(
          firebaseAuth,
          email.trim().toLowerCase(),
          password,
        );

        createdFirebaseUser = credential.user;

        await updateProfile(createdFirebaseUser, {
          displayName: fullName.trim(),
        });

        await createdFirebaseUser.getIdToken(true);

        const sessionData = await registerCustomerAccount({
          full_name: fullName.trim(),
          phone: phone.trim(),
          address: address.trim() || null,
        });

        setFirebaseUser(createdFirebaseUser);
        applySession(sessionData);

        return {
          session: sessionData,
          redirectTo: getDefaultPath(sessionData.user.role),
        };
      } catch (error) {
        if (createdFirebaseUser) {
          try {
            await signOut(firebaseAuth);
          } catch {
            // Firebase logout failure should not hide registration failure.
          }
        }

        clearLocalSession();
        throw error;
      }
    },
    [applySession, clearLocalSession],
  );

  const login = useCallback(
    async ({ email, password }) => {
      setSessionError("");

      try {
        const credential = await signInWithEmailAndPassword(
          firebaseAuth,
          email.trim().toLowerCase(),
          password,
        );

        await credential.user.getIdToken(true);

        const sessionData = await createApplicationSession();

        setFirebaseUser(credential.user);
        applySession(sessionData);

        return {
          session: sessionData,
          redirectTo: getDefaultPath(sessionData.user.role),
        };
      } catch (error) {
        try {
          await signOut(firebaseAuth);
        } catch {
          // The original login error remains more useful.
        }

        clearLocalSession();
        throw error;
      }
    },
    [applySession, clearLocalSession],
  );

  const logout = useCallback(async () => {
    await signOut(firebaseAuth);
    setFirebaseUser(null);
    clearLocalSession();
  }, [clearLocalSession]);

  const resetPassword = useCallback(async (email) => {
    await sendPasswordResetEmail(
      firebaseAuth,
      email.trim().toLowerCase(),
    );
  }, []);

  const refreshSession = useCallback(async () => {
    if (!firebaseAuth.currentUser) {
      clearLocalSession();
      return null;
    }

    await firebaseAuth.currentUser.getIdToken(true);
    return loadCurrentAccount();
  }, [clearLocalSession, loadCurrentAccount]);

  const value = useMemo(
    () => ({
      firebaseUser,
      user: appUser,
      customer,
      loading,
      sessionError,
      isAuthenticated: Boolean(firebaseUser && appUser),
      role: appUser?.role ?? null,
      registerCustomer,
      login,
      logout,
      resetPassword,
      refreshSession,
      clearSessionError: () => setSessionError(""),
      getDefaultPath,
    }),
    [
      firebaseUser,
      appUser,
      customer,
      loading,
      sessionError,
      registerCustomer,
      login,
      logout,
      resetPassword,
      refreshSession,
    ],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }

  return context;
}