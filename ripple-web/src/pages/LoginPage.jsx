import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../App.css";
import {
  signInWithEmailAndPassword,
  sendPasswordResetEmail,
} from "firebase/auth";

import { auth } from "../firebase";

function LoginPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const handleLogin = async (event) => {
    event.preventDefault();

    setLoading(true);
    setError("");
    setMessage("");

    try {
      await signInWithEmailAndPassword(
        auth,
        email.trim(),
        password
      );

      navigate("/dashboard");
    } catch (err) {
      console.error(err);
      setError(
        "Login failed. Check your email and password."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!email.trim()) {
      setError(
        "Enter your email first, then click Forgot password."
      );
      return;
    }

    setError("");
    setMessage("");

    try {
      await sendPasswordResetEmail(
        auth,
        email.trim()
      );

      setMessage(
        "Password reset email sent. Check your inbox."
      );
    } catch (err) {
      console.error(err);
      setError(
        "Could not send the password reset email."
      );
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="brand-mark">
            <span />
            <span />
            <span />
          </div>

          <div>
            <h1>RIPPLE</h1>
            <p>Production Change Intelligence</p>
          </div>
        </div>

        <div className="auth-heading">
          <span className="section-kicker">
            WELCOME BACK
          </span>

          <h2>Sign in to RIPPLE</h2>

          <p>
            Continue to your productions, script revisions,
            and production intelligence.
          </p>
        </div>

        <form
          className="auth-form"
          onSubmit={handleLogin}
        >
          <div>
            <label>Email</label>

            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              required
            />
          </div>

          <div>
            <label>Password</label>

            <input
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              required
            />
          </div>

          <button
            className="auth-primary-button"
            type="submit"
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <button
          className="auth-link-button"
          type="button"
          onClick={handleForgotPassword}
        >
          Forgot password?
        </button>

        {error && (
          <div className="auth-error">
            {error}
          </div>
        )}

        {message && (
          <div className="auth-success">
            {message}
          </div>
        )}

        <div className="auth-footer">
          <span>New to RIPPLE?</span>

          <Link to="/signup">
            Create account
          </Link>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;