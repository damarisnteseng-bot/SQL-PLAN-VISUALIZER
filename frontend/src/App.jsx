import { useState } from 'react'
import './App.css'

const API_URL = 'https://sql-plan-visualizer-production.up.railway.app'

function severityColor(severity) {
  if (severity === 'high') return '#dc2626'
  if (severity === 'medium') return '#d97706'
  return '#6b7280'
}

function App() {
  const [sql, setSql] = useState("SELECT * FROM orders WHERE order_status = 'pending'")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  async function handleAnalyze() {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql }),
      })
      const data = await response.json()

      if (data.error) {
        setError(data.error)
      } else {
        setResult(data)
      }
    } catch (err) {
      setError('Could not reach the API. Is the backend server running?')
    } finally {
      setLoading(false)
    }
  }

  function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
  }

  return (
    <div className="app">
      <h1>SQL Query Plan Visualizer</h1>
      <p className="subtitle">
        Paste a query, see how Postgres actually executes it, and get suggested fixes.
      </p>

      <textarea
        className="sql-input"
        value={sql}
        onChange={(e) => setSql(e.target.value)}
        rows={5}
        placeholder="Paste your SQL query here..."
      />

      <button onClick={handleAnalyze} disabled={loading} className="analyze-btn">
        {loading ? (<><span className="spinner"></span>Analyzing...</>) : "Analyze Query"}
      </button>

      {error && (
        <div className="error-box">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className="results">
          <div className="execution-time">
            Execution time: <strong>{result.plan[0]['Execution Time']?.toFixed(2)} ms</strong>
          </div>

          <h2>Issues Found ({result.issues.length})</h2>
          {result.issues.length === 0 && (
            <p className="no-issues">No issues detected. This query looks efficient.</p>
          )}

          {result.issues.map((issue, idx) => (
            <div key={idx} className="issue-card" style={{ borderLeftColor: severityColor(issue.severity) }}>
              <div className="issue-header">
                <span
                  className="severity-badge"
                  style={{ backgroundColor: severityColor(issue.severity) }}
                >
                  {issue.severity}
                </span>
                <span className="issue-type">{issue.type}</span>
              </div>
              <p className="issue-message">{issue.message}</p>
              {issue.suggested_index && (
                <div className="suggested-index">
                  <code>{issue.suggested_index}</code>
                  <button
                    className="copy-btn"
                    onClick={() => copyToClipboard(issue.suggested_index)}
                  >
                    Copy
                  </button>
                </div>
              )}
            </div>
          ))}

          <details className="raw-plan">
            <summary>View raw execution plan (JSON)</summary>
            <pre>{JSON.stringify(result.plan, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  )
}

export default App
