import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../App.css";
import {
  createUserWithEmailAndPassword,
  updateProfile,
} from "firebase/auth";

import { auth } from "../firebase";

function SignupPage() {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSignup = async (event) => {
    event.preventDefault();

    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setLoading(true);

    try {
      const credential = await createUserWithEmailAndPassword(
        auth,
        email.trim(),
        password
      );

      await updateProfile(credential.user, {
        displayName: name.trim(),
      });

      navigate("/dashboard");
    } catch (err) {
      console.error(err);

      if (err.code === "auth/email-already-in-use") {
        setError("An account already exists with this email.");
      } else if (err.code === "auth/invalid-email") {
        setError("Enter a valid email address.");
      } else if (err.code === "auth/weak-password") {
        setError("Choose a stronger password.");
      } else {
        setError("Could not create your account.");
      }
    } finally {
      setLoading(false);
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
            CREATE ACCOUNT
          </span>

          <h2>Start using RIPPLE</h2>

          <p>
            Create your account to manage productions,
            screenplay revisions, and downstream production analysis.
          </p>
        </div>

        <form
          className="auth-form"
          onSubmit={handleSignup}
        >
          <div>
            <label>Name</label>

            <input
              type="text"
              placeholder="Your name"
              value={name}
              onChange={(event) =>
                setName(event.target.value)
              }
              required
            />
          </div>

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
              placeholder="Minimum 6 characters"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              required
            />
          </div>

          <div>
            <label>Confirm password</label>

            <input
              type="password"
              placeholder="Re-enter password"
              value={confirmPassword}
              onChange={(event) =>
                setConfirmPassword(event.target.value)
              }
              required
            />
          </div>

          <button
            className="auth-primary-button"
            type="submit"
            disabled={loading}
          >
            {loading
              ? "Creating account..."
              : "Create Account"}
          </button>
        </form>

        {error && (
          <div className="auth-error">
            {error}
          </div>
        )}

        <div className="auth-footer">
          <span>Already have an account?</span>

          <Link to="/">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}

export default SignupPage;