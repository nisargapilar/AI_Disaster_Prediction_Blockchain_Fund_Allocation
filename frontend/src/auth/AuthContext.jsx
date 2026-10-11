import { useState, useEffect } from "react";
import {
  loginRequest,
  fetchMe,
  getStoredToken,
  storeToken,
  clearToken,
} from "../api/auth";
import { AuthContext } from "./contextObject";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => getStoredToken());
  const [operator, setOperator] = useState(null);
  const [loading, setLoading] = useState(() => !!getStoredToken());

  // On page load, check that a stored token is still valid
  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    fetchMe(token)
      .then((me) => {
        if (!cancelled) setOperator(me);
      })
      .catch(() => {
        if (!cancelled) {
          clearToken();
          setToken(null);
          setOperator(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  async function login(username, password) {
    const data = await loginRequest(username, password);
    storeToken(data.access_token);
    setToken(data.access_token);
    setOperator({ username: data.username });
  }

  function logout() {
    clearToken();
    setToken(null);
    setOperator(null);
  }

  return (
    <AuthContext.Provider value={{ token, operator, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
