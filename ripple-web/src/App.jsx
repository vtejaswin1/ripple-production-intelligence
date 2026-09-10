import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";
import { useNavigate } from "react-router-dom";
import { auth } from "./firebase";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState("");
  const navigate = useNavigate();

  const [manifestFile, setManifestFile] = useState(null);
  const [manifestUploading, setManifestUploading] = useState(false);
  const [manifestResult, setManifestResult] = useState(null);
  const [manifestError, setManifestError] = useState("");

  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [expandedImpact, setExpandedImpact] = useState(null);

  const [question, setQuestion] = useState("");
  const [askLoading, setAskLoading] = useState(false);
  const [askAnswer, setAskAnswer] = useState("");
  const [askError, setAskError] = useState("");

  const [production, setProduction] = useState(null);

  useEffect(() => {
  const loadSavedProduction = async () => {
    const savedProductionId = localStorage.getItem(
      "rippleCurrentProductionId"
    );

    if (!savedProductionId) {
      setProduction(null);
      return;
    }

    try {
      const token = await auth.currentUser.getIdToken();

      const response = await fetch(
        `${API_BASE}/api/productions`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(
          "Could not load saved production."
        );
      }

      const data = await response.json();

      const selectedProduction =
        data.productions?.find(
          (item) =>
            item.production_id ===
            Number(savedProductionId)
        );

      if (selectedProduction) {
        setProduction(selectedProduction);
      } else {
        localStorage.removeItem(
          "rippleCurrentProductionId"
        );
      }
    } catch (error) {
      console.error(
        "Failed to restore production:",
        error
      );
    }
  };

  loadSavedProduction();
}, []);

  const [productionName, setProductionName] = useState("");
  const [productionStartDate, setProductionStartDate] = useState("");
  const [productionEndDate, setProductionEndDate] = useState("");
  const [creatingProduction, setCreatingProduction] = useState(false);
  const [productionError, setProductionError] = useState("");

  const currentVersion =
    analysis?.current_version ??
    uploadResult?.version_id ??
    null;

  const changedSceneCount =
    analysis?.status === "CHANGES"
      ? analysis.changed_scenes?.length ?? 0
      : 0;

  const totalConflicts = useMemo(() => {
    if (analysis?.status !== "CHANGES") {
      return 0;
    }

    return (analysis.changed_scenes ?? []).reduce(
      (sum, scene) =>
        sum + (scene.analysis?.conflict_count ?? 0),
      0
    );
  }, [analysis]);

  const totalDependencies = useMemo(() => {
    if (analysis?.status !== "CHANGES") {
      return 0;
    }

    return (analysis.changed_scenes ?? []).reduce(
      (sum, scene) =>
        sum + (scene.dependencies?.length ?? 0),
      0
    );
  }, [analysis]);

  const hasScene42 =
    analysis?.status === "CHANGES" &&
    (analysis.changed_scenes ?? []).some(
      (scene) => Number(scene.scene_number) === 42
    );

  const createProduction = async () => {
  if (
    !productionName.trim() ||
    !productionStartDate ||
    !productionEndDate
  ) {
    setProductionError(
      "Enter a production name, start date, and end date."
    );
    return;
  }

  setCreatingProduction(true);
  setProductionError("");

  try {
    const token = await auth.currentUser.getIdToken();
    const response = await fetch(
      `${API_BASE}/api/productions`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          production_name: productionName.trim(),
          start_date: productionStartDate,
          end_date: productionEndDate,
        }),
      }
    );

    const data = await response.json();

    if (!response.ok || data.status === "error") {
      throw new Error(
        data.message ||
          `Backend returned ${response.status}`
      );
    }

    setProduction(data.production);
    localStorage.setItem(
      "rippleCurrentProductionId",
      String(data.production.production_id)
    );
    setUploadResult(null);
    setAnalysis(null);
    setSelectedFile(null);
  } catch (err) {
    console.error(err);
    setProductionError(
      err.message ||
        "RIPPLE could not create the production."
    );
  } finally {
    setCreatingProduction(false);
  }
};

  const uploadProductionManifest = async () => {
    if (!production) {
      setManifestError("Select or create a production first.");
      return;
    }

    if (!manifestFile) {
      setManifestError("Choose a production manifest JSON file.");
      return;
    }

    setManifestUploading(true);
    setManifestError("");
    setManifestResult(null);

    try {
      const token = await auth.currentUser.getIdToken();
      const manifestText = await manifestFile.text();
      const manifestData = JSON.parse(manifestText);

      const response = await fetch(
        `${API_BASE}/api/productions/${production.production_id}/manifest`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(manifestData),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Production data import failed."
        );
      }

      setManifestResult(data.import);
      setManifestFile(null);
    } catch (err) {
      console.error(err);
      setManifestError(
        err.message ||
          "RIPPLE could not import the production manifest."
      );
    } finally {
      setManifestUploading(false);
    }
  };

  const uploadScript = async () => {
    if (!production) {
      setUploadError("Create a production first.");
      return;
    }

    if (!selectedFile) {
      setUploadError("Choose a screenplay file first.");
      return;
    }

    setUploading(true);
    setUploadError("");
    setUploadResult(null);
    setAnalysis(null);
    setError("");
    setAskAnswer("");
    setAskError("");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      const token = await auth.currentUser.getIdToken();

      const response = await fetch(
        `${API_BASE}/api/scripts/upload?production_id=${production.production_id}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok || data.status === "error") {
        throw new Error(
          data.message ||
            `Backend returned ${response.status}`
        );
      }

      setUploadResult(data);
      setSelectedFile(null);
    } catch (err) {
      console.error(err);
      setUploadError(
        err.message ||
          "RIPPLE could not upload this script."
      );
    } finally {
      setUploading(false);
    }
  };

  const analyzeRipple = async () => {
    if (!production) {
      setError("Create a production first.");
      return;
    }

    setLoading(true);
    setError("");
    setAnalysis(null);
    setExpandedImpact(null);
    setAskAnswer("");
    setAskError("");

    try {
      const token = await auth.currentUser.getIdToken();
      const response = await fetch(
  `${API_BASE}/api/scripts/analyze?production_id=${production.production_id}`,
  {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  }
);

      if (!response.ok) {
        throw new Error(
          `Backend returned ${response.status}`
        );
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      console.error(err);
      setError(
        "RIPPLE could not analyze the latest script. Check that the FastAPI backend is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleAskRipple = async () => {
    if (!question.trim()) {
      return;
    }

    setAskLoading(true);
    setAskAnswer("");
    setAskError("");

    try {
      /*
        Current demo endpoint is grounded in Scene 42.
        Keep this panel visible only when Scene 42 is part
        of the latest changed-scene analysis.
      */
      const response = await fetch(
        `${API_BASE}/api/scenes/42/ask`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: question.trim(),
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          `Backend returned ${response.status}`
        );
      }

      const data = await response.json();
      setAskAnswer(data.answer);
    } catch (err) {
      console.error(err);
      setAskError(
        "RIPPLE could not get a Gemini response. Check that the backend is running."
      );
    } finally {
      setAskLoading(false);
    }
  };

  const renderValue = (value) => {
    if (value === null || value === undefined) {
      return "—";
    }

    if (Array.isArray(value)) {
      return value.length ? value.join(", ") : "—";
    }

    return String(value);
  };

  const conflictIcon = (type) => {
    if (type === "ACTOR_AVAILABILITY") return "◉";
    if (type === "LOCATION_TYPE") return "◇";
    if (type === "NIGHT_SHOOT") return "☾";
    if (type === "DAY_SHOOT") return "☀";
    if (type === "CAST_DEPENDENCY") return "◎";
    return "!";
  };

  return (
    <div className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <header className="topbar">
        <div className="brand">
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

        <div className="topbar-right">
          <div className="status-pill">
            <span className="status-dot" />
            Intelligence Engine Online
          </div>

          <button
            className="avatar avatar-button"
            onClick={() => navigate("/profile")}
            title="Open profile"
          >
            {production?.production_name
              ? production.production_name
                  .split(" ")
                  .slice(0, 2)
                  .map((part) => part[0])
                  .join("")
                  .toUpperCase()
              : "RP"}
          </button>

        </div>
      </header>

      <main className="dashboard">
        <section className="hero-section">
          <div>
            <div className="eyebrow">
              {production?.production_name?.toUpperCase() ?? "RIPPLE"}
              {currentVersion
                ? ` · REVISION ${currentVersion}`
                : production
                  ? " · SCRIPT INTELLIGENCE"
                  : " · NEW PRODUCTION"}
            </div>

            <h2>
              One script change.
              <br />
              <span>Every downstream ripple.</span>
            </h2>

            <p className="hero-copy">
              Upload a screenplay revision, compare it with the
              previous version, trace affected production
              dependencies, and surface conflicts before they
              become expensive.
            </p>
          </div>

          <div className="scene-card">
            <div className="scene-card-top">
              <div>
                <span className="scene-label">
                  CURRENT VERSION
                </span>
                <strong>
                  {currentVersion ?? "—"}
                </strong>
              </div>

              <span className="revision-badge">
                {uploadResult
                  ? `${uploadResult.scene_count ?? 0} SCENES`
                  : "READY"}
              </span>
            </div>

            <h3>
              {uploadResult?.filename ??
                "Upload a screenplay"}
            </h3>

            <div className="scene-meta">
              <span>
                {analysis?.status ??
                  "WAITING FOR SCRIPT"}
              </span>
              <span>
                {changedSceneCount} changed
              </span>
              <span>
                {totalConflicts} conflicts
              </span>
            </div>
          </div>
        </section>


        <section className="production-control-section">
          <div className="panel production-control-panel">
            {!production ? (
              <>
                <div className="panel-heading">
                  <div>
                    <span className="section-kicker">
                      START NEW PRODUCTION
                    </span>
                    <h3>Create a production workspace</h3>
                  </div>

                  <span className="change-count">
                    NEW
                  </span>
                </div>

                <div className="production-form">
                  <input
                    type="text"
                    placeholder="Production name"
                    value={productionName}
                    onChange={(event) =>
                      setProductionName(event.target.value)
                    }
                  />

                  <div className="production-date-row">
                    <div>
                      <label>Start date</label>
                      <input
                        type="date"
                        value={productionStartDate}
                        onChange={(event) =>
                          setProductionStartDate(
                            event.target.value
                          )
                        }
                      />
                    </div>

                    <div>
                      <label>End date</label>
                      <input
                        type="date"
                        value={productionEndDate}
                        onChange={(event) =>
                          setProductionEndDate(
                            event.target.value
                          )
                        }
                      />
                    </div>
                  </div>

                  <button
                    className="analyze-button"
                    onClick={createProduction}
                    disabled={creatingProduction}
                  >
                    {creatingProduction ? (
                      <>
                        <span className="spinner" />
                        Creating production...
                      </>
                    ) : (
                      <>
                        <span className="button-icon">＋</span>
                        Start Production
                      </>
                    )}
                  </button>

                  {productionError && (
                    <div className="error-box">
                      {productionError}
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="active-production-box">
                <div>
                  <span className="section-kicker">
                    ACTIVE PRODUCTION
                  </span>
                  <h3>{production.production_name}</h3>
                  <p>
                    Production #{production.production_id} ·{" "}
                    {production.start_date} → {production.end_date}
                  </p>
                </div>

                <span className="live-label">
                  ACTIVE
                </span>
              </div>
            )}
          </div>
        </section>

        <section className="panel manifest-panel">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">PRODUCTION DATA</span>
              <h3>Import production logistics</h3>
            </div>

            <span className="change-count">JSON</span>
          </div>

          <div className="script-upload-box">
            <input
              id="manifest-file"
              type="file"
              accept=".json,application/json"
              onChange={(event) => {
                setManifestFile(event.target.files?.[0] ?? null);
                setManifestError("");
              }}
            />

            <label
              htmlFor="manifest-file"
              className="script-file-label"
            >
              <span className="upload-icon">⇧</span>

              <div>
                <strong>
                  {manifestFile
                    ? manifestFile.name
                    : "Choose production manifest"}
                </strong>

                <p>
                  Import actors, availability, locations,
                  constraints, scene schedules, cast links,
                  and location dependencies.
                </p>
              </div>
            </label>
          </div>

          <button
            className={`analyze-button ${
              manifestUploading ? "loading" : ""
            }`}
            onClick={uploadProductionManifest}
            disabled={
              manifestUploading ||
              !production ||
              !manifestFile
            }
          >
            {manifestUploading ? (
              <>
                <span className="spinner" />
                Importing production data...
              </>
            ) : (
              <>
                <span className="button-icon">＋</span>
                Import Production Data
              </>
            )}
          </button>

          {manifestError && (
            <div className="error-box">
              {manifestError}
            </div>
          )}

          {manifestResult && (
            <div className="upload-success-box">
              <span>✓</span>

              <div>
                <strong>
                  Production logistics imported
                </strong>

                <p>
                  {manifestResult.actors_imported} actors ·{" "}
                  {manifestResult.locations_imported} locations ·{" "}
                  {manifestResult.scenes_imported} scenes ·{" "}
                  {manifestResult.location_dependencies} dependencies
                </p>
              </div>
            </div>
          )}
        </section>

        <section className="workspace-grid">
          <div className="panel revision-panel">
            <div className="panel-heading">
              <div>
                <span className="section-kicker">
                  SCRIPT REVISION
                </span>
                <h3>Upload new revision</h3>
              </div>

              <span className="change-count">
                TXT
              </span>
            </div>

            <div className="script-upload-box">
              <input
                id="script-file"
                type="file"
                accept=".txt,text/plain"
                onChange={(event) => {
                  setSelectedFile(
                    event.target.files?.[0] ?? null
                  );
                  setUploadError("");
                }}
              />

              <label
                htmlFor="script-file"
                className="script-file-label"
              >
                <span className="upload-icon">↑</span>

                <div>
                  <strong>
                    {selectedFile
                      ? selectedFile.name
                      : "Choose screenplay"}
                  </strong>
                  <p>
                    {production
                      ? "Upload the first script as a baseline, then upload revisions to detect changes."
                      : "Create a production first, then upload its screenplay."}
                  </p>
                </div>
              </label>
            </div>

            <button
              className={`analyze-button ${
                uploading ? "loading" : ""
              }`}
              onClick={uploadScript}
              disabled={uploading || !production}
            >
              {uploading ? (
                <>
                  <span className="spinner" />
                  Extracting screenplay with Gemini...
                </>
              ) : (
                <>
                  <span className="button-icon">↑</span>
                  {uploadResult
                  ? "Upload Next Revision"
                  : "Upload Baseline"}
                </>
              )}
            </button>

            {uploadError && (
              <div className="error-box">
                {uploadError}
              </div>
            )}

            {uploadResult && (
              <div className="upload-success-box">
                <span>✓</span>

                <div>
                  <strong>
                    Revision {uploadResult.version_id} stored
                  </strong>
                  <p>
                    {uploadResult.version_id === 1
                    ? `${uploadResult.scene_count} scenes extracted. This is your baseline. Upload another revision to compare changes.`
                    : `${uploadResult.scene_count} scenes extracted. You can now analyze Revision ${
                      uploadResult.version_id - 1
                      } → Revision ${uploadResult.version_id}.`}
                  </p>
                </div>
              </div>
            )}

            <button
              className={`analyze-button secondary-analyze-button ${
                loading ? "loading" : ""
              }`}
              onClick={analyzeRipple}
              disabled={
                loading ||
                uploading ||
                !production ||
                !uploadResult ||
                uploadResult.version_id < 2
              }
            >
              {loading ? (
                <>
                  <span className="spinner" />
                  Tracing downstream dependencies...
                </>
              ) : (
                <>
                  <span className="button-icon">⌁</span>
                  Analyze Ripple
                </>
              )}
            </button>

            {error && (
              <div className="error-box">
                {error}
              </div>
            )}
          </div>

          <div className="panel system-panel">
            <div className="panel-heading">
              <div>
                <span className="section-kicker">
                  INTELLIGENCE PIPELINE
                </span>

                <h3>Production systems</h3>
              </div>

              <span className="live-label">LIVE</span>
            </div>

            <div className="dependency-map">
              <div className="dependency-node primary-node">
                <span>Δ</span>
                Revision
              </div>

              <div className="dependency-line line-one" />
              <div className="dependency-line line-two" />
              <div className="dependency-line line-three" />

              <div className="dependency-node actor-node">
                <span>A</span>
                Cast
              </div>

              <div className="dependency-node location-node">
                <span>L</span>
                Location
              </div>

              <div className="dependency-node schedule-node">
                <span>S</span>
                Schedule
              </div>
            </div>

            <div className="engine-stats">
              <div>
                <strong>
                  {changedSceneCount}
                </strong>
                <span>Changed scenes</span>
              </div>

              <div>
                <strong>
                  {totalDependencies}
                </strong>
                <span>Dependencies traced</span>
              </div>

              <div>
                <strong>
                  {totalConflicts}
                </strong>
                <span>Conflicts detected</span>
              </div>
            </div>
          </div>
        </section>

        {!analysis && !loading && (
          <section className="empty-state">
            <div className="pulse-ring">
              <div className="pulse-core">⌁</div>
            </div>

            <h3>Ready to trace the ripple</h3>

            <p>
              {production
                ? "Upload a screenplay, then run the analysis. The first upload becomes the baseline; later revisions are compared automatically."
                : "Create a production first. Then upload its baseline screenplay and future revisions."}
            </p>
          </section>
        )}

        {loading && (
          <section className="analysis-loader">
            <div className="loader-line">
              <span />
            </div>

            <div className="loader-steps">
              <div className="active-step">
                <span>01</span>
                Comparing revisions
              </div>

              <div className="active-step">
                <span>02</span>
                Mapping dependencies
              </div>

              <div className="active-step">
                <span>03</span>
                Testing constraints
              </div>

              <div>
                <span>04</span>
                Preparing recommendations
              </div>
            </div>
          </section>
        )}

        {analysis && (
          <div className="results-section">
            {analysis.status === "NO_UPLOAD" && (
              <section className="empty-state">
                <div className="pulse-ring">
                  <div className="pulse-core">↑</div>
                </div>

                <h3>No script uploaded yet</h3>

                <p>
                  Upload a screenplay to create the
                  production baseline before running change
                  analysis.
                </p>
              </section>
            )}

            {analysis.status === "BASELINE" && (
              <section className="empty-state">
                <div className="pulse-ring">
                  <div className="pulse-core">✓</div>
                </div>

                <h3>Baseline script created</h3>

                <p>
                  Revision {analysis.current_version} is now
                  the baseline. There is no previous revision
                  to compare, so no changes were detected.
                </p>
              </section>
            )}

            {analysis.status === "NO_CHANGES" && (
              <section className="empty-state">
                <div className="pulse-ring">
                  <div className="pulse-core">✓</div>
                </div>

                <h3>No production changes detected</h3>

                <p>
                  Revision {analysis.previous_version} and
                  Revision {analysis.current_version} contain
                  no scene-level changes.
                </p>
              </section>
            )}

            {analysis.status === "CHANGES" && (
              <>
                <section className="results-header">
                  <div>
                    <span className="section-kicker">
                      REVISION ANALYSIS COMPLETE
                    </span>

                    <h2>
                      {changedSceneCount} changed{" "}
                      {changedSceneCount === 1
                        ? "scene"
                        : "scenes"}{" "}
                      detected
                    </h2>

                    <p>
                      Revision {analysis.previous_version} →{" "}
                      Revision {analysis.current_version}
                    </p>
                  </div>

                  <div className="analysis-complete">
                    <span>✓</span>
                    Dependencies traced
                  </div>
                </section>

                {(analysis.changed_scenes ?? []).map(
                  (scene, sceneIndex) => (
                    <section
                      className="panel dynamic-scene-panel"
                      key={`${scene.scene_number}-${sceneIndex}`}
                    >
                      <div className="panel-heading">
                        <div>
                          <span className="section-kicker">
                            {scene.change_type}
                          </span>

                          <h3>
                            Scene {scene.scene_number}
                          </h3>
                        </div>

                        <span className="change-count">
                          {scene.changes?.length ?? 0}{" "}
                          {(scene.changes?.length ?? 0) === 1
                            ? "change"
                            : "changes"}
                        </span>
                      </div>

                      <div className="dynamic-section">
                        <span className="section-kicker">
                          WHAT CHANGED
                        </span>

                        {scene.change_type === "ADDED" && (
                          <div className="status-message">
                            Scene {scene.scene_number} was
                            added in the latest revision.
                          </div>
                        )}

                        {scene.change_type ===
                          "REMOVED" && (
                          <div className="status-message">
                            Scene {scene.scene_number} was
                            removed from the latest revision.
                          </div>
                        )}

                        {(scene.changes?.length ?? 0) > 0 && (
                          <div className="changes-list">
                            {scene.changes.map(
                              (change, index) => (
                                <div
                                  className="change-row"
                                  key={`${change.field}-${index}`}
                                >
                                  <div className="change-label">
                                    {change.field
                                      .replaceAll("_", " ")
                                      .toUpperCase()}
                                  </div>

                                  <div className="change-values">
                                    <span className="before-value">
                                      {renderValue(
                                        change.before
                                      )}
                                    </span>

                                    <span className="arrow">
                                      →
                                    </span>

                                    <span className="after-value">
                                      {renderValue(
                                        change.after
                                      )}
                                    </span>
                                  </div>
                                </div>
                              )
                            )}
                          </div>
                        )}
                      </div>

                      {scene.change_type !== "REMOVED" && (
                        <div className="dynamic-section">
                          <span className="section-kicker">
                            DEPENDENCIES
                          </span>

                          {(scene.dependencies?.length ??
                            0) === 0 ? (
                            <div className="status-message">
                              No registered production
                              dependencies were found for this
                              scene.
                            </div>
                          ) : (
                            <div className="dependency-results-grid">
                              {scene.dependencies.map(
                                (dependency, index) => (
                                  <div
                                    className="dependency-result-card"
                                    key={`${dependency.dependency_type}-${dependency.dependency_id}-${index}`}
                                  >
                                    <div className="dependency-result-top">
                                      <span>
                                        {
                                          dependency.dependency_type
                                        }
                                      </span>

                                      <span className="dependency-status">
                                        {dependency.status}
                                      </span>
                                    </div>

                                    <strong>
                                      {
                                        dependency.dependency_name
                                      }
                                    </strong>

                                    <p>
                                      {dependency.evidence}
                                    </p>
                                  </div>
                                )
                              )}
                            </div>
                          )}
                        </div>
                      )}

                      {scene.analysis && (
                        <div className="dynamic-section">
                          <div className="dynamic-analysis-heading">
                            <div>
                              <span className="section-kicker">
                                DOWNSTREAM IMPACT
                              </span>

                              <h3>
                                {scene.analysis.status ===
                                "NO_CONFLICTS"
                                  ? "No production conflicts found"
                                  : `${
                                      scene.analysis
                                        .conflict_count
                                    } production ${
                                      scene.analysis
                                        .conflict_count === 1
                                        ? "conflict"
                                        : "conflicts"
                                    } detected`}
                              </h3>
                            </div>

                            <span
                              className={`dynamic-status ${
                                scene.analysis.status ===
                                "NO_CONFLICTS"
                                  ? "safe"
                                  : "warning"
                              }`}
                            >
                              {scene.analysis.status ===
                              "NO_CONFLICTS"
                                ? "SAFE"
                                : "ACTION REQUIRED"}
                            </span>
                          </div>

                          {scene.analysis.status ===
                            "NO_CONFLICTS" && (
                            <div className="no-conflict-box">
                              <span className="no-conflict-icon">
                                ✓
                              </span>

                              <div>
                                <strong>
                                  Change detected, but no
                                  downstream production
                                  conflict
                                </strong>

                                <p>
                                  RIPPLE checked the
                                  registered dependencies and
                                  current production
                                  constraints for this scene.
                                </p>
                              </div>
                            </div>
                          )}

                          {(scene.analysis.conflicts
                            ?.length ?? 0) > 0 && (
                            <div className="impact-grid">
                              {scene.analysis.conflicts.map(
                                (
                                  conflict,
                                  conflictIndex
                                ) => {
                                  const impactKey = `${sceneIndex}-${conflictIndex}`;
                                  const isExpanded =
                                    expandedImpact ===
                                    impactKey;

                                  return (
                                    <article
                                      className={`impact-card ${
                                        isExpanded
                                          ? "expanded"
                                          : ""
                                      }`}
                                      key={impactKey}
                                      style={{
                                        animationDelay: `${
                                          conflictIndex *
                                          140
                                        }ms`,
                                      }}
                                    >
                                      <div className="impact-top">
                                        <div className="impact-number">
                                          {String(
                                            conflictIndex +
                                              1
                                          ).padStart(
                                            2,
                                            "0"
                                          )}
                                        </div>

                                        <span className="severity-badge">
                                          {
                                            conflict.severity
                                          }
                                        </span>
                                      </div>

                                      <div className="impact-icon">
                                        {conflictIcon(
                                          conflict.conflict_type
                                        )}
                                      </div>

                                      <span className="impact-type">
                                        {conflict.conflict_type.replaceAll(
                                          "_",
                                          " "
                                        )}
                                      </span>

                                      <h3>
                                        {conflict.message}
                                      </h3>

                                      <button
                                        className="evidence-button"
                                        onClick={() =>
                                          setExpandedImpact(
                                            isExpanded
                                              ? null
                                              : impactKey
                                          )
                                        }
                                      >
                                        {isExpanded
                                          ? "Hide evidence"
                                          : "View evidence"}

                                        <span>
                                          {isExpanded
                                            ? "−"
                                            : "+"}
                                        </span>
                                      </button>

                                      {isExpanded && (
                                        <div className="evidence-box">
                                          <span>
                                            EVIDENCE
                                          </span>
                                          <p>
                                            {
                                              conflict.evidence
                                            }
                                          </p>
                                        </div>
                                      )}
                                    </article>
                                  );
                                }
                              )}
                            </div>
                          )}
                        </div>
                      )}

                      {(scene.recovery_options?.length ?? 0) > 0 && (
  <div className="dynamic-section">
    <div className="dynamic-analysis-heading">
      <div>
        <span className="section-kicker">
          RECOVERY OPTIONS
        </span>

        <h3>
          Ranked production alternatives
        </h3>
      </div>

      <span className="dynamic-status safe">
        {scene.recovery_options.length} OPTIONS
      </span>
    </div>

    <div className="recovery-options-grid">
      {scene.recovery_options.map(
        (option, index) => (
          <article
            className="recovery-option-card"
            key={`${scene.scene_number}-${option.location_id}-${index}`}
          >
            <div className="recovery-option-top">
              <span>
                OPTION {index + 1}
              </span>

              <span
                className={`recovery-risk ${
                  option.risk_level?.toLowerCase()
                }`}
              >
                {option.risk_level}
              </span>
            </div>

            <h4>{option.location_name}</h4>

            <div className="recovery-option-details">
              <div>
                <span>START</span>
                <strong>
                  {option.start_time}
                </strong>
              </div>

              <div>
                <span>END</span>
                <strong>
                  {option.end_time}
                </strong>
              </div>

              <div>
                <span>DELAY</span>
                <strong>
                  {option.delay_minutes} min
                </strong>
              </div>

              <div>
                <span>LOCATION COST</span>
                <strong>
                  $
                  {Number(
                    option.estimated_location_cost
                  ).toLocaleString()}
                </strong>
              </div>
            </div>

            <p className="recovery-option-reason">
              {option.reason}
            </p>
          </article>
        )
      )}
    </div>
  </div>
)}
                    </section>
                  )
                )}

                {totalConflicts > 0 && (
                  <section className="recovery-panel">
                    <div className="recovery-header">
                      <div>
                        <span className="section-kicker">
                          RECOVERY INTELLIGENCE
                        </span>

                        <h2>
                          Recovery options generated
                        </h2>

                        <p>
                          RIPPLE evaluated compatible locations,
                          production timing, registered cast
                          availability, and scene duration to
                          identify feasible recovery alternatives.
                        </p>
                      </div>

                      <div className="risk-chip">
                        <span>LIVE</span>
                        RECOVERY
                      </div>
                    </div>
                  </section>
                )}

                {hasScene42 && (
                  <section className="gemini-panel">
                    <div className="gemini-heading">
                      <div>
                        <span className="section-kicker">
                          ASK RIPPLE
                        </span>

                        <h3>
                          Explore Scene 42 impact
                        </h3>
                      </div>

                      <span className="gemini-badge">
                        GEMINI
                      </span>
                    </div>

                    <p className="gemini-copy">
                      Ask a follow-up question about Scene
                      42. This current demo endpoint is
                      grounded in the Scene 42 ClickHouse
                      intelligence view.
                    </p>

                    <div className="question-row">
                      <input
                        type="text"
                        placeholder="Ask about Scene 42..."
                        value={question}
                        onChange={(event) =>
                          setQuestion(
                            event.target.value
                          )
                        }
                        onKeyDown={(event) => {
                          if (
                            event.key === "Enter"
                          ) {
                            handleAskRipple();
                          }
                        }}
                      />

                      <button
                        onClick={handleAskRipple}
                        disabled={askLoading}
                      >
                        {askLoading
                          ? "Thinking..."
                          : "Ask RIPPLE"}
                      </button>
                    </div>

                    {askError && (
                      <div className="ask-error">
                        {askError}
                      </div>
                    )}

                    {askAnswer && (
                      <div className="gemini-answer">
                        <div className="gemini-answer-header">
                          <span>
                            RIPPLE RESPONSE
                          </span>
                          <span className="answer-status">
                            GEMINI
                          </span>
                        </div>

                        <div className="gemini-answer-content">
                          <ReactMarkdown>
                            {askAnswer}
                          </ReactMarkdown>
                        </div>
                      </div>
                    )}

                    <div className="suggested-questions">
                      <button
                        onClick={() =>
                          setQuestion(
                            "What changed in Scene 42?"
                          )
                        }
                      >
                        What changed?
                      </button>

                      <button
                        onClick={() =>
                          setQuestion(
                            "Which Scene 42 production dependencies are affected?"
                          )
                        }
                      >
                        Which dependencies?
                      </button>

                      <button
                        onClick={() =>
                          setQuestion(
                            "Does Scene 42 create any production conflicts?"
                          )
                        }
                      >
                        Any conflicts?
                      </button>
                    </div>
                  </section>
                )}

                <section className="confidence-bar">
                  <div>
                    <span className="confidence-icon">
                      ✓
                    </span>

                    <div>
                      <strong>
                        Analysis grounded in production data
                      </strong>

                      <p>
                        Script changes and registered
                        production dependencies were
                        verified before impact analysis.
                      </p>
                    </div>
                  </div>

                  <span className="powered-by">
                    Gemini + ClickHouse
                  </span>
                </section>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;