import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

// REACT_APP_API_BASE_URL — API origin (no /api prefix; routes match FastAPI directly).
// Target architecture: separate UI and API hostnames (see docs/PHASE_7_CLOUDFRONT.md).
// Local: http://localhost:3000 (UI) + http://localhost:5001 (API).
// REACT_APP_SKIP_AUTH=true → call /dev-login (local only); reverse by setting false/removing.
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "";
const SKIP_AUTH =
  String(process.env.REACT_APP_SKIP_AUTH || "")
    .trim()
    .toLowerCase() === "true";

function App() {
  const [categoriesFile, setCategoriesFile] = useState(null);
  const [mockDataFile, setMockDataFile] = useState(null);
  const [feedback, setFeedback] = useState({});
  const [userEmail, setUserEmail] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);
  const [testName, setTestName] = useState("");
  const [instructorName, setInstructorName] = useState("");

  // Session check; optional local bypass via REACT_APP_SKIP_AUTH + backend SKIP_AUTH
  useEffect(() => {
    const checkSession = async () => {
      try {
        if (SKIP_AUTH) {
          const dev = await axios.get(`${API_BASE_URL}/dev-login`, {
            withCredentials: true,
          });
          if (dev.data.email) {
            setUserEmail(dev.data.email);
            setIsLoggedIn(true);
            return;
          }
        }

        const response = await axios.get(
          `${API_BASE_URL}/get-session-email`,
          { withCredentials: true }
        );
        if (response.data.email) {
          setUserEmail(response.data.email);
          setIsLoggedIn(true);
        }
      } catch (error) {
        console.warn(
          "Session check failed (normal for first visit):",
          error.message
        );
      } finally {
        setLoading(false);
      }
    };

    checkSession();

    const savedInstructor = sessionStorage.getItem("instructorName");
    if (savedInstructor) setInstructorName(savedInstructor);
  }, []);

  // ✅ Login & logout handlers
  const handleLogin = () => {
    window.location.href = `${API_BASE_URL}/login`;
  };

  const handleLogout = async () => {
    try {
      await axios.get(`${API_BASE_URL}/logout`, { withCredentials: true });
      setUserEmail(null);
      setIsLoggedIn(false);
      setInstructorName("");
      sessionStorage.removeItem("instructorName");
    } catch (error) {
      console.error("Logout error:", error);
    }
  };

  // ✅ File upload handlers
  const handleFileUpload = (e, type) => {
    const file = e.target.files[0];
    if (type === "categories") setCategoriesFile(file);
    if (type === "mockdata") setMockDataFile(file);
  };

  const handleSubmit = async () => {
    if (!categoriesFile || !mockDataFile) {
      alert("Please upload both files first.");
      return;
    }

    try {
      const formDataCategories = new FormData();
      formDataCategories.append("file", categoriesFile);
      await axios.post(`${API_BASE_URL}/upload-categories`, formDataCategories, {
        headers: { "Content-Type": "multipart/form-data" },
        withCredentials: true,
      });

      const formDataMockData = new FormData();
      formDataMockData.append("file", mockDataFile);
      const response = await axios.post(
        `${API_BASE_URL}/upload-mockdata`,
        formDataMockData,
        {
          headers: { "Content-Type": "multipart/form-data" },
          withCredentials: true,
        }
      );

      setFeedback(response.data);
    } catch (error) {
      console.error("File processing error:", error);
      alert("Error processing files. See console for details.");
    }
  };

  const handleSendFeedback = async () => {
    if (Object.keys(feedback).length === 0) {
      alert("No feedback to send. Generate feedback first.");
      return;
    }
    if (!instructorName) {
      alert("Please set your instructor name first.");
      return;
    }

    try {
      const payload = {
        test_name: testName,
        instructor_name: instructorName,
        feedback: feedback,
      };
      await axios.post(`${API_BASE_URL}/send-feedback`, payload, {
        withCredentials: true,
      });
      alert("Feedback sent successfully!");
    } catch (error) {
      console.error("Feedback send error:", error);
      alert("Failed to send feedback. See console for details.");
    }
  };

  // ✅ Grade color helper
  const getGradeColor = (grade) => {
    if (!grade) return "black";
    const g = String(grade).toUpperCase().trim();
    if (!isNaN(g)) {
      const n = parseFloat(g);
      if (n >= 90) return "#007f00";
      if (n >= 80) return "#0066cc";
      if (n >= 70) return "#ff8800";
      if (n >= 60) return "#cc3300";
      return "#cc0000";
    }
    if (g.startsWith("A")) return "#007f00";
    if (g.startsWith("B")) return "#0066cc";
    if (g.startsWith("C")) return "#ff8800";
    if (g.startsWith("D")) return "#cc3300";
    return "#cc0000";
  };

  // ✅ Loading screen
  if (loading) {
    return (
      <div className="App">
        <h1>Student Feedback System</h1>
        <p>Checking login status...</p>
      </div>
    );
  }

  // ✅ Login screen
  if (!isLoggedIn) {
    return (
      <div className="App">
        <h1>Student Feedback System</h1>
        <button onClick={handleLogin}>Login</button>
      </div>
    );
  }

  // ✅ Main interface
  return (
    <div className="App">
      <h1>Student Feedback System</h1>

      <div>
        <p>
          Logged in as: <strong>{userEmail}</strong>
        </p>
        <button onClick={handleLogout}>Logout</button>
      </div>

      {/* Instructor info */}
      <div
        style={{
          border: "1px solid #ddd",
          borderRadius: "8px",
          padding: "15px",
          marginTop: "20px",
          backgroundColor: "#f8f8f8",
        }}
      >
        <h2>Instructor Information</h2>
        <input
          type="text"
          placeholder="Enter your name/title (e.g., Dr. Jane Doe, PT, PhD)"
          value={instructorName}
          onChange={(e) => setInstructorName(e.target.value)}
          style={{
            width: "100%",
            padding: "8px",
            borderRadius: "6px",
            border: "1px solid #ccc",
            marginBottom: "8px",
          }}
          disabled={sessionStorage.getItem("instructorName") !== null}
        />
        {sessionStorage.getItem("instructorName") ? (
          <button
            style={{
              background: "#ccc",
              color: "white",
              padding: "8px 12px",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
            }}
            onClick={() => {
              sessionStorage.removeItem("instructorName");
              setInstructorName("");
            }}
          >
            Edit
          </button>
        ) : (
          <button
            style={{
              background: "#004080",
              color: "white",
              padding: "8px 12px",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
            }}
            onClick={() => {
              if (instructorName.trim()) {
                sessionStorage.setItem("instructorName", instructorName.trim());
                alert("Instructor name saved for this session.");
              } else {
                alert("Please enter your name or title.");
              }
            }}
          >
            Save
          </button>
        )}
      </div>

      <div>
        <h2>Upload Exam</h2>
        <input type="file" onChange={(e) => handleFileUpload(e, "categories")} />
      </div>

      <div>
        <h2>Upload Data File</h2>
        <input type="file" onChange={(e) => handleFileUpload(e, "mockdata")} />
      </div>

      <button onClick={handleSubmit}>Generate Feedback</button>

      <div>
        <h2>Feedback</h2>
        {Object.entries(feedback).length > 0 ? (
          Object.entries(feedback).map(([email, details]) => (
            <div
              key={email}
              style={{
                border: "1px solid #ddd",
                borderRadius: "8px",
                padding: "20px",
                margin: "15px 0",
                backgroundColor: "#fafafa",
              }}
            >
              <h3>{email}</h3>
              <div
                style={{
                  backgroundColor: "#eef5ff",
                  padding: "10px",
                  borderRadius: "6px",
                  border: `2px solid ${getGradeColor(details.predicted_grade)}`,
                }}
              >
                <p
                  style={{
                    fontSize: "20px",
                    fontWeight: "bold",
                    color: getGradeColor(details.predicted_grade),
                    margin: 0,
                  }}
                >
                  Predicted Course Grade:{" "}
                  {details.predicted_grade || "N/A"}
                </p>
              </div>
              <p><strong>Exam Score:</strong> {details.score}</p>
              <p><strong>Summary of Incorrect Answers:</strong></p>
              <ul>
                {details.summary &&
                  Object.entries(details.summary).map(([cat, count]) => (
                    <li key={cat}>
                      {cat}: {count} wrong
                    </li>
                  ))}
              </ul>
              <p><strong>Modules to Focus On:</strong></p>
              <ul>
                {details.categories &&
                  Object.entries(
                    details.categories.reduce((acc, curr) => {
                      acc[curr.category] = acc[curr.category] || new Set();
                      acc[curr.category].add(curr.module);
                      return acc;
                    }, {})
                  ).map(([cat, mods]) => (
                    <li key={cat}>
                      {cat}: {Array.from(mods).join(", ")}
                    </li>
                  ))}
              </ul>
              <p>
                <strong>Needs Most Work:</strong>{" "}
                {details.most_work_category || "N/A"}
              </p>
            </div>
          ))
        ) : (
          <p>No feedback available yet.</p>
        )}
      </div>

      <div
        style={{
          border: "1px solid #ddd",
          borderRadius: "8px",
          padding: "15px",
          marginTop: "20px",
          backgroundColor: "#f0f4ff",
        }}
      >
        <h2>Test Information</h2>
        <input
          type="text"
          placeholder="Enter test name (e.g., Midterm Exam 1)"
          value={testName}
          onChange={(e) => setTestName(e.target.value)}
          style={{
            width: "100%",
            padding: "8px",
            borderRadius: "6px",
            border: "1px solid #ccc",
            marginBottom: "8px",
          }}
        />
        <p style={{ color: "#555", fontStyle: "italic" }}>
          Appears in the email subject line.
        </p>
      </div>

      <button onClick={handleSendFeedback}>Send Feedback to Students</button>
    </div>
  );
}

export default App;
