import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  EmailAuthProvider,
  reauthenticateWithCredential,
  signOut,
  updatePassword,
} from "firebase/auth";

import { auth } from "../firebase";
import "../App.css";

function ProfilePage() {
  const navigate = useNavigate();
  const user = auth.currentUser;
  const [currentProductionId, setCurrentProductionId] = useState(() => {
    const saved = localStorage.getItem("rippleCurrentProductionId");
    return saved ? Number(saved) : null;
  });
  const API_BASE = "http://127.0.0.1:8000";
  const [productions, setProductions] = useState([]);
  const [productionRevisions, setProductionRevisions] = useState({});
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState("");

  const [currentPassword, setCurrentPassword] =
    useState("");
  const [newPassword, setNewPassword] =
    useState("");
  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [passwordLoading, setPasswordLoading] =
    useState(false);
  const [passwordError, setPasswordError] =
    useState("");
  const [passwordSuccess, setPasswordSuccess] =
    useState("");

    useEffect(() => {
  const loadProductionHistory = async () => {
    setHistoryLoading(true);
    setHistoryError("");

    try {
      const token = await auth.currentUser.getIdToken();

      const productionResponse = await fetch(
        `${API_BASE}/api/productions`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!productionResponse.ok) {
        throw new Error("Failed to load productions.");
      }

      const productionData =
        await productionResponse.json();

      const productionList =
        productionData.productions || [];

      setProductions(productionList);

      const revisionEntries =
        await Promise.all(
          productionList.map(
            async (production) => {
              const response = await fetch(
                `${API_BASE}/api/productions/${production.production_id}/revisions`,
                {
                  headers: {
                    Authorization: `Bearer ${token}`,
                  },
                }
              );

              if (!response.ok) {
                throw new Error(
                  `Failed to load revisions for ${production.production_name}.`
                );
              }

              const data =
                await response.json();

              return [
                production.production_id,
                data.revisions || [],
              ];
            }
          )
        );

      setProductionRevisions(
        Object.fromEntries(revisionEntries)
      );
    } catch (error) {
      console.error(error);

      setHistoryError(
        error.message ||
          "Could not load production history."
      );
    } finally {
      setHistoryLoading(false);
    }
  };

  loadProductionHistory();
}, []);

  const handleUseProduction = (production) => {
  localStorage.setItem(
    "rippleCurrentProductionId",
    String(production.production_id)
  );

  setCurrentProductionId(production.production_id);

  navigate("/dashboard");
};

const handleStartFresh = () => {
  localStorage.removeItem("rippleCurrentProductionId");
  setCurrentProductionId(null);
  navigate("/dashboard");
};

const handleDeleteRevision = async (
  productionId,
  versionId,
  versionName
) => {
  const confirmed = window.confirm(
    `Delete ${versionName}?\n\nThis will permanently remove only this revision. The production and other revisions will remain.`
  );

  if (!confirmed) {
    return;
  }

  try {
    const token = await auth.currentUser.getIdToken();
    const response = await fetch(
      `${API_BASE}/api/productions/${productionId}/revisions/${versionId}`,
      {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        }
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "Could not delete revision."
      );
    }

    setProductionRevisions((current) => ({
      ...current,
      [productionId]: (
        current[productionId] || []
      ).filter(
        (revision) =>
          revision.version_id !== versionId
      ),
    }));
  } catch (error) {
    console.error(error);

    alert(
      error.message ||
        "Could not delete the revision."
    );
  }
};



  const handleLogout = async () => {
    try {
      await signOut(auth);
      navigate("/");
    } catch (err) {
      console.error(err);
    }
  };

  const handleChangePassword = async (event) => {
    event.preventDefault();

    setPasswordError("");
    setPasswordSuccess("");

    if (!user?.email) {
      setPasswordError(
        "No email is associated with this account."
      );
      return;
    }

    if (newPassword.length < 6) {
      setPasswordError(
        "New password must be at least 6 characters."
      );
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError(
        "New passwords do not match."
      );
      return;
    }

    setPasswordLoading(true);

    try {
      const credential =
        EmailAuthProvider.credential(
          user.email,
          currentPassword
        );

      await reauthenticateWithCredential(
        user,
        credential
      );

      await updatePassword(
        user,
        newPassword
      );

      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");

      setPasswordSuccess(
        "Password updated successfully."
      );
    } catch (err) {
      console.error(err);

      if (
        err.code ===
        "auth/invalid-credential"
      ) {
        setPasswordError(
          "Your current password is incorrect."
        );
      } else {
        setPasswordError(
          "Could not update your password."
        );
      }
    } finally {
      setPasswordLoading(false);
    }
  };

  const displayName =
    user?.displayName ||
    user?.email?.split("@")[0] ||
    "RIPPLE User";

  const initials = displayName
    .split(" ")
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

  return (
    <div className="profile-page">
      <header className="profile-topbar">
        <button
          className="profile-back-button"
          onClick={() =>
            navigate("/dashboard")
          }
        >
          ← Dashboard
        </button>

        <div className="brand">
          <div className="brand-mark">
            <span />
            <span />
            <span />
          </div>

          <div>
            <h1>RIPPLE</h1>
            <p>
              Production Change Intelligence
            </p>
          </div>
        </div>
      </header>

      <main className="profile-container">
        <section className="profile-hero">
          <div className="profile-avatar-large">
            {initials}
          </div>

          <div>
            <span className="section-kicker">
              PROFILE
            </span>

            <h2>{displayName}</h2>
            <p>{user?.email}</p>
          </div>
        </section>

        <div className="profile-grid">
          <section className="panel profile-panel">
            <div className="panel-heading">
              <div>
                <span className="section-kicker">
                  ACCOUNT
                </span>

                <h3>Account details</h3>
              </div>
            </div>

            <div className="profile-info-list">
              <div>
                <span>Name</span>
                <strong>
                  {displayName}
                </strong>
              </div>

              <div>
                <span>Email</span>
                <strong>
                  {user?.email}
                </strong>
              </div>

              <div>
                <span>Account ID</span>
                <strong className="profile-id">
                  {user?.uid}
                </strong>
              </div>
            </div>

            

            <button
              className="profile-danger-button"
              onClick={handleLogout}
            >
              Log Out
            </button>
          </section>

          <section className="panel profile-panel">
            <div className="panel-heading">
              <div>
                <span className="section-kicker">
                  SECURITY
                </span>

                <h3>Change password</h3>
              </div>
            </div>

            <form
              className="profile-password-form"
              onSubmit={
                handleChangePassword
              }
            >
              <div>
                <label>
                  Current password
                </label>

                <input
                  type="password"
                  value={currentPassword}
                  onChange={(event) =>
                    setCurrentPassword(
                      event.target.value
                    )
                  }
                  required
                />
              </div>

              <div>
                <label>
                  New password
                </label>

                <input
                  type="password"
                  value={newPassword}
                  onChange={(event) =>
                    setNewPassword(
                      event.target.value
                    )
                  }
                  required
                />
              </div>

              <div>
                <label>
                  Confirm new password
                </label>

                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(event) =>
                    setConfirmPassword(
                      event.target.value
                    )
                  }
                  required
                />
              </div>

              <button
                className="auth-primary-button"
                type="submit"
                disabled={
                  passwordLoading
                }
              >
                {passwordLoading
                  ? "Updating..."
                  : "Update Password"}
              </button>
            </form>

            {passwordError && (
              <div className="auth-error">
                {passwordError}
              </div>
            )}

            {passwordSuccess && (
              <div className="auth-success">
                {passwordSuccess}
              </div>
            )}
          </section>
        </div>

        <section className="panel profile-panel profile-productions-panel">
  <div className="panel-heading">
    <div>
      <span className="section-kicker">
        PRODUCTIONS
      </span>

      <h3>Production history</h3>
      <button
  className="start-fresh-button"
  onClick={handleStartFresh}
>
  Start Fresh
</button>
    </div>
  </div>

  {historyLoading && (
    <div className="profile-placeholder">
      <span>LOADING</span>
      <h4>Loading production history...</h4>
    </div>
  )}

  {historyError && (
    <div className="auth-error">
      {historyError}
    </div>
  )}

  {!historyLoading &&
    !historyError &&
    productions.length === 0 && (
      <div className="profile-placeholder">
        <span>NO PRODUCTIONS</span>
        <h4>No production history yet</h4>
        <p>
          Create a production from the dashboard
          and it will appear here.
        </p>
      </div>
    )}

  {!historyLoading &&
    !historyError &&
    productions.length > 0 && (
      <div className="production-history-list">
        {productions.map((production) => {
          const revisions =
            productionRevisions[
              production.production_id
            ] || [];

          return (
            <div
              className="production-history-card"
              key={production.production_id}
            >
              <div className="production-history-header">
                <div>
                  <span className="production-id-label">
                    PRODUCTION #{production.production_id}
                  </span>

                  <h4>
                    {production.production_name}
                  </h4>

                  <p>
                    {production.start_date}
                    {" → "}
                    {production.end_date}
                  </p>
                </div>

                <div className="production-history-actions">
  <span className="production-status-badge">
    {production.status}
  </span>

  {currentProductionId === production.production_id ? (
    <span className="current-production-badge">
      CURRENT
    </span>
  ) : (
    <button
      className="use-production-button"
      onClick={() => handleUseProduction(production)}
    >
      Use Production
    </button>
  )}
</div>

              </div>

              <div className="revision-history-section">
                <div className="revision-history-title">
                  <span>
                    SCRIPT REVISIONS
                  </span>

                  <strong>
                    {revisions.length}
                  </strong>
                </div>

                {revisions.length === 0 ? (
                  <div className="revision-empty">
                    No screenplay revisions uploaded yet.
                  </div>
                ) : (
                  <div className="revision-list">
                    {revisions.map((revision) => (
                      <div
                        className="revision-row"
                        key={revision.version_id}
                      >
                        <div>
                          <strong>
                            {revision.version_name}
                          </strong>

                          <span>
                            {revision.filename}
                          </span>
                        </div>

                        <div className="revision-meta">
                          <span>
                            {revision.scene_count} scenes
                          </span>

                          <span>
                            {revision.uploaded_at}
                          </span>
                          <button
    className="revision-delete-button"
    onClick={() =>
      handleDeleteRevision(
        production.production_id,
        revision.version_id,
        revision.version_name
      )
    }
  >
    Delete
  </button>

                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    )}
</section>


      </main>
    </div>
  );
}

export default ProfilePage;